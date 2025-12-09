"""
Workflow edge definitions for LangGraph.

Conditional edge functions that determine routing between nodes
based on the current workflow state.
"""

from typing import Literal

import structlog

from cassava_optimizer.workflow.state import OptimizationState, WorkflowStatus

logger = structlog.get_logger(__name__)


def should_continue(
    state: OptimizationState,
) -> Literal["analyze", "error"]:
    """
    Determine whether to continue to analysis after data collection.
    
    Routes to:
    - "analyze": Continue with analysis
    - "error": Handle error condition
    """
    logger.debug(
        "Evaluating should_continue",
        status=state.status.value,
        has_errors=len(state.errors) > 0,
    )
    
    if state.status == WorkflowStatus.FAILED or state.has_critical_errors():
        return "error"
    
    if not state.collected_data:
        logger.warning("No collected data - routing to error")
        return "error"
    
    return "analyze"


def should_plan(
    state: OptimizationState,
) -> Literal["strategy", "no_issues", "error"]:
    """
    Determine whether to continue to strategy planning after analysis.
    
    Routes to:
    - "strategy": Continue with strategy planning (issues found)
    - "no_issues": Skip to completion (no issues found)
    - "error": Handle error condition
    """
    logger.debug(
        "Evaluating should_plan",
        status=state.status.value,
        issues_found=len(state.issues_found),
        health_score=state.health_score,
    )
    
    if state.status == WorkflowStatus.FAILED or state.has_critical_errors():
        return "error"
    
    # If health score is very high and no critical issues, skip optimization
    if state.health_score >= 95 and not state.issues_found:
        logger.info("Network is healthy - no optimization needed")
        return "no_issues"
    
    # If no issues found, skip optimization
    if not state.issues_found:
        logger.info("No issues found - skipping optimization")
        return "no_issues"
    
    return "strategy"


def should_validate(
    state: OptimizationState,
) -> Literal["validate", "no_issues", "error"]:
    """
    Determine whether to continue to validation after strategy planning.
    
    Routes to:
    - "validate": Continue with validation
    - "no_issues": Skip (no recommendations generated)
    - "error": Handle error condition
    """
    logger.debug(
        "Evaluating should_validate",
        status=state.status.value,
        recommendations=len(state.recommendations),
    )
    
    if state.status == WorkflowStatus.FAILED or state.has_critical_errors():
        return "error"
    
    if not state.recommendations:
        logger.info("No recommendations generated - completing workflow")
        return "no_issues"
    
    return "validate"


def should_execute(
    state: OptimizationState,
) -> Literal["execute", "await_approval", "error"]:
    """
    Determine whether to execute after validation.
    
    Routes to:
    - "execute": Proceed with execution
    - "await_approval": Pause for human approval
    - "error": Handle error condition
    """
    logger.debug(
        "Evaluating should_execute",
        status=state.status.value,
        requires_approval=state.requires_approval,
        auto_approve=state.auto_approve,
        validated=len(state.validated_recommendations),
    )
    
    if state.status == WorkflowStatus.FAILED or state.has_critical_errors():
        return "error"
    
    if not state.validated_recommendations:
        logger.warning("No validated recommendations - routing to error")
        return "error"
    
    # Check if approval is needed
    if state.requires_approval and not state.auto_approve:
        if state.approval_status != "approved":
            logger.info("Awaiting human approval")
            return "await_approval"
    
    return "execute"


def check_approval(
    state: OptimizationState,
) -> Literal["execute", "await_approval", "error"]:
    """
    Check approval status after awaiting approval.
    
    Routes to:
    - "execute": Approval granted, proceed
    - "await_approval": Still waiting
    - "error": Approval rejected or error
    """
    logger.debug(
        "Checking approval status",
        approval_status=state.approval_status,
    )
    
    if state.approval_status == "approved":
        return "execute"
    
    if state.approval_status == "rejected":
        return "error"
    
    # Still pending
    return "await_approval"


def should_review(
    state: OptimizationState,
) -> Literal["review", "error"]:
    """
    Determine whether to continue to review after execution.
    
    Routes to:
    - "review": Continue with review
    - "error": Handle error condition
    """
    logger.debug(
        "Evaluating should_review",
        status=state.status.value,
        executed=len(state.executed_commands),
        failed=len(state.failed_commands),
        rollback=state.rollback_performed,
    )
    
    if state.status == WorkflowStatus.FAILED or state.has_critical_errors():
        return "error"
    
    # Always review, even if execution partially failed
    return "review"


def should_rollback(
    state: OptimizationState,
) -> Literal["complete", "rollback"]:
    """
    Determine whether rollback is needed after review.
    
    Routes to:
    - "complete": Optimization complete
    - "rollback": Rollback recommended
    """
    logger.debug(
        "Evaluating should_rollback",
        rollback_recommended=state.rollback_recommended,
        effectiveness_score=state.effectiveness_score,
    )
    
    if state.rollback_recommended and not state.rollback_performed:
        return "rollback"
    
    return "complete"


def get_next_node(
    state: OptimizationState,
) -> str:
    """
    Main routing function that determines the next node based on current status.
    
    This is a general-purpose router for the main workflow path.
    
    Returns:
        Name of the next node to execute
    """
    status = state.status
    
    logger.debug(
        "Getting next node",
        current_status=status.value,
        current_agent=state.current_agent,
    )
    
    # Status-based routing
    routing_map = {
        WorkflowStatus.PENDING: "collect_data",
        WorkflowStatus.COLLECTING: "collect_data",
        WorkflowStatus.ANALYZING: "analyze",
        WorkflowStatus.PLANNING: "strategy",
        WorkflowStatus.VALIDATING: "validate",
        WorkflowStatus.AWAITING_APPROVAL: "approval",
        WorkflowStatus.EXECUTING: "execute",
        WorkflowStatus.REVIEWING: "review",
        WorkflowStatus.COMPLETED: "end",
        WorkflowStatus.FAILED: "error",
        WorkflowStatus.ROLLED_BACK: "end",
    }
    
    next_node = routing_map.get(status, "error")
    
    logger.debug("Routed to", next_node=next_node)
    return next_node
