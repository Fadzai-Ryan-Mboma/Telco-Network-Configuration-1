"""
Workflow node definitions for LangGraph.

Each node represents a stage in the optimization pipeline,
wrapping the corresponding agent's execution.
"""

from datetime import datetime
from typing import Any

import structlog

from cassava_optimizer.agents.analyzer import AnalyzerAgent
from cassava_optimizer.agents.base import AgentContext
from cassava_optimizer.agents.commander import CommanderAgent
from cassava_optimizer.agents.data_collector import DataCollectorAgent
from cassava_optimizer.agents.reviewer import ReviewerAgent
from cassava_optimizer.agents.strategy_planner import StrategyPlannerAgent
from cassava_optimizer.agents.validator import ValidatorAgent
from cassava_optimizer.workflow.state import OptimizationState, WorkflowStatus

logger = structlog.get_logger(__name__)


def _state_to_context(state: OptimizationState) -> AgentContext:
    """Convert workflow state to agent context."""
    return AgentContext(
        site_id=state.site_id,
        site_name=state.site_name,
        optimization_id=state.optimization_id,
        user_id=state.user_id,
        collected_data=state.collected_data,
        analysis_results=state.analysis_results,
        recommendations=state.validated_recommendations or state.recommendations,
        applied_commands=state.executed_commands,
        validation_results={
            "effectiveness_score": state.effectiveness_score,
            "kpi_changes": state.kpi_changes,
        },
        errors=state.errors,
        warnings=state.warnings,
        dry_run=state.dry_run,
        auto_approve=state.auto_approve,
        max_retries=state.max_retries,
    )


async def collect_data_node(
    state: OptimizationState,
    data_collector: DataCollectorAgent,
) -> dict[str, Any]:
    """
    Data collection workflow node.
    
    Executes the DataCollectorAgent to gather network data.
    
    Args:
        state: Current workflow state
        data_collector: Injected data collector agent
        
    Returns:
        State updates dictionary
    """
    start_time = datetime.utcnow()
    
    logger.info(
        "Entering collect_data_node",
        site_id=state.site_id,
        optimization_id=state.optimization_id,
    )
    
    context = _state_to_context(state)
    result = await data_collector.run(context)
    
    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    updates: dict[str, Any] = {
        "current_agent": "data_collector",
        "stage_timings": {**state.stage_timings, "collect_data": duration_ms},
    }
    
    if result.success:
        updates.update({
            "status": WorkflowStatus.ANALYZING,
            "collected_data": result.output,
            "before_kpis": {
                k: v.get("value") for k, v in result.output.get("current_kpis", {}).items()
            },
        })
    else:
        updates.update({
            "status": WorkflowStatus.FAILED,
            "collection_errors": result.errors,
            "errors": state.errors + result.errors,
        })
    
    logger.info(
        "Exiting collect_data_node",
        success=result.success,
        duration_ms=duration_ms,
    )
    
    return updates


async def analyze_node(
    state: OptimizationState,
    analyzer: AnalyzerAgent,
) -> dict[str, Any]:
    """
    Analysis workflow node.
    
    Executes the AnalyzerAgent to identify performance issues.
    
    Args:
        state: Current workflow state
        analyzer: Injected analyzer agent
        
    Returns:
        State updates dictionary
    """
    start_time = datetime.utcnow()
    
    logger.info(
        "Entering analyze_node",
        site_id=state.site_id,
    )
    
    context = _state_to_context(state)
    result = await analyzer.run(context)
    
    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    updates: dict[str, Any] = {
        "current_agent": "analyzer",
        "stage_timings": {**state.stage_timings, "analyze": duration_ms},
    }
    
    if result.success:
        output = result.output
        updates.update({
            "status": WorkflowStatus.PLANNING,
            "analysis_results": output,
            "health_score": output.get("health_score", 0),
            "issues_found": output.get("issues", []),
        })
    else:
        updates.update({
            "status": WorkflowStatus.FAILED,
            "errors": state.errors + result.errors,
        })
    
    logger.info(
        "Exiting analyze_node",
        success=result.success,
        health_score=updates.get("health_score", 0),
        issues_found=len(updates.get("issues_found", [])),
    )
    
    return updates


