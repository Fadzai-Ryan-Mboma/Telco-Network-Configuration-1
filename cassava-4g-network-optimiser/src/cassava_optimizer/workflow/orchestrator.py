"""
Workflow orchestrator module.

Re-exports workflow management classes from graph module for backwards
compatibility and provides NetworkOptimizer as main entry point.
"""

from cassava_optimizer.workflow.graph import (
    WorkflowManager,
    create_optimization_graph,
    run_optimization,
    run_optimization_simple,
    create_workflow_manager,
)

# Alias for backwards compatibility
WorkflowOrchestrator = WorkflowManager
NetworkOptimizer = WorkflowManager

__all__ = [
    "WorkflowManager",
    "WorkflowOrchestrator",
    "NetworkOptimizer",
    "create_optimization_graph",
    "run_optimization",
    "run_optimization_simple",
    "create_workflow_manager",
]
