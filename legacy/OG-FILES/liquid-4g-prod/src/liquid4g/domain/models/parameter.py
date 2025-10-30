"""
Parameter Domain Models

Represents network configuration parameters:
- Parameter definitions (metadata)
- Parameter values (current settings)
- Parameter changes (audit trail)
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ParameterCategory(str, Enum):
    """Parameter category classification"""

    POWER_CONTROL = "power_control"
    MOBILITY = "mobility"
    RADIO_RESOURCE = "radio_resource"
    TIMING = "timing"
    SCHEDULING = "scheduling"


class ImpactLevel(str, Enum):
    """Impact level of parameter changes"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ParameterDefinition(BaseModel):
    """
    Parameter Definition

    Defines metadata about a network parameter including valid ranges,
    MML commands, and impact assessment.
    """

    id: Optional[int] = Field(default=None)
    param_key: str = Field(..., description="Parameter identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(default=None)
    unit: Optional[str] = Field(default=None, description="Measurement unit")
    category: ParameterCategory = Field(..., description="Parameter category")

    # Valid range
    min_value: Optional[float] = Field(default=None, description="Minimum allowed value")
    max_value: Optional[float] = Field(default=None, description="Maximum allowed value")
    default_value: Optional[float] = Field(default=None, description="Default/recommended value")
    step_size: Optional[float] = Field(default=None, description="Minimum increment")

    # MML commands
    mml_query_command: Optional[str] = Field(default=None, description="Command to query value")
    mml_modify_command: Optional[str] = Field(
        default=None, description="Command template to modify value"
    )

    # Impact assessment
    impact_level: ImpactLevel = Field(..., description="Change impact level")

    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("param_key")
    @classmethod
    def validate_param_key(cls, v: str) -> str:
        """Validate parameter key format"""
        if not v or v.isspace():
            raise ValueError("Parameter key cannot be empty")
        return v.strip().lower().replace(" ", "_")

    def is_valid_value(self, value: float) -> bool:
        """Check if value is within valid range"""
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True

    def get_change_magnitude(self, old_value: float, new_value: float) -> float:
        """Calculate change magnitude as percentage"""
        if old_value == 0:
            return 100.0 if new_value != 0 else 0.0
        return abs((new_value - old_value) / old_value) * 100

    class Config:
        json_schema_extra = {
            "example": {
                "param_key": "reference_signal_power_rs",
                "display_name": "Reference Signal Power (RS)",
                "description": "Cell-specific reference signal power",
                "unit": "0.1 dBm",
                "category": "power_control",
                "min_value": -600,
                "max_value": 500,
                "default_value": 180,
                "step_size": 10,
                "mml_query_command": "LST PDSCHCFG: LOCALCELLID={cell_id};",
                "mml_modify_command": "MOD PDSCHCFG: LOCALCELLID={cell_id}, REFERENCESIGNALPWR={value};",
                "impact_level": "high",
            }
        }


class Parameter(BaseModel):
    """
    Parameter Value

    Represents the current value of a parameter for a specific cell.
    """

    id: Optional[int] = Field(default=None)
    cell_id: str = Field(..., description="Cell identifier")
    param_key: str = Field(..., description="Parameter identifier")
    value: float = Field(..., description="Current value")
    measured_at: datetime = Field(..., description="When value was measured")
    data_source: str = Field(default="api", description="Source of data")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("cell_id", "param_key")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        """Validate IDs"""
        if not v or v.isspace():
            raise ValueError("ID cannot be empty")
        return v.strip()

    def __str__(self) -> str:
        return f"Parameter({self.param_key}={self.value} @ {self.cell_id})"

    class Config:
        json_schema_extra = {
            "example": {
                "cell_id": "HARARE_CENTRAL_001_1",
                "param_key": "reference_signal_power_rs",
                "value": 180,
                "measured_at": "2025-01-13T10:30:00Z",
                "data_source": "api",
            }
        }


class ChangeType(str, Enum):
    """Type of parameter change"""

    OPTIMIZATION = "optimization"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"
    ROLLBACK = "rollback"
    MANUAL = "manual"


class ParameterChange(BaseModel):
    """
    Parameter Change Record

    Audit trail of parameter modifications including before/after values,
    reason, approval, and impact assessment.
    """

    id: Optional[int] = Field(default=None)
    change_id: str = Field(..., description="Unique change identifier")

    cell_id: str = Field(..., description="Affected cell")
    param_key: str = Field(..., description="Parameter identifier")

    old_value: Optional[float] = Field(default=None, description="Value before change")
    new_value: float = Field(..., description="Value after change")

    change_type: ChangeType = Field(..., description="Type of change")
    change_reason: Optional[str] = Field(default=None, description="Reason for change")

    # Approval tracking
    requested_by: str = Field(..., description="Who requested the change")
    approved_by: Optional[str] = Field(default=None, description="Who approved the change")

    # Execution tracking
    executed_at: Optional[datetime] = Field(default=None, description="When change was executed")
    success: Optional[bool] = Field(default=None, description="Whether change succeeded")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")

    # Rollback capability
    rollback_available: bool = Field(default=True, description="Can this change be rolled back")
    rollback_command: Optional[str] = Field(default=None, description="MML command to rollback")

    # Impact assessment
    kpi_snapshot_before: Optional[Dict[str, Any]] = Field(
        default=None, description="KPI values before change"
    )
    kpi_snapshot_after: Optional[Dict[str, Any]] = Field(
        default=None, description="KPI values after change"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("change_id")
    @classmethod
    def validate_change_id(cls, v: str) -> str:
        """Validate change ID"""
        if not v or v.isspace():
            raise ValueError("Change ID cannot be empty")
        return v.strip()

    def is_executed(self) -> bool:
        """Check if change has been executed"""
        return self.executed_at is not None

    def is_successful(self) -> bool:
        """Check if change was successful"""
        return self.success is True

    def can_rollback(self) -> bool:
        """Check if change can be rolled back"""
        return self.rollback_available and self.is_executed() and self.is_successful()

    def get_change_magnitude_percent(self) -> float:
        """Calculate change magnitude as percentage"""
        if self.old_value is None or self.old_value == 0:
            return 100.0 if self.new_value != 0 else 0.0
        return abs((self.new_value - self.old_value) / self.old_value) * 100

    def __str__(self) -> str:
        return f"ParameterChange({self.param_key}: {self.old_value} → {self.new_value})"

    class Config:
        json_schema_extra = {
            "example": {
                "change_id": "CHG_20250113_001",
                "cell_id": "HARARE_CENTRAL_001_1",
                "param_key": "reference_signal_power_rs",
                "old_value": 180,
                "new_value": 190,
                "change_type": "optimization",
                "change_reason": "Improve network access success rate",
                "requested_by": "optimizer_agent",
                "approved_by": "network_engineer",
                "executed_at": "2025-01-13T10:45:00Z",
                "success": True,
                "rollback_available": True,
                "kpi_snapshot_before": {"network_access_success": 89.2},
                "kpi_snapshot_after": {"network_access_success": 93.5},
            }
        }
