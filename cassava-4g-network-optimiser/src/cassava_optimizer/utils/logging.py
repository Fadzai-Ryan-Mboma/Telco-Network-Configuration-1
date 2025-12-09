"""
Logging configuration and utilities.

Configures structured logging using structlog with JSON formatting
for production and colorful console output for development.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import structlog
from structlog.typing import EventDict

from cassava_optimizer.config.settings import Settings


def add_timestamp(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Add ISO timestamp to log events."""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_service_info(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Add service information to log events."""
    event_dict["service"] = "cassava-optimizer"
    event_dict["version"] = "1.0.0"
    return event_dict


def setup_logging(
    settings: Optional[Settings] = None,
    log_level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[Path] = None,
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        settings: Application settings (optional)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON format for logs
        log_file: Optional file path for log output
    """
    if settings:
        log_level = settings.log_level
        json_format = settings.log_json_format
        log_file = settings.log_file
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure structlog processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_timestamp,
        add_service_info,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if json_format:
        # JSON formatting for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Colorful console output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        # Use JSON format for file logs
        file_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        )
        file_handler.setFormatter(file_formatter)
        
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def log_agent_action(
    agent_name: str,
    action: str,
    details: Optional[dict[str, Any]] = None,
    success: bool = True,
    error: Optional[str] = None,
    duration_ms: Optional[float] = None,
) -> None:
    """
    Log an agent action with standardized format.
    
    Args:
        agent_name: Name of the agent
        action: Action being performed
        details: Additional details
        success: Whether action succeeded
        error: Error message if failed
        duration_ms: Action duration in milliseconds
    """
    logger = get_logger("agent")
    
    log_data = {
        "agent": agent_name,
        "action": action,
        "success": success,
    }
    
    if details:
        log_data["details"] = details
    
    if duration_ms is not None:
        log_data["duration_ms"] = round(duration_ms, 2)
    
    if error:
        log_data["error"] = error
        logger.error("Agent action failed", **log_data)
    else:
        logger.info("Agent action completed", **log_data)


def log_api_call(
    service: str,
    endpoint: str,
    method: str = "GET",
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    success: bool = True,
    error: Optional[str] = None,
    request_size: Optional[int] = None,
    response_size: Optional[int] = None,
) -> None:
    """
    Log an API call with standardized format.
    
    Args:
        service: Service name (e.g., "huawei", "nvidia")
        endpoint: API endpoint
        method: HTTP method
        status_code: Response status code
        duration_ms: Request duration
        success: Whether call succeeded
        error: Error message if failed
        request_size: Request payload size
        response_size: Response payload size
    """
    logger = get_logger("api")
    
    log_data = {
        "service": service,
        "endpoint": endpoint,
        "method": method,
        "success": success,
    }
    
    if status_code is not None:
        log_data["status_code"] = status_code
    
    if duration_ms is not None:
        log_data["duration_ms"] = round(duration_ms, 2)
    
    if request_size is not None:
        log_data["request_size_bytes"] = request_size
    
    if response_size is not None:
        log_data["response_size_bytes"] = response_size
    
    if error:
        log_data["error"] = error
        logger.error("API call failed", **log_data)
    elif status_code and status_code >= 400:
        logger.warning("API call returned error status", **log_data)
    else:
        logger.debug("API call completed", **log_data)


def log_optimization_event(
    event_type: str,
    site_name: str,
    optimization_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    severity: str = "info",
) -> None:
    """
    Log an optimization workflow event.
    
    Event types:
    - started: Optimization started
    - collecting_data: Data collection phase
    - analyzing: Analysis phase
    - planning: Strategy planning phase
    - validating: Validation phase
    - executing: Execution phase
    - reviewing: Review phase
    - completed: Optimization completed
    - failed: Optimization failed
    - rolled_back: Changes rolled back
    
    Args:
        event_type: Type of event
        site_name: Site being optimized
        optimization_id: Unique optimization ID
        details: Additional event details
        severity: Log severity (debug, info, warning, error)
    """
    logger = get_logger("optimization")
    
    log_data = {
        "event_type": event_type,
        "site_name": site_name,
    }
    
    if optimization_id:
        log_data["optimization_id"] = optimization_id
    
    if details:
        log_data.update(details)
    
    log_method = getattr(logger, severity, logger.info)
    log_method(f"Optimization event: {event_type}", **log_data)


class OptimizationLogContext:
    """
    Context manager for optimization workflow logging.
    
    Automatically logs start and end events with timing.
    """
    
    def __init__(
        self,
        site_name: str,
        optimization_type: str,
        optimization_id: Optional[str] = None,
    ):
        self.site_name = site_name
        self.optimization_type = optimization_type
        self.optimization_id = optimization_id
        self.start_time: Optional[datetime] = None
        self.logger = get_logger("optimization")
    
    def __enter__(self) -> "OptimizationLogContext":
        self.start_time = datetime.utcnow()
        log_optimization_event(
            event_type="started",
            site_name=self.site_name,
            optimization_id=self.optimization_id,
            details={
                "optimization_type": self.optimization_type,
                "started_at": self.start_time.isoformat(),
            },
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds() if self.start_time else 0
        
        if exc_type is not None:
            log_optimization_event(
                event_type="failed",
                site_name=self.site_name,
                optimization_id=self.optimization_id,
                details={
                    "error": str(exc_val),
                    "error_type": exc_type.__name__,
                    "duration_seconds": duration,
                },
                severity="error",
            )
        else:
            log_optimization_event(
                event_type="completed",
                site_name=self.site_name,
                optimization_id=self.optimization_id,
                details={
                    "duration_seconds": duration,
                    "ended_at": end_time.isoformat(),
                },
            )
        
        return False  # Don't suppress exceptions


class AgentLogContext:
    """
    Context manager for agent action logging.
    
    Automatically logs start and end with timing.
    """
    
    def __init__(
        self,
        agent_name: str,
        action: str,
        details: Optional[dict[str, Any]] = None,
    ):
        self.agent_name = agent_name
        self.action = action
        self.details = details or {}
        self.start_time: Optional[datetime] = None
    
    def __enter__(self) -> "AgentLogContext":
        self.start_time = datetime.utcnow()
        log_agent_action(
            agent_name=self.agent_name,
            action=f"{self.action}_started",
            details=self.details,
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (
            (datetime.utcnow() - self.start_time).total_seconds() * 1000
            if self.start_time
            else 0
        )
        
        if exc_type is not None:
            log_agent_action(
                agent_name=self.agent_name,
                action=self.action,
                details=self.details,
                success=False,
                error=str(exc_val),
                duration_ms=duration_ms,
            )
        else:
            log_agent_action(
                agent_name=self.agent_name,
                action=self.action,
                details=self.details,
                success=True,
                duration_ms=duration_ms,
            )
        
        return False
