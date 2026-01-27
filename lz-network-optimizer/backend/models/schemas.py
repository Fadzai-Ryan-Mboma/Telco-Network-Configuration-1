"""
Pydantic models for API request/response schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# SITE MODELS
# ============================================================================

class SiteBasic(BaseModel):
    """Basic site information."""
    site_name: str


class SiteInfo(BaseModel):
    """Detailed site information."""
    site_name: str
    location: str
    cell_count: int
    cell_id: int
    status: str
    last_updated: Optional[str] = None


class SiteStatus(BaseModel):
    """Site connectivity status."""
    api_connected: bool
    ne_connected: bool
    db_connected: bool
    api_status: str
    ne_status: str
    db_status: str


class ParameterValue(BaseModel):
    """Single parameter value with metadata."""
    value: Optional[Any] = None
    unit: str = ""
    source: str = "database"  # "live_api" or "database"


class SiteParameters(BaseModel):
    """Site parameter values."""
    site_name: str
    parameters: Dict[str, ParameterValue]
    status: str = "success"  # "success", "fallback", "error"
    site_offline: bool = False
    last_updated: Optional[str] = None
    errors: List[str] = []


# ============================================================================
# OPTIMIZATION MODELS
# ============================================================================

class OptimizationRequest(BaseModel):
    """Request to run optimization."""
    site_name: str
    cell_id: int = 1
    query: str = Field(..., min_length=3, description="Natural language optimization query")


class ParameterRecommendation(BaseModel):
    """Single parameter change recommendation."""
    parameter: str
    current_value: Any
    recommended_value: Any
    unit: str = ""
    description: str = ""


class OptimizationResult(BaseModel):
    """Optimization result."""
    status: str  # "success", "rejected", "error"
    issue: str = ""
    detailed_issue: Optional[str] = None
    recommendations: List[ParameterRecommendation] = []
    detailed_recommendations: Optional[str] = None
    risk_level: str = "LOW"  # "LOW", "MEDIUM", "HIGH"
    risk_score: float = 0.0
    detailed_risk: Optional[str] = None
    expected_impact: str = ""
    detailed_impact: Optional[str] = None
    mml_commands: List[str] = []
    kpi_issue: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None


class ExecutionRequest(BaseModel):
    """Request to execute optimization."""
    site_name: str
    recommendations: List[Dict[str, Any]]
    mml_commands: List[str]


class ExecutionDetail(BaseModel):
    """Single execution command detail."""
    command: str
    status: str  # "success", "failed", "skipped"
    message: Optional[str] = None


class ExecutionResult(BaseModel):
    """Execution result."""
    status: str  # "success", "partial", "failed"
    message: str
    dry_run: bool = False
    details: List[ExecutionDetail] = []


# ============================================================================
# KPI MODELS
# ============================================================================

class KPIValues(BaseModel):
    """Current KPI values for a site."""
    site_name: str
    network_access_success: Optional[float] = None
    download_speed: Optional[float] = None
    download_quality: Optional[float] = None
    upload_speed: Optional[float] = None
    upload_quality: Optional[float] = None
    control_channel_load: Optional[float] = None
    feedback_channel_load: Optional[float] = None
    timestamp: Optional[str] = None


class KPIHistoryPoint(BaseModel):
    """Single KPI history data point."""
    date: str
    value: float


class KPIHistory(BaseModel):
    """KPI history for charting."""
    site_name: str
    kpi_name: str
    days: int
    data: List[KPIHistoryPoint]
    threshold: float


class KPIThresholds(BaseModel):
    """Operating average thresholds."""
    network_access_success: float = 90.0
    download_speed: float = 5.0
    upload_speed: float = 3.0
    download_quality: float = 80.0
    upload_quality: float = 92.0
    control_channel_load: float = 70.0
    feedback_channel_load: float = 20.0


# ============================================================================
# ACTIVITY MODELS
# ============================================================================

class ActivityRecord(BaseModel):
    """Single activity log entry."""
    site_name: str
    timestamp: str
    action_type: str
    description: str
    changes: Optional[str] = None
    result: Optional[str] = None
    status: str  # "success", "rejected", "detected", "info"


class ActivityList(BaseModel):
    """List of activity records."""
    activities: List[ActivityRecord]
    total: int


# ============================================================================
# STATUS MODELS
# ============================================================================

class SystemStatus(BaseModel):
    """System health status."""
    api_connected: bool
    ne_connected: bool
    db_connected: bool
    api_status: str
    ne_status: str
    db_status: str


class DatabaseStats(BaseModel):
    """Database statistics."""
    total_sites: int
    total_records: int
    latest_update: Optional[str] = None
