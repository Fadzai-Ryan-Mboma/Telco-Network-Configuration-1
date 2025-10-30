"""
System Integration Tests

Tests the complete system with sample data.
"""

import pytest
from datetime import datetime
from pathlib import Path

from liquid4g.infrastructure.database import get_db
from liquid4g.infrastructure.database.migrations import get_migration_manager
from liquid4g.infrastructure.repositories import (
    NetworkRepository,
    KPIRepository,
    ParameterRepository,
    AgentRepository,
)
from liquid4g.domain.models.network import NetworkSite, NetworkCell
from liquid4g.domain.models.kpi import KPI, KPIThreshold
from liquid4g.domain.models.parameter import Parameter, ParameterDefinition
from liquid4g.domain.models.agent import Agent
from liquid4g.agents.orchestrator import AgentOrchestrator


@pytest.fixture(scope="module")
def test_db():
    """Create test database"""
    # Use in-memory database for testing
    import os
    os.environ["DATABASE_PATH"] = ":memory:"

    db = get_db()
    migration = get_migration_manager()

    # Initialize schema
    migration.initialize_schema()

    yield db

    # Cleanup
    db.close()


@pytest.fixture
def sample_data(test_db):
    """Create sample network data"""
    net_repo = NetworkRepository()
    kpi_repo = KPIRepository()
    param_repo = ParameterRepository()
    agent_repo = AgentRepository()

    # Create site
    site = NetworkSite(
        site_id="TEST_SITE_001",
        site_name="Test Site 1",
        location="Test Location",
        region="Test Region",
        status="active"
    )
    net_repo.create(site)

    # Create cell
    cell = NetworkCell(
        cell_id="TEST_CELL_001",
        site_id="TEST_SITE_001",
        cell_name="Test Cell 1",
        technology="LTE_4G",
        pci=150,
        sector=1,
        status="active"
    )
    net_repo.create_cell(cell)

    # Create KPI thresholds
    thresholds = [
        KPIThreshold(
            kpi_key="network_access_success",
            display_name="Network Access Success Rate",
            category="accessibility",
            higher_is_better=True,
            optimal_min=95.0,
            critical_threshold=90.0
        ),
        KPIThreshold(
            kpi_key="drop_rate",
            display_name="Drop Rate",
            category="retainability",
            higher_is_better=False,
            optimal_max=2.0,
            critical_threshold=3.0
        )
    ]

    for threshold in thresholds:
        kpi_repo.create_threshold(threshold)

    # Create KPI measurements (simulating poor performance)
    kpis = [
        KPI(
            measurement_time=datetime.utcnow(),
            cell_id="TEST_CELL_001",
            kpi_key="network_access_success",
            value=88.5,  # Below critical threshold
            data_source="api"
        ),
        KPI(
            measurement_time=datetime.utcnow(),
            cell_id="TEST_CELL_001",
            kpi_key="drop_rate",
            value=3.5,  # Above critical threshold
            data_source="api"
        )
    ]

    for kpi in kpis:
        kpi_repo.create(kpi)

    # Create parameter definitions
    param_defs = [
        ParameterDefinition(
            param_key="handover_margin",
            display_name="Handover Margin",
            category="mobility",
            min_value=0,
            max_value=10,
            default_value=3,
            impact_level="low",
            mml_query_command="LST HANDOVERGROUP: LOCALCELLID={cell_id};",
            mml_modify_command="MOD HANDOVERGROUP: LOCALCELLID={cell_id}, HANDOVERMARGIN={value};"
        ),
        ParameterDefinition(
            param_key="reference_signal_power_rs",
            display_name="Reference Signal Power",
            category="power_control",
            min_value=-600,
            max_value=500,
            default_value=180,
            impact_level="medium",
            mml_query_command="LST PDSCHCFG: LOCALCELLID={cell_id};",
            mml_modify_command="MOD PDSCHCFG: LOCALCELLID={cell_id}, REFERENCEPOWER={value};"
        )
    ]

    for defn in param_defs:
        param_repo.create_definition(defn)

    # Create current parameter values
    params = [
        Parameter(
            cell_id="TEST_CELL_001",
            param_key="handover_margin",
            value=3,
            measured_at=datetime.utcnow(),
            data_source="api"
        ),
        Parameter(
            cell_id="TEST_CELL_001",
            param_key="reference_signal_power_rs",
            value=180,
            measured_at=datetime.utcnow(),
            data_source="api"
        )
    ]

    for param in params:
        param_repo.create(param)

    # Create agents
    agents = [
        Agent(
            agent_id="monitor_agent",
            agent_type="monitor",
            display_name="Monitor Agent",
            status="idle",
            capabilities=["kpi_monitoring", "issue_detection"]
        ),
        Agent(
            agent_id="analyzer_agent",
            agent_type="analyzer",
            display_name="Analyzer Agent",
            status="idle",
            capabilities=["root_cause_analysis", "optimization"]
        ),
        Agent(
            agent_id="configuration_agent",
            agent_type="configuration",
            display_name="Configuration Agent",
            status="idle",
            capabilities=["mml_generation"]
        ),
        Agent(
            agent_id="validation_agent",
            agent_type="validation",
            display_name="Validation Agent",
            status="idle",
            capabilities=["validation", "approval"]
        ),
        Agent(
            agent_id="execution_agent",
            agent_type="execution",
            display_name="Execution Agent",
            status="idle",
            capabilities=["change_execution", "rollback"]
        )
    ]

    for agent in agents:
        agent_repo.create(agent)

    return {
        "site": site,
        "cell": cell,
        "kpis": kpis,
        "thresholds": thresholds,
        "parameters": params
    }


