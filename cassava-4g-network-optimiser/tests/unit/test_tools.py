"""Unit tests for tools layer."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio


class TestMAETools:
    """Tests for Huawei MAE tools."""

    @pytest.mark.asyncio
    async def test_fetch_site_kpis(self, test_settings, mock_mae_client):
        """Test fetch_site_kpis tool."""
        from cassava_optimizer.tools.mae_tools import fetch_site_kpis
        
        with patch("cassava_optimizer.tools.mae_tools.HuaweiMAEClient") as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await fetch_site_kpis.ainvoke({"site_name": "TestSite001"})
            
            assert result is not None
            assert "kpis" in result or isinstance(result, list)

    @pytest.mark.asyncio
    async def test_check_site_health(self, test_settings, mock_mae_client):
        """Test check_site_health tool."""
        from cassava_optimizer.tools.mae_tools import check_site_health
        
        with patch("cassava_optimizer.tools.mae_tools.HuaweiMAEClient") as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await check_site_health.ainvoke({"site_name": "TestSite001"})
            
            assert result is not None
            assert "status" in result or "health" in result

    @pytest.mark.asyncio
    async def test_get_cell_configuration(self, test_settings, mock_mae_client):
        """Test get_cell_configuration tool."""
        from cassava_optimizer.tools.mae_tools import get_cell_configuration
        
        with patch("cassava_optimizer.tools.mae_tools.HuaweiMAEClient") as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await get_cell_configuration.ainvoke({
                "site_name": "TestSite001",
                "cell_id": "Cell001",
            })
            
            assert result is not None
            assert "parameters" in result or "config" in result

    @pytest.mark.asyncio
    async def test_execute_mml_command(self, test_settings, mock_mae_client):
        """Test execute_mml_command tool."""
        from cassava_optimizer.tools.mae_tools import execute_mml_command
        
        with patch("cassava_optimizer.tools.mae_tools.HuaweiMAEClient") as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_mae_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await execute_mml_command.ainvoke({
                "ne_id": "NE001",
                "command": "DSP CELL:",
            })
            
            assert result is not None
            assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_tool_fails_fast_on_error(self, test_settings):
        """Test tools fail fast on API errors."""
        from cassava_optimizer.tools.mae_tools import fetch_site_kpis
        from cassava_optimizer.domain.exceptions import APIError
        
        mock_client = AsyncMock()
        mock_client.get_performance_data.side_effect = APIError("Connection refused", status_code=503)
        
        with patch("cassava_optimizer.tools.mae_tools.HuaweiMAEClient") as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            with pytest.raises(APIError):
                await fetch_site_kpis.ainvoke({"site_name": "TestSite001"})


class TestDBTools:
    """Tests for database tools."""

    @pytest.mark.asyncio
    async def test_get_site_info(self, seeded_db):
        """Test get_site_info tool."""
        from cassava_optimizer.tools.db_tools import get_site_info
        
        with patch("cassava_optimizer.tools.db_tools.get_db_manager", return_value=seeded_db):
            result = await get_site_info.ainvoke({"site_name": "TestSite001"})
            
            assert result is not None
            assert result.get("name") == "TestSite001"

    @pytest.mark.asyncio
    async def test_get_cells_for_site(self, seeded_db):
        """Test get_cells_for_site tool."""
        from cassava_optimizer.tools.db_tools import get_cells_for_site
        
        with patch("cassava_optimizer.tools.db_tools.get_db_manager", return_value=seeded_db):
            result = await get_cells_for_site.ainvoke({"site_id": 1})
            
            assert result is not None
            assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_kpi_history(self, seeded_db):
        """Test get_kpi_history tool."""
        from cassava_optimizer.tools.db_tools import get_kpi_history
        
        with patch("cassava_optimizer.tools.db_tools.get_db_manager", return_value=seeded_db):
            result = await get_kpi_history.ainvoke({
                "cell_id": 1,
                "kpi_name": "call_setup_success_rate",
            })
            
            assert result is not None
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_save_recommendation(self, seeded_db, sample_recommendation):
        """Test save_recommendation tool."""
        from cassava_optimizer.tools.db_tools import save_recommendation
        
        # Create optimization run first
        await seeded_db.execute(
            "INSERT INTO optimization_runs (run_id, site_id, status) VALUES (?, ?, ?)",
            (sample_recommendation["run_id"], 1, "in_progress"),
        )
        
        with patch("cassava_optimizer.tools.db_tools.get_db_manager", return_value=seeded_db):
            result = await save_recommendation.ainvoke({
                "recommendation": sample_recommendation,
            })
            
            assert result is not None
            assert result.get("saved") is True

    @pytest.mark.asyncio
    async def test_get_pending_recommendations(self, seeded_db):
        """Test get_pending_recommendations tool."""
        from cassava_optimizer.tools.db_tools import get_pending_recommendations
        
        # Create test data
        run_id = "test-run-tool"
        await seeded_db.execute(
            "INSERT INTO optimization_runs (run_id, site_id, status) VALUES (?, ?, ?)",
            (run_id, 1, "completed"),
        )
        await seeded_db.execute(
            """
            INSERT INTO optimization_recommendations 
            (run_id, cell_id, parameter_name, recommended_value, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, 1, "testParam", "10", "pending"),
        )
        
        with patch("cassava_optimizer.tools.db_tools.get_db_manager", return_value=seeded_db):
            result = await get_pending_recommendations.ainvoke({})
            
            assert result is not None
            assert len(result) >= 1