async def strategy_node(
    state: OptimizationState,
    planner: StrategyPlannerAgent,
) -> dict[str, Any]:
    """
    Strategy planning workflow node.
    
    Executes the StrategyPlannerAgent to generate recommendations.
    
    Args:
        state: Current workflow state
        planner: Injected strategy planner agent
        
    Returns:
        State updates dictionary
    """
    start_time = datetime.utcnow()
    
    logger.info(
        "Entering strategy_node",
        site_id=state.site_id,
        issues_count=len(state.issues_found),
    )
    
    context = _state_to_context(state)
    result = await planner.run(context)
    
    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    updates: dict[str, Any] = {
        "current_agent": "strategy_planner",
        "stage_timings": {**state.stage_timings, "strategy": duration_ms},
    }
    
    if result.success:
        output = result.output
        recommendations = output.get("recommendations", [])
        
        updates.update({
            "status": WorkflowStatus.VALIDATING,
            "recommendations": recommendations,
            "strategy_summary": output.get("summary", ""),
            "overall_risk": output.get("risk_assessment", "unknown"),
        })
    else:
        updates.update({
            "status": WorkflowStatus.FAILED,
            "errors": state.errors + result.errors,
        })
    
    logger.info(
        "Exiting strategy_node",
        success=result.success,
        recommendations=len(updates.get("recommendations", [])),
    )
    
    return updates


async def validate_node(
    state: OptimizationState,
    validator: ValidatorAgent,
) -> dict[str, Any]:
    """
    Validation workflow node.
    
    Executes the ValidatorAgent to validate recommendations.
    
    Args:
        state: Current workflow state
        validator: Injected validator agent
        
    Returns:
        State updates dictionary
    """
    start_time = datetime.utcnow()
    
    logger.info(
        "Entering validate_node",
        site_id=state.site_id,
        recommendations=len(state.recommendations),
    )
    
    context = _state_to_context(state)
    result = await validator.run(context)
    
    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    updates: dict[str, Any] = {
        "current_agent": "validator",
        "stage_timings": {**state.stage_timings, "validate": duration_ms},
    }
    
    if result.success:
        output = result.output
        requires_approval = output.get("requires_approval", False)
        
        # Determine next status
        if requires_approval and not state.auto_approve:
            next_status = WorkflowStatus.AWAITING_APPROVAL
        else:
            next_status = WorkflowStatus.EXECUTING
        
        updates.update({
            "status": next_status,
            "validated_recommendations": output.get("validated_recommendations", []),
            "rejected_recommendations": output.get("rejected_recommendations", []),
            "requires_approval": requires_approval,
        })
    else:
        updates.update({
            "status": WorkflowStatus.FAILED,
            "errors": state.errors + result.errors,
        })
    
    logger.info(
        "Exiting validate_node",
        success=result.success,
        validated=len(updates.get("validated_recommendations", [])),
        requires_approval=updates.get("requires_approval", False),
    )
    
    return updates


async def execute_node(
    state: OptimizationState,
    commander: CommanderAgent,
) -> dict[str, Any]:
    """
    Execution workflow node.
    
    Executes the CommanderAgent to apply network changes.
    
    Args:
        state: Current workflow state
        commander: Injected commander agent
        
    Returns:
        State updates dictionary
    """
    start_time = datetime.utcnow()
    
    logger.info(
        "Entering execute_node",
        site_id=state.site_id,
        recommendations=len(state.validated_recommendations),
        dry_run=state.dry_run,
    )
    
    context = _state_to_context(state)
    result = await commander.run(context)
    
    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    updates: dict[str, Any] = {
        "current_agent": "commander",
        "stage_timings": {**state.stage_timings, "execute": duration_ms},
    }
    
    if result.success:
        output = result.output
        
        updates.update({
            "status": WorkflowStatus.REVIEWING,
            "executed_commands": output.get("executed_commands", []),
            "failed_commands": output.get("failed_commands", []),
            "rollback_performed": output.get("rollback_performed", False),
            "pre_execution_snapshot": output.get("snapshot", {}),
        })
    else:
        updates.update({
            "status": WorkflowStatus.FAILED,
            "errors": state.errors + result.errors,
        })
    
    logger.info(
        "Exiting execute_node",
        success=result.success,
        executed=len(updates.get("executed_commands", [])),
        failed=len(updates.get("failed_commands", [])),
    )
    
    return updates


