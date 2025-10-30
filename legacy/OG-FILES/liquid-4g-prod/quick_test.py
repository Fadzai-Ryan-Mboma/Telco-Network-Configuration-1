#!/usr/bin/env python3
"""
Quick Test Script

Tests the system with sample data without needing real Huawei API.
"""

import os
os.environ["DATABASE_PATH"] = "data/test_liquid4g.db"
os.environ["AGENT_LLM_ENABLED"] = "false"  # Use rules only for testing

from datetime import datetime
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

print("="*60)
print("Liquid 4G Network Optimizer - Quick Test")
print("="*60)

# Step 1: Initialize database
print("\n[1/7] Initializing database...")
db = get_db()
migration = get_migration_manager()

if not migration.is_initialized():
    migration.initialize_schema()
    print("✓ Database schema initialized")
else:
    print("✓ Database already initialized")

# Step 2: Create sample network
print("\n[2/7] Creating sample network...")
net_repo = NetworkRepository()

from liquid4g.domain.models.network import SiteStatus

site = NetworkSite(
    site_id="HAR_001",
    site_name="Harare Central",
    location="Harare CBD",
    region="Harare",
    status=SiteStatus.ACTIVE
)
try:
    net_repo.create(site)
    print(f"✓ Created site: {site.site_name}")
except:
    print(f"✓ Site already exists: {site.site_name}")

from liquid4g.domain.models.network import CellTechnology, CellStatus

cell = NetworkCell(
    cell_id="HAR_001_1",
    site_id="HAR_001",
    cell_name="Harare Central Sector 1",
    technology=CellTechnology.LTE_4G,  # Use enum value "4G"
    pci=150,
    sector=1,
    status=CellStatus.ACTIVE
)
try:
    net_repo.create_cell(cell)
    print(f"✓ Created cell: {cell.cell_name}")
except:
    print(f"✓ Cell already exists: {cell.cell_name}")

# Step 3: Create KPI thresholds
print("\n[3/7] Creating KPI thresholds...")
kpi_repo = KPIRepository()

thresholds = [
    KPIThreshold(
        kpi_key="network_access_success",
        display_name="Network Access Success Rate",
        description="Percentage of successful network access attempts",
        unit="%",
        category="accessibility",
        higher_is_better=True,
        optimal_min=95.0,
        critical_threshold=90.0
    ),
    KPIThreshold(
        kpi_key="drop_rate",
        display_name="Drop Rate",
        description="Percentage of dropped calls",
        unit="%",
        category="retainability",
        higher_is_better=False,
        optimal_max=2.0,
        critical_threshold=3.0
    ),
]

for threshold in thresholds:
    try:
        kpi_repo.create_threshold(threshold)
        print(f"✓ Created threshold: {threshold.display_name}")
    except:
        print(f"✓ Threshold exists: {threshold.display_name}")

# Step 4: Create poor KPI data (to trigger optimization)
print("\n[4/7] Creating sample KPI data (poor performance)...")

from liquid4g.domain.models.kpi import DataSource

kpis = [
    KPI(
        measurement_time=datetime.utcnow(),
        cell_id="HAR_001_1",
        kpi_key="network_access_success",
        value=88.5,  # Below critical threshold (90%)
        data_source=DataSource.MANUAL  # Use enum instead of "test"
    ),
    KPI(
        measurement_time=datetime.utcnow(),
        cell_id="HAR_001_1",
        kpi_key="drop_rate",
        value=3.5,  # Above critical threshold (3%)
        data_source=DataSource.MANUAL  # Use enum instead of "test"
    ),
]

for kpi in kpis:
    kpi_repo.create(kpi)
    status = "CRITICAL" if kpi.value < 90 or kpi.value > 3 else "OK"
    print(f"✓ Created KPI: {kpi.kpi_key} = {kpi.value} [{status}]")

# Step 5: Create parameter definitions
print("\n[5/7] Creating parameter definitions...")
param_repo = ParameterRepository()

