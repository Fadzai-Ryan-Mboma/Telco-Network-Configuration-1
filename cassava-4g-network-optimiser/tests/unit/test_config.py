"""Unit tests for configuration module."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError


class TestSettings:
    """Tests for Settings class."""

    def test_settings_loads_from_env(self):
        """Test that settings load from environment variables."""
        env_vars = {
            "NVIDIA_API_KEY": "test-nvidia-key",
            "HUAWEI_MAE_URL": "https://test.huawei.com",
            "HUAWEI_MAE_USERNAME": "test_user",
            "HUAWEI_MAE_PASSWORD": "test_pass",
            "DATABASE_URL": "sqlite+aiosqlite:///test.db",
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            from cassava_optimizer.config.settings import Settings
            settings = Settings()
            
            assert settings.nvidia_api_key == "test-nvidia-key"
            assert settings.huawei_mae_url == "https://test.huawei.com"
            assert settings.huawei_mae_username == "test_user"

    def test_settings_validates_required_fields(self):
        """Test that settings validates required fields."""
        # Clear relevant env vars
        env_vars = {
            "NVIDIA_API_KEY": "",
            "HUAWEI_MAE_URL": "",
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            from cassava_optimizer.config.settings import Settings
            # Should raise validation error for empty required fields
            with pytest.raises(ValidationError):
                Settings(nvidia_api_key="")

    def test_database_url_default(self):
        """Test default database URL."""
        from cassava_optimizer.config.settings import Settings
        
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "test"}, clear=False):
            settings = Settings()
            assert "cassava_network.db" in settings.database_url

    def test_log_level_default(self):
        """Test default log level."""
        from cassava_optimizer.config.settings import Settings
        
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "test"}, clear=False):
            settings = Settings()
            assert settings.log_level in ["INFO", "DEBUG"]


class TestConstants:
    """Tests for constants module."""

    def test_kpi_names_defined(self):
        """Test that KPI names are defined."""
        from cassava_optimizer.config.constants import KPINames
        
        assert hasattr(KPINames, "CALL_SETUP_SUCCESS_RATE")
        assert hasattr(KPINames, "CALL_DROP_RATE")
        assert hasattr(KPINames, "HANDOVER_SUCCESS_RATE")

    def test_agent_names_defined(self):
        """Test that agent names are defined."""
        from cassava_optimizer.config.constants import AgentNames
        
        assert hasattr(AgentNames, "DATA_COLLECTOR")
        assert hasattr(AgentNames, "ANALYZER")
        assert hasattr(AgentNames, "RECOMMENDER")
        assert hasattr(AgentNames, "EXECUTOR")
        assert hasattr(AgentNames, "VALIDATOR")
        assert hasattr(AgentNames, "REPORTER")

    def test_cassava_branding_colors(self):
        """Test Cassava branding colors are defined."""
        from cassava_optimizer.config.constants import CassavaBranding
        
        assert CassavaBranding.NAVY == "#001D58"
        assert CassavaBranding.GREEN == "#00F19C"
        assert CassavaBranding.PURPLE == "#964BEA"


class TestValidators:
    """Tests for validators module."""

    def test_validate_site_name(self):
        """Test site name validation."""
        from cassava_optimizer.config.validators import validate_site_name
        
        # Valid names
        assert validate_site_name("TestSite001") == "TestSite001"
        assert validate_site_name("Site-123") == "Site-123"
        assert validate_site_name("Site_ABC") == "Site_ABC"
        
        # Invalid names
        with pytest.raises(ValueError):
            validate_site_name("")
        
        with pytest.raises(ValueError):
            validate_site_name("x" * 256)  # Too long

    def test_validate_kpi_value(self):
        """Test KPI value validation."""
        from cassava_optimizer.config.validators import validate_kpi_value
        
        # Valid values
        assert validate_kpi_value(99.5) == 99.5
        assert validate_kpi_value(0.0) == 0.0
        assert validate_kpi_value(100.0) == 100.0
        
        # Invalid values for percentage KPIs
        with pytest.raises(ValueError):
            validate_kpi_value(-1.0)
        
        with pytest.raises(ValueError):
            validate_kpi_value(101.0)

    def test_validate_confidence_score(self):
        """Test confidence score validation."""
        from cassava_optimizer.config.validators import validate_confidence_score
        
        # Valid scores
        assert validate_confidence_score(0.75) == 0.75
        assert validate_confidence_score(0.0) == 0.0
        assert validate_confidence_score(1.0) == 1.0
        
        # Invalid scores
        with pytest.raises(ValueError):
            validate_confidence_score(-0.1)
        
        with pytest.raises(ValueError):
            validate_confidence_score(1.5)

    def test_validate_cell_id(self):
        """Test cell ID validation."""
        from cassava_optimizer.config.validators import validate_cell_id
        
        # Valid IDs
        assert validate_cell_id("Cell001") == "Cell001"
        assert validate_cell_id("CELL-123-ABC") == "CELL-123-ABC"
        
        # Invalid IDs
        with pytest.raises(ValueError):
            validate_cell_id("")


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_same_instance(self, mock_settings):
        """Test that get_settings returns cached instance."""
        from cassava_optimizer.config import get_settings
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2

    def test_get_settings_is_callable(self):
        """Test that get_settings is callable."""
        from cassava_optimizer.config import get_settings
        
        assert callable(get_settings)
