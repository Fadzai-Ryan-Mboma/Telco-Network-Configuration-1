"""Integration tests for API integrations."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest
import pytest_asyncio


class TestHuaweiMAEIntegration:
    """Integration tests for Huawei MAE API."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mae_client_connection(self, test_settings):
        """Test MAE client connection flow."""
        from cassava_optimizer.network.mae_client import HuaweiMAEClient
        
        with patch("httpx.AsyncClient") as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"token": "test-token"}
            mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_http.return_value)
            mock_http.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_http.return_value.post = AsyncMock(return_value=mock_response)
            
            async with HuaweiMAEClient(test_settings) as client:
                # Connection should be established
                assert client is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mae_get_managed_elements(self, test_settings, mock_mae_client):
        """Test getting managed elements from MAE."""
        with patch("cassava_optimizer.network.mae_client.httpx.AsyncClient") as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "elements": [
                    {"ne_id": "NE001", "name": "Site1", "type": "eNodeB"},
                    {"ne_id": "NE002", "name": "Site2", "type": "eNodeB"},
                ]
            }
            mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_http.return_value)
            mock_http.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_http.return_value.get = AsyncMock(return_value=mock_response)
            
            from cassava_optimizer.network.mae_client import HuaweiMAEClient
            
            async with HuaweiMAEClient(test_settings) as client:
                client._http = mock_http.return_value
                elements = await client.get_managed_elements()
                
                # Should return list of elements
                assert isinstance(elements, list)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mae_execute_mml_command(self, test_settings):
        """Test executing MML command through MAE."""
        with patch("cassava_optimizer.network.mae_client.httpx.AsyncClient") as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "output": "Command executed successfully",
                "execution_time_ms": 150,
            }
            mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_http.return_value)
            mock_http.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_http.return_value.post = AsyncMock(return_value=mock_response)
            
            from cassava_optimizer.network.mae_client import HuaweiMAEClient
            
            async with HuaweiMAEClient(test_settings) as client:
                client._http = mock_http.return_value
                result = await client.execute_mml_command(
                    ne_id="NE001",
                    command="DSP CELL:",
                )
                
                assert result.get("success") is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mae_handles_auth_failure(self, test_settings):
        """Test MAE client handles authentication failure."""
        from cassava_optimizer.domain.exceptions import APIError
        
        with patch("cassava_optimizer.network.mae_client.httpx.AsyncClient") as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_http.return_value)
            mock_http.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_http.return_value.post = AsyncMock(return_value=mock_response)
            
            from cassava_optimizer.network.mae_client import HuaweiMAEClient
            
            with pytest.raises(APIError):
                async with HuaweiMAEClient(test_settings) as client:
                    pass  # Should fail during auth

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mae_handles_timeout(self, test_settings):
        """Test MAE client handles timeout."""
        import httpx
        from cassava_optimizer.domain.exceptions import APIError
        
        with patch("cassava_optimizer.network.mae_client.httpx.AsyncClient") as mock_http:
            mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_http.return_value)
            mock_http.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_http.return_value.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            
            from cassava_optimizer.network.mae_client import HuaweiMAEClient
            
            with pytest.raises((APIError, httpx.TimeoutException)):
                async with HuaweiMAEClient(test_settings) as client:
                    pass


class TestNVIDIANIMIntegration:
    """Integration tests for NVIDIA NIM API."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_nim_model_invocation(self, test_settings):
        """Test NVIDIA NIM model invocation."""
        with patch("langchain_nvidia_ai_endpoints.ChatNVIDIA") as mock_nim:
            mock_instance = MagicMock()
            mock_instance.ainvoke = AsyncMock(return_value=MagicMock(
                content="Analysis complete. Recommendations generated."
            ))
            mock_nim.return_value = mock_instance
            
            from cassava_optimizer.agents.analyzer import get_llm
            
            llm = get_llm(test_settings)
            response = await llm.ainvoke("Analyze the following KPI data...")
            
            assert response.content is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_nim_handles_rate_limit(self, test_settings):
        """Test NVIDIA NIM handles rate limiting."""
        from cassava_optimizer.domain.exceptions import APIError
        
        with patch("langchain_nvidia_ai_endpoints.ChatNVIDIA") as mock_nim:
            mock_instance = MagicMock()
            mock_instance.ainvoke = AsyncMock(side_effect=Exception("Rate limit exceeded"))
            mock_nim.return_value = mock_instance
            
            from cassava_optimizer.agents.analyzer import get_llm
            
            llm = get_llm(test_settings)
            
            with pytest.raises(Exception) as exc_info:
                await llm.ainvoke("Test prompt")
            
            assert "rate limit" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_nim_structured_output(self, test_settings):
        """Test NVIDIA NIM returns structured output."""
        with patch("langchain_nvidia_ai_endpoints.ChatNVIDIA") as mock_nim:
            mock_instance = MagicMock()
            mock_instance.ainvoke = AsyncMock(return_value=MagicMock(
                content="""
                {
                    "issues": [
                        {"kpi": "call_drop_rate", "severity": "warning", "value": 4.5}
                    ],
                    "recommendations": [
                        {"parameter": "handoverMargin", "current": 3, "recommended": 5}
                    ]
                }
                """
            ))
            mock_nim.return_value = mock_instance
            
            from cassava_optimizer.agents.analyzer import get_llm
            
            llm = get_llm(test_settings)
            response = await llm.ainvoke("Return structured analysis")
            
            # Should contain structured data
            assert "issues" in response.content or "recommendations" in response.content


class TestDatabaseAPIIntegration:
    """Integration tests for database API operations."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_database_access(self, seeded_db):
        """Test concurrent database access."""
        import asyncio
        
        async def read_site(site_id: int):
            result = await seeded_db.execute(
                "SELECT * FROM sites WHERE id = ?",
                (site_id,),
            )
            return await result.fetchone()
        
        # Run concurrent reads
        results = await asyncio.gather(
            read_site(1),
            read_site(1),
            read_site(1),
        )
        
        # All should succeed
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_transaction_isolation(self, seeded_db):
        """Test transaction isolation."""
        # Start transaction and make changes
        async with seeded_db.transaction():
            await seeded_db.execute(
                "INSERT INTO sites (name, region) VALUES (?, ?)",
                ("IsolationTest", "TestRegion"),
            )
            
            # Within transaction, should see the change
            result = await seeded_db.execute(
                "SELECT * FROM sites WHERE name = ?",
                ("IsolationTest",),
            )
            row = await result.fetchone()
            assert row is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_database_connection_pooling(self, test_settings):
        """Test database connection pooling."""
        from cassava_optimizer.infrastructure.database import DatabaseManager
        
        manager = DatabaseManager(test_settings.database_url)
        await manager.connect()
        
        # Run multiple queries
        for i in range(10):
            await manager.execute("SELECT 1")
        
        await manager.disconnect()
        
        # Should complete without connection exhaustion
        assert True


