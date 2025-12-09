"""
LangGraph workflow definition for the optimization pipeline.

Creates a StateGraph that orchestrates the multi-agent optimization
workflow with conditional routing and error handling.
"""

from typing import Optional
import uuid

import structlog
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from cassava_optimizer.config.settings import Settings
from cassava_optimizer.infrastructure.huawei_client import HuaweiMAEClient
from cassava_optimizer.infrastructure.llm_client import NVIDIANIMClient
from cassava_optimizer.infrastructure.repository import NetworkRepository
from cassava_optimizer.workflow.state import OptimizationState, WorkflowStatus, create_initial_state
from cassava_optimizer.workflow.nodes import (
    collect_data_node,
    analyze_node,
    strategy_node,
    validate_node,
    execute_node,
    review_node,
    error_node,
    no_issues_node,
    approval_node,
)
from cassava_optimizer.workflow.edges import (
    should_continue,
    should_plan,
    should_validate,
    should_execute,
    should_review,
    should_rollback,
)
from cassava_optimizer.services.query_parser import QueryParser
from cassava_optimizer.utils.audit_logging import get_audit_logger

logger = structlog.get_logger(__name__)
audit = get_audit_logger("workflow")


def create_optimization_graph(
    settings: Settings,
    huawei_client: HuaweiMAEClient,
    llm_client: NVIDIANIMClient,
    repository: NetworkRepository,
    checkpointer: Optional[MemorySaver] = None,
) -> StateGraph:
    """
    Create the optimization workflow graph.
    
    The workflow follows this structure:
    
    START -> collect_data -> analyze -> strategy -> validate -> execute -> review -> END
                  |             |           |           |          |         |
                  +-> error <---+-----------|-----------|----------|--------+
                                            |           |
                                            +-> skip -->+
    
    Args:
        settings: Application settings
        huawei_client: Huawei API client
        llm_client: LLM client
        repository: Database repository
        checkpointer: Optional memory saver for persistence
        
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Creating optimization workflow graph")
    
    # Create the graph with our state schema
    graph = StateGraph(OptimizationState)
    
    # Create bound node functions with dependencies injected
    def bound_collect_data(state: OptimizationState) -> OptimizationState:
        return collect_data_node(state, settings, huawei_client, repository)
    
    def bound_analyze(state: OptimizationState) -> OptimizationState:
        return analyze_node(state, settings, llm_client, repository)
    
    def bound_strategy(state: OptimizationState) -> OptimizationState:
        return strategy_node(state, settings, llm_client, repository)
    
    def bound_validate(state: OptimizationState) -> OptimizationState:
        return validate_node(state, settings, llm_client, repository)
    
    def bound_execute(state: OptimizationState) -> OptimizationState:
        return execute_node(state, settings, huawei_client, repository)
    
    def bound_review(state: OptimizationState) -> OptimizationState:
        return review_node(state, settings, llm_client, repository)
    
    def bound_error(state: OptimizationState) -> OptimizationState:
        return error_node(state, settings)
    
    def bound_no_issues(state: OptimizationState) -> OptimizationState:
        return no_issues_node(state)
    
    def bound_approval(state: OptimizationState) -> OptimizationState:
        return approval_node(state, settings)
    
    # Add nodes
    graph.add_node("collect_data", bound_collect_data)
    graph.add_node("analyze", bound_analyze)
    graph.add_node("strategy", bound_strategy)
    graph.add_node("validate", bound_validate)
    graph.add_node("approval", bound_approval)
    graph.add_node("execute", bound_execute)
    graph.add_node("review", bound_review)
    graph.add_node("no_issues", bound_no_issues)
    graph.add_node("error", bound_error)
    
    # Set entry point
    graph.set_entry_point("collect_data")
    
    # Add edges with conditional routing
    
    # After data collection: continue to analyze or handle error
    graph.add_conditional_edges(
        "collect_data",
        should_continue,
        {
            "analyze": "analyze",
            "error": "error",
        },
    )
    
    # After analysis: plan strategy, skip if no issues, or handle error
    graph.add_conditional_edges(
        "analyze",
        should_plan,
        {
            "strategy": "strategy",
            "no_issues": "complete",
            "error": "error",
        },
    )
    
    # After strategy: validate recommendations or skip if none
    graph.add_conditional_edges(
        "strategy",
        should_validate,
        {
            "validate": "validate",
            "no_issues": "complete",
            "error": "error",
        },
    )
    
    # After validation: execute, await approval, or handle error
    graph.add_conditional_edges(
        "validate",
        should_execute,
        {
            "execute": "execute",
            "await_approval": "approval",
            "error": "error",
        },
    )
    
    # After approval: execute or continue waiting
    graph.add_conditional_edges(
        "approval",
        lambda state: "execute" if state.approval_status == "approved" else "error" if state.approval_status == "rejected" else "approval",
        {
            "execute": "execute",
            "approval": "approval",  # Loop back (for external approval polling)
            "error": "error",
        },
    )
    
    # After execution: review
    graph.add_conditional_edges(
        "execute",
        should_review,
        {
            "review": "review",
            "error": "error",
        },
    )
    
    # After review: complete or rollback
    graph.add_conditional_edges(
        "review",
        should_rollback,
        {
            "complete": "complete",
            "rollback": "rollback",
        },
    )
    
    # After rollback: go to complete
    graph.add_edge("rollback", "complete")
    
    # After complete: end
    graph.add_edge("complete", END)
    
    # After error: end
    graph.add_edge("error", END)
    
    logger.info("Workflow graph created successfully")
    
    # Compile with optional checkpointer for state persistence
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    
    return graph.compile()


async def run_optimization(
    graph: StateGraph,
    site_name: str,
    optimization_type: str = "full",
    config: Optional[dict] = None,
    auto_approve: bool = False,
    thread_id: str = "default",
) -> OptimizationState:
    """
    Execute the optimization workflow for a site.
    
    Args:
        graph: Compiled workflow graph
        site_name: Name of the site to optimize
        optimization_type: Type of optimization (full, coverage, capacity, interference)
        config: Optional configuration overrides
        auto_approve: Whether to auto-approve recommendations
        thread_id: Thread ID for checkpointing
        
    Returns:
        Final workflow state
    """
    logger.info(
        "Starting optimization workflow",
        site_name=site_name,
        optimization_type=optimization_type,
        auto_approve=auto_approve,
    )
    
    # Create initial state
    initial_state = OptimizationState.create_initial(
        site_name=site_name,
        optimization_type=optimization_type,
        config=config,
        auto_approve=auto_approve,
    )
    
    # Run the workflow
    config_dict = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Stream through workflow nodes
        async for step in graph.astream(initial_state, config=config_dict):
            node_name = list(step.keys())[0] if step else "unknown"
            logger.info(
                "Workflow step completed",
                node=node_name,
                status=step[node_name].status.value if node_name in step else "unknown",
            )
        
        # Get final state
        final_state = await graph.aget_state(config_dict)
        
        logger.info(
            "Optimization workflow completed",
            site_name=site_name,
            status=final_state.values.status.value,
            duration_seconds=final_state.values.get_duration_seconds(),
        )
        
        return final_state.values
        
    except Exception as e:
        logger.exception(
            "Optimization workflow failed",
            site_name=site_name,
            error=str(e),
        )
        raise


async def run_optimization_simple(
    graph: StateGraph,
    site_name: str,
    optimization_type: str = "full",
    auto_approve: bool = False,
) -> OptimizationState:
    """
    Simple execution without streaming (for simpler use cases).
    
    Args:
        graph: Compiled workflow graph
        site_name: Name of the site to optimize
        optimization_type: Type of optimization
        auto_approve: Whether to auto-approve recommendations
        
    Returns:
        Final workflow state
    """
    logger.info(
        "Starting simple optimization",
        site_name=site_name,
        optimization_type=optimization_type,
    )
    
    initial_state = OptimizationState.create_initial(
        site_name=site_name,
        optimization_type=optimization_type,
        auto_approve=auto_approve,
    )
    
    # Invoke directly
    result = await graph.ainvoke(initial_state)
    
    logger.info(
        "Simple optimization completed",
        site_name=site_name,
        status=result.status.value,
    )
    
    return result


def create_workflow_manager(
    settings: Settings,
    huawei_client: HuaweiMAEClient,
    llm_client: NVIDIANIMClient,
    repository: NetworkRepository,
) -> "WorkflowManager":
    """
    Create a workflow manager for managing multiple workflow executions.
    
    Args:
        settings: Application settings
        huawei_client: Huawei API client
        llm_client: LLM client
        repository: Database repository
        
    Returns:
        WorkflowManager instance
    """
    return WorkflowManager(settings, huawei_client, llm_client, repository)


class WorkflowManager:
    """
    Manages workflow execution and state tracking.
    
    Provides a high-level interface for running optimizations
    with proper dependency management and state persistence.
    """
    
    def __init__(
        self,
        settings: Settings,
        huawei_client: HuaweiMAEClient,
        llm_client: NVIDIANIMClient,
        repository: NetworkRepository,
    ):
        """Initialize the workflow manager."""
        self.settings = settings
        self.huawei_client = huawei_client
        self.llm_client = llm_client
        self.repository = repository
        
        # Create checkpointer for state persistence
        self.checkpointer = MemorySaver()
        
        # Create the workflow graph
        self.graph = create_optimization_graph(
            settings=settings,
            huawei_client=huawei_client,
            llm_client=llm_client,
            repository=repository,
            checkpointer=self.checkpointer,
        )
        
        # Track active workflows
        self._active_workflows: dict[str, OptimizationState] = {}
        
        logger.info("WorkflowManager initialized")
    
    async def start_optimization(
        self,
        site_id: str,
        site_name: str,
        user_query: str = "",
        optimization_type: str = "full",
        config: Optional[dict] = None,
        auto_approve: bool = False,
        dry_run: bool = False,
        user_id: str = "system",
    ) -> str:
        """
        Start an optimization workflow with natural language query support.
        
        Args:
            site_id: Site identifier
            site_name: Name of the site to optimize
            user_query: Natural language query from user
            optimization_type: Type of optimization (fallback if no query)
            config: Optional configuration overrides
            auto_approve: Whether to auto-approve recommendations
            dry_run: If True, don't execute commands
            user_id: ID of user initiating optimization
            
        Returns:
            Workflow ID for tracking
        """
        workflow_id = str(uuid.uuid4())
        
        # Parse user query if provided
        intent_type = "optimize"
        target_kpis: list[str] = []
        urgency = "medium"
        constraints: dict = {}
        
        if user_query:
            parser = QueryParser()
            intent = parser.parse(user_query)
            intent_type = intent.intent_type
            target_kpis = intent.target_kpis
            urgency = intent.urgency
            constraints = intent.constraints
            
            logger.info(
                "Query parsed",
                workflow_id=workflow_id,
                intent_type=intent_type,
                target_kpis=target_kpis,
                urgency=urgency,
            )
        
        # Log optimization start
        audit.log_optimization_start(
            session_id=workflow_id,
            site_id=site_id,
            user_query=user_query or f"Run {optimization_type} optimization",
            user_id=user_id,
        )
        
        logger.info(
            "Starting optimization workflow",
            workflow_id=workflow_id,
            site_name=site_name,
            intent_type=intent_type,
        )
        
        # Create initial state with parsed intent
        initial_state = create_initial_state(
            site_id=site_id,
            site_name=site_name,
            optimization_id=workflow_id,
            user_id=user_id,
            user_query=user_query,
            intent_type=intent_type,
            target_kpis=target_kpis,
            urgency=urgency,
            constraints=constraints,
            dry_run=dry_run,
            auto_approve=auto_approve,
        )
        
        self._active_workflows[workflow_id] = initial_state
        
        return workflow_id
    
    async def run_workflow(
        self,
        workflow_id: str,
    ) -> OptimizationState:
        """
        Run a workflow by ID.
        
        Args:
            workflow_id: ID of the workflow to run
            
        Returns:
            Final workflow state
        """
        import time
        
        if workflow_id not in self._active_workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        initial_state = self._active_workflows[workflow_id]
        start_time = time.time()
        
        try:
            # Run the workflow using the graph directly
            config_dict = {"configurable": {"thread_id": workflow_id}}
            
            async for step in self.graph.astream(initial_state, config=config_dict):
                node_name = list(step.keys())[0] if step else "unknown"
                logger.info(
                    "Workflow step completed",
                    workflow_id=workflow_id,
                    node=node_name,
                )
                
                # Log agent action
                audit.log_agent_action(
                    agent_name=node_name,
                    action="completed",
                    session_id=workflow_id,
                )
            
            # Get final state
            final_state = await self.graph.aget_state(config_dict)
            result = final_state.values if hasattr(final_state, 'values') else final_state
            
            # Update stored state
            self._active_workflows[workflow_id] = result
            
            duration = time.time() - start_time
            
            # Log completion
            audit.log_optimization_complete(
                session_id=workflow_id,
                site_id=initial_state.site_id,
                recommendations_count=len(result.recommendations) if hasattr(result, 'recommendations') else 0,
                duration_seconds=duration,
                success=result.status != WorkflowStatus.FAILED if hasattr(result, 'status') else True,
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error
            audit.log_error(
                error_type=type(e).__name__,
                message=str(e),
                component="workflow",
                context={"workflow_id": workflow_id},
            )
            
            audit.log_optimization_complete(
                session_id=workflow_id,
                site_id=initial_state.site_id,
                recommendations_count=0,
                duration_seconds=duration,
                success=False,
            )
            
            raise
    
    async def get_workflow_state(
        self,
        workflow_id: str,
    ) -> Optional[OptimizationState]:
        """
        Get the current state of a workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Current workflow state or None if not found
        """
        return self._active_workflows.get(workflow_id)
    
    async def approve_workflow(
        self,
        workflow_id: str,
    ) -> bool:
        """
        Approve a workflow waiting for approval.
        
        Args:
            workflow_id: ID of the workflow to approve
            
        Returns:
            True if approved successfully
        """
        state = self._active_workflows.get(workflow_id)
        if not state:
            return False
        
        if state.status != WorkflowStatus.AWAITING_APPROVAL:
            logger.warning(
                "Workflow not awaiting approval",
                workflow_id=workflow_id,
                status=state.status.value,
            )
            return False
        
        state.approval_status = "approved"
        logger.info("Workflow approved", workflow_id=workflow_id)
        return True
    
    async def reject_workflow(
        self,
        workflow_id: str,
        reason: str = "",
    ) -> bool:
        """
        Reject a workflow waiting for approval.
        
        Args:
            workflow_id: ID of the workflow to reject
            reason: Reason for rejection
            
        Returns:
            True if rejected successfully
        """
        state = self._active_workflows.get(workflow_id)
        if not state:
            return False
        
        if state.status != WorkflowStatus.AWAITING_APPROVAL:
            logger.warning(
                "Workflow not awaiting approval",
                workflow_id=workflow_id,
                status=state.status.value,
            )
            return False
        
        state.approval_status = "rejected"
        state.add_error("approval", f"Rejected: {reason}" if reason else "Rejected by user")
        logger.info("Workflow rejected", workflow_id=workflow_id, reason=reason)
        return True
    
    def list_active_workflows(self) -> list[dict]:
        """
        List all active workflows.
        
        Returns:
            List of workflow summaries
        """
        return [
            {
                "workflow_id": wid,
                "site_name": state.site_name,
                "status": state.status.value,
                "optimization_type": state.optimization_type,
                "started_at": state.started_at.isoformat() if state.started_at else None,
            }
            for wid, state in self._active_workflows.items()
        ]