def test_database_initialization(test_db):
    """Test database is properly initialized"""
    migration = get_migration_manager()

    assert migration.is_initialized()
    assert migration.get_current_version() == "1.0.0"


def test_repositories(sample_data, test_db):
    """Test repository operations"""
    net_repo = NetworkRepository()
    kpi_repo = KPIRepository()

    # Test network repository
    site = net_repo.get_by_site_id("TEST_SITE_001")
    assert site is not None
    assert site.site_name == "Test Site 1"

    cell = net_repo.get_cell_by_id("TEST_CELL_001")
    assert cell is not None
    assert cell.site_id == "TEST_SITE_001"

    # Test KPI repository
    kpi = kpi_repo.get_latest_for_cell("TEST_CELL_001", "network_access_success")
    assert kpi is not None
    assert kpi.value == 88.5

    threshold = kpi_repo.get_threshold("network_access_success")
    assert threshold is not None
    assert threshold.critical_threshold == 90.0


def test_monitor_agent(sample_data, test_db):
    """Test monitor agent with rule-based execution"""
    from liquid4g.agents.monitor_agent import MonitorAgent
    from liquid4g.domain.models.operation import Operation

    agent = MonitorAgent()
    operation = Operation.create("monitoring", target_cell="TEST_CELL_001")

    # Execute with rules (LLM unavailable in tests)
    result = agent._execute_with_rules(operation, cell_id="TEST_CELL_001")

    assert "issues" in result
    assert len(result["issues"]) > 0

    # Should detect critical KPIs
    critical_issues = [i for i in result["issues"] if i["severity"] == "critical"]
    assert len(critical_issues) > 0


def test_analyzer_agent(sample_data, test_db):
    """Test analyzer agent with rule-based execution"""
    from liquid4g.agents.analyzer_agent import AnalyzerAgent
    from liquid4g.domain.models.operation import Operation

    agent = AnalyzerAgent()
    operation = Operation.create("analysis", target_cell="TEST_CELL_001")

    issues = [{"kpi_key": "drop_rate", "current_value": 3.5, "severity": "critical"}]

    result = agent._execute_with_rules(operation, cell_id="TEST_CELL_001", issues=issues)

    assert "recommended_changes" in result
    # Should recommend parameter changes based on rules


def test_validation_agent(sample_data, test_db):
    """Test validation agent"""
    from liquid4g.agents.validation_agent import ValidationAgent
    from liquid4g.domain.models.operation import Operation

    agent = ValidationAgent()
    operation = Operation.create("validation", target_cell="TEST_CELL_001")

    proposed_changes = [
        {
            "param_key": "handover_margin",
            "current_value": 3,
            "recommended_value": 5,
            "risk_level": "low"
        }
    ]

    result = agent._execute_with_rules(operation, proposed_changes=proposed_changes)

    assert "approval_decision" in result
    assert "validation_results" in result


def test_configuration_agent(sample_data, test_db):
    """Test configuration agent"""
    from liquid4g.agents.configuration_agent import ConfigurationAgent
    from liquid4g.domain.models.operation import Operation

    agent = ConfigurationAgent()
    operation = Operation.create("configuration", target_cell="TEST_CELL_001")

    approved_changes = [
        {
            "param_key": "handover_margin",
            "current_value": 3,
            "recommended_value": 5
        }
    ]

    result = agent._execute_with_rules(
        operation,
        cell_id="TEST_CELL_001",
        approved_changes=approved_changes
    )

    assert "modification_commands" in result
    assert "rollback_commands" in result
    assert len(result["modification_commands"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
