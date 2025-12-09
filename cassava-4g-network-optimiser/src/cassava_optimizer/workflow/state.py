"""
Workflow state definitions for LangGraph orchestration.

Defines the state schema that flows through the optimization pipeline,
tracking progress, results, and errors at each stage.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from langgraph.graph import add_messages


class WorkflowStatus(str, Enum):
    """Overall workflow execution status."""
    
    PENDING = "pending"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    VALIDATING = "validating"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class OptimizationState:
    """
    State object that flows through the LangGraph optimization workflow.
    
    This is the central state container that accumulates data and results
    as it passes through each agent in the pipeline.
    
    LangGraph uses this state to:
    - Track workflow progress
    - Pass data between nodes
    - Enable conditional routing
    - Support checkpointing and resumption
    """
    
    # Identification
    optimization_id: str = ""
    site_id: str = ""
    site_name: str = ""
    user_id: str | None = None
    
    # User query and intent
    user_query: str = ""
    intent_type: str = "optimize"  # optimize, analyze, troubleshoot, compare
    target_kpis: list[str] = field(default_factory=list)
    urgency: str = "medium"  # low, medium, high, critical
    constraints: dict[str, Any] = field(default_factory=dict)
    
    # Workflow control
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_agent: str = ""
    dry_run: bool = False
    auto_approve: bool = False
    
    # Configuration
    max_recommendations: int = 10
    max_retries: int = 3
    
    # Data collection stage
    collected_data: dict[str, Any] = field(default_factory=dict)
    collection_errors: list[str] = field(default_factory=list)
    
    # Analysis stage
    analysis_results: dict[str, Any] = field(default_factory=dict)
    health_score: float = 0.0
    issues_found: list[dict[str, Any]] = field(default_factory=list)
    
    # Strategy planning stage
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    strategy_summary: str = ""
    overall_risk: str = "unknown"
    
    # Validation stage
    validated_recommendations: list[dict[str, Any]] = field(default_factory=list)
    rejected_recommendations: list[dict[str, Any]] = field(default_factory=list)
    requires_approval: bool = False
    approval_status: str = "pending"  # pending, approved, rejected
    
    # Execution stage
    executed_commands: list[dict[str, Any]] = field(default_factory=list)
    failed_commands: list[dict[str, Any]] = field(default_factory=list)
    rollback_performed: bool = False
    pre_execution_snapshot: dict[str, Any] = field(default_factory=dict)
    
    # Review stage
    before_kpis: dict[str, float] = field(default_factory=dict)
    after_kpis: dict[str, float] = field(default_factory=dict)
    kpi_changes: list[dict[str, Any]] = field(default_factory=list)
    effectiveness_score: float = 0.0
    rollback_recommended: bool = False
    final_report: str = ""
    next_steps: list[str] = field(default_factory=list)
    
    # Error tracking
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    stage_timings: dict[str, float] = field(default_factory=dict)
    
    # Message history for LangGraph
    messages: Annotated[list[Any], add_messages] = field(default_factory=list)
    
    def add_error(self, error: str, stage: str = "") -> None:
        """Add an error with timestamp and optional stage."""
        prefix = f"[{stage}] " if stage else ""
        self.errors.append(f"{prefix}{error}")
    
    def add_warning(self, warning: str, stage: str = "") -> None:
        """Add a warning with optional stage."""
        prefix = f"[{stage}] " if stage else ""
        self.warnings.append(f"{prefix}{warning}")
    
    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors that should stop execution."""
        # Critical error keywords
        critical_keywords = ["failed", "connection", "authentication", "timeout"]
        return any(
            any(kw in err.lower() for kw in critical_keywords)
            for err in self.errors
        )
    
    def can_proceed_to_execution(self) -> bool:
        """Check if workflow can proceed to execution stage."""
        return (
            len(self.validated_recommendations) > 0
            and not self.has_critical_errors()
            and (self.auto_approve or self.approval_status == "approved" or not self.requires_approval)
        )
    
    def record_stage_timing(self, stage: str, duration_ms: float) -> None:
        """Record timing for a workflow stage."""
        self.stage_timings[stage] = duration_ms
    
    def get_total_duration_ms(self) -> float:
        """Get total workflow duration in milliseconds."""
        return sum(self.stage_timings.values())
    
    def to_context_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for agent context."""
        return {
            "site_id": self.site_id,
            "site_name": self.site_name,
            "optimization_id": self.optimization_id,
            "user_id": self.user_id,
            "collected_data": self.collected_data,
            "analysis_results": self.analysis_results,
            "recommendations": self.recommendations,
            "applied_commands": self.executed_commands,
            "validation_results": {
                "effectiveness_score": self.effectiveness_score,
                "kpi_changes": self.kpi_changes,
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "dry_run": self.dry_run,
            "auto_approve": self.auto_approve,
            "max_retries": self.max_retries,
        }
    
    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the workflow state."""
        return {
            "optimization_id": self.optimization_id,
            "site_id": self.site_id,
            "status": self.status.value,
            "health_score": self.health_score,
            "issues_found": len(self.issues_found),
            "recommendations": len(self.recommendations),
            "validated": len(self.validated_recommendations),
            "executed": len(self.executed_commands),
            "effectiveness_score": self.effectiveness_score,
            "errors": len(self.errors),
            "duration_ms": self.get_total_duration_ms(),
        }


def create_initial_state(
    site_id: str,
    site_name: str,
    optimization_id: str,
    user_id: str | None = None,
    user_query: str = "",
    intent_type: str = "optimize",
    target_kpis: list[str] | None = None,
    urgency: str = "medium",
    constraints: dict[str, Any] | None = None,
    dry_run: bool = False,
    auto_approve: bool = False,
) -> OptimizationState:
    """
    Create initial state for a new optimization workflow.
    
    Args:
        site_id: Network site identifier
        site_name: Human-readable site name
        optimization_id: Unique optimization run identifier
        user_id: Optional user initiating the optimization
        user_query: Natural language query from user
        intent_type: Parsed intent type (optimize, analyze, troubleshoot, compare)
        target_kpis: Specific KPIs to focus on
        urgency: Priority level (low, medium, high, critical)
        constraints: Additional constraints from query
        dry_run: If True, don't actually execute commands
        auto_approve: If True, skip manual approval for high-risk changes
        
    Returns:
        Initialized OptimizationState
    """
    return OptimizationState(
        optimization_id=optimization_id,
        site_id=site_id,
        site_name=site_name,
        user_id=user_id,
        user_query=user_query,
        intent_type=intent_type,
        target_kpis=target_kpis or [],
        urgency=urgency,
        constraints=constraints or {},
        status=WorkflowStatus.PENDING,
        dry_run=dry_run,
        auto_approve=auto_approve,
        started_at=datetime.utcnow(),
    )
