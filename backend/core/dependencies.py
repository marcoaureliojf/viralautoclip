"""
依赖注入配置
提供FastAPI的依赖注入服务
"""

from typing import Generator, Optional
from sqlalchemy.orm import Session
from fastapi import Header

from ..core.database import get_db
from ..services.project_service import ProjectService
from ..services.clip_service import ClipService
from ..services.collection_service import CollectionService
from ..services.task_service import TaskService


def get_project_service(db: Session) -> ProjectService:
    """Get project service with database dependency."""
    return ProjectService(db)


def get_clip_service(db: Session) -> ClipService:
    """Get clip service with database dependency."""
    return ClipService(db)


def get_collection_service(db: Session) -> CollectionService:
    """Get collection service with database dependency."""
    return CollectionService(db)


def get_task_service(db: Session) -> TaskService:
    """Get task service with database dependency."""
    return TaskService(db)


def get_lang(accept_language: Optional[str] = Header(None)) -> str:
    """
    从 Accept-Language 请求头中获取语言设置
    默认为 'zh'
    """
    if not accept_language:
        return "zh"
    
    # 简单的解析逻辑，获取第一个语言
    # 例如: "zh-CN,zh;q=0.9,en;q=0.8" -> "zh"
    primary_lang = accept_language.split(',')[0].split('-')[0].lower()
    
    if primary_lang in ["zh", "en", "pt"]:
        return primary_lang
    
    return "zh"