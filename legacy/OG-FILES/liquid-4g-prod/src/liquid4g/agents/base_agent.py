"""
Base Hybrid Agent

Abstract base class for all agents with LLM primary and rule-based fallback.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

from liquid4g.core.config import get_settings
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import (
    AgentError,
    CircuitBreakerOpenError,
    LLMExecutionError,
    LLMResponseError,
)
from liquid4g.llm import get_llm_executor
from liquid4g.domain.models.operation import Operation, OperationLog
from liquid4g.infrastructure.repositories import AgentRepository, OperationRepository

logger = get_logger(__name__)


class AgentResult(BaseModel):
    """Result from agent execution"""
    success: bool
    data: Dict[str, Any]
    used_llm: bool
    execution_time: float
    error_message: Optional[str] = None


class BaseAgent(ABC):
    """
    Base class for hybrid agents

    Features:
    - LLM primary execution with circuit breaker
    - Rule-based fallback when LLM unavailable
    - Automatic result tracking
    - Operation logging
    """

    def __init__(self, agent_id: str, agent_type: str):
        """
        Initialize agent

        Args:
            agent_id: Unique agent identifier
            agent_type: Agent type for prompt selection
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.settings = get_settings()

        # Components
        self.llm_executor = get_llm_executor()
        self.agent_repo = AgentRepository()
        self.operation_repo = OperationRepository()

        # Configuration
        self.llm_enabled = getattr(self.settings, "agent_llm_enabled", True)

        logger.info(f"Initialized agent: {self.agent_id} (type: {self.agent_type})")

    def execute(self, operation: Operation, **kwargs) -> AgentResult:
        """
        Execute agent with hybrid approach

        Args:
            operation: Operation to execute
            **kwargs: Additional execution parameters

        Returns:
            AgentResult: Execution result
        """
        start_time = datetime.utcnow()
        used_llm = False
        error_message = None

        try:
            # Log start
            self._log_operation(operation, "INFO", "Agent execution started")

            # Try LLM first if enabled
            if self.llm_enabled and self.llm_executor.is_available():
                try:
                    logger.info(f"{self.agent_id}: Attempting LLM execution")
                    result_data = self._execute_with_llm(operation, **kwargs)
                    used_llm = True
                    self._log_operation(operation, "INFO", "LLM execution successful")

                except (CircuitBreakerOpenError, LLMExecutionError, LLMResponseError) as e:
                    logger.warning(f"{self.agent_id}: LLM failed, falling back to rules: {e}")
                    self._log_operation(operation, "WARNING", f"LLM failed, using fallback: {e}")
                    result_data = self._execute_with_rules(operation, **kwargs)

            else:
                # LLM disabled or unavailable, use rules
                logger.info(f"{self.agent_id}: Using rule-based execution")
                result_data = self._execute_with_rules(operation, **kwargs)

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Update metrics
            self.agent_repo.increment_execution_count(
                self.agent_id,
                success=True,
                used_llm=used_llm,
                duration_seconds=execution_time
            )

            # Log completion
            self._log_operation(operation, "INFO", "Agent execution completed")

            return AgentResult(
                success=True,
                data=result_data,
                used_llm=used_llm,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_message = str(e)

            logger.error(f"{self.agent_id}: Execution failed: {e}")
            self._log_operation(operation, "ERROR", f"Execution failed: {e}")

            # Update metrics with failure
            self.agent_repo.increment_execution_count(
                self.agent_id,
                success=False,
                used_llm=used_llm,
                duration_seconds=execution_time,
                error_message=error_message
            )

            return AgentResult(
                success=False,
                data={},
                used_llm=used_llm,
                execution_time=execution_time,
                error_message=error_message
            )

    @abstractmethod
    def _execute_with_llm(self, operation: Operation, **kwargs) -> Dict[str, Any]:
        """
        Execute using LLM

        Args:
            operation: Operation to execute
            **kwargs: Additional parameters

        Returns:
            Dict[str, Any]: Execution result data

        Raises:
            LLMExecutionError: If LLM execution fails
        """
        pass

    @abstractmethod
    def _execute_with_rules(self, operation: Operation, **kwargs) -> Dict[str, Any]:
        """
        Execute using rule-based logic

        Args:
            operation: Operation to execute
            **kwargs: Additional parameters

        Returns:
            Dict[str, Any]: Execution result data
        """
        pass

    def _log_operation(
        self,
        operation: Operation,
        level: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log operation event

        Args:
            operation: Operation
            level: Log level (DEBUG/INFO/WARNING/ERROR)
            message: Log message
            details: Optional details
        """
        try:
            log = OperationLog(
                operation_id=operation.operation_id,
                log_level=level,
                stage=operation.stage,
                message=message,
                details=details
            )
            self.operation_repo.create_log(log)
        except Exception as e:
            logger.error(f"Failed to log operation event: {e}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status

        Returns:
            Dict[str, Any]: Agent status
        """
        metrics = self.agent_repo.get_metrics(self.agent_id)
        circuit_stats = self.llm_executor.get_circuit_breaker_stats()

        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "llm_enabled": self.llm_enabled,
            "llm_available": self.llm_executor.is_available(),
            "circuit_breaker_state": circuit_stats["state"],
            "metrics": {
                "total_executions": metrics.total_executions if metrics else 0,
                "success_rate": metrics.success_rate() if metrics else 0,
                "llm_usage_rate": metrics.llm_usage_rate() if metrics else 0,
                "avg_duration": metrics.average_duration_seconds if metrics else 0,
            }
        }
