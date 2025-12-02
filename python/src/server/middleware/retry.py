"""
Retry logic with exponential backoff for transient failures.
"""

import asyncio
import time
from typing import Callable, Any, Optional, Type
from structlog import get_logger

logger = get_logger(__name__)


async def retry_async(
    func: Callable,
    *args,
    max_attempts: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    **kwargs
) -> Any:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Result of successful function call
        
    Raises:
        Last exception if all attempts fail
    """
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            result = await func(*args, **kwargs)
            if attempt > 1:
                logger.info(
                    "retry_succeeded",
                    function=func.__name__,
                    attempt=attempt,
                    max_attempts=max_attempts
                )
            return result
        except exceptions as e:
            last_exception = e
            
            if attempt == max_attempts:
                logger.error(
                    "retry_exhausted",
                    function=func.__name__,
                    attempts=attempt,
                    error=str(e)
                )
                raise
            
            # Calculate delay with exponential backoff
            delay = min(initial_delay * (exponential_base ** (attempt - 1)), max_delay)
            
            logger.warning(
                "retry_attempt",
                function=func.__name__,
                attempt=attempt,
                max_attempts=max_attempts,
                delay=delay,
                error=str(e)
            )
            
            await asyncio.sleep(delay)
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


def retry_sync(
    func: Callable,
    *args,
    max_attempts: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    **kwargs
) -> Any:
    """
    Retry a sync function with exponential backoff.
    
    Args:
        func: Sync function to retry
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Result of successful function call
        
    Raises:
        Last exception if all attempts fail
    """
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            result = func(*args, **kwargs)
            if attempt > 1:
                logger.info(
                    "retry_succeeded",
                    function=func.__name__,
                    attempt=attempt,
                    max_attempts=max_attempts
                )
            return result
        except exceptions as e:
            last_exception = e
            
            if attempt == max_attempts:
                logger.error(
                    "retry_exhausted",
                    function=func.__name__,
                    attempts=attempt,
                    error=str(e)
                )
                raise
            
            # Calculate delay with exponential backoff
            delay = min(initial_delay * (exponential_base ** (attempt - 1)), max_delay)
            
            logger.warning(
                "retry_attempt",
                function=func.__name__,
                attempt=attempt,
                max_attempts=max_attempts,
                delay=delay,
                error=str(e)
            )
            
            time.sleep(delay)
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception
