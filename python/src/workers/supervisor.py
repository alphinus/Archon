"""
Worker Supervisor.
Monitors workers and automatically restarts them on failure.
"""

import asyncio
from typing import List, Dict
from datetime import datetime
from structlog import get_logger

from .base import BaseWorker

logger = get_logger(__name__)

class WorkerSupervisor:
    """
    Supervises background workers and ensures they stay healthy.
    
    Features:
    - Auto-restart crashed workers
    - Exponential backoff for restart delays
    - Health status tracking
    - Graceful shutdown
    """
    
    def __init__(self):
        self.workers: List[BaseWorker] = []
        self._running = False
        self._supervisor_tasks: List[asyncio.Task] = []
        self._worker_health: Dict[str, Dict] = {}
        
    def add_worker(self, worker: BaseWorker):
        """Add a worker to supervision."""
        self.workers.append(worker)
        self._worker_health[worker.name] = {
            "status": "not_started",
            "crashes": 0,
            "last_crash": None,
            "last_success": None
        }
        logger.info("worker_added_to_supervision", worker=worker.name)
        
    async def start(self):
        """Start supervising all workers."""
        self._running = True
        logger.info("worker_supervisor_starting", worker_count=len(self.workers))
        
        # Start supervisor task for each worker
        for worker in self.workers:
            task = asyncio.create_task(self._supervise_worker(worker))
            self._supervisor_tasks.append(task)
            
        # Wait for all supervisor tasks
        await asyncio.gather(*self._supervisor_tasks, return_exceptions=True)
        
    async def stop(self):
        """Stop all workers gracefully."""
        self._running = False
        logger.info("worker_supervisor_stopping")
        
        # Stop all workers
        for worker in self.workers:
            try:
                await worker.stop()
            except Exception as e:
                logger.error("worker_stop_failed", worker=worker.name, error=str(e))
        
        # Cancel supervisor tasks
        for task in self._supervisor_tasks:
            if not task.done():
                task.cancel()
                
        logger.info("worker_supervisor_stopped")
        
    async def _supervise_worker(self, worker: BaseWorker):
        """Supervise a single worker with auto-restart."""
        backoff = 1  # Start with 1 second
        max_backoff = 300  # Max 5 minutes
        
        while self._running:
            try:
                logger.info("worker_starting", worker=worker.name)
                self._worker_health[worker.name]["status"] = "running"
                
                # Run the worker
                await worker.start()
                
                # If we get here, worker exited normally
                logger.info("worker_exited_normally", worker=worker.name)
                self._worker_health[worker.name]["status"] = "stopped"
                self._worker_health[worker.name]["last_success"] = datetime.now().isoformat()
                
                # Reset backoff on successful run
                backoff = 1
                
            except Exception as e:
                # Worker crashed
                logger.error(
                    "worker_crashed",
                    worker=worker.name,
                    error=str(e),
                    backoff=backoff
                )
                
                # Update health
                self._worker_health[worker.name]["status"] = "crashed"
                self._worker_health[worker.name]["crashes"] += 1
                self._worker_health[worker.name]["last_crash"] = datetime.now().isoformat()
                
                # Wait before restarting (exponential backoff)
                if self._running:
                    logger.info(
                        "worker_restarting",
                        worker=worker.name,
                        backoff=backoff
                    )
                    await asyncio.sleep(backoff)
                    
                    # Increase backoff
                    backoff = min(backoff * 2, max_backoff)
                    
    def get_health_status(self) -> Dict[str, Dict]:
        """Get health status of all workers."""
        status = {}
        for worker_name, health in self._worker_health.items():
            status[worker_name] = {
                **health,
                "supervised": True
            }
        return status
    
    def is_healthy(self) -> bool:
        """Check if all workers are healthy."""
        for health in self._worker_health.values():
            if health["status"] not in ["running", "not_started"]:
                return False
        return True
