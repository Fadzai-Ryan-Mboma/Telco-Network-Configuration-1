"""
Base agent class for all specialized agents.

Provides common functionality for async execution, state management,
error handling, and logging.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar

import structlog

from cassava_optimizer.domain.enums import AgentType
from cassava_optimizer.domain.exceptions import (
    AgentExecutionError as DomainAgentError,
    CassavaOptimiserError,
)

logger = structlog.get_logger(__name__)

# Type variable for agent state
StateT = TypeVar("StateT")


class AgentExecutionError(CassavaOptimiserError):
    """Raised when agent execution fails."""
    
    def __init__(
        self,
        message: str,
        agent_type: AgentType,
        step: str | None = None,
        recoverable: bool = False,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, cause=cause)
        self.agent_type = agent_type
        self.step = step
        self.recoverable = recoverable


@dataclass
class AgentResult:
    """Container for agent execution results."""
    
    success: bool
    agent_type: AgentType
    output: dict[str, Any]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    
    def __post_init__(self) -> None:
        if self.completed_at is None:
            self.completed_at = datetime.utcnow()


@dataclass
class AgentContext:
    """
    Context passed between agents during workflow execution.
    
    Contains shared state, configuration, and resources.
    """
    
    site_id: str
    site_name: str
    optimization_id: str
    user_id: str | None = None
    
    # Shared data between agents
    collected_data: dict[str, Any] = field(default_factory=dict)
    analysis_results: dict[str, Any] = field(default_factory=dict)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    applied_commands: list[dict[str, Any]] = field(default_factory=list)
    validation_results: dict[str, Any] = field(default_factory=dict)
    
    # Execution tracking
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    # Configuration
    dry_run: bool = False
    auto_approve: bool = False
    max_retries: int = 3
    
    def add_error(self, error: str) -> None:
        """Add an error message to the context."""
        self.errors.append(f"[{datetime.utcnow().isoformat()}] {error}")
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message to the context."""
        self.warnings.append(f"[{datetime.utcnow().isoformat()}] {warning}")
    
    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors."""
        return len(self.errors) > 0


class BaseAgent(ABC, Generic[StateT]):
    """
    Abstract base class for all optimization agents.
    
    Provides:
    - Async execution framework
    - Error handling with fail-fast behavior
    - Structured logging
    - Execution metrics collection
    
    Subclasses must implement:
    - agent_type: The type of agent
    - _execute: The main execution logic
    """
    
    def __init__(self) -> None:
        self._log = logger.bind(agent=self.agent_type.value)
        self._execution_count = 0
        self._total_execution_time_ms = 0.0
    
    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        """Return the type of this agent."""
        ...
    
    @property
    def name(self) -> str:
        """Human-readable agent name."""
        return self.agent_type.value.replace("_", " ").title()
    
    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute the agent with full error handling and metrics.
        
        Args:
            context: Shared execution context
            
        Returns:
            AgentResult with execution outcome
            
        Raises:
            AgentExecutionError: If execution fails and is not recoverable
        """
        start_time = datetime.utcnow()
        
        self._log.info(
            "Agent starting",
            site_id=context.site_id,
            optimization_id=context.optimization_id,
        )
        
        try:
            # Pre-execution validation
            await self._validate_preconditions(context)
            
            # Execute main logic
            output = await self._execute(context)
            
            # Calculate execution time
            execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._total_execution_time_ms += execution_time_ms
            self._execution_count += 1
            
            result = AgentResult(
                success=True,
                agent_type=self.agent_type,
                output=output,
                execution_time_ms=execution_time_ms,
                started_at=start_time,
            )
            
            self._log.info(
                "Agent completed successfully",
                execution_time_ms=execution_time_ms,
            )
            
            return result
            
        except CassavaOptimizerError as e:
            # Known domain errors
            execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self._log.error(
                "Agent execution failed",
                error=str(e),
                error_type=type(e).__name__,
                execution_time_ms=execution_time_ms,
            )
            
            context.add_error(f"{self.name}: {e}")
            
            return AgentResult(
                success=False,
                agent_type=self.agent_type,
                output={},
                errors=[str(e)],
                execution_time_ms=execution_time_ms,
                started_at=start_time,
            )
            
        except Exception as e:
            # Unexpected errors - fail fast
            execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self._log.exception(
                "Agent execution failed with unexpected error",
                error=str(e),
            )
            
            raise AgentExecutionError(
                f"Unexpected error in {self.name}: {e}",
                agent_type=self.agent_type,
                recoverable=False,
                cause=e,
            )
    
    async def _validate_preconditions(self, context: AgentContext) -> None:
        """
        Validate preconditions before execution.
        
        Override in subclasses to add specific validation.
        
        Raises:
            AgentExecutionError: If preconditions are not met
        """
        if not context.site_id:
            raise AgentExecutionError(
                "Site ID is required",
                agent_type=self.agent_type,
                step="precondition_check",
            )
        
        if not context.optimization_id:
            raise AgentExecutionError(
                "Optimization ID is required",
                agent_type=self.agent_type,
                step="precondition_check",
            )
    
    @abstractmethod
    async def _execute(self, context: AgentContext) -> dict[str, Any]:
        """
        Execute the main agent logic.
        
        Args:
            context: Shared execution context
            
        Returns:
            Dictionary of outputs from this agent
            
        Raises:
            CassavaOptimizerError: On known errors
        """
        ...
    
    def get_metrics(self) -> dict[str, Any]:
        """Get execution metrics for this agent."""
        return {
            "agent_type": self.agent_type.value,
            "execution_count": self._execution_count,
            "total_execution_time_ms": self._total_execution_time_ms,
            "avg_execution_time_ms": (
                self._total_execution_time_ms / self._execution_count
                if self._execution_count > 0
                else 0
            ),
        }
