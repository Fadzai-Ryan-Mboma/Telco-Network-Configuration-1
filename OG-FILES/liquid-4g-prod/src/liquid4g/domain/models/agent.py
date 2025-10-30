"""
Agent Domain Models

Represents agentic operators:
- Agent definitions and configuration
- Agent status and health
- Agent capabilities
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class AgentType(str, Enum):
    """Type of agent"""

    MONITOR = "monitor"
    ANALYZER = "analyzer"
    OPTIMIZER = "optimizer"
    VALIDATOR = "validator"
    EXECUTOR = "executor"
    ORCHESTRATOR = "orchestrator"


class AgentStatusEnum(str, Enum):
    """Agent operational status"""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class Agent(BaseModel):
    """
    Agent Definition

    Represents an autonomous agent in the system.
    """

    id: Optional[int] = Field(default=None)
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: AgentType = Field(..., description="Type of agent")

    display_name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(default=None, description="Agent description")

    status: AgentStatusEnum = Field(default=AgentStatusEnum.IDLE, description="Current status")
    current_task: Optional[str] = Field(default=None, description="Current task description")

    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    config: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: Optional[datetime] = Field(default=None, description="Last activity time")

    @field_validator("agent_id")
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        """Validate agent ID"""
        if not v or v.isspace():
            raise ValueError("Agent ID cannot be empty")
        return v.strip().lower()

    def is_available(self) -> bool:
        """Check if agent is available for tasks"""
        return self.status == AgentStatusEnum.IDLE

    def is_busy(self) -> bool:
        """Check if agent is currently busy"""
        return self.status == AgentStatusEnum.RUNNING

    def start_task(self, task_description: str) -> None:
        """Mark agent as running a task"""
        self.status = AgentStatusEnum.RUNNING
        self.current_task = task_description
        self.last_active_at = datetime.utcnow()

    def complete_task(self) -> None:
        """Mark task as complete"""
        self.status = AgentStatusEnum.IDLE
        self.current_task = None
        self.last_active_at = datetime.utcnow()

    def report_error(self, error_message: str) -> None:
        """Report an error"""
        self.status = AgentStatusEnum.ERROR
        self.current_task = f"ERROR: {error_message}"

    def __str__(self) -> str:
        return f"Agent({self.agent_id}: {self.display_name})"

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "optimizer_agent",
                "agent_type": "optimizer",
                "display_name": "Optimizer Agent",
                "description": "Generates parameter optimization strategies",
                "status": "idle",
                "capabilities": [
                    "kpi_analysis",
                    "root_cause_identification",
                    "optimization_strategy_generation",
                ],
                "config": {"llm_enabled": True, "fallback_enabled": True, "timeout": 120},
            }
        }


class ExecutionMode(str, Enum):
    """Agent execution mode"""

    LLM_PRIMARY = "llm_primary"
    RULE_FALLBACK = "rule_fallback"
    LLM_FAILED = "llm_failed"


class AgentStatus(BaseModel):
    """
    Agent Status Report

    Detailed status information about an agent's operation.
    """

    agent_id: str = Field(..., description="Agent identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    status: AgentStatusEnum = Field(..., description="Current status")
    active_tasks: int = Field(default=0, description="Number of active tasks")
    last_activity: Optional[datetime] = Field(default=None, description="Last activity time")

    # Execution metrics
    total_executions: int = Field(default=0, description="Total executions")
    successful_executions: int = Field(default=0, description="Successful executions")
    failed_executions: int = Field(default=0, description="Failed executions")

    # LLM vs Rule usage
    llm_executions: int = Field(default=0, description="LLM mode executions")
    rule_executions: int = Field(default=0, description="Rule fallback executions")
    circuit_breaker_open: bool = Field(default=False, description="Circuit breaker state")

    # Performance
    average_duration_seconds: Optional[float] = Field(
        default=None, description="Average execution time"
    )
    last_error: Optional[str] = Field(default=None, description="Last error message")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100

    def llm_usage_rate(self) -> float:
        """Calculate LLM usage rate as percentage"""
        if self.total_executions == 0:
            return 0.0
        return (self.llm_executions / self.total_executions) * 100

    def __str__(self) -> str:
        return (
            f"AgentStatus({self.agent_id}: {self.status}, "
            f"success_rate={self.success_rate():.1f}%)"
        )

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "optimizer_agent",
                "status": "idle",
                "active_tasks": 0,
                "total_executions": 150,
                "successful_executions": 142,
                "failed_executions": 8,
                "llm_executions": 120,
                "rule_executions": 30,
                "circuit_breaker_open": False,
                "average_duration_seconds": 12.5,
            }
        }
