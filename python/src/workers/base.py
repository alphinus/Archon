"""
Base Worker class for background tasks.
"""

import asyncio
import signal
from abc import ABC, abstractmethod
from typing import Optional
from structlog import get_logger

logger = get_logger(__name__)

class BaseWorker(ABC):
    """
    Abstract base class for background workers.
    Handles lifecycle, graceful shutdown, and error logging.
    """
    
    def __init__(self, name: str, interval_seconds: int = 3600):
        self.name = name
        self.interval_seconds = interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the worker loop."""
        if self._running:
            return
            
        self._running = True
        logger.info("worker_started", worker=self.name, interval=self.interval_seconds)
        
        while self._running:
            try:
                logger.info("worker_run_started", worker=self.name)
                await self.run()
                logger.info("worker_run_completed", worker=self.name)
            except Exception as e:
                logger.error("worker_failed", worker=self.name, error=str(e))
                # Don't crash the loop, just log and wait
                
            # Wait for next interval
            if self._running:
                await asyncio.sleep(self.interval_seconds)
                
    async def stop(self):
        """Stop the worker gracefully."""
        self._running = False
        logger.info("worker_stopping", worker=self.name)
        
    @abstractmethod
    async def run(self):
        """Execute the worker's task. Must be implemented by subclasses."""
        pass
