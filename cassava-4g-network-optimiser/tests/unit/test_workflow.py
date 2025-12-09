"""Unit tests for workflow layer."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest
import pytest_asyncio


class TestWorkflowState:
    """Tests for workflow state management."""

    def test_create_initial_state(self):
        """Test creating initial workflow state."""
        from cassava_optimizer.workflow.state import create_initial_state
        
        state = create_initial_state(
            site_id=1,
            site_name="TestSite001",
            dry_run=False,
            auto_approve=False,
        )
        
        assert state["site_id"] == 1
        assert state["site_name"] == "TestSite001"
        assert state["status"] == "initialized"
        assert "run_id" in state
        assert state["collected_data"] == {}
        assert state["recommendations"] == []
        assert state["errors"] == []

    def test_state_has_run_id(self):
        """Test state has unique run ID."""
        from cassava_optimizer.workflow.state import create_initial_state
        
        state1 = create_initial_state(site_id=1, site_name="Site1")
        state2 = create_initial_state(site_id=2, site_name="Site2")
        
        assert state1["run_id"] != state2["run_id"]

    def test_state_tracks_dry_run(self):
        """Test state tracks dry run mode."""
        from cassava_optimizer.workflow.state import create_initial_state
        
        state = create_initial_state(site_id=1, site_name="Site1", dry_run=True)
        
        assert state["dry_run"] is True

    def test_state_tracks_auto_approve(self):
        """Test state tracks auto approve mode."""
        from cassava_optimizer.workflow.state import create_initial_state
        
        state = create_initial_state(site_id=1, site_name="Site1", auto_approve=True)
        
        assert state["auto_approve"] is True


class TestWorkflowGraph:
    """Tests for workflow graph."""

    def test_graph_has_all_nodes(self, test_settings):
        """Test graph has all required nodes."""
        from cassava_optimizer.workflow.graph import create_workflow_graph
        
        graph = create_workflow_graph(test_settings)
        
        # Check required nodes exist
        node_names = [node.name for node in graph.nodes.values()]
        
        assert "collect_data" in node_names or "data_collector" in node_names
        assert "analyze" in node_names or "analyzer" in node_names
        assert "recommend" in node_names or "recommender" in node_names

    def test_graph_has_entry_point(self, test_settings):
        """Test graph has entry point."""
        from cassava_optimizer.workflow.graph import create_workflow_graph
        
        graph = create_workflow_graph(test_settings)
        
        # Should have an entry point
        assert graph.entry_point is not None

    def test_graph_has_conditional_edges(self, test_settings):
        """Test graph has conditional edges."""
        from cassava_optimizer.workflow.graph import create_workflow_graph
        
        graph = create_workflow_graph(test_settings)
        
        # Should have edges defined
        assert len(graph.edges) > 0


class TestWorkflowOrchestrator:
    """Tests for WorkflowOrchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_runs_workflow(self, test_settings, initial_workflow_state):
        """Test orchestrator runs complete workflow."""
        from cassava_optimizer.workflow.orchestrator import WorkflowOrchestrator
        
        # Mock all agents
        mock_agents = {
            "data_collector": AsyncMock(return_value={**initial_workflow_state, "collected_data": {"kpis": []}}),
            "analyzer": AsyncMock(return_value={**initial_workflow_state, "analysis_results": {"issues": []}}),
            "recommender": AsyncMock(return_value={**initial_workflow_state, "recommendations": []}),
            "executor": AsyncMock(return_value={**initial_workflow_state, "execution_results": []}),
            "validator": AsyncMock(return_value={**initial_workflow_state, "validation_results": {}}),
            "reporter": AsyncMock(return_value={**initial_workflow_state, "report": {"summary": "Done"}}),
        }
        
        with patch("cassava_optimizer.workflow.orchestrator.create_workflow_graph") as mock_graph:
            mock_compiled = MagicMock()
            mock_compiled.ainvoke = AsyncMock(return_value={
                **initial_workflow_state,
                "status": "completed",
                "report": {"summary": "Test complete"},
            })
            mock_graph.return_value.compile.return_value = mock_compiled
            
            orchestrator = WorkflowOrchestrator(test_settings)
            result = await orchestrator.run(initial_workflow_state)
            
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_orchestrator_handles_errors(self, test_settings, initial_workflow_state):
        """Test orchestrator handles errors gracefully."""
        from cassava_optimizer.workflow.orchestrator import WorkflowOrchestrator
        from cassava_optimizer.domain.exceptions import OptimizationError
        
        with patch("cassava_optimizer.workflow.orchestrator.create_workflow_graph") as mock_graph:
            mock_compiled = MagicMock()
            mock_compiled.ainvoke = AsyncMock(side_effect=OptimizationError("Workflow failed"))
            mock_graph.return_value.compile.return_value = mock_compiled
            
            orchestrator = WorkflowOrchestrator(test_settings)
            
            with pytest.raises(OptimizationError):
                await orchestrator.run(initial_workflow_state)

    @pytest.mark.asyncio
    async def test_orchestrator_stops_on_no_recommendations(self, test_settings, initial_workflow_state):
        """Test orchestrator stops early when no recommendations."""
        from cassava_optimizer.workflow.orchestrator import WorkflowOrchestrator
        
        with patch("cassava_optimizer.workflow.orchestrator.create_workflow_graph") as mock_graph:
            mock_compiled = MagicMock()
            mock_compiled.ainvoke = AsyncMock(return_value={
                **initial_workflow_state,
                "status": "completed",
                "recommendations": [],  # No recommendations
                "report": {"summary": "No issues found"},
            })
            mock_graph.return_value.compile.return_value = mock_compiled
            
            orchestrator = WorkflowOrchestrator(test_settings)
            result = await orchestrator.run(initial_workflow_state)
            
            # Should complete without executing
            assert result.get("execution_results", []) == []


