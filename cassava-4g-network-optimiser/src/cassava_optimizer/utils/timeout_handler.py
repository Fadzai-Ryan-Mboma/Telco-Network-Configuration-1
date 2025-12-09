"""
Timeout handler for async operations.

Provides a 45-second timeout wrapper for LLM and API calls.
"""

import asyncio
import functools
import logging
from typing import Any, Callable, TypeVar

from cassava_optimizer.domain.exceptions import TimeoutError as OptimizationTimeoutError

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_TIMEOUT = 45  # seconds


class TimeoutHandler:
    """Handler for managing operation timeouts."""
    
    def __init__(self, timeout_seconds: int = DEFAULT_TIMEOUT) -> None:
        """
        Initialize timeout handler.
        
        Args:
            timeout_seconds: Default timeout in seconds
        """
        self.timeout_seconds = timeout_seconds
    
    async def execute(
        self,
        coro: Any,
        timeout: int | None = None,
        operation_name: str = "operation",
    ) -> Any:
        """
        Execute a coroutine with timeout.
        
        Args:
            coro: Coroutine to execute
            timeout: Override timeout in seconds (None uses default)
            operation_name: Name for logging purposes
            
        Returns:
            Result of the coroutine
            
        Raises:
            OptimizationTimeoutError: If operation times out
        """
        timeout_value = timeout or self.timeout_seconds
        
        try:
            logger.debug(f"Starting {operation_name} with {timeout_value}s timeout")
            result = await asyncio.wait_for(coro, timeout=timeout_value)
            logger.debug(f"{operation_name} completed successfully")
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"{operation_name} timed out after {timeout_value}s")
            raise OptimizationTimeoutError(
                f"{operation_name} timed out after {timeout_value} seconds"
            )


def with_timeout(
    timeout_seconds: int = DEFAULT_TIMEOUT,
    operation_name: str | None = None,
) -> Callable:
    """
    Decorator to add timeout to async functions.
    
    Args:
        timeout_seconds: Timeout in seconds
        operation_name: Name for logging (defaults to function name)
        
    Returns:
        Decorated function
        
    Usage:
        @with_timeout(45, "LLM Analysis")
        async def analyze_network(data):
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            name = operation_name or func.__name__
            
            try:
                logger.debug(f"Starting {name} with {timeout_seconds}s timeout")
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds,
                )
                logger.debug(f"{name} completed successfully")
                return result
                
            except asyncio.TimeoutError:
                logger.error(f"{name} timed out after {timeout_seconds}s")
                raise OptimizationTimeoutError(
                    f"{name} timed out after {timeout_seconds} seconds"
                )
        
        return wrapper
    return decorator


# =============================================================================
# Pre-configured Timeouts
# =============================================================================

# LLM operations typically need more time
LLM_TIMEOUT = 60

# API calls should be faster
API_TIMEOUT = 30

# Database operations should be quick
DB_TIMEOUT = 10


# Pre-configured handlers
llm_timeout = TimeoutHandler(LLM_TIMEOUT)
api_timeout = TimeoutHandler(API_TIMEOUT)
db_timeout = TimeoutHandler(DB_TIMEOUT)


async def with_llm_timeout(coro: Any, operation_name: str = "LLM call") -> Any:
    """Execute with LLM timeout (60s)."""
    return await llm_timeout.execute(coro, operation_name=operation_name)


async def with_api_timeout(coro: Any, operation_name: str = "API call") -> Any:
    """Execute with API timeout (30s)."""
    return await api_timeout.execute(coro, operation_name=operation_name)


async def with_db_timeout(coro: Any, operation_name: str = "Database query") -> Any:
    """Execute with database timeout (10s)."""
    return await db_timeout.execute(coro, operation_name=operation_name)