class TestAnalysisTools:
    """Tests for analysis tools."""

    @pytest.mark.asyncio
    async def test_calculate_kpi_statistics(self, sample_kpi_data):
        """Test calculate_kpi_statistics tool."""
        from cassava_optimizer.tools.analysis_tools import calculate_kpi_statistics
        
        result = await calculate_kpi_statistics.ainvoke({
            "kpi_data": sample_kpi_data,
        })
        
        assert result is not None
        assert "statistics" in result or "mean" in result

    @pytest.mark.asyncio
    async def test_identify_anomalies(self, sample_kpi_data):
        """Test identify_anomalies tool."""
        from cassava_optimizer.tools.analysis_tools import identify_anomalies
        
        # Add an anomaly
        kpi_data = sample_kpi_data + [
            {"kpi_name": "call_drop_rate", "value": 25.0, "unit": "%", "timestamp": datetime.now(timezone.utc)},
        ]
        
        result = await identify_anomalies.ainvoke({
            "kpi_data": kpi_data,
        })
        
        assert result is not None
        assert "anomalies" in result or isinstance(result, list)

    @pytest.mark.asyncio
    async def test_compare_with_thresholds(self, sample_kpi_data):
        """Test compare_with_thresholds tool."""
        from cassava_optimizer.tools.analysis_tools import compare_with_thresholds
        
        thresholds = {
            "call_setup_success_rate": {"warning": 95.0, "critical": 90.0},
            "call_drop_rate": {"warning": 2.0, "critical": 5.0},
        }
        
        result = await compare_with_thresholds.ainvoke({
            "kpi_data": sample_kpi_data,
            "thresholds": thresholds,
        })
        
        assert result is not None
        assert "status" in result or "violations" in result

    @pytest.mark.asyncio
    async def test_calculate_trend(self):
        """Test calculate_trend tool."""
        from cassava_optimizer.tools.analysis_tools import calculate_trend
        
        # Create time series data
        now = datetime.now(timezone.utc)
        data_points = [
            {"value": 95.0, "timestamp": now},
            {"value": 94.5, "timestamp": now},
            {"value": 94.0, "timestamp": now},
            {"value": 93.5, "timestamp": now},
        ]
        
        result = await calculate_trend.ainvoke({
            "data_points": data_points,
        })
        
        assert result is not None
        assert "trend" in result or "direction" in result

    @pytest.mark.asyncio
    async def test_generate_mml_command(self):
        """Test generate_mml_command tool."""
        from cassava_optimizer.tools.analysis_tools import generate_mml_command
        
        result = await generate_mml_command.ainvoke({
            "parameter_name": "handoverMargin",
            "new_value": "5",
            "cell_id": "Cell001",
        })
        
        assert result is not None
        assert "command" in result or "mml" in result


class TestToolValidation:
    """Tests for tool input validation."""

    @pytest.mark.asyncio
    async def test_site_name_required(self):
        """Test site_name is required for site tools."""
        from cassava_optimizer.tools.mae_tools import fetch_site_kpis
        
        with pytest.raises((ValueError, KeyError, TypeError)):
            await fetch_site_kpis.ainvoke({})

    @pytest.mark.asyncio
    async def test_cell_id_required_for_cell_tools(self):
        """Test cell_id is required for cell tools."""
        from cassava_optimizer.tools.db_tools import get_kpi_history
        
        with pytest.raises((ValueError, KeyError, TypeError)):
            await get_kpi_history.ainvoke({"kpi_name": "test"})

    @pytest.mark.asyncio
    async def test_empty_data_handled(self):
        """Test empty data is handled gracefully."""
        from cassava_optimizer.tools.analysis_tools import calculate_kpi_statistics
        
        result = await calculate_kpi_statistics.ainvoke({
            "kpi_data": [],
        })
        
        # Should return empty result, not raise
        assert result is not None
