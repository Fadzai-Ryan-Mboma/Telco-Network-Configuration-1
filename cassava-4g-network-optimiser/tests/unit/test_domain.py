"""Unit tests for domain layer."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest


class TestSiteModel:
    """Tests for Site domain model."""

    def test_create_site(self, sample_site):
        """Test creating a site."""
        from cassava_optimizer.domain.models import Site
        
        site = Site(**sample_site)
        
        assert site.id == 1
        assert site.name == "TestSite001"
        assert site.region == "Harare"
        assert site.latitude == -17.8292
        assert site.longitude == 31.0522
        assert site.status == "online"

    def test_site_validation_name_required(self):
        """Test that site name is required."""
        from cassava_optimizer.domain.models import Site
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            Site(id=1, name="", region="Test")

    def test_site_status_enum(self):
        """Test site status values."""
        from cassava_optimizer.domain.models import Site
        from cassava_optimizer.domain.enums import SiteStatus
        
        site = Site(id=1, name="Test", region="Region", status=SiteStatus.ONLINE)
        assert site.status == SiteStatus.ONLINE
        
        site = Site(id=2, name="Test2", region="Region", status=SiteStatus.OFFLINE)
        assert site.status == SiteStatus.OFFLINE


class TestCellModel:
    """Tests for Cell domain model."""

    def test_create_cell(self, sample_cell):
        """Test creating a cell."""
        from cassava_optimizer.domain.models import Cell
        
        cell = Cell(**sample_cell)
        
        assert cell.id == 1
        assert cell.site_id == 1
        assert cell.cell_id == "Cell001"
        assert cell.technology == "LTE"
        assert cell.band == "B3"
        assert cell.pci == 100

    def test_cell_has_site_reference(self, sample_cell):
        """Test cell has site_id reference."""
        from cassava_optimizer.domain.models import Cell
        
        cell = Cell(**sample_cell)
        assert cell.site_id == 1

    def test_cell_power_validation(self):
        """Test cell power validation."""
        from cassava_optimizer.domain.models import Cell
        from pydantic import ValidationError
        
        # Valid power
        cell = Cell(
            id=1, site_id=1, cell_id="C1", cell_name="Cell1",
            power=40.0
        )
        assert cell.power == 40.0
        
        # Power should be positive
        with pytest.raises(ValidationError):
            Cell(
                id=1, site_id=1, cell_id="C1", cell_name="Cell1",
                power=-10.0
            )


class TestKPIDataModel:
    """Tests for KPIData domain model."""

    def test_create_kpi_data(self):
        """Test creating KPI data."""
        from cassava_optimizer.domain.models import KPIData
        
        now = datetime.now(timezone.utc)
        kpi = KPIData(
            id=1,
            cell_id=1,
            site_id=1,
            kpi_name="call_setup_success_rate",
            kpi_value=97.5,
            kpi_unit="%",
            timestamp=now,
        )
        
        assert kpi.kpi_name == "call_setup_success_rate"
        assert kpi.kpi_value == 97.5
        assert kpi.timestamp == now

    def test_kpi_data_has_timestamp(self):
        """Test KPI data has timestamp."""
        from cassava_optimizer.domain.models import KPIData
        
        now = datetime.now(timezone.utc)
        kpi = KPIData(
            kpi_name="test",
            kpi_value=100.0,
            timestamp=now,
        )
        
        assert kpi.timestamp is not None


class TestRecommendationModel:
    """Tests for Recommendation domain model."""

    def test_create_recommendation(self, sample_recommendation):
        """Test creating a recommendation."""
        from cassava_optimizer.domain.models import Recommendation
        
        rec = Recommendation(**sample_recommendation)
        
        assert rec.parameter_name == "handoverMargin"
        assert rec.current_value == "3"
        assert rec.recommended_value == "5"
        assert rec.confidence == 0.85
        assert rec.risk_level == "low"

    def test_recommendation_status_transitions(self, sample_recommendation):
        """Test recommendation status transitions."""
        from cassava_optimizer.domain.models import Recommendation
        from cassava_optimizer.domain.enums import RecommendationStatus
        
        rec = Recommendation(**sample_recommendation)
        assert rec.status == RecommendationStatus.PENDING
        
        rec.status = RecommendationStatus.APPROVED
        assert rec.status == RecommendationStatus.APPROVED
        
        rec.status = RecommendationStatus.EXECUTED
        assert rec.status == RecommendationStatus.EXECUTED

    def test_recommendation_requires_reasoning(self, sample_recommendation):
        """Test recommendation has reasoning."""
        from cassava_optimizer.domain.models import Recommendation
        
        rec = Recommendation(**sample_recommendation)
        assert rec.reasoning is not None
        assert len(rec.reasoning) > 0


class TestEnums:
    """Tests for domain enums."""

    def test_site_status_values(self):
        """Test SiteStatus enum values."""
        from cassava_optimizer.domain.enums import SiteStatus
        
        assert SiteStatus.ONLINE.value == "online"
        assert SiteStatus.OFFLINE.value == "offline"
        assert SiteStatus.MAINTENANCE.value == "maintenance"

    def test_cell_status_values(self):
        """Test CellStatus enum values."""
        from cassava_optimizer.domain.enums import CellStatus
        
        assert CellStatus.ACTIVE.value == "active"
        assert CellStatus.INACTIVE.value == "inactive"
        assert CellStatus.DEGRADED.value == "degraded"

    def test_recommendation_status_values(self):
        """Test RecommendationStatus enum values."""
        from cassava_optimizer.domain.enums import RecommendationStatus
        
        assert RecommendationStatus.PENDING.value == "pending"
        assert RecommendationStatus.APPROVED.value == "approved"
        assert RecommendationStatus.REJECTED.value == "rejected"
        assert RecommendationStatus.EXECUTED.value == "executed"
        assert RecommendationStatus.ROLLED_BACK.value == "rolled_back"

    def test_risk_level_values(self):
        """Test RiskLevel enum values."""
        from cassava_optimizer.domain.enums import RiskLevel
        
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"


class TestExceptions:
    """Tests for domain exceptions."""

    def test_optimization_error(self):
        """Test OptimizationError exception."""
        from cassava_optimizer.domain.exceptions import OptimizationError
        
        error = OptimizationError("Test error message")
        assert str(error) == "Test error message"

    def test_configuration_error(self):
        """Test ConfigurationError exception."""
        from cassava_optimizer.domain.exceptions import ConfigurationError
        
        error = ConfigurationError("Invalid config")
        assert str(error) == "Invalid config"

    def test_api_error_with_status_code(self):
        """Test APIError exception with status code."""
        from cassava_optimizer.domain.exceptions import APIError
        
        error = APIError("API failed", status_code=500)
        assert str(error) == "API failed"
        assert error.status_code == 500

    def test_database_error(self):
        """Test DatabaseError exception."""
        from cassava_optimizer.domain.exceptions import DatabaseError
        
        error = DatabaseError("DB connection failed")
        assert str(error) == "DB connection failed"


class TestValueObjects:
    """Tests for domain value objects."""

    def test_kpi_threshold(self):
        """Test KPIThreshold value object."""
        from cassava_optimizer.domain.value_objects import KPIThreshold
        
        threshold = KPIThreshold(
            kpi_name="call_drop_rate",
            warning_threshold=2.0,
            critical_threshold=5.0,
            target_value=1.0,
            direction="lower_is_better",
        )
        
        assert threshold.kpi_name == "call_drop_rate"
        assert threshold.is_warning(3.0)
        assert threshold.is_critical(6.0)

    def test_cell_parameter(self):
        """Test CellParameter value object."""
        from cassava_optimizer.domain.value_objects import CellParameter
        
        param = CellParameter(
            name="handoverMargin",
            value="3",
            category="mobility",
        )
        
        assert param.name == "handoverMargin"
        assert param.value == "3"
        assert param.category == "mobility"
