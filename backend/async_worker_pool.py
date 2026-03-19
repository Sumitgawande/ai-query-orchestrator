"""
Async Worker Pool for Background Tasks
Offloads heavy tasks like embedding generation and document processing
"""

import logging
import asyncio
from typing import Callable, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Async task with metadata"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    func: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    priority: int = 5  # 1=highest, 10=lowest


class AsyncWorkerPool:
    """Thread pool executor for async tasks"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.queue: asyncio.Queue = asyncio.Queue()
        self.tasks: dict[str, Task] = {}
        self.active_tasks: int = 0
        self.workers = []
        self.is_running = False
    
    async def start(self):
        """Start worker pool"""
        self.is_running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        logger.info(f"AsyncWorkerPool started with {self.max_workers} workers")
    
    async def stop(self):
        """Stop worker pool and wait for pending tasks"""
        self.is_running = False
        
        # Wait for all tasks to complete
        pending_count = self.queue.qsize()
        if pending_count > 0:
            logger.info(f"Waiting for {pending_count} pending tasks to complete")
            await self.queue.join()
        
        # Cancel workers
        for worker in self.workers:
            worker.cancel()
        
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("AsyncWorkerPool stopped")
    
    async def submit(
        self,
        func: Callable,
        *args,
        priority: int = 5,
        task_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Submit task to worker pool"""
        task = Task(
            task_id=task_id or str(uuid.uuid4()),
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority
        )
        
        self.tasks[task.task_id] = task
        await self.queue.put(task)
        
        logger.info(f"Task submitted: {task.task_id}")
        return task.task_id
    
    async def get_result(self, task_id: str, timeout: int = 300) -> Any:
        """Wait for task to complete and get result"""
        start_time = datetime.now()
        
        while True:
            if task_id not in self.tasks:
                raise ValueError(f"Task {task_id} not found")
            
            task = self.tasks[task_id]
            
            if task.status == TaskStatus.COMPLETED:
                return task.result
            elif task.status == TaskStatus.FAILED:
                raise Exception(f"Task failed: {task.error}")
            elif task.status == TaskStatus.CANCELLED:
                raise Exception(f"Task was cancelled")
            
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                raise asyncio.TimeoutError(f"Task {task_id} timed out after {timeout}s")
            
            # Wait and retry
            await asyncio.sleep(0.1)
    
    async def _worker(self, worker_id: int):
        """Worker coroutine"""
        while self.is_running:
            try:
                task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                
                self.active_tasks += 1
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                
                logger.info(f"Worker {worker_id} executing task {task.task_id}")
                
                try:
                    if asyncio.iscoroutinefunction(task.func):
                        task.result = await task.func(*task.args, **task.kwargs)
                    else:
                        task.result = task.func(*task.args, **task.kwargs)
                    
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    logger.info(f"Task {task.task_id} completed successfully")
                
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.completed_at = datetime.now()
                    logger.error(f"Task {task.task_id} failed: {str(e)}")
                
                finally:
                    self.active_tasks -= 1
                    self.queue.task_done()
            
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")
    
    def get_status(self) -> dict:
        """Get worker pool status"""
        task_counts = {
            "pending": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
        }
        
        return {
            "active_workers": self.max_workers,
            "active_tasks": self.active_tasks,
            "queue_size": self.queue.qsize(),
            "task_counts": task_counts,
            "is_running": self.is_running
        }


# Global worker pool instance
global_worker_pool = AsyncWorkerPool(max_workers=4)
