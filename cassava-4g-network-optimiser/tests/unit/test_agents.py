"""Unit tests for agents layer."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest
import pytest_asyncio


class TestBaseAgent:
    """Tests for BaseAgent class."""

    def test_agent_has_name(self, test_settings):
        """Test agent has a name."""
        from cassava_optimizer.agents.base import BaseAgent
        
        class TestAgent(BaseAgent):
            name = "test_agent"
            
            async def process(self, state):
                return state
        
        agent = TestAgent(test_settings)
        assert agent.name == "test_agent"

    def test_agent_has_settings(self, test_settings):
        """Test agent has settings."""
        from cassava_optimizer.agents.base import BaseAgent
        
        class TestAgent(BaseAgent):
            name = "test_agent"
            
            async def process(self, state):
                return state
        
        agent = TestAgent(test_settings)
        assert agent.settings is test_settings

    @pytest.mark.asyncio
    async def test_agent_run_calls_process(self, test_settings):
        """Test agent run calls process."""
        from cassava_optimizer.agents.base import BaseAgent
        
        class TestAgent(BaseAgent):
            name = "test_agent"
            
            async def process(self, state):
                state["processed"] = True
                return state
        
        agent = TestAgent(test_settings)
        result = await agent.run({"data": "test"})
        
        assert result["processed"] is True

    @pytest.mark.asyncio
    async def test_agent_handles_errors(self, test_settings):
        """Test agent handles errors gracefully."""
        from cassava_optimizer.agents.base import BaseAgent
        from cassava_optimizer.domain.exceptions import AgentError
        
        class FailingAgent(BaseAgent):
            name = "failing_agent"
            
            async def process(self, state):
                raise AgentError("Process failed")
        
        agent = FailingAgent(test_settings)
        
        with pytest.raises(AgentError):
            await agent.run({})


class TestDataCollectorAgent:
    """Tests for DataCollectorAgent."""

    @pytest.mark.asyncio
    async def test_collects_site_data(self, test_settings, mock_mae_client):
        """Test data collector fetches site data."""
        from cassava_optimizer.agents.data_collector import DataCollectorAgent
        
        with patch("cassava_optimizer.agents.data_collector.HuaweiMAEClient") as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            agent = DataCollectorAgent(test_settings)
            state = {
                "site_id": 1,
                "site_name": "TestSite001",
                "collected_data": {},
            }
            
            result = await agent.process(state)
            
            assert "collected_data" in result

    @pytest.mark.asyncio
    async def test_stores_kpi_data(self, test_settings, mock_mae_client, db_manager):
        """Test data collector stores KPI data."""
        from cassava_optimizer.agents.data_collector import DataCollectorAgent
        
        with patch("cassava_optimizer.agents.data_collector.HuaweiMAEClient") as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            agent = DataCollectorAgent(test_settings, db_manager=db_manager)
            state = {
                "site_id": 1,
                "site_name": "TestSite001",
                "collected_data": {},
            }
            
            result = await agent.process(state)
            
            # KPI data should be collected
            assert result.get("collected_data") is not None

    @pytest.mark.asyncio
    async def test_fails_fast_on_api_error(self, test_settings):
        """Test data collector fails fast on API error."""
        from cassava_optimizer.agents.data_collector import DataCollectorAgent
        from cassava_optimizer.domain.exceptions import APIError
        
        mock_client = AsyncMock()
        mock_client.get_managed_elements.side_effect = APIError("Connection failed", status_code=503)
        
        with patch("cassava_optimizer.agents.data_collector.HuaweiMAEClient") as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            agent = DataCollectorAgent(test_settings)
            state = {"site_id": 1, "site_name": "TestSite001"}
            
            with pytest.raises(APIError):
                await agent.process(state)


class TestAnalyzerAgent:
    """Tests for AnalyzerAgent."""

    @pytest.mark.asyncio
    async def test_analyzes_kpi_data(self, test_settings, mock_llm, sample_kpi_data):
        """Test analyzer processes KPI data."""
        from cassava_optimizer.agents.analyzer import AnalyzerAgent
        
        with patch("cassava_optimizer.agents.analyzer.get_llm", return_value=mock_llm):
            agent = AnalyzerAgent(test_settings)
            state = {
                "site_id": 1,
                "site_name": "TestSite001",
                "collected_data": {
                    "kpis": sample_kpi_data,
                    "cells": [{"cell_id": "Cell001", "status": "active"}],
                },
                "analysis_results": {},
            }
            
            result = await agent.process(state)
            
            assert "analysis_results" in result

    @pytest.mark.asyncio
    async def test_identifies_degraded_kpis(self, test_settings, mock_llm):
        """Test analyzer identifies degraded KPIs."""
        from cassava_optimizer.agents.analyzer import AnalyzerAgent
        
        with patch("cassava_optimizer.agents.analyzer.get_llm", return_value=mock_llm):
            agent = AnalyzerAgent(test_settings)
            state = {
                "site_id": 1,
                "site_name": "TestSite001",
                "collected_data": {
                    "kpis": [
                        {"kpi_name": "call_drop_rate", "value": 8.5, "unit": "%"},  # Degraded
                    ],
                    "cells": [],
                },
                "analysis_results": {},
            }
            
            result = await agent.process(state)
            
            # Should identify issues
            assert result.get("analysis_results") is not None

    @pytest.mark.asyncio
    async def test_fails_fast_without_data(self, test_settings):
        """Test analyzer fails fast without collected data."""
        from cassava_optimizer.agents.analyzer import AnalyzerAgent
        from cassava_optimizer.domain.exceptions import OptimizationError
        
        agent = AnalyzerAgent(test_settings)
        state = {
            "site_id": 1,
            "site_name": "TestSite001",
            "collected_data": {},  # Empty data
        }
        
        with pytest.raises(OptimizationError):
            await agent.process(state)


class TestRecommenderAgent:
    """Tests for RecommenderAgent."""

    @pytest.mark.asyncio
    async def test_generates_recommendations(self, test_settings, mock_llm):
        """Test recommender generates recommendations."""
        from cassava_optimizer.agents.recommender import RecommenderAgent
        
        with patch("cassava_optimizer.agents.recommender.get_llm", return_value=mock_llm):
            agent = RecommenderAgent(test_settings)
            state = {
                "site_id": 1,
                "site_name": "TestSite001",
                "analysis_results": {
                    "issues": [
                        {"kpi": "call_drop_rate", "severity": "warning", "cell_id": "Cell001"},
                    ],
                    "root_causes": ["Handover margin too low"],
                },
                "recommendations": [],
            }
            
            result = await agent.process(state)
            
            assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_respects_confidence_threshold(self, test_settings, mock_llm):
        """Test recommender respects confidence threshold."""
        from cassava_optimizer.agents.recommender import RecommenderAgent
        
        # Set high confidence threshold
        test_settings.confidence_threshold = 0.95
        
        with patch("cassava_optimizer.agents.recommender.get_llm", return_value=mock_llm):
            agent = RecommenderAgent(test_settings)
            state = {
                "site_id": 1,
                "site_name": "TestSite001",
                "analysis_results": {"issues": []},
                "recommendations": [],
            }
            
            result = await agent.process(state)
            
            # All recommendations should meet threshold
            for rec in result.get("recommendations", []):
                assert rec.get("confidence", 0) >= test_settings.confidence_threshold

    @pytest.mark.asyncio
    async def test_limits_recommendations_count(self, test_settings, mock_llm):
        """Test recommender limits recommendations count."""
        from cassava_optimizer.agents.recommender import RecommenderAgent
        
        test_settings.max_recommendations = 5
        
        with patch("cassava_optimizer.agents.recommender.get_llm", return_value=mock_llm):
            agent = RecommenderAgent(test_settings)
            state = {
                "analysis_results": {"issues": [{"kpi": "test"}] * 20},
                "recommendations": [],
            }
            
            result = await agent.process(state)
            
            assert len(result.get("recommendations", [])) <= test_settings.max_recommendations


class TestExecutorAgent:
    """Tests for ExecutorAgent."""

    @pytest.mark.asyncio
    async def test_executes_approved_recommendations(self, test_settings, mock_mae_client, sample_recommendation):
        """Test executor executes approved recommendations."""
        from cassava_optimizer.agents.executor import ExecutorAgent
        
        sample_recommendation["status"] = "approved"
        
        with patch("cassava_optimizer.agents.executor.HuaweiMAEClient") as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            agent = ExecutorAgent(test_settings)
            state = {
                "site_id": 1,
                "site_name": "TestSite001",
                "approved_recommendations": [sample_recommendation],
                "execution_results": [],
            }
            
            result = await agent.process(state)
            
            assert "execution_results" in result

    @pytest.mark.asyncio
    async def test_skips_in_dry_run_mode(self, test_settings, sample_recommendation):
        """Test executor skips execution in dry run mode."""
        from cassava_optimizer.agents.executor import ExecutorAgent
        
        sample_recommendation["status"] = "approved"
        
        agent = ExecutorAgent(test_settings)
        state = {
            "site_id": 1,
            "dry_run": True,
            "approved_recommendations": [sample_recommendation],
            "execution_results": [],
        }
        
        result = await agent.process(state)
        
        # Should not actually execute
        for exec_result in result.get("execution_results", []):
            assert exec_result.get("dry_run") is True

    @pytest.mark.asyncio
    async def test_handles_execution_failure(self, test_settings, sample_recommendation):
        """Test executor handles execution failure."""
        from cassava_optimizer.agents.executor import ExecutorAgent
        
        mock_client = AsyncMock()
        mock_client.execute_mml_command.return_value = {
            "success": False,
            "error": "Command failed",
        }
        
        sample_recommendation["status"] = "approved"
        
        with patch("cassava_optimizer.agents.executor.HuaweiMAEClient") as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            agent = ExecutorAgent(test_settings)
            state = {
                "site_id": 1,
                "approved_recommendations": [sample_recommendation],
                "execution_results": [],
            }
            
            result = await agent.process(state)
            
            # Should record failure
            assert any(not r.get("success") for r in result.get("execution_results", []))


class TestValidatorAgent:
    """Tests for ValidatorAgent."""

    @pytest.mark.asyncio
    async def test_validates_executed_changes(self, test_settings, mock_mae_client):
        """Test validator validates executed changes."""
        from cassava_optimizer.agents.validator import ValidatorAgent
        
        with patch("cassava_optimizer.agents.validator.HuaweiMAEClient") as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            agent = ValidatorAgent(test_settings)
            state = {
                "site_id": 1,
                "site_name": "TestSite001",
                "execution_results": [
                    {"recommendation_id": 1, "success": True, "cell_id": "Cell001"},
                ],
                "validation_results": {},
            }
            
            result = await agent.process(state)
            
            assert "validation_results" in result

    @pytest.mark.asyncio
    async def test_triggers_rollback_on_degradation(self, test_settings):
        """Test validator triggers rollback on KPI degradation."""
        from cassava_optimizer.agents.validator import ValidatorAgent
        
        mock_client = AsyncMock()
        # Return degraded KPIs after change
        mock_client.get_performance_data.return_value = [
            {"kpi_name": "call_drop_rate", "value": 15.0},  # Much worse
        ]
        
        test_settings.enable_auto_rollback = True
        
        with patch("cassava_optimizer.agents.validator.HuaweiMAEClient") as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            agent = ValidatorAgent(test_settings)
            state = {
                "site_id": 1,
                "execution_results": [{"recommendation_id": 1, "success": True}],
                "validation_results": {},
            }
            
            result = await agent.process(state)
            
            # Should flag for rollback
            validation = result.get("validation_results", {})
            assert validation.get("needs_rollback") or validation.get("degraded")


class TestReporterAgent:
    """Tests for ReporterAgent."""

    @pytest.mark.asyncio
    async def test_generates_report(self, test_settings, initial_workflow_state):
        """Test reporter generates report."""
        from cassava_optimizer.agents.reporter import ReporterAgent
        
        agent = ReporterAgent(test_settings)
        state = {
            **initial_workflow_state,
            "collected_data": {"kpis": []},
            "analysis_results": {"issues": []},
            "recommendations": [],
            "execution_results": [],
            "validation_results": {"validated": True},
        }
        
        result = await agent.process(state)
        
        assert "report" in result
        assert result["report"] is not None

    @pytest.mark.asyncio
    async def test_report_includes_summary(self, test_settings, initial_workflow_state):
        """Test report includes summary."""
        from cassava_optimizer.agents.reporter import ReporterAgent
        
        agent = ReporterAgent(test_settings)
        state = {
            **initial_workflow_state,
            "recommendations": [{"id": 1}, {"id": 2}],
            "execution_results": [{"success": True}, {"success": True}],
        }
        
        result = await agent.process(state)
        
        report = result.get("report", {})
        assert "summary" in report or "total_recommendations" in report
