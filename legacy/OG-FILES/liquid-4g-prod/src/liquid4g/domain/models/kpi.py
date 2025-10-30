"""
KPI Domain Models

Represents network performance indicators:
- KPI definitions (metadata about each KPI)
- KPI measurements (actual data points)
- KPI alerts (threshold violations)
"""

from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class KPICategory(str, Enum):
    """KPI category classification"""

    ACCESSIBILITY = "accessibility"
    RETAINABILITY = "retainability"
    QUALITY = "quality"
    CAPACITY = "capacity"
    COVERAGE = "coverage"


class KPIThreshold(BaseModel):
    """
    KPI Threshold Definition

    Defines acceptable ranges and alert thresholds for a KPI.
    """

    id: Optional[int] = Field(default=None)
    kpi_key: str = Field(..., description="KPI identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(default=None)
    unit: Optional[str] = Field(default=None, description="Measurement unit (%, dBm, Mbps)")
    category: KPICategory = Field(..., description="KPI category")

    # Threshold values
    higher_is_better: bool = Field(..., description="True if higher values are better")
    optimal_min: Optional[float] = Field(default=None, description="Optimal minimum value")
    optimal_max: Optional[float] = Field(default=None, description="Optimal maximum value")
    warning_threshold: Optional[float] = Field(default=None, description="Warning level")
    critical_threshold: Optional[float] = Field(default=None, description="Critical level")

    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("kpi_key")
    @classmethod
    def validate_kpi_key(cls, v: str) -> str:
        """Validate KPI key format"""
        if not v or v.isspace():
            raise ValueError("KPI key cannot be empty")
        return v.strip().lower().replace(" ", "_")

    def is_critical(self, value: float) -> bool:
        """Check if value is at critical threshold"""
        if self.critical_threshold is None:
            return False

        if self.higher_is_better:
            return value < self.critical_threshold
        else:
            return value > self.critical_threshold

    def is_warning(self, value: float) -> bool:
        """Check if value is at warning threshold"""
        if self.warning_threshold is None:
            return False

        if self.higher_is_better:
            return value < self.warning_threshold
        else:
            return value > self.warning_threshold

    def get_status(self, value: float) -> str:
        """Get status for a value: good|warning|critical"""
        if self.is_critical(value):
            return "critical"
        elif self.is_warning(value):
            return "warning"
        else:
            return "good"

    class Config:
        json_schema_extra = {
            "example": {
                "kpi_key": "network_access_success",
                "display_name": "Network Access Success Rate",
                "description": "RACH Setup Success Rate (%)",
                "unit": "%",
                "category": "accessibility",
                "higher_is_better": True,
                "optimal_min": 95.0,
                "optimal_max": 100.0,
                "warning_threshold": 93.0,
                "critical_threshold": 90.0,
            }
        }


class DataSource(str, Enum):
    """Source of KPI data"""

    API = "api"
    DATABASE = "database"
    SIMULATION = "simulation"
    MANUAL = "manual"


class KPI(BaseModel):
    """
    KPI Measurement

    Represents a single KPI measurement at a point in time.
    """

    id: Optional[int] = Field(default=None)
    measurement_time: datetime = Field(..., description="When measurement was taken")
    cell_id: str = Field(..., description="Cell identifier")
    kpi_key: str = Field(..., description="KPI identifier")
    value: float = Field(..., description="Measured value")
    data_source: DataSource = Field(default=DataSource.API, description="Source of data")
    quality_score: Optional[float] = Field(
        default=None, ge=0, le=1, description="Data quality score (0-1)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("cell_id", "kpi_key")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        """Validate IDs"""
        if not v or v.isspace():
            raise ValueError("ID cannot be empty")
        return v.strip()

    def __str__(self) -> str:
        return f"KPI({self.kpi_key}={self.value} @ {self.cell_id})"

    class Config:
        json_schema_extra = {
            "example": {
                "measurement_time": "2025-01-13T10:30:00Z",
                "cell_id": "HARARE_CENTRAL_001_1",
                "kpi_key": "network_access_success",
                "value": 92.5,
                "data_source": "api",
                "quality_score": 0.95,
            }
        }


class AlertSeverity(str, Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert lifecycle status"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CLOSED = "closed"


class KPIAlert(BaseModel):
    """
    KPI Alert

    Triggered when a KPI crosses a threshold.
    """

    id: Optional[int] = Field(default=None)
    alert_id: str = Field(..., description="Unique alert identifier")
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = Field(default=None)

    cell_id: str = Field(..., description="Affected cell")
    kpi_key: str = Field(..., description="KPI identifier")

    severity: AlertSeverity = Field(..., description="Alert severity")
    current_value: float = Field(..., description="Current KPI value")
    threshold_value: float = Field(..., description="Threshold that was crossed")

    message: str = Field(..., description="Alert message")
    status: AlertStatus = Field(default=AlertStatus.ACTIVE, description="Alert status")

    @field_validator("alert_id")
    @classmethod
    def validate_alert_id(cls, v: str) -> str:
        """Validate alert ID"""
        if not v or v.isspace():
            raise ValueError("Alert ID cannot be empty")
        return v.strip()

    def is_active(self) -> bool:
        """Check if alert is still active"""
        return self.status == AlertStatus.ACTIVE

    def resolve(self) -> None:
        """Mark alert as resolved"""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()

    def duration_seconds(self) -> Optional[float]:
        """Get alert duration in seconds"""
        if not self.resolved_at:
            return (datetime.utcnow() - self.triggered_at).total_seconds()
        return (self.resolved_at - self.triggered_at).total_seconds()

    def __str__(self) -> str:
        return f"KPIAlert({self.severity}: {self.kpi_key} @ {self.cell_id})"

    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "ALERT_20250113_001",
                "triggered_at": "2025-01-13T10:30:00Z",
                "cell_id": "HARARE_CENTRAL_001_1",
                "kpi_key": "network_access_success",
                "severity": "critical",
                "current_value": 89.2,
                "threshold_value": 90.0,
                "message": "Network Access Success Rate below critical threshold (89.2% < 90%)",
                "status": "active",
            }
        }
