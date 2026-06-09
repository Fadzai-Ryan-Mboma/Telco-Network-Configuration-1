"""
Liquid Zimbabwe 4G Network Optimizer - LangGraph Workflow
Purpose: Orchestrate 6-agent workflow for network optimization
Created: 2025-10-30
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import logging

# Import all agents (relative imports from agents package)
from .network_connector_agent import network_connector_agent
from .monitoring_agent import monitoring_agent
from .kpi_analytics_agent import kpi_analytics_agent
from .config_agent import config_agent
from .validation_agent import validation_agent
from .mml_executor_agent import mml_executor_agent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# STATE DEFINITION
# ============================================================================

class OptimizationState(TypedDict):
    """
    State for the optimization workflow.

    This state is passed between agents and updated at each step.
    """
    # Input
    site_name: str
    cell_id: int
    user_query: str

    # Agent outputs
    network_connector_output: str
    monitoring_output: str
    kpi_analytics_output: str
    config_output: str
    validation_output: str
    executor_output: str

    # Decision points
    data_source: str  # 'live' or 'historical'
    needs_optimization: bool  # True if optimization required
    primary_kpi_issue: str  # Identified KPI problem
    validation_status: str  # 'APPROVED', 'REVIEW', or 'REJECTED'
    optimization_success: bool  # Final outcome

    # Agent outputs storage
    agent_outputs: dict


# ============================================================================
# ROUTING FUNCTIONS
# ============================================================================

def should_continue_to_analytics(state: OptimizationState) -> str:
    """
    Determine if workflow should proceed to KPI Analytics.

    After Monitoring Agent, check if optimization is needed.
    """
    if state.get("needs_optimization", False):
        logger.info("Optimization needed - proceeding to KPI Analytics")
        return "kpi_analytics"
    else:
        logger.info("No optimization needed - ending workflow")
        return END


def should_continue_to_executor(state: OptimizationState) -> str:
    """
    Determine if workflow should proceed to MML Executor.

    After Validation Agent, check if changes were approved.
    """
    validation_status = state.get("validation_status", "REJECTED")

    if validation_status in ["APPROVED", "REVIEW"]:
        logger.info(f"Validation status: {validation_status} - proceeding to execution")
        return "mml_executor"
    else:
        logger.info(f"Validation status: {validation_status} - ending workflow")
        return END


# ============================================================================
# BUILD WORKFLOW GRAPH
# ============================================================================

def build_workflow() -> StateGraph:
    """
    Build the LangGraph workflow.

    Workflow:
    1. Network Connector → Query network data
    2. Monitoring → Check KPIs and detect issues
    3. [Conditional] If issues → KPI Analytics → Analyze priorities
    4. Configuration → Recommend parameter changes
    5. Validation → Assess safety
    6. [Conditional] If approved → MML Executor → Execute changes
    """
    # Create workflow graph
    workflow = StateGraph(OptimizationState)

    # Add nodes (agents)
    workflow.add_node("network_connector", network_connector_agent)
    workflow.add_node("monitoring", monitoring_agent)
    workflow.add_node("kpi_analytics", kpi_analytics_agent)
    workflow.add_node("configuration", config_agent)
    workflow.add_node("validation", validation_agent)
    workflow.add_node("mml_executor", mml_executor_agent)

    # Define edges (workflow flow)
    workflow.set_entry_point("network_connector")

    # Linear flow: network_connector → monitoring
    workflow.add_edge("network_connector", "monitoring")

    # Conditional: monitoring → kpi_analytics OR END
    workflow.add_conditional_edges(
        "monitoring",
        should_continue_to_analytics,
        {
            "kpi_analytics": "kpi_analytics",
            END: END
        }
    )

    # Linear flow: kpi_analytics → configuration → validation
    workflow.add_edge("kpi_analytics", "configuration")
    workflow.add_edge("configuration", "validation")

    # Conditional: validation → mml_executor OR END
    workflow.add_conditional_edges(
        "validation",
        should_continue_to_executor,
        {
            "mml_executor": "mml_executor",
            END: END
        }
    )

    # Final edge: mml_executor → END
    workflow.add_edge("mml_executor", END)

    return workflow


def create_optimization_workflow():
    """
    Create compiled optimization workflow with memory.

    Returns:
        Compiled workflow ready for execution
    """
    workflow = build_workflow()

    # Add memory saver for state persistence
    memory = MemorySaver()

    # Compile workflow
    app = workflow.compile(checkpointer=memory)

    logger.info("Optimization workflow compiled successfully")
    return app


# ============================================================================
# EXECUTION FUNCTION
# ============================================================================

def run_optimization(site_name: str, user_query: str = "Optimize network performance", cell_id: int = 1):
    """
    Run complete optimization workflow for a site.

    Args:
        site_name: Site/eNodeB to optimize
        user_query: User's optimization request
        cell_id: Cell ID (default: 1)

    Returns:
        Final state after workflow execution
    """
    logger.info(f"Starting optimization workflow for {site_name}")

    # Create workflow
    app = create_optimization_workflow()

    # Initial state
    initial_state = {
        "site_name": site_name,
        "cell_id": cell_id,
        "user_query": user_query,
        "agent_outputs": {},
        "needs_optimization": False,
        "optimization_success": False
    }

    # Execute workflow
    config = {"configurable": {"thread_id": f"{site_name}_{cell_id}"}}

    try:
        # Use invoke instead of stream to get complete final state
        final_state = app.invoke(initial_state, config)

        logger.info("Optimization workflow completed successfully")
        logger.info(f"Final state keys: {list(final_state.keys())}")
        logger.info(f"Needs optimization: {final_state.get('needs_optimization', False)}")
        logger.info(f"Validation status: {final_state.get('validation_status', 'N/A')}")

        return final_state

    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Run optimization for a site
    result = run_optimization(
        site_name="MSH0013-Bindura-Zaoga",
        user_query="Optimize download speed and network access",
        cell_id=1
    )

    print("\n" + "=" * 80)
    print("OPTIMIZATION WORKFLOW COMPLETE")
    print("=" * 80)
    print(f"Site: {result.get('site_name', 'Unknown')}")
    print(f"Data Source: {result.get('data_source', 'Unknown')}")
    print(f"Optimization Needed: {result.get('needs_optimization', False)}")
    print(f"Primary KPI Issue: {result.get('primary_kpi_issue', 'None')}")
    print(f"Validation Status: {result.get('validation_status', 'N/A')}")
    print(f"Optimization Success: {result.get('optimization_success', False)}")
    print("=" * 80)

    # Print agent outputs
    for agent_name, output in result.get('agent_outputs', {}).items():
        print(f"\n{agent_name.upper()}:")
        print("-" * 80)
        print(output[:500] + "..." if len(output) > 500 else output)
