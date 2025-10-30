"""
Logging Configuration for Liquid4G

Provides:
- Structured logging (JSON format for production)
- Console and file handlers
- Log rotation
- Context logging
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from liquid4g.core.config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "agent_id"):
            log_data["agent_id"] = record.agent_id
        if hasattr(record, "operation_id"):
            log_data["operation_id"] = record.operation_id
        if hasattr(record, "site_id"):
            log_data["site_id"] = record.site_id

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Colored text formatter for console"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging() -> None:
    """Setup logging configuration"""
    settings = get_settings()

    # Create logs directory
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.log_format == "json" and settings.is_production:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            TextFormatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    root_logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        settings.log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )

    if settings.log_format == "json":
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    root_logger.addHandler(file_handler)

    # Log startup message
    root_logger.info(
        f"Logging initialized: level={settings.log_level}, "
        f"format={settings.log_format}, "
        f"file={settings.log_file}"
    )


def get_logger(name: str, **context) -> logging.Logger:
    """
    Get logger with optional context.

    Args:
        name: Logger name (usually __name__)
        **context: Additional context (agent_id, operation_id, etc.)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Add context as extra
    if context:
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)

    return logger


# Initialize logging on import
setup_logging()