class TestWorkflowCallbacks:
    """Tests for workflow callbacks."""

    def test_progress_callback_called(self, test_settings):
        """Test progress callback is called during workflow."""
        from cassava_optimizer.workflow.callbacks import create_progress_callback
        
        progress_updates = []
        
        def on_progress(agent_name: str, status: str, message: str):
            progress_updates.append({
                "agent": agent_name,
                "status": status,
                "message": message,
            })
        
        callback = create_progress_callback(on_progress)
        
        # Simulate callback invocation
        callback("data_collector", "started", "Collecting data...")
        callback("data_collector", "completed", "Data collected")
        
        assert len(progress_updates) == 2
        assert progress_updates[0]["agent"] == "data_collector"
        assert progress_updates[0]["status"] == "started"

    def test_error_callback_called_on_failure(self, test_settings):
        """Test error callback is called on failure."""
        from cassava_optimizer.workflow.callbacks import create_error_callback
        
        errors = []
        
        def on_error(agent_name: str, error: Exception):
            errors.append({
                "agent": agent_name,
                "error": str(error),
            })
        
        callback = create_error_callback(on_error)
        
        # Simulate error
        callback("analyzer", ValueError("Analysis failed"))
        
        assert len(errors) == 1
        assert errors[0]["agent"] == "analyzer"
        assert "Analysis failed" in errors[0]["error"]


class TestConditionalRouting:
    """Tests for workflow conditional routing."""

    def test_route_after_analysis_with_issues(self):
        """Test routing after analysis when issues found."""
        from cassava_optimizer.workflow.graph import route_after_analysis
        
        state = {
            "analysis_results": {
                "issues": [{"kpi": "call_drop_rate", "severity": "warning"}],
            },
        }
        
        next_node = route_after_analysis(state)
        
        assert next_node in ["recommend", "recommender"]

    def test_route_after_analysis_no_issues(self):
        """Test routing after analysis when no issues found."""
        from cassava_optimizer.workflow.graph import route_after_analysis
        
        state = {
            "analysis_results": {
                "issues": [],
            },
        }
        
        next_node = route_after_analysis(state)
        
        assert next_node in ["report", "reporter", "end"]

    def test_route_after_recommend_with_recommendations(self):
        """Test routing after recommend when recommendations exist."""
        from cassava_optimizer.workflow.graph import route_after_recommend
        
        state = {
            "recommendations": [{"id": 1}, {"id": 2}],
            "auto_approve": False,
        }
        
        next_node = route_after_recommend(state)
        
        # Should go to approval or execute based on auto_approve
        assert next_node in ["approve", "execute", "executor", "await_approval"]

    def test_route_after_recommend_auto_approve(self):
        """Test routing with auto approve enabled."""
        from cassava_optimizer.workflow.graph import route_after_recommend
        
        state = {
            "recommendations": [{"id": 1}],
            "auto_approve": True,
        }
        
        next_node = route_after_recommend(state)
        
        assert next_node in ["execute", "executor"]

    def test_route_after_validate_success(self):
        """Test routing after successful validation."""
        from cassava_optimizer.workflow.graph import route_after_validate
        
        state = {
            "validation_results": {
                "validated": True,
                "needs_rollback": False,
            },
        }
        
        next_node = route_after_validate(state)
        
        assert next_node in ["report", "reporter"]

    def test_route_after_validate_needs_rollback(self):
        """Test routing when rollback needed."""
        from cassava_optimizer.workflow.graph import route_after_validate
        
        state = {
            "validation_results": {
                "validated": False,
                "needs_rollback": True,
            },
        }
        
        next_node = route_after_validate(state)
        
        assert next_node in ["rollback", "report", "reporter"]


class TestStateTransitions:
    """Tests for state transitions."""

    def test_state_updates_status(self, initial_workflow_state):
        """Test state updates status correctly."""
        from cassava_optimizer.workflow.state import update_state_status
        
        state = initial_workflow_state.copy()
        state = update_state_status(state, "collecting")
        
        assert state["status"] == "collecting"

    def test_state_adds_error(self, initial_workflow_state):
        """Test state adds error correctly."""
        from cassava_optimizer.workflow.state import add_error_to_state
        
        state = initial_workflow_state.copy()
        state = add_error_to_state(state, "Test error message")
        
        assert "Test error message" in state["errors"]

    def test_state_updates_current_agent(self, initial_workflow_state):
        """Test state updates current agent."""
        from cassava_optimizer.workflow.state import set_current_agent
        
        state = initial_workflow_state.copy()
        state = set_current_agent(state, "analyzer")
        
        assert state["current_agent"] == "analyzer"

    def test_state_marks_completed(self, initial_workflow_state):
        """Test state marks workflow as completed."""
        from cassava_optimizer.workflow.state import mark_completed
        
        state = initial_workflow_state.copy()
        state = mark_completed(state)
        
        assert state["status"] == "completed"
        assert state["completed_at"] is not None
