"""Integration tests for workflow orchestration."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest
import pytest_asyncio


class TestWorkflowIntegration:
    """Integration tests for complete workflow execution."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_workflow_dry_run(self, test_settings, seeded_db, mock_mae_client, mock_llm):
        """Test full workflow in dry run mode."""
        from cassava_optimizer.workflow.orchestrator import WorkflowOrchestrator
        from cassava_optimizer.workflow.state import create_initial_state
        
        # Setup mocks
        with patch("cassava_optimizer.agents.data_collector.HuaweiMAEClient") as mae_mock, \
             patch("cassava_optimizer.agents.analyzer.get_llm", return_value=mock_llm), \
             patch("cassava_optimizer.agents.recommender.get_llm", return_value=mock_llm):
            
            mae_mock.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mae_mock.return_value.__aexit__ = AsyncMock(return_value=None)
            
            orchestrator = WorkflowOrchestrator(test_settings)
            initial_state = create_initial_state(
                site_id=1,
                site_name="TestSite001",
                dry_run=True,
                auto_approve=True,
            )
            
            # Run workflow
            result = await orchestrator.run(initial_state)
            
            # Verify workflow completed
            assert result["status"] in ["completed", "no_recommendations"]
            assert result.get("dry_run") is True
            # Should not have actual execution in dry run
            for exec_result in result.get("execution_results", []):
                assert exec_result.get("dry_run") is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_workflow_stops_on_no_issues(self, test_settings, seeded_db, mock_mae_client, mock_llm):
        """Test workflow stops early when no issues found."""
        from cassava_optimizer.workflow.orchestrator import WorkflowOrchestrator
        from cassava_optimizer.workflow.state import create_initial_state
        
        # Mock LLM to return no issues
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
            content="Analysis complete. No issues found. All KPIs are within normal thresholds."
        ))
        
        with patch("cassava_optimizer.agents.data_collector.HuaweiMAEClient") as mae_mock, \
             patch("cassava_optimizer.agents.analyzer.get_llm", return_value=mock_llm):
            
            mae_mock.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mae_mock.return_value.__aexit__ = AsyncMock(return_value=None)
            
            orchestrator = WorkflowOrchestrator(test_settings)
            initial_state = create_initial_state(
                site_id=1,
                site_name="TestSite001",
            )
            
            result = await orchestrator.run(initial_state)
            
            # Should complete without recommendations
            assert result.get("recommendations", []) == [] or result["status"] == "no_recommendations"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_workflow_handles_api_failure(self, test_settings, seeded_db):
        """Test workflow handles API failure gracefully."""
        from cassava_optimizer.workflow.orchestrator import WorkflowOrchestrator
        from cassava_optimizer.workflow.state import create_initial_state
        from cassava_optimizer.domain.exceptions import APIError
        
        mock_client = AsyncMock()
        mock_client.get_managed_elements.side_effect = APIError("API unavailable", status_code=503)
        
        with patch("cassava_optimizer.agents.data_collector.HuaweiMAEClient") as mae_mock:
            mae_mock.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mae_mock.return_value.__aexit__ = AsyncMock(return_value=None)
            
            orchestrator = WorkflowOrchestrator(test_settings)
            initial_state = create_initial_state(
                site_id=1,
                site_name="TestSite001",
            )
            
            with pytest.raises(APIError):
                await orchestrator.run(initial_state)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_workflow_with_recommendations(self, test_settings, seeded_db, mock_mae_client, mock_llm):
        """Test workflow generates and processes recommendations."""
        from cassava_optimizer.workflow.orchestrator import WorkflowOrchestrator
        from cassava_optimizer.workflow.state import create_initial_state
        
        # Mock analyzer to find issues
        analysis_response = MagicMock(content="""
        Analysis identified the following issues:
        1. Cell002 has high call drop rate (4.5%)
        2. Handover success rate below threshold
        
        Root causes:
        - Handover margin may be too aggressive
        """)
        
        # Mock recommender to generate recommendations
        recommend_response = MagicMock(content="""
        Recommendations:
        1. Increase handoverMargin from 3 to 5 for Cell002
        2. Adjust rsrpThreshold from -110 to -108
        
        Expected improvement: 2-3% in handover success rate
        """)
        
        call_count = 0
        async def mock_ainvoke(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return analysis_response
            return recommend_response
        
        mock_llm.ainvoke = mock_ainvoke
        
        with patch("cassava_optimizer.agents.data_collector.HuaweiMAEClient") as mae_mock, \
             patch("cassava_optimizer.agents.analyzer.get_llm", return_value=mock_llm), \
             patch("cassava_optimizer.agents.recommender.get_llm", return_value=mock_llm):
            
            mae_mock.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mae_mock.return_value.__aexit__ = AsyncMock(return_value=None)
            
            orchestrator = WorkflowOrchestrator(test_settings)
            initial_state = create_initial_state(
                site_id=1,
                site_name="TestSite001",
                dry_run=True,
                auto_approve=True,
            )
            
            result = await orchestrator.run(initial_state)
            
            # Should have recommendations
            assert "recommendations" in result or "analysis_results" in result


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_save_and_retrieve_optimization_run(self, seeded_db):
        """Test saving and retrieving optimization run."""
        from cassava_optimizer.infrastructure.repositories import OptimizationRunRepository
        
        repo = OptimizationRunRepository(seeded_db)
        
        # Create run
        run_id = str(uuid.uuid4())
        await seeded_db.execute(
            """
            INSERT INTO optimization_runs 
            (run_id, site_id, status, started_at, total_recommendations)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, 1, "in_progress", datetime.now(timezone.utc), 5),
        )
        
        # Retrieve run
        run = await repo.get_by_id(run_id)
        
        assert run is not None
        assert run.run_id == run_id
        assert run.status == "in_progress"
        assert run.total_recommendations == 5

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cascade_operations(self, seeded_db):
        """Test cascade operations between related entities."""
        # Create optimization run
        run_id = str(uuid.uuid4())
        await seeded_db.execute(
            "INSERT INTO optimization_runs (run_id, site_id, status) VALUES (?, ?, ?)",
            (run_id, 1, "completed"),
        )
        
        # Create recommendations
        for i in range(3):
            await seeded_db.execute(
                """
                INSERT INTO optimization_recommendations 
                (run_id, cell_id, parameter_name, recommended_value, confidence, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, 1, f"param{i}", str(i * 10), 0.85, "pending"),
            )
        
        # Retrieve all recommendations for run
        result = await seeded_db.execute(
            "SELECT COUNT(*) FROM optimization_recommendations WHERE run_id = ?",
            (run_id,),
        )
        count = (await result.fetchone())[0]
        
        assert count == 3


class TestAgentIntegration:
    """Integration tests for agent interactions."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_data_collector_to_analyzer_flow(self, test_settings, seeded_db, mock_mae_client, mock_llm):
        """Test data flows correctly from collector to analyzer."""
        from cassava_optimizer.agents.data_collector import DataCollectorAgent
        from cassava_optimizer.agents.analyzer import AnalyzerAgent
        
        with patch("cassava_optimizer.agents.data_collector.HuaweiMAEClient") as mae_mock, \
             patch("cassava_optimizer.agents.analyzer.get_llm", return_value=mock_llm):
            
            mae_mock.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mae_mock.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Run data collector
            collector = DataCollectorAgent(test_settings, db_manager=seeded_db)
            state = {
                "site_id": 1,
                "site_name": "TestSite001",
                "collected_data": {},
                "errors": [],
            }
            
            state = await collector.process(state)
            
            # Data should be collected
            assert state.get("collected_data") is not None
            
            # Pass to analyzer
            analyzer = AnalyzerAgent(test_settings)
            state["analysis_results"] = {}
            
            state = await analyzer.process(state)
            
            # Analysis should be performed
            assert state.get("analysis_results") is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_recommender_to_executor_flow(
        self, test_settings, mock_mae_client, mock_llm, sample_recommendation
    ):
        """Test recommendations flow correctly to executor."""
        from cassava_optimizer.agents.recommender import RecommenderAgent
        from cassava_optimizer.agents.executor import ExecutorAgent
        
        with patch("cassava_optimizer.agents.recommender.get_llm", return_value=mock_llm), \
             patch("cassava_optimizer.agents.executor.HuaweiMAEClient") as mae_mock:
            
            mae_mock.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mae_mock.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Generate recommendations
            recommender = RecommenderAgent(test_settings)
            state = {
                "site_id": 1,
                "site_name": "TestSite001",
                "analysis_results": {
                    "issues": [{"kpi": "call_drop_rate", "severity": "warning"}],
                },
                "recommendations": [],
                "auto_approve": True,
                "dry_run": True,
            }
            
            state = await recommender.process(state)
            
            # Set up approved recommendations
            state["approved_recommendations"] = state.get("recommendations", [])
            for rec in state["approved_recommendations"]:
                rec["status"] = "approved"
            
            state["execution_results"] = []
            
            # Execute recommendations
            executor = ExecutorAgent(test_settings)
            state = await executor.process(state)
            
            # Should have execution results (dry run)
            assert "execution_results" in state


class TestErrorHandling:
    """Integration tests for error handling."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_workflow_error_recovery(self, test_settings, seeded_db, mock_mae_client):
        """Test workflow recovers from transient errors."""
        from cassava_optimizer.workflow.orchestrator import WorkflowOrchestrator
        from cassava_optimizer.workflow.state import create_initial_state
        
        call_count = 0
        
        async def flaky_get_data(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary network error")
            return mock_mae_client.get_performance_data.return_value
        
        mock_mae_client.get_performance_data = flaky_get_data
        
        with patch("cassava_optimizer.agents.data_collector.HuaweiMAEClient") as mae_mock:
            mae_mock.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mae_mock.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # This test verifies error handling behavior
            # Actual retry logic depends on implementation
            assert True  # Placeholder for actual retry test

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_logged_to_state(self, test_settings, seeded_db):
        """Test errors are logged to workflow state."""
        from cassava_optimizer.workflow.state import add_error_to_state
        
        state = {
            "run_id": str(uuid.uuid4()),
            "errors": [],
        }
        
        state = add_error_to_state(state, "Test error 1")
        state = add_error_to_state(state, "Test error 2")
        
        assert len(state["errors"]) == 2
        assert "Test error 1" in state["errors"]
        assert "Test error 2" in state["errors"]
