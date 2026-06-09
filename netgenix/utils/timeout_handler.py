"""
Thread-safe timeout helpers for optimizer agent calls.

These utilities mirror the original optimizer blueprint but avoid signal-based
timeouts so they are safe inside FastAPI worker threads.
"""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Raised when an operation exceeds its configured timeout."""


class TimeoutHandler:
    """Track elapsed time for long-running LLM calls."""

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self._timer: Optional[threading.Timer] = None
        self._timed_out = threading.Event()

    def _timeout_callback(self) -> None:
        self._timed_out.set()
        logger.error("Operation exceeded %s second timeout", self.timeout_seconds)

    @contextmanager
    def timeout_context(self, operation_name: str = "LLM call"):
        self._timed_out.clear()
        self._timer = threading.Timer(self.timeout_seconds, self._timeout_callback)
        self._timer.daemon = True
        self._timer.start()

        try:
            logger.info("Starting %s with %ss timeout", operation_name, self.timeout_seconds)
            yield
            if self._timed_out.is_set():
                raise TimeoutError(f"{operation_name} exceeded {self.timeout_seconds} second timeout")
            logger.info("%s completed within timeout", operation_name)
        finally:
            if self._timer:
                self._timer.cancel()
                self._timer = None


def with_timeout(timeout_seconds: int = 30, operation_name: Optional[str] = None):
    """Decorator wrapper for calls that should fail fast."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            handler = TimeoutHandler(timeout_seconds)
            name = operation_name or f"{func.__name__}()"
            with handler.timeout_context(name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


MONITORING_TIMEOUT = 30
KPI_ANALYTICS_TIMEOUT = 45
CONFIG_TIMEOUT = 45
VALIDATION_TIMEOUT = 30
EXECUTION_TIMEOUT = 60
