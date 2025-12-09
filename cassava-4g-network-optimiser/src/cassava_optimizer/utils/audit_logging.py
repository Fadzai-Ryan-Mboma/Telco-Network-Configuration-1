"""
Structured Logging for Audit Trail.

Provides comprehensive logging for all optimization operations,
MML command executions, and system events.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog


# =============================================================================
# Log Configuration
# =============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json or console
LOG_DIR = Path(os.getenv("LOG_DIR", "./logs"))


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, LOG_LEVEL),
    )
    
    # Add file handler for audit logs
    audit_handler = logging.FileHandler(LOG_DIR / "audit.log")
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(logging.Formatter("%(message)s"))
    
    audit_logger = logging.getLogger("audit")
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)


# =============================================================================
# Audit Logger
# =============================================================================

class AuditLogger:
    """
    Audit logger for tracking all optimization operations.
    
    Logs are stored in JSON format for easy parsing and analysis.
    """
    
    def __init__(self, component: str = "cassava-optimizer") -> None:
        """Initialize audit logger."""
        self._logger = structlog.get_logger(component)
        self._audit_logger = logging.getLogger("audit")
        self._component = component
    
    def _write_audit(self, event_type: str, data: dict[str, Any]) -> None:
        """Write an audit log entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "component": self._component,
            "event_type": event_type,
            **data,
        }
        self._audit_logger.info(json.dumps(entry))
    
    def log_optimization_start(
        self,
        session_id: str,
        site_id: str,
        user_query: str,
        user_id: str = "system",
    ) -> None:
        """Log the start of an optimization session."""
        self._logger.info(
            "Optimization session started",
            session_id=session_id,
            site_id=site_id,
            user_query=user_query[:100],
        )
        
        self._write_audit("OPTIMIZATION_START", {
            "session_id": session_id,
            "site_id": site_id,
            "user_query": user_query,
            "user_id": user_id,
        })
    
    def log_optimization_complete(
        self,
        session_id: str,
        site_id: str,
        recommendations_count: int,
        duration_seconds: float,
        success: bool,
    ) -> None:
        """Log completion of an optimization session."""
        self._logger.info(
            "Optimization session completed",
            session_id=session_id,
            site_id=site_id,
            recommendations=recommendations_count,
            duration=duration_seconds,
            success=success,
        )
        
        self._write_audit("OPTIMIZATION_COMPLETE", {
            "session_id": session_id,
            "site_id": site_id,
            "recommendations_count": recommendations_count,
            "duration_seconds": duration_seconds,
            "success": success,
        })
    
    def log_mml_command(
        self,
        command_id: str,
        session_id: str,
        site_id: str,
        cell_id: str,
        command: str,
        parameter_name: str,
        old_value: Any,
        new_value: Any,
        status: str,
        execution_time_ms: int = 0,
        error_message: str = "",
    ) -> None:
        """Log MML command execution."""
        self._logger.info(
            "MML command executed",
            command_id=command_id,
            site_id=site_id,
            cell_id=cell_id,
            parameter=parameter_name,
            status=status,
        )
        
        self._write_audit("MML_COMMAND", {
            "command_id": command_id,
            "session_id": session_id,
            "site_id": site_id,
            "cell_id": cell_id,
            "command": command,
            "parameter_name": parameter_name,
            "old_value": str(old_value),
            "new_value": str(new_value),
            "status": status,
            "execution_time_ms": execution_time_ms,
            "error_message": error_message,
        })
    
    def log_rollback(
        self,
        command_id: str,
        session_id: str,
        site_id: str,
        parameter_name: str,
        restored_value: Any,
        success: bool,
        reason: str = "",
    ) -> None:
        """Log rollback operation."""
        self._logger.info(
            "Rollback executed",
            command_id=command_id,
            site_id=site_id,
            parameter=parameter_name,
            success=success,
        )
        
        self._write_audit("ROLLBACK", {
            "command_id": command_id,
            "session_id": session_id,
            "site_id": site_id,
            "parameter_name": parameter_name,
            "restored_value": str(restored_value),
            "success": success,
            "reason": reason,
        })
    
    def log_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: int,
        success: bool,
        error_message: str = "",
    ) -> None:
        """Log external API calls."""
        log_method = self._logger.info if success else self._logger.warning
        log_method(
            "API call",
            endpoint=endpoint,
            method=method,
            status=status_code,
            duration_ms=duration_ms,
        )
        
        self._write_audit("API_CALL", {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "success": success,
            "error_message": error_message,
        })
    
    def log_agent_action(
        self,
        agent_name: str,
        action: str,
        session_id: str,
        input_summary: str = "",
        output_summary: str = "",
        duration_ms: int = 0,
    ) -> None:
        """Log agent actions in the workflow."""
        self._logger.info(
            "Agent action",
            agent=agent_name,
            action=action,
            session_id=session_id,
        )
        
        self._write_audit("AGENT_ACTION", {
            "agent_name": agent_name,
            "action": action,
            "session_id": session_id,
            "input_summary": input_summary[:200] if input_summary else "",
            "output_summary": output_summary[:200] if output_summary else "",
            "duration_ms": duration_ms,
        })
    
    def log_kpi_poll(
        self,
        site_id: str,
        kpis_collected: int,
        source: str,
        success: bool,
        error_message: str = "",
    ) -> None:
        """Log KPI polling events."""
        self._logger.debug(
            "KPI poll",
            site_id=site_id,
            kpis=kpis_collected,
            source=source,
            success=success,
        )
        
        self._write_audit("KPI_POLL", {
            "site_id": site_id,
            "kpis_collected": kpis_collected,
            "source": source,
            "success": success,
            "error_message": error_message,
        })
    
    def log_user_action(
        self,
        action: str,
        user_id: str = "anonymous",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log user actions in the UI."""
        self._logger.info(
            "User action",
            action=action,
            user_id=user_id,
        )
        
        self._write_audit("USER_ACTION", {
            "action": action,
            "user_id": user_id,
            "details": details or {},
        })
    
    def log_error(
        self,
        error_type: str,
        message: str,
        component: str = "",
        stack_trace: str = "",
        context: dict[str, Any] | None = None,
    ) -> None:
        """Log error events."""
        self._logger.error(
            "Error occurred",
            error_type=error_type,
            message=message,
            component=component,
        )
        
        self._write_audit("ERROR", {
            "error_type": error_type,
            "message": message,
            "component": component or self._component,
            "stack_trace": stack_trace[:1000] if stack_trace else "",
            "context": context or {},
        })


# =============================================================================
# Singleton Instance
# =============================================================================

_audit_logger: AuditLogger | None = None


def get_audit_logger(component: str = "cassava-optimizer") -> AuditLogger:
    """Get singleton audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        setup_logging()
        _audit_logger = AuditLogger(component)
    return _audit_logger


# Convenience functions
def log_optimization_start(**kwargs: Any) -> None:
    """Log optimization session start."""
    get_audit_logger().log_optimization_start(**kwargs)


def log_mml_command(**kwargs: Any) -> None:
    """Log MML command execution."""
    get_audit_logger().log_mml_command(**kwargs)


def log_rollback(**kwargs: Any) -> None:
    """Log rollback operation."""
    get_audit_logger().log_rollback(**kwargs)


def log_error(**kwargs: Any) -> None:
    """Log error event."""
    get_audit_logger().log_error(**kwargs)
