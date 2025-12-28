"""
合集服务
提供合集相关的业务逻辑操作
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.services.base import BaseService
from backend.repositories.collection_repository import CollectionRepository
from backend.models.collection import Collection
from backend.schemas.collection import CollectionCreate, CollectionUpdate, CollectionResponse, CollectionListResponse, CollectionFilter
from backend.schemas.base import PaginationParams, PaginationResponse


class CollectionService(BaseService[Collection, CollectionCreate, CollectionUpdate, CollectionResponse]):
    """Collection service with business logic."""
    
    def __init__(self, db: Session):
        repository = CollectionRepository(db)
        super().__init__(repository)
        self.db = db
    
    def create_collection(self, collection_data: CollectionCreate) -> Collection:
        """Create a new collection with business logic."""
        collection_dict = collection_data.model_dump()
        
        # Mapping metadata to collection_metadata
        clip_ids = []
        if 'metadata' in collection_dict:
            metadata = collection_dict.pop('metadata')
            collection_dict['collection_metadata'] = metadata
            if metadata and 'clip_ids' in metadata:
                clip_ids = metadata['clip_ids']
        
        # Create the collection instance
        collection = self.create(**collection_dict)
        
        # Associate clips if any were selected
        if clip_ids:
            from backend.models.clip import Clip
            from backend.models.collection import clip_collection
            
            added_count = 0
            for i, clip_id in enumerate(clip_ids):
                clip = self.db.query(Clip).filter(Clip.id == clip_id).first()
                if clip:
                    # Associate clip with collection in the join table
                    stmt = clip_collection.insert().values(
                        clip_id=clip_id,
                        collection_id=collection.id,
                        order_index=i
                    )
                    self.db.execute(stmt)
                    added_count += 1
            
            if added_count > 0:
                collection.clips_count = added_count
                self.db.add(collection)
                self.db.commit()
                self.db.refresh(collection)
        
        return collection
    
    def update_collection(self, collection_id: str, collection_data: CollectionUpdate) -> Optional[Collection]:
        """Update a collection with business logic."""
        # 获取所有字段，包括None值
        all_data = collection_data.model_dump()
        
        # 过滤掉None值，但保留metadata字段
        update_data = {k: v for k, v in all_data.items() if v is not None or k == 'metadata'}
        
        clip_ids_updated = False
        clip_ids = []
        
        # 如果metadata字段存在，需要合并而不是覆盖
        if 'metadata' in all_data:
            # 获取当前合集的metadata
            current_collection = self.get(collection_id)
            if current_collection:
                current_metadata = getattr(current_collection, 'collection_metadata', {}) or {}
                new_metadata = collection_data.metadata or {}
                
                # Check if clip_ids is in new_metadata
                if new_metadata and 'clip_ids' in new_metadata:
                    clip_ids_updated = True
                    clip_ids = new_metadata['clip_ids']
                
                # 合并metadata，新值覆盖旧值
                merged_metadata = {**current_metadata, **new_metadata}
                # 使用正确的字段名 collection_metadata
                update_data['collection_metadata'] = merged_metadata
                # 移除错误的字段名
                if 'metadata' in update_data:
                    del update_data['metadata']
        
        updated_collection = self.update(collection_id, **update_data)
        
        # Update clip associations if clip_ids were changed
        if clip_ids_updated and updated_collection:
            from backend.models.collection import clip_collection
            from backend.models.clip import Clip
            
            # Remove existing associations
            stmt = clip_collection.delete().where(
                clip_collection.c.collection_id == collection_id
            )
            self.db.execute(stmt)
            
            # Add new associations
            added_count = 0
            for i, clip_id in enumerate(clip_ids):
                clip = self.db.query(Clip).filter(Clip.id == clip_id).first()
                if clip:
                    stmt = clip_collection.insert().values(
                        clip_id=clip_id,
                        collection_id=collection_id,
                        order_index=i
                    )
                    self.db.execute(stmt)
                    added_count += 1
            
            updated_collection.clips_count = added_count
            self.db.add(updated_collection)
            self.db.commit()
            self.db.refresh(updated_collection)
            
        return updated_collection
    
    def delete_collection_with_filesystem_update(self, collection_id: str) -> bool:
        """删除合集并更新文件系统的删除记录"""
        import logging
        import json
        from pathlib import Path
        from datetime import datetime
        from ..core.path_utils import get_project_directory
        
        logger = logging.getLogger(__name__)
        
        # 获取合集信息
        collection = self.get(collection_id)
        if not collection:
            return False
        
        project_id = collection.project_id
        
        # 删除数据库记录
        success = self.delete(collection_id)
        if not success:
            return False
        
        # 更新文件系统的删除记录
        try:
            project_dir = get_project_directory(project_id)
            deleted_collections_file = project_dir / "deleted_collections.json"
            
            # 读取现有的删除记录
            deleted_collections = []
            if deleted_collections_file.exists():
                try:
                    with open(deleted_collections_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        deleted_collections = data.get('deleted_collection_ids', [])
                except Exception as e:
                    logger.warning(f"读取删除记录文件失败: {e}")
            
            # 添加新的删除记录
            if collection_id not in deleted_collections:
                deleted_collections.append(collection_id)
                
                # 保存更新后的删除记录
                deleted_data = {
                    'deleted_collection_ids': deleted_collections,
                    'last_updated': datetime.now().isoformat()
                }
                
                with open(deleted_collections_file, 'w', encoding='utf-8') as f:
                    json.dump(deleted_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已更新删除记录文件: {deleted_collections_file}")
            
        except Exception as e:
            logger.error(f"更新删除记录文件失败: {e}")
            # 即使文件更新失败，数据库删除已经成功，所以返回True
        
        return True
    
    def get_collections_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[Collection]:
        """Get collections by project ID."""
        return self.repository.find_by(project_id=project_id)
    
    def get_collections_paginated(
        self, 
        pagination: PaginationParams,
        filters: Optional[CollectionFilter] = None
    ) -> CollectionListResponse:
        """Get paginated collections with filtering."""
        # Convert filters to dict
        filter_dict = {}
        if filters:
            filter_data = filters.model_dump()
            filter_dict = {k: v for k, v in filter_data.items() if v is not None}
        
        items, pagination_response = self.get_paginated(pagination, filter_dict)
        
        # Convert to response schemas
        collection_responses = []
        for collection in items:
            # 获取clip_ids
            clip_ids = []
            metadata = getattr(collection, 'collection_metadata', {}) or {}
            if metadata and 'clip_ids' in metadata:
                # 直接使用metadata中的clip_ids，它们已经是UUID格式
                clip_ids = metadata['clip_ids']
            
            collection_responses.append(CollectionResponse(
                id=str(getattr(collection, 'id', '')),
                project_id=str(getattr(collection, 'project_id', '')),
                name=str(getattr(collection, 'name', '')),
                description=str(getattr(collection, 'description', '')) if getattr(collection, 'description', None) else None,
                theme=getattr(collection, 'theme', None),
                status=getattr(collection, 'status', 'created').value if hasattr(getattr(collection, 'status', 'created'), 'value') else str(getattr(collection, 'status', 'created')),
                tags=getattr(collection, 'tags', []) or [],
                metadata=getattr(collection, 'collection_metadata', {}) or {},
                video_path=getattr(collection, 'export_path', None),
                thumbnail_path=getattr(collection, 'thumbnail_path', None),
                created_at=getattr(collection, 'created_at', None),
                updated_at=getattr(collection, 'updated_at', None),
                total_clips=getattr(collection, 'clips_count', 0) or 0,
                clip_ids=clip_ids
            ))
        
        return CollectionListResponse(
            items=collection_responses,
            pagination=pagination_response
        ) 