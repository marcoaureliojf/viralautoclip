"""
任务提交工具
独立的工具函数，避免循环导入问题
"""

import logging
import os
from typing import Dict, Any, Optional
from redis import from_url
from ..core.celery_app import celery_app

logger = logging.getLogger(__name__)

def submit_video_pipeline_task(project_id: str, input_video_path: str, input_srt_path: str) -> Dict[str, Any]:
    """
    提交视频流水线任务
    
    Args:
        project_id: 项目ID
        input_video_path: 输入视频路径
        input_srt_path: 输入SRT路径
        
    Returns:
        任务提交结果
    """
    try:
        logger.info(f"提交视频流水线任务: {project_id}")
        
        # 直接使用celery_app提交任务
        logger.info(f"准备提交任务到队列...")
        logger.info(f"任务名称: backend.tasks.processing.process_video_pipeline")
        logger.info(f"任务参数: {[project_id, input_video_path, input_srt_path]}")
        
        try:
            celery_task = celery_app.send_task(
                'backend.tasks.processing.process_video_pipeline',
                args=[project_id, input_video_path, input_srt_path]
            )
            
            logger.info(f"视频流水线任务已提交: {celery_task.id}")
            logger.info(f"任务状态: {celery_task.state}")
            
            # --- CORREÇÃO AQUI: Usar variável de ambiente em vez de localhost ---
            try:
                redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
                r = from_url(redis_url)
                queue_length = r.llen('processing')
                logger.info(f"Redis队列 ({redis_url}) 长度: {queue_length}")
            except Exception as redis_err:
                # Se a verificação de depuração falhar, não paramos o fluxo principal
                logger.warning(f"无法检查Redis队列长度 (调试信息): {redis_err}")
            # --- FIM DA CORREÇÃO ---
            
        except Exception as e:
            logger.error(f"任务提交过程中出现异常: {e}")
            raise
        
        return {
            'success': True,
            'task_id': celery_task.id,
            'status': 'PENDING',
            'message': '视频流水线任务已提交'
        }
        
    except Exception as e:
        logger.error(f"提交视频流水线任务失败: {project_id}, 错误: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': '任务提交失败'
        }

def submit_single_step_task(project_id: str, step: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    提交单个步骤任务
    """
    try:
        logger.info(f"提交单个步骤任务: {project_id}, {step}")
        
        celery_task = celery_app.send_task(
            'tasks.processing.process_single_step',
            args=[project_id, step, config]
        )
        
        logger.info(f"单个步骤任务已提交: {celery_task.id}")
        
        return {
            'success': True,
            'task_id': celery_task.id,
            'step': step,
            'status': 'PENDING',
            'message': f'步骤 {step} 任务已提交'
        }
        
    except Exception as e:
        logger.error(f"提交单个步骤任务失败: {project_id}, {step}, 错误: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': '任务提交失败'
        }