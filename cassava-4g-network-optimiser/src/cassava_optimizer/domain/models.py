"""
Domain models using Pydantic for validation and serialization.

All models are immutable (frozen) for thread safety in async context.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from cassava_optimizer.domain.enums import (
    AgentStatus,
    CellState,
    CommandExecutionStatus,
    KPIDirection,
    KPISeverity,
    KPITier,
    OptimizationCategory,
    ParameterType,
)


# =============================================================================
# Base Model Configuration
# =============================================================================

class FrozenModel(BaseModel):
    """Base model with immutable configuration."""
    
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class MutableModel(BaseModel):
    """Base model for state objects that need mutation."""
    
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


# =============================================================================
# Network Topology Models
# =============================================================================

class Cell(FrozenModel):
    """Represents a single LTE cell (sector) on an eNodeB."""
    
    cell_id: str = Field(..., description="Unique cell identifier")
    local_cell_id: int = Field(..., ge=0, le=255, description="Local cell ID (0-255)")
    cell_name: str = Field(..., description="Human-readable cell name")
    site_id: str = Field(..., description="Parent site identifier")
    pci: int = Field(..., ge=0, le=503, description="Physical Cell ID")
    tac: int = Field(..., ge=0, le=65535, description="Tracking Area Code")
    earfcn: int = Field(..., ge=0, description="E-UTRA Absolute Radio Frequency Channel Number")
    bandwidth: int = Field(..., description="Channel bandwidth in MHz")
    azimuth: float = Field(..., ge=0, lt=360, description="Antenna azimuth in degrees")
    electrical_tilt: float = Field(default=0.0, description="Electrical downtilt in degrees")
    mechanical_tilt: float = Field(default=0.0, description="Mechanical downtilt in degrees")
    tx_power: float = Field(..., description="Transmission power in dBm")
    state: CellState = Field(default=CellState.UNKNOWN, description="Operational state")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def total_tilt(self) -> float:
        """Calculate total antenna downtilt."""
        return self.electrical_tilt + self.mechanical_tilt
    
    @property
    def display_name(self) -> str:
        """Get formatted display name."""
        return f"{self.cell_name} (PCI: {self.pci})"


class Site(FrozenModel):
    """Represents an eNodeB site with multiple cells."""
    
    site_id: str = Field(..., description="Unique site identifier")
    site_name: str = Field(..., description="Human-readable site name")
    enodeb_id: int = Field(..., ge=0, description="eNodeB ID")
    latitude: float = Field(..., ge=-90, le=90, description="Site latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Site longitude")
    region: str = Field(default="", description="Geographic region")
    cluster: str = Field(default="", description="Network cluster")
    cells: tuple[Cell, ...] = Field(default=(), description="Cells at this site")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def cell_count(self) -> int:
        """Get number of cells at this site."""
        return len(self.cells)
    
    @property
    def display_name(self) -> str:
        """Get formatted display name."""
        return f"{self.site_name} ({self.site_id})"

    def get_cell(self, cell_id: str) -> Cell | None:
        """Get a specific cell by ID."""
        for cell in self.cells:
            if cell.cell_id == cell_id:
                return cell
        return None


# =============================================================================
# KPI Models
# =============================================================================

class KPIThreshold(FrozenModel):
    """Threshold configuration for a KPI."""
    
    critical: float = Field(..., description="Critical threshold value")
    warning: float = Field(..., description="Warning threshold value")
    target: float = Field(..., description="Target threshold value")


class KPIMetric(FrozenModel):
    """A single KPI measurement."""
    
    name: str = Field(..., description="KPI name identifier")
    display_name: str = Field(..., description="Human-readable name")
    value: float = Field(..., description="Current KPI value")
    unit: str = Field(..., description="Unit of measurement")
    tier: KPITier = Field(..., description="KPI tier classification")
    direction: KPIDirection = Field(..., description="Value direction preference")
    threshold: KPIThreshold = Field(..., description="Threshold configuration")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    site_id: str = Field(default="", description="Associated site ID")
    cell_id: str = Field(default="", description="Associated cell ID")
    
    @property
    def severity(self) -> KPISeverity:
        """Calculate severity based on value and thresholds."""
        if self.direction == KPIDirection.HIGHER_IS_BETTER:
            if self.value < self.threshold.critical:
                return KPISeverity.CRITICAL
            elif self.value < self.threshold.warning:
                return KPISeverity.WARNING
            elif self.value < self.threshold.target:
                return KPISeverity.TARGET
            else:
                return KPISeverity.HEALTHY
        elif self.direction == KPIDirection.LOWER_IS_BETTER:
            if self.value > self.threshold.critical:
                return KPISeverity.CRITICAL
            elif self.value > self.threshold.warning:
                return KPISeverity.WARNING
            elif self.value > self.threshold.target:
                return KPISeverity.TARGET
            else:
                return KPISeverity.HEALTHY
        else:
            return KPISeverity.HEALTHY
    
    @property
    def is_healthy(self) -> bool:
        """Check if KPI is at target or better."""
        return self.severity in (KPISeverity.TARGET, KPISeverity.HEALTHY)
    
    @property
    def normalized_score(self) -> float:
        """
        Calculate normalized score (0-1) where 1 is best.
        Uses threshold boundaries for normalization.
        """
        if self.direction == KPIDirection.HIGHER_IS_BETTER:
            # Score increases as value goes from critical to target+
            if self.value >= self.threshold.target:
                return 1.0
            elif self.value <= self.threshold.critical:
                return 0.0
            else:
                return (self.value - self.threshold.critical) / (
                    self.threshold.target - self.threshold.critical
                )
        elif self.direction == KPIDirection.LOWER_IS_BETTER:
            # Score increases as value goes from critical to target-
            if self.value <= self.threshold.target:
                return 1.0
            elif self.value >= self.threshold.critical:
                return 0.0
            else:
                return (self.threshold.critical - self.value) / (
                    self.threshold.critical - self.threshold.target
                )
        else:
            return 0.5  # Informational KPIs get neutral score


class KPIScore(FrozenModel):
    """Aggregated KPI score for a site or cell."""
    
    site_id: str = Field(..., description="Site identifier")
    cell_id: str = Field(default="", description="Cell identifier (empty for site-level)")
    overall_score: float = Field(..., ge=0, le=1, description="Overall weighted score")
    foundation_score: float = Field(..., ge=0, le=1, description="Foundation tier score")
    revenue_experience_score: float = Field(..., ge=0, le=1, description="Revenue/Experience tier score")
    efficiency_score: float = Field(..., ge=0, le=1, description="Efficiency tier score")
    metrics: tuple[KPIMetric, ...] = Field(default=(), description="Individual KPI metrics")
    critical_count: int = Field(default=0, ge=0, description="Number of critical KPIs")
    warning_count: int = Field(default=0, ge=0, description="Number of warning KPIs")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def health_status(self) -> str:
        """Get overall health status as a string."""
        if self.critical_count > 0:
            return "Critical"
        elif self.warning_count > 0:
            return "Warning"
        elif self.overall_score >= 0.95:
            return "Excellent"
        elif self.overall_score >= 0.80:
            return "Good"
        else:
            return "Needs Attention"


# =============================================================================
# Optimization Models
# =============================================================================

class ParameterChange(FrozenModel):
    """Represents a proposed parameter change."""
    
    parameter: ParameterType = Field(..., description="Parameter type")
    current_value: float | int | str = Field(..., description="Current parameter value")
    recommended_value: float | int | str = Field(..., description="Recommended new value")
    unit: str = Field(default="", description="Unit of measurement")
    reason: str = Field(default="", description="Reason for the change")
    expected_impact: str = Field(default="", description="Expected impact description")
    risk_level: str = Field(default="low", description="Risk level: low, medium, high")
    
    @property
    def change_magnitude(self) -> float | None:
        """Calculate the magnitude of change for numeric values."""
        if isinstance(self.current_value, (int, float)) and isinstance(
            self.recommended_value, (int, float)
        ):
            return abs(float(self.recommended_value) - float(self.current_value))
        return None


class OptimizationRecommendation(FrozenModel):
    """A complete optimization recommendation."""
    
    id: str = Field(..., description="Unique recommendation ID")
    site_id: str = Field(..., description="Target site ID")
    cell_id: str = Field(default="", description="Target cell ID (empty for site-level)")
    category: OptimizationCategory = Field(..., description="Optimization category")
    title: str = Field(..., description="Short recommendation title")
    description: str = Field(..., description="Detailed description")
    root_cause: str = Field(default="", description="Identified root cause")
    parameter_changes: tuple[ParameterChange, ...] = Field(
        default=(), description="Proposed parameter changes"
    )
    expected_improvement: str = Field(default="", description="Expected KPI improvements")
    confidence: float = Field(default=0.0, ge=0, le=1, description="Confidence score")
    priority: int = Field(default=3, ge=1, le=5, description="Priority (1=highest)")
    is_validated: bool = Field(default=False, description="Validation status")
    validation_notes: str = Field(default="", description="Validation notes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def change_count(self) -> int:
        """Get number of parameter changes."""
        return len(self.parameter_changes)


class MMLCommand(FrozenModel):
    """A Huawei MML command for execution."""
    
    command_id: str = Field(..., description="Unique command ID")
    command_text: str = Field(..., description="Raw MML command text")
    description: str = Field(default="", description="Command description")
    target_cell_id: str = Field(default="", description="Target cell ID")
    target_site_id: str = Field(default="", description="Target site ID")
    recommendation_id: str = Field(default="", description="Associated recommendation ID")
    rollback_command: str = Field(default="", description="Command to rollback this change")
    is_safe: bool = Field(default=True, description="Whether command is safe to execute")
    requires_confirmation: bool = Field(default=True, description="Requires user confirmation")
    estimated_impact: str = Field(default="", description="Estimated impact description")
    
    @field_validator("command_text")
    @classmethod
    def validate_command_text(cls, v: str) -> str:
        """Validate MML command syntax."""
        v = v.strip()
        if not v:
            raise ValueError("Command text cannot be empty")
        # Basic MML command validation
        if not any(v.upper().startswith(cmd) for cmd in ["MOD ", "SET ", "ADD ", "LST ", "DSP "]):
            raise ValueError(f"Invalid MML command prefix: {v[:20]}")
        return v


class CommandResult(FrozenModel):
    """Result of MML command execution."""
    
    command_id: str = Field(..., description="Command ID that was executed")
    status: CommandExecutionStatus = Field(..., description="Execution status")
    output: str = Field(default="", description="Command output")
    error_message: str = Field(default="", description="Error message if failed")
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: int = Field(default=0, ge=0, description="Execution time in milliseconds")
    rollback_executed: bool = Field(default=False, description="Whether rollback was executed")


# =============================================================================
# Historical Data Models
# =============================================================================

class HistoricalRecord(FrozenModel):
    """Historical KPI record from database."""
    
    id: int = Field(..., description="Record ID")
    site_id: str = Field(..., description="Site identifier")
    cell_id: str = Field(default="", description="Cell identifier")
    timestamp: datetime = Field(..., description="Record timestamp")
    kpi_name: str = Field(..., description="KPI name")
    kpi_value: float = Field(..., description="KPI value")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# =============================================================================
# Agent State Models
# =============================================================================

class AgentProgress(MutableModel):
    """Progress tracking for a single agent."""
    
    agent_name: str = Field(..., description="Agent name")
    status: AgentStatus = Field(default=AgentStatus.PENDING, description="Current status")
    started_at: datetime | None = Field(default=None, description="Start timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")
    message: str = Field(default="", description="Status message")
    progress_percent: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    error: str = Field(default="", description="Error message if failed")
    
    @property
    def duration_seconds(self) -> float | None:
        """Calculate duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class WorkflowResult(FrozenModel):
    """Complete result of a workflow execution."""
    
    session_id: str = Field(..., description="Unique session identifier")
    site_id: str = Field(..., description="Target site ID")
    query: str = Field(..., description="Original user query")
    kpi_score: KPIScore | None = Field(default=None, description="KPI analysis result")
    recommendations: tuple[OptimizationRecommendation, ...] = Field(
        default=(), description="Generated recommendations"
    )
    commands: tuple[MMLCommand, ...] = Field(default=(), description="Generated MML commands")
    agent_progress: tuple[AgentProgress, ...] = Field(
        default=(), description="Agent execution progress"
    )
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(default=None)
    success: bool = Field(default=False, description="Overall success status")
    error_message: str = Field(default="", description="Error message if failed")
    
    @property
    def total_duration_seconds(self) -> float | None:
        """Calculate total workflow duration."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def recommendation_count(self) -> int:
        """Get number of recommendations."""
        return len(self.recommendations)
    
    @property
    def command_count(self) -> int:
        """Get number of commands."""
        return len(self.commands)
