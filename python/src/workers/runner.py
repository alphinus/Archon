"""
Worker Runner.
Entry point for running background workers.
"""

import asyncio
import signal
import sys
from typing import List
from structlog import get_logger

from src.workers import BaseWorker, MemoryConsolidator, CleanupWorker
from src.workers.supervisor import WorkerSupervisor
from src.events.retry_worker import EventRetryWorker

logger = get_logger(__name__)

class WorkerRunner:
    def __init__(self):
        self.workers: List[BaseWorker] = []
        self._running = False
        
    def add_worker(self, worker: BaseWorker):
        self.workers.append(worker)
        
    async def start(self):
        self._running = True
        logger.info("worker_runner_starting", worker_count=len(self.workers))
        
        # Start all workers
        tasks = [asyncio.create_task(worker.start()) for worker in self.workers]
        
        # Wait for stop signal
        while self._running:
            await asyncio.sleep(1)
            
        # Stop all workers
        logger.info("worker_runner_stopping")
        for worker in self.workers:
            await worker.stop()
            
        # Wait for tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("worker_runner_stopped")
        
    def stop(self):
        self._running = False

async def main():
    supervisor = WorkerSupervisor()
    
    # Add workers
    # In production, intervals would be longer (e.g. 6 hours, 24 hours)
    # For demo/dev, we use shorter intervals
    supervisor.add_worker(MemoryConsolidator(interval_seconds=3600))  # 1 hour
    supervisor.add_worker(CleanupWorker(interval_seconds=86400))      # 24 hours
    supervisor.add_worker(EventRetryWorker(interval_seconds=300))     # 5 minutes
    
    # Handle signals
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(supervisor.stop()))
        
    await supervisor.start()

if __name__ == "__main__":
    asyncio.run(main())
