"""
Task management service for background operations
"""

import uuid
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

from ..models import TaskInfo, TaskStatus as TaskStatusEnum
from ..config import get_settings
from ..database import get_db_session

logger = structlog.get_logger()
settings = get_settings()

class TaskManager:
    """Manage background tasks and their status"""
    
    @staticmethod
    async def initialize():
        """Initialize task manager"""
        try:
            logger.info("Task manager initialized")
        except Exception as e:
            logger.error("Failed to initialize task manager", error=str(e))
            raise
    
    @staticmethod
    async def create_document_processing_task(files: List, user_id: str) -> TaskInfo:
        """Create a new document processing task"""
        try:
            task_id = str(uuid.uuid4())
            
            task = TaskInfo(
                id=task_id,
                type="document_processing",
                status=TaskStatusEnum.PENDING,
                progress=0.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                user_id=user_id,
                metadata={
                    "file_count": len(files),
                    "file_names": [f.filename for f in files],
                    "total_size": sum(f.size for f in files)
                }
            )
            
            # Save to database
            await TaskManager._save_task(task)
            
            logger.info("Document processing task created", task_id=task_id, user_id=user_id)
            return task
            
        except Exception as e:
            logger.error("Error creating task", error=str(e), user_id=user_id)
            raise
    
    @staticmethod
    async def create_search_task(query: str, user_id: str, options: Dict[str, Any]) -> TaskInfo:
        """Create a new search task"""
        try:
            task_id = str(uuid.uuid4())
            
            task = TaskInfo(
                id=task_id,
                type="search",
                status=TaskStatusEnum.PENDING,
                progress=0.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                user_id=user_id,
                metadata={
                    "query": query,
                    "options": options
                }
            )
            
            # Save to database
            await TaskManager._save_task(task)
            
            logger.info("Search task created", task_id=task_id, user_id=user_id)
            return task
            
        except Exception as e:
            logger.error("Error creating search task", error=str(e), user_id=user_id)
            raise
    
    @staticmethod
    async def update_task_progress(
        task_id: str,
        progress: float,
        status: Optional[TaskStatusEnum] = None,
        message: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update task progress and status"""
        try:
            async with get_db_session() as session:
                task = await session.query(TaskInfo).filter(TaskInfo.id == task_id).first()
                
                if not task:
                    logger.warning("Task not found for update", task_id=task_id)
                    return False
                
                # Update fields
                task.progress = max(0.0, min(100.0, progress))
                task.updated_at = datetime.utcnow()
                
                if status:
                    task.status = status
                    
                if status == TaskStatusEnum.COMPLETED:
                    task.completed_at = datetime.utcnow()
                    task.progress = 100.0
                
                if message:
                    if "messages" not in task.metadata:
                        task.metadata["messages"] = []
                    task.metadata["messages"].append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": message
                    })
                
                if error_message:
                    task.error_message = error_message
                    task.status = TaskStatusEnum.FAILED
                
                await session.commit()
                
                logger.info(
                    "Task progress updated",
                    task_id=task_id,
                    progress=progress,
                    status=status
                )
                
                return True
                
        except Exception as e:
            logger.error("Error updating task progress", error=str(e), task_id=task_id)
            return False
    
    @staticmethod
    async def get_task_status(task_id: str, user_id: str) -> Optional[TaskInfo]:
        """Get task status by ID"""
        try:
            async with get_db_session() as session:
                task = await session.query(TaskInfo).filter(
                    TaskInfo.id == task_id,
                    TaskInfo.user_id == user_id
                ).first()
                
                return task
                
        except Exception as e:
            logger.error("Error getting task status", error=str(e), task_id=task_id)
            return None
    
    @staticmethod
    async def get_user_tasks(user_id: str, limit: int = 10) -> List[TaskInfo]:
        """Get recent tasks for a user"""
        try:
            async with get_db_session() as session:
                tasks = await session.query(TaskInfo).filter(
                    TaskInfo.user_id == user_id
                ).order_by(TaskInfo.created_at.desc()).limit(limit).all()
                
                return tasks
                
        except Exception as e:
            logger.error("Error getting user tasks", error=str(e), user_id=user_id)
            return []
    
    @staticmethod
    async def get_active_tasks(user_id: Optional[str] = None) -> List[TaskInfo]:
        """Get all active (non-completed) tasks"""
        try:
            async with get_db_session() as session:
                query = session.query(TaskInfo).filter(
                    TaskInfo.status.in_([TaskStatusEnum.PENDING, TaskStatusEnum.PROCESSING])
                )
                
                if user_id:
                    query = query.filter(TaskInfo.user_id == user_id)
                
                tasks = await query.order_by(TaskInfo.created_at.desc()).all()
                return tasks
                
        except Exception as e:
            logger.error("Error getting active tasks", error=str(e))
            return []
    
    @staticmethod
    async def cancel_task(task_id: str, user_id: str) -> bool:
        """Cancel a running task"""
        try:
            async with get_db_session() as session:
                task = await session.query(TaskInfo).filter(
                    TaskInfo.id == task_id,
                    TaskInfo.user_id == user_id,
                    TaskInfo.status.in_([TaskStatusEnum.PENDING, TaskStatusEnum.PROCESSING])
                ).first()
                
                if not task:
                    return False
                
                task.status = TaskStatusEnum.FAILED
                task.error_message = "Task cancelled by user"
                task.updated_at = datetime.utcnow()
                
                await session.commit()
                
                logger.info("Task cancelled", task_id=task_id, user_id=user_id)
                return True
                
        except Exception as e:
            logger.error("Error cancelling task", error=str(e), task_id=task_id)
            return False
    
    @staticmethod
    async def cleanup_old_tasks(days: int = 30) -> int:
        """Clean up old completed tasks"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            async with get_db_session() as session:
                deleted_count = await session.query(TaskInfo).filter(
                    TaskInfo.status.in_([TaskStatusEnum.COMPLETED, TaskStatusEnum.FAILED]),
                    TaskInfo.created_at < cutoff_date
                ).delete()
                
                await session.commit()
                
                logger.info(f"Cleaned up {deleted_count} old tasks")
                return deleted_count
                
        except Exception as e:
            logger.error("Error cleaning up old tasks", error=str(e))
            return 0
    
    @staticmethod
    async def get_task_statistics(user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get task statistics"""
        try:
            async with get_db_session() as session:
                query = session.query(TaskInfo)
                
                if user_id:
                    query = query.filter(TaskInfo.user_id == user_id)
                
                all_tasks = await query.all()
                
                stats = {
                    "total_tasks": len(all_tasks),
                    "by_status": {},
                    "by_type": {},
                    "average_processing_time": 0.0
                }
                
                # Count by status
                for status in TaskStatusEnum:
                    count = len([t for t in all_tasks if t.status == status])
                    stats["by_status"][status.value] = count
                
                # Count by type
                task_types = set(t.type for t in all_tasks)
                for task_type in task_types:
                    count = len([t for t in all_tasks if t.type == task_type])
                    stats["by_type"][task_type] = count
                
                # Calculate average processing time for completed tasks
                completed_tasks = [
                    t for t in all_tasks 
                    if t.status == TaskStatusEnum.COMPLETED and t.completed_at
                ]
                
                if completed_tasks:
                    total_time = sum(
                        (t.completed_at - t.created_at).total_seconds()
                        for t in completed_tasks
                    )
                    stats["average_processing_time"] = total_time / len(completed_tasks)
                
                return stats
                
        except Exception as e:
            logger.error("Error getting task statistics", error=str(e))
            return {}
    
    @staticmethod
    async def _save_task(task: TaskInfo):
        """Save task to database"""
        try:
            async with get_db_session() as session:
                session.add(task)
                await session.commit()
        except Exception as e:
            logger.error("Error saving task", error=str(e), task_id=task.id)
            raise
    
    @staticmethod
    async def cleanup():
        """Cleanup task manager"""
        # Cancel any running tasks
        try:
            active_tasks = await TaskManager.get_active_tasks()
            for task in active_tasks:
                await TaskManager.update_task_progress(
                    task.id,
                    task.progress,
                    TaskStatusEnum.FAILED,
                    error_message="System shutdown"
                )
            
            logger.info("Task manager cleanup completed")
            
        except Exception as e:
            logger.error("Error during task manager cleanup", error=str(e))
