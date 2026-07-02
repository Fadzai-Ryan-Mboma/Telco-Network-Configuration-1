"""
Pydantic models for API request/response schemas
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import date, datetime


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
    label: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[int] = None
    description: Optional[str] = None


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


class KPIComparison(BaseModel):
    """Current value vs. this network's calibrated operating-average baseline for one KPI."""
    kpi: str
    current_value: Any = None
    baseline: Any = None
    status: str = ""  # "above_baseline", "at_baseline", "below_baseline"


class OptimizationResult(BaseModel):
    """Optimization result."""
    status: str  # "success", "rejected", "error"
    issue: str = ""
    detailed_issue: Optional[str] = None
    recommendations: List[ParameterRecommendation] = []
    detailed_recommendations: Optional[str] = None
    risk_level: str = "MEDIUM"  # "LOW", "MEDIUM", "HIGH" - Default to MEDIUM
    risk_score: float = 5.0  # Default to medium risk (5.0), not 0.0
    detailed_risk: Optional[str] = None
    expected_impact: str = ""
    detailed_impact: Optional[str] = None
    mml_commands: List[str] = []
    kpi_issue: Optional[str] = None
    kpi_comparison: List[KPIComparison] = []
    clarifying_question: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None


class ExecutionRequest(BaseModel):
    """Request to execute optimization."""
    site_name: str
    recommendations: List[Dict[str, Any]]
    mml_commands: List[str]
    execute_live: bool = False


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


# ============================================================================
# DIAGNOSTICS MODELS
# ============================================================================

class NBIEnvironmentDiagnostic(BaseModel):
    """Huawei iMaster MAE environment diagnostic result."""
    name: str
    gui_url: str
    nbi_base_url: str
    token_url: str
    gui_reachable: bool
    gui_status_code: Optional[int] = None
    nbi_reachable: bool
    nbi_status_code: Optional[int] = None
    classification: Literal[
        "success",
        "auth_failed",
        "timeout",
        "endpoint_missing",
        "method_wrong",
        "unknown",
    ]
    ret_code: Optional[str] = None
    ret_message: Optional[str] = None
    error: Optional[str] = None
    credentials_supplied: bool = False


class NBIDiagnosticsSummary(BaseModel):
    """Aggregated Huawei NBI diagnostics summary."""
    success: int = 0
    auth_failed: int = 0
    timeout: int = 0
    unavailable: int = 0


class NBIDiagnosticsResponse(BaseModel):
    """Access/Evaluation Huawei NBI diagnostics."""
    environments: List[NBIEnvironmentDiagnostic]
    summary: NBIDiagnosticsSummary


# ============================================================================
# REPORTING MODELS
# ============================================================================

class ReportFormulaPreviewRequest(BaseModel):
    """Inputs for deterministic v2 report formula preview."""
    daily_traffic_gb: List[float] = Field(default_factory=list)
    prb_busy_hour_values: List[float] = Field(default_factory=list)
    code_drop_values: List[float] = Field(default_factory=list)
    active_subscribers: float = 0.0
    addressable_subscribers: float = 0.0
    total_throughput_mbps: float = 0.0


class ReportFormulaPreviewResponse(BaseModel):
    """Computed v2 report formula outputs."""
    weekly_traffic_gb: float
    weekly_traffic_tb: float
    prb_busy_hour_weekly_average: float
    code_drop_average: float
    penetration_rate: float
    average_gb_per_active_user: float
    average_throughput_per_active_user: float


class ReportSiteMetric(BaseModel):
    """Computed reporting metrics for a site."""
    site_name: str
    weekly_traffic_gb: float = 0.0
    weekly_traffic_tb: float = 0.0
    prb_busy_hour_weekly_average: float = 0.0
    code_drop_average: float = 0.0
    radio_network_availability: float = 0.0
    peak_throughput_mbps: float = 0.0
    active_subscribers: float = 0.0
    addressable_subscribers: float = 0.0
    penetration_rate: float = 0.0
    average_gb_per_active_user: float = 0.0
    average_throughput_per_active_user: float = 0.0
    excluded: bool = False


class ReportSection(BaseModel):
    """Generated report workbook section."""
    name: str
    worksheet: str
    description: str
    status: str = "generated"


class ReportColumnMapping(BaseModel):
    """Detected input column mapping for report import preview."""
    concept: str
    matched_column: Optional[str] = None
    confidence: str = "missing"
    required: bool = False


class ReportColumnPreviewResponse(BaseModel):
    """Preview of source file columns and detected reporting mappings."""
    filename: str
    row_count: int
    columns: List[str]
    mappings: List[ReportColumnMapping]
    warnings: List[str] = Field(default_factory=list)


class ReportRunSummary(BaseModel):
    """Persisted report run summary for report history."""
    run_id: str
    created_at: Optional[str] = None
    original_filename: Optional[str] = None
    site_count: int = 0
    sections_count: int = 0
    output_file: str
    download_url: str
    pdf_file: Optional[str] = None
    pdf_download_url: Optional[str] = None
    audit_file: str


class ReportRunResponse(BaseModel):
    """Report import/generation result."""
    run_id: str
    status: str
    input_file: str
    output_file: str
    download_url: str
    pdf_file: str
    pdf_download_url: str
    site_count: int
    sections: List[ReportSection]
    top_traffic_sites: List[ReportSiteMetric]
    bottom_traffic_sites: List[ReportSiteMetric]
    audit_file: str


class ReportAutomationRequest(BaseModel):
    """One-click Evaluation report request."""
    period_start: date
    period_end: date
    refresh: bool = True
    exclusion_overrides: List[str] = Field(default_factory=list)


class ReportAutomationJob(BaseModel):
    """Persistent status for an asynchronous report job."""
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    refresh_requested: bool
    period_start: str
    period_end: str
    exclusions: List[str] = Field(default_factory=list)
    stage: str
    error_message: Optional[str] = None
    report_run_id: Optional[str] = None
    source_freshness: Optional[str] = None
    rows_ingested: int = 0
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    download_url: Optional[str] = None
    pdf_download_url: Optional[str] = None


class ReportExclusions(BaseModel):
    sites: List[str] = Field(default_factory=list)


class EvaluationStatus(BaseModel):
    connected: bool
    reason: Optional[str] = None
    updated_at: Optional[str] = None
    last_successful_extraction: Optional[str] = None
    last_period_start: Optional[str] = None
    last_period_end: Optional[str] = None
    last_rows_ingested: int = 0


class ReconnectSessionStatus(BaseModel):
    session_id: str
    status: str  # starting|awaiting_login|session_saved|failed|timeout|cancelled
    error_message: Optional[str] = None
    started_at: Optional[float] = None
    novnc_url: Optional[str] = None


# ============================================================================
# TOPOLOGY MODELS
# ============================================================================

class TopologySite(BaseModel):
    """Site marker for the first topology/NOC view."""
    site_name: str
    status: str = "unknown"
    latitude: float
    longitude: float
    network_access_success: Optional[float] = None
    download_speed: Optional[float] = None
    control_channel_load: Optional[float] = None
    cell_count: Optional[int] = None
    total_traffic_gb: Optional[float] = None
    availability: Optional[float] = None
    call_drop_rate: Optional[float] = None
    source: Optional[str] = None
    last_updated: Optional[str] = None


class TopologyResponse(BaseModel):
    """Topology payload for dashboard map-style view."""
    sites: List[TopologySite]
    site_count: int
    generated_at: str
