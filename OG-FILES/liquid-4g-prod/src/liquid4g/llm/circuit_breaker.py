"""
Circuit Breaker Pattern for LLM Resilience

Prevents cascading failures when LLM is unavailable or slow.
"""

import threading
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable, Any

from liquid4g.core.config import get_settings
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import CircuitBreakerOpenError

logger = get_logger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for LLM calls

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, blocking all requests
    - HALF_OPEN: Testing if service recovered, allowing limited requests

    Flow:
    1. Start in CLOSED state
    2. After threshold failures → OPEN (blocks all requests)
    3. After timeout → HALF_OPEN (allows test request)
    4. If test succeeds → CLOSED
    5. If test fails → OPEN again
    """

    def __init__(
        self,
        failure_threshold: Optional[int] = None,
        recovery_timeout: Optional[int] = None,
        success_threshold: Optional[int] = None,
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening (default: 5)
            recovery_timeout: Seconds to wait before half-open (default: 60)
            success_threshold: Successes in half-open before closing (default: 2)
        """
        self.settings = get_settings()

        # Configuration
        self.failure_threshold = failure_threshold or getattr(
            self.settings, "circuit_breaker_threshold", 5
        )
        self.recovery_timeout = recovery_timeout or getattr(
            self.settings, "circuit_breaker_recovery_timeout", 60
        )
        self.success_threshold = success_threshold or getattr(
            self.settings, "circuit_breaker_success_threshold", 2
        )

        # State
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = threading.Lock()

        logger.info(
            f"Circuit breaker initialized: threshold={self.failure_threshold}, "
            f"timeout={self.recovery_timeout}s"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        with self._lock:
            return self._state

    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)"""
        return self.state == CircuitState.CLOSED

    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)"""
        return self.state == CircuitState.OPEN

    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)"""
        return self.state == CircuitState.HALF_OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Any: Function return value

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        # Check if we should allow the call
        if not self._allow_request():
            raise CircuitBreakerOpenError(
                f"Circuit breaker is OPEN. "
                f"Service unavailable after {self._failure_count} failures. "
                f"Will retry in {self._time_until_retry():.0f} seconds."
            )

        # Execute the call
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _allow_request(self) -> bool:
        """
        Check if request should be allowed

        Returns:
            bool: True if request is allowed
        """
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True

            elif self._state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if self._should_attempt_recovery():
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    return True
                else:
                    return False

            elif self._state == CircuitState.HALF_OPEN:
                # Allow limited requests in half-open state
                return True

            return False

    def _should_attempt_recovery(self) -> bool:
        """
        Check if we should attempt recovery (transition to half-open)

        Returns:
            bool: True if enough time has passed since last failure
        """
        if self._last_failure_time is None:
            return True

        elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _on_success(self):
        """Handle successful call"""
        with self._lock:
            if self._state == CircuitState.CLOSED:
                # Reset failure count on success in closed state
                if self._failure_count > 0:
                    logger.debug(f"Circuit breaker: resetting failure count from {self._failure_count}")
                self._failure_count = 0

            elif self._state == CircuitState.HALF_OPEN:
                # Count successes in half-open state
                self._success_count += 1
                logger.info(
                    f"Circuit breaker: success {self._success_count}/{self.success_threshold} "
                    f"in HALF_OPEN state"
                )

                # If enough successes, transition to closed
                if self._success_count >= self.success_threshold:
                    logger.info("Circuit breaker transitioning to CLOSED (recovered)")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0

    def _on_failure(self):
        """Handle failed call"""
        with self._lock:
            self._last_failure_time = datetime.utcnow()

            if self._state == CircuitState.CLOSED:
                self._failure_count += 1
                logger.warning(
                    f"Circuit breaker: failure {self._failure_count}/{self.failure_threshold}"
                )

                # Check if we should open the circuit
                if self._failure_count >= self.failure_threshold:
                    logger.error(
                        f"Circuit breaker transitioning to OPEN after "
                        f"{self._failure_count} failures"
                    )
                    self._state = CircuitState.OPEN

            elif self._state == CircuitState.HALF_OPEN:
                # Failed during recovery test, go back to open
                logger.warning("Circuit breaker: recovery test failed, returning to OPEN")
                self._state = CircuitState.OPEN
                self._failure_count = self.failure_threshold  # Keep it maxed
                self._success_count = 0

    def _time_until_retry(self) -> float:
        """
        Get seconds until next retry attempt

        Returns:
            float: Seconds until retry
        """
        if self._last_failure_time is None:
            return 0.0

        elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
        remaining = max(0, self.recovery_timeout - elapsed)
        return remaining

    def reset(self):
        """Reset circuit breaker to closed state"""
        with self._lock:
            logger.info("Circuit breaker manually reset to CLOSED")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None

    def get_stats(self) -> dict:
        """
        Get circuit breaker statistics

        Returns:
            dict: Statistics
        """
        with self._lock:
            return {
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "failure_threshold": self.failure_threshold,
                "success_threshold": self.success_threshold,
                "recovery_timeout": self.recovery_timeout,
                "last_failure_time": (
                    self._last_failure_time.isoformat()
                    if self._last_failure_time
                    else None
                ),
                "time_until_retry": self._time_until_retry() if self.is_open() else 0,
            }