async def review_node(
    state: OptimizationState,
    reviewer: ReviewerAgent,
) -> dict[str, Any]:
    """
    Review workflow node.
    
    Executes the ReviewerAgent to evaluate optimization results.
    
    Args:
        state: Current workflow state
        reviewer: Injected reviewer agent
        
    Returns:
        State updates dictionary
    """
    start_time = datetime.utcnow()
    
    logger.info(
        "Entering review_node",
        site_id=state.site_id,
        executed_commands=len(state.executed_commands),
    )
    
    context = _state_to_context(state)
    result = await reviewer.run(context)
    
    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    updates: dict[str, Any] = {
        "current_agent": "reviewer",
        "stage_timings": {**state.stage_timings, "review": duration_ms},
        "completed_at": datetime.utcnow(),
    }
    
    if result.success:
        output = result.output
        
        # Determine final status based on results
        if output.get("rollback_recommended"):
            final_status = WorkflowStatus.ROLLED_BACK
        else:
            final_status = WorkflowStatus.COMPLETED
        
        updates.update({
            "status": final_status,
            "after_kpis": output.get("after_kpis", {}),
            "kpi_changes": output.get("kpi_changes", []),
            "effectiveness_score": output.get("effectiveness_score", 0),
            "rollback_recommended": output.get("rollback_recommended", False),
            "final_report": output.get("report", ""),
            "next_steps": output.get("next_steps", []),
        })
    else:
        updates.update({
            "status": WorkflowStatus.FAILED,
            "errors": state.errors + result.errors,
        })
    
    logger.info(
        "Exiting review_node",
        success=result.success,
        effectiveness_score=updates.get("effectiveness_score", 0),
        status=updates.get("status", WorkflowStatus.FAILED).value,
    )
    
    return updates


async def approval_node(state: OptimizationState) -> dict[str, Any]:
    """
    Human approval checkpoint node.
    
    This node represents a pause point where human approval is required.
    The workflow will checkpoint here and resume when approval is provided.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates dictionary
    """
    logger.info(
        "Entering approval_node",
        site_id=state.site_id,
        requires_approval=state.requires_approval,
    )
    
    # Check if already approved
    if state.approval_status == "approved" or state.auto_approve:
        return {
            "status": WorkflowStatus.EXECUTING,
            "approval_status": "approved",
        }
    
    # Check if rejected
    if state.approval_status == "rejected":
        return {
            "status": WorkflowStatus.FAILED,
            "errors": state.errors + ["Optimization rejected by approver"],
        }
    
    # Still pending - stay in awaiting state
    return {
        "status": WorkflowStatus.AWAITING_APPROVAL,
    }


async def no_issues_node(state: OptimizationState) -> dict[str, Any]:
    """
    Node for handling case when no issues are found.
    
    Skips to completed status when analysis finds no issues.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates dictionary
    """
    logger.info(
        "Entering no_issues_node - network is healthy",
        site_id=state.site_id,
        health_score=state.health_score,
    )
    
    return {
        "status": WorkflowStatus.COMPLETED,
        "completed_at": datetime.utcnow(),
        "final_report": f"Network health score: {state.health_score}/100. No optimization required.",
        "next_steps": ["Continue monitoring", "Schedule next assessment"],
    }


async def error_node(state: OptimizationState) -> dict[str, Any]:
    """
    Error handling node.
    
    Handles workflow errors and generates error report.
    
    Args:
        state: Current workflow state
        
    Returns:
        State updates dictionary
    """
    logger.error(
        "Workflow error",
        site_id=state.site_id,
        errors=state.errors,
    )
    
    error_report = "\n".join([
        "=" * 60,
        "OPTIMIZATION WORKFLOW FAILED",
        "=" * 60,
        f"Site: {state.site_name} ({state.site_id})",
        f"Optimization ID: {state.optimization_id}",
        "",
        "Errors:",
        *[f"  - {e}" for e in state.errors],
        "",
        "Last successful stage: " + state.current_agent,
        "=" * 60,
    ])
    
    return {
        "status": WorkflowStatus.FAILED,
        "completed_at": datetime.utcnow(),
        "final_report": error_report,
        "next_steps": ["Review errors", "Fix issues", "Retry optimization"],
    }