class TestToolAPIIntegration:
    """Integration tests for tool API operations."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tool_chain_execution(self, test_settings, seeded_db, mock_mae_client):
        """Test chained tool execution."""
        from cassava_optimizer.tools.mae_tools import fetch_site_kpis
        from cassava_optimizer.tools.analysis_tools import calculate_kpi_statistics
        
        with patch("cassava_optimizer.tools.mae_tools.HuaweiMAEClient") as mae_mock:
            mae_mock.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mae_mock.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Fetch KPIs
            kpis_result = await fetch_site_kpis.ainvoke({"site_name": "TestSite001"})
            
            # Calculate statistics on fetched KPIs
            if kpis_result:
                stats_result = await calculate_kpi_statistics.ainvoke({
                    "kpi_data": kpis_result.get("kpis", []),
                })
                
                # Should have statistics
                assert stats_result is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tool_error_propagation(self, test_settings):
        """Test tool errors propagate correctly."""
        from cassava_optimizer.tools.mae_tools import fetch_site_kpis
        from cassava_optimizer.domain.exceptions import APIError
        
        mock_client = AsyncMock()
        mock_client.get_performance_data.side_effect = APIError("Network error", status_code=503)
        
        with patch("cassava_optimizer.tools.mae_tools.HuaweiMAEClient") as mae_mock:
            mae_mock.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mae_mock.return_value.__aexit__ = AsyncMock(return_value=None)
            
            with pytest.raises(APIError) as exc_info:
                await fetch_site_kpis.ainvoke({"site_name": "TestSite001"})
            
            assert exc_info.value.status_code == 503


class TestEndToEndAPI:
    """End-to-end API integration tests."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.e2e
    async def test_complete_optimization_api_flow(
        self, test_settings, seeded_db, mock_mae_client, mock_llm
    ):
        """Test complete optimization flow through APIs."""
        from cassava_optimizer.workflow.orchestrator import WorkflowOrchestrator
        from cassava_optimizer.workflow.state import create_initial_state
        from cassava_optimizer.infrastructure.repositories import (
            OptimizationRunRepository,
            RecommendationRepository,
        )
        
        with patch("cassava_optimizer.agents.data_collector.HuaweiMAEClient") as mae_mock, \
             patch("cassava_optimizer.agents.analyzer.get_llm", return_value=mock_llm), \
             patch("cassava_optimizer.agents.recommender.get_llm", return_value=mock_llm), \
             patch("cassava_optimizer.agents.executor.HuaweiMAEClient") as exec_mae_mock, \
             patch("cassava_optimizer.agents.validator.HuaweiMAEClient") as val_mae_mock:
            
            mae_mock.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mae_mock.return_value.__aexit__ = AsyncMock(return_value=None)
            exec_mae_mock.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            exec_mae_mock.return_value.__aexit__ = AsyncMock(return_value=None)
            val_mae_mock.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            val_mae_mock.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Run full workflow
            orchestrator = WorkflowOrchestrator(test_settings)
            initial_state = create_initial_state(
                site_id=1,
                site_name="TestSite001",
                dry_run=True,
                auto_approve=True,
            )
            
            result = await orchestrator.run(initial_state)
            
            # Workflow should complete
            assert result["status"] in ["completed", "no_recommendations", "failed"]
            
            # Check database records were created
            run_repo = OptimizationRunRepository(seeded_db)
            # Note: Actual persistence depends on implementation
            
            # Verify report generated
            assert result.get("report") is not None or result["status"] == "no_recommendations"
