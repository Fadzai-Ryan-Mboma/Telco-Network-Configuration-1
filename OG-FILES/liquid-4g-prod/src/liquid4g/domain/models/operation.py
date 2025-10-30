"""
Operation Domain Models

Represents agentic operations and their execution:
- Operations (workflow executions)
- Operation logs (detailed execution logs)
- Operation stages
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid

from pydantic import BaseModel, Field, field_validator


class OperationType(str, Enum):
    """Type of operation"""

    FULL_OPTIMIZATION = "full_optimization"
    KPI_ANALYSIS = "kpi_analysis"
    PARAMETER_QUERY = "parameter_query"
    VALIDATION = "validation"
    EXECUTION = "execution"
    MONITORING = "monitoring"


class OperationStage(str, Enum):
    """Stage in the 6-stage workflow"""

    STAGE_1_NETWORK_CONNECTOR = "stage_1_network_connector"
    STAGE_2_MONITORING_ANALYSIS = "stage_2_monitoring_analysis"
    STAGE_3_KPI_ANALYTICS = "stage_3_kpi_analytics"
    STAGE_4_CONFIGURATION = "stage_4_configuration"
    STAGE_5_VALIDATION = "stage_5_validation"
    STAGE_6_EXECUTION = "stage_6_execution"


class OperationStatus(str, Enum):
    """Operation execution status"""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PriorityLevel(str, Enum):
    """Operation priority"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Operation(BaseModel):
    """
    Operation

    Represents a single agentic operation (workflow execution).
    """

    id: Optional[int] = Field(default=None)
    operation_id: str = Field(
        default_factory=lambda: f"OP_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
        description="Unique operation identifier",
    )

    operation_type: OperationType = Field(..., description="Type of operation")
    stage: Optional[OperationStage] = Field(default=None, description="Current stage")

    target_site: Optional[str] = Field(default=None, description="Target site ID")
    target_cell: Optional[str] = Field(default=None, description="Target cell ID")

    status: OperationStatus = Field(default=OperationStatus.PENDING, description="Current status")
    priority: PriorityLevel = Field(default=PriorityLevel.NORMAL, description="Priority level")

    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Input parameters for operation"
    )
    results: Dict[str, Any] = Field(default_factory=dict, description="Operation results")

    agent_id: Optional[str] = Field(default=None, description="Executing agent ID")
    parent_operation_id: Optional[str] = Field(
        default=None, description="Parent operation (for sub-operations)"
    )

    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")
    duration_seconds: Optional[float] = Field(default=None, description="Execution duration")

    error_message: Optional[str] = Field(default=None, description="Error message if failed")

    @field_validator("operation_id")
    @classmethod
    def validate_operation_id(cls, v: str) -> str:
        """Validate operation ID"""
        if not v or v.isspace():
            raise ValueError("Operation ID cannot be empty")
        return v.strip()

    @classmethod
    def create(
        cls,
        operation_type: OperationType,
        target_site: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> "Operation":
        """Factory method to create a new operation"""
        return cls(
            operation_type=operation_type, target_site=target_site, parameters=parameters or {}
        )

    def start(self, agent_id: str, stage: Optional[OperationStage] = None) -> None:
        """Mark operation as started"""
        self.status = OperationStatus.RUNNING
        self.agent_id = agent_id
        if stage:
            self.stage = stage
        self.started_at = datetime.utcnow()

    def complete(self, results: Optional[Dict[str, Any]] = None) -> None:
        """Mark operation as completed"""
        self.status = OperationStatus.COMPLETED
        if results:
            self.results = results
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()

    def fail(self, error_message: str) -> None:
        """Mark operation as failed"""
        self.status = OperationStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()

    def create_sub_operation(
        self, operation_type: OperationType, agent_id: str, stage: Optional[OperationStage] = None
    ) -> "Operation":
        """Create a sub-operation"""
        return Operation(
            operation_type=operation_type,
            stage=stage,
            target_site=self.target_site,
            target_cell=self.target_cell,
            agent_id=agent_id,
            parent_operation_id=self.operation_id,
        )

    def is_running(self) -> bool:
        """Check if operation is running"""
        return self.status == OperationStatus.RUNNING

    def is_complete(self) -> bool:
        """Check if operation is complete"""
        return self.status == OperationStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if operation failed"""
        return self.status == OperationStatus.FAILED

    def __str__(self) -> str:
        return f"Operation({self.operation_id}: {self.operation_type} - {self.status})"

    class Config:
        json_schema_extra = {
            "example": {
                "operation_id": "OP_20250113_103000_a1b2c3d4",
                "operation_type": "full_optimization",
                "stage": "stage_3_kpi_analytics",
                "target_site": "HARARE_CENTRAL_001",
                "status": "running",
                "priority": "normal",
                "parameters": {"trigger": "poor_kpi", "kpi_threshold": 90.0},
                "agent_id": "optimizer_agent",
            }
        }


class LogLevel(str, Enum):
    """Log entry severity level"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class OperationLog(BaseModel):
    """
    Operation Log Entry

    Detailed log entry for operation execution.
    """

    id: Optional[int] = Field(default=None)
    operation_id: str = Field(..., description="Associated operation ID")

    log_time: datetime = Field(default_factory=datetime.utcnow)
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Log severity")
    stage: Optional[OperationStage] = Field(default=None, description="Current stage")

    message: str = Field(..., description="Log message")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional structured details"
    )

    @field_validator("operation_id")
    @classmethod
    def validate_operation_id(cls, v: str) -> str:
        """Validate operation ID"""
        if not v or v.isspace():
            raise ValueError("Operation ID cannot be empty")
        return v.strip()

    def __str__(self) -> str:
        return f"OperationLog({self.log_level}: {self.message})"

    class Config:
        json_schema_extra = {
            "example": {
                "operation_id": "OP_20250113_103000_a1b2c3d4",
                "log_time": "2025-01-13T10:30:15Z",
                "log_level": "INFO",
                "stage": "stage_3_kpi_analytics",
                "message": "Identified 2 optimization opportunities",
                "details": {
                    "opportunities": ["improve_network_access", "reduce_dl_ibler"],
                    "confidence": 0.85,
                },
            }
        }
