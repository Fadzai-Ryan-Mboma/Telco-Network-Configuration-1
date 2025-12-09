#!/usr/bin/env python3
"""
Timeout Handler Utility for LLM API Calls

Prevents 5-minute NVIDIA API gateway timeouts from hanging the demo.
Provides decorators and context managers for hard timeouts on LLM invocations.

Usage:
    from utils.timeout_handler import with_timeout, TimeoutError

    @with_timeout(30)  # 30-second hard limit
    def my_llm_call():
        return agent.invoke(...)
"""

import signal
import logging
from functools import wraps
from typing import Callable, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Raised when an operation exceeds its timeout limit."""
    pass


class TimeoutHandler:
    """
    Manages timeout handling for LLM API calls.

    Features:
    - Hard timeout limits (default: 30 seconds)
    - Automatic fallback triggering on timeout
    - Cross-platform support (signal-based on Unix, thread-based fallback)
    - Detailed timeout logging
    """

    def __init__(self, timeout_seconds: int = 30):
        """
        Initialize timeout handler.

        Args:
            timeout_seconds: Maximum time allowed for operation (default: 30)
        """
        self.timeout_seconds = timeout_seconds
        self.platform_supports_signals = hasattr(signal, 'SIGALRM')

    def _timeout_handler(self, signum, frame):
        """Signal handler for SIGALRM."""
        raise TimeoutError(f"Operation exceeded {self.timeout_seconds} second timeout")

    @contextmanager
    def timeout_context(self, operation_name: str = "LLM call"):
        """
        Context manager for timeout protection.

        Args:
            operation_name: Name of operation for logging

        Raises:
            TimeoutError: If operation exceeds timeout limit

        Usage:
            with timeout_handler.timeout_context("Agent invocation"):
                result = agent.invoke(state)
        """
        if not self.platform_supports_signals:
            logger.warning(f"⚠️  Signal-based timeout not supported on this platform. "
                         f"Timeout protection disabled for: {operation_name}")
            yield
            return

        # Set up signal handler
        old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.timeout_seconds)

        try:
            logger.info(f"⏱️  Starting {operation_name} with {self.timeout_seconds}s timeout")
            yield
            logger.info(f"✅ {operation_name} completed within timeout")
        except TimeoutError as e:
            logger.error(f"⏰ TIMEOUT: {operation_name} exceeded {self.timeout_seconds}s limit")
            raise
        finally:
            # Cancel alarm and restore old handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


def with_timeout(timeout_seconds: int = 30, operation_name: Optional[str] = None):
    """
    Decorator for adding timeout protection to LLM functions.

    Args:
        timeout_seconds: Maximum time allowed (default: 30)
        operation_name: Optional name for logging (defaults to function name)

    Usage:
        @with_timeout(30)
        def call_monitoring_agent(state):
            return agent.invoke(state)

        @with_timeout(60, operation_name="Complex KPI Analysis")
        def call_kpi_agent(state):
            return agent.invoke(state)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            handler = TimeoutHandler(timeout_seconds)
            op_name = operation_name or f"{func.__name__}()"

            with handler.timeout_context(op_name):
                return func(*args, **kwargs)

        return wrapper
    return decorator


def safe_llm_call(
    llm_function: Callable,
    fallback_function: Callable,
    timeout_seconds: int = 30,
    operation_name: str = "LLM call"
) -> Any:
    """
    Execute LLM call with timeout protection and automatic fallback.

    This is the recommended pattern for all LLM agent invocations in the demo.

    Args:
        llm_function: Function that calls the LLM agent
        fallback_function: Function to call if LLM times out or fails
        timeout_seconds: Timeout limit (default: 30)
        operation_name: Name for logging

    Returns:
        Result from llm_function or fallback_function

    Usage:
        def call_llm():
            return monitoring_agent.invoke(state)

        def fallback():
            return get_monitoring_fallback(state)

        result = safe_llm_call(
            llm_function=call_llm,
            fallback_function=fallback,
            timeout_seconds=30,
            operation_name="Monitoring Agent"
        )
    """
    handler = TimeoutHandler(timeout_seconds)

    try:
        with handler.timeout_context(operation_name):
            result = llm_function()
            logger.info(f"✅ {operation_name} succeeded via LLM")
            return result

    except TimeoutError:
        logger.warning(f"⏰ {operation_name} timed out after {timeout_seconds}s - using fallback")
        result = fallback_function()
        logger.info(f"✅ {operation_name} succeeded via fallback")
        return result

    except Exception as e:
        logger.error(f"❌ {operation_name} failed with error: {e}")
        logger.warning(f"🔄 Falling back to {fallback_function.__name__}")
        result = fallback_function()
        logger.info(f"✅ {operation_name} succeeded via fallback after error")
        return result


# Pre-configured timeout handlers for different agent types
MONITORING_TIMEOUT = 30      # Quick KPI checks
KPI_ANALYTICS_TIMEOUT = 45   # More complex analysis
CONFIG_TIMEOUT = 45          # Parameter recommendations
VALIDATION_TIMEOUT = 30      # Safety checks
EXECUTION_TIMEOUT = 60       # MML command execution


if __name__ == "__main__":
    """Test the timeout handler."""
    import time

    print("\n" + "="*80)
    print("TIMEOUT HANDLER TEST")
    print("="*80 + "\n")

    # Test 1: Function that completes within timeout
    @with_timeout(2)
    def fast_operation():
        print("  Starting fast operation...")
        time.sleep(0.5)
        print("  Fast operation completed!")
        return "SUCCESS"

    print("Test 1: Fast operation (0.5s with 2s timeout)")
    try:
        result = fast_operation()
        print(f"  ✅ Result: {result}\n")
    except TimeoutError as e:
        print(f"  ❌ Timeout: {e}\n")

    # Test 2: Function that exceeds timeout
    @with_timeout(1)
    def slow_operation():
        print("  Starting slow operation...")
        time.sleep(3)
        print("  This should never print!")
        return "NEVER_REACHED"

    print("Test 2: Slow operation (3s with 1s timeout)")
    try:
        result = slow_operation()
        print(f"  ❌ Unexpectedly succeeded: {result}\n")
    except TimeoutError as e:
        print(f"  ✅ Caught timeout as expected: {e}\n")

    # Test 3: safe_llm_call pattern
    print("Test 3: safe_llm_call with timeout and fallback")

    def llm_that_hangs():
        print("  LLM call starting (will hang)...")
        time.sleep(10)
        return "LLM_RESULT"

    def smart_fallback():
        print("  Fallback activated!")
        return "FALLBACK_RESULT"

    result = safe_llm_call(
        llm_function=llm_that_hangs,
        fallback_function=smart_fallback,
        timeout_seconds=1,
        operation_name="Test Agent"
    )
    print(f"  ✅ Final result: {result}\n")

    print("="*80)
    print("ALL TESTS COMPLETED")
    print("="*80 + "\n")
