"""
Pytest Configuration and Fixtures

Provides common test fixtures for all tests.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from liquid4g.core.config import get_settings
from liquid4g.domain.models.network import NetworkSite, NetworkCell
from liquid4g.domain.models.kpi import KPI, KPIThreshold, KPIAlert
from liquid4g.domain.models.parameter import Parameter, ParameterDefinition
from liquid4g.domain.models.agent import Agent, AgentStatus
from liquid4g.domain.models.operation import Operation


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def sample_site():
    """Create a sample network site"""
    return NetworkSite(
        site_id="TEST_SITE_001",
        site_name="Test Site 1",
        location="Test Location",
        latitude=-17.8252,
        longitude=31.0335,
        region="Test Region",
        status="active",
    )


@pytest.fixture
def sample_cell(sample_site):
    """Create a sample network cell"""
    return NetworkCell(
        cell_id="TEST_CELL_001",
        site_id=sample_site.site_id,
        cell_name="Test Cell 1",
        technology="4G",
        frequency_band="B3",
        pci=150,
        sector=1,
        status="active",
    )


@pytest.fixture
def sample_kpi_threshold():
    """Create a sample KPI threshold definition"""
    return KPIThreshold(
        kpi_key="network_access_success",
        display_name="Network Access Success Rate",
        description="RACH Setup Success Rate",
        unit="%",
        category="accessibility",
        higher_is_better=True,
        optimal_min=95.0,
        optimal_max=100.0,
        warning_threshold=93.0,
        critical_threshold=90.0,
    )


@pytest.fixture
def sample_kpi(sample_cell, sample_kpi_threshold):
    """Create a sample KPI measurement"""
    return KPI(
        measurement_time=datetime.utcnow(),
        cell_id=sample_cell.cell_id,
        kpi_key=sample_kpi_threshold.kpi_key,
        value=92.5,
        data_source="api",
        quality_score=0.95,
    )


@pytest.fixture
def sample_parameter_definition():
    """Create a sample parameter definition"""
    return ParameterDefinition(
        param_key="reference_signal_power_rs",
        display_name="Reference Signal Power (RS)",
        description="Cell-specific reference signal power",
        unit="0.1 dBm",
        category="power_control",
        min_value=-600,
        max_value=500,
        default_value=180,
        step_size=10,
        mml_query_command="LST PDSCHCFG: LOCALCELLID={cell_id};",
        mml_modify_command="MOD PDSCHCFG: LOCALCELLID={cell_id}, REFERENCESIGNALPWR={value};",
        impact_level="high",
    )


@pytest.fixture
def sample_parameter(sample_cell, sample_parameter_definition):
    """Create a sample parameter value"""
    return Parameter(
        cell_id=sample_cell.cell_id,
        param_key=sample_parameter_definition.param_key,
        value=180,
        measured_at=datetime.utcnow(),
        data_source="api",
    )


@pytest.fixture
def sample_agent():
    """Create a sample agent"""
    return Agent(
        agent_id="optimizer_agent",
        agent_type="optimizer",
        display_name="Optimizer Agent",
        description="Test optimizer agent",
        status="idle",
        capabilities=["optimization", "analysis"],
        config={"llm_enabled": True, "fallback_enabled": True},
    )


@pytest.fixture
def sample_operation(sample_site):
    """Create a sample operation"""
    return Operation(
        operation_type="full_optimization",
        target_site=sample_site.site_id,
        status="pending",
        parameters={"trigger": "manual"},
    )