param_defs = [
    ParameterDefinition(
        param_key="handover_margin",
        display_name="Handover Margin",
        description="Margin for handover triggering",
        unit="dB",
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
        description="Reference signal power for downlink",
        unit="0.1 dBm",
        category="power_control",
        min_value=-600,
        max_value=500,
        default_value=180,
        impact_level="medium",
        mml_query_command="LST PDSCHCFG: LOCALCELLID={cell_id};",
        mml_modify_command="MOD PDSCHCFG: LOCALCELLID={cell_id}, REFERENCEPOWER={value};"
    ),
]

for defn in param_defs:
    try:
        param_repo.create_definition(defn)
        print(f"✓ Created parameter: {defn.display_name}")
    except:
        print(f"✓ Parameter exists: {defn.display_name}")

# Create current parameter values
from liquid4g.domain.models.parameter import DataSource as ParamDataSource

params = [
    Parameter(
        cell_id="HAR_001_1",
        param_key="handover_margin",
        value=3,
        measured_at=datetime.utcnow(),
        data_source=ParamDataSource.MANUAL  # Use enum instead of "test"
    ),
]

for param in params:
    param_repo.create(param)
    print(f"✓ Set parameter: {param.param_key} = {param.value}")

# Step 6: Create agents
print("\n[6/7] Creating agents...")
agent_repo = AgentRepository()

agents = [
    Agent(
        agent_id="monitor_agent",
        agent_type="monitor",
        display_name="Monitor Agent",
        description="Monitors network KPIs",
        status="idle",
        capabilities=["kpi_monitoring", "issue_detection"]
    ),
    Agent(
        agent_id="analyzer_agent",
        agent_type="analyzer",
        display_name="Analyzer Agent",
        description="Analyzes performance issues",
        status="idle",
        capabilities=["root_cause_analysis", "optimization"]
    ),
    Agent(
        agent_id="configuration_agent",
        agent_type="configuration",
        display_name="Configuration Agent",
        description="Generates MML commands",
        status="idle",
        capabilities=["mml_generation"]
    ),
    Agent(
        agent_id="validation_agent",
        agent_type="validation",
        display_name="Validation Agent",
        description="Validates proposed changes",
        status="idle",
        capabilities=["validation", "approval"]
    ),
    Agent(
        agent_id="execution_agent",
        agent_type="execution",
        display_name="Execution Agent",
        description="Executes approved changes",
        status="idle",
        capabilities=["change_execution", "rollback"]
    ),
]

for agent in agents:
    try:
        agent_repo.create(agent)
        print(f"✓ Created agent: {agent.display_name}")
    except:
        print(f"✓ Agent exists: {agent.display_name}")

# Step 7: Run optimization
print("\n[7/7] Running optimization workflow...")
print("-"*60)

orchestrator = AgentOrchestrator()

result = orchestrator.optimize_cell(
    cell_id="HAR_001_1",
    auto_execute=False  # Don't execute without real API
)

print(f"\nOptimization Status: {result['status']}")
print(f"Message: {result['message']}")

if 'agent_data' in result:
    data = result['agent_data']

    if 'issues' in data:
        print(f"\n Issues Found: {len(data['issues'])}")
        for issue in data['issues'][:3]:  # Show first 3
            print(f"  - {issue['kpi_key']}: {issue['current_value']} (severity: {issue['severity']})")

    if 'recommended_changes' in data:
        print(f"\nRecommended Changes: {len(data['recommended_changes'])}")
        for change in data['recommended_changes'][:3]:  # Show first 3
            print(f"  - {change['param_key']}: {change['current_value']} → {change['recommended_value']}")
            print(f"    Risk: {change['risk_level']}, Expected: {change['expected_improvement']}")

    if 'validation' in data:
        validation = data['validation']
        print(f"\nValidation Decision: {validation['approval_decision']}")
        if validation.get('conditions'):
            print(f"Conditions: {validation['conditions']}")

print("\n" + "="*60)
print("✓ Test Complete!")
print("="*60)

print("\nNext Steps:")
print("1. Start API: python -m liquid4g api")
print("2. Start UI: python -m liquid4g ui")
print("3. Access UI at: http://localhost:8501")
print("4. Access API docs at: http://localhost:8000/docs")

print("\nTest Data Location:")
print(f"  Database: {os.environ['DATABASE_PATH']}")
print(f"  Site: {site.site_id}")
print(f"  Cell: {cell.cell_id}")
