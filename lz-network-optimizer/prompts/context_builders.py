"""
Liquid Zimbabwe 4G Network Optimizer - Context Builders
Purpose: Build rich context for agent prompts
Created: 2025-10-30

These functions inject domain knowledge and current state into agent prompts.
"""

from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.liquid_zimbabwe_parameters import PARAMETERS
from domain.liquid_zimbabwe_kpi import KPIS
from domain.optimization_rules import OPTIMIZATION_RULES


# ============================================================================
# CONTEXT BUILDER: Parameter Knowledge
# ============================================================================

def build_parameter_context() -> str:
    """
    Build context string with all parameter knowledge.

    Returns:
        Formatted string describing all 5 parameters
    """
    context = "\nPARAMETER KNOWLEDGE:\n"
    context += "=" * 80 + "\n\n"

    for param_name, param_info in PARAMETERS.items():
        context += f"{param_name}:\n"
        context += f"  Description: {param_info.get('description', 'N/A')}\n"
        context += f"  Range: {param_info.get('range', 'N/A')}\n"
        context += f"  Default: {param_info.get('default', 'N/A')}\n"
        context += f"  Units: {param_info.get('units', 'N/A')}\n"
        context += f"  Impact KPIs: {', '.join(param_info.get('impact', []))}\n"
        context += f"  MML Query: {param_info.get('mml_query', 'N/A')}\n"
        context += "\n"

    return context


# ============================================================================
# CONTEXT BUILDER: KPI Knowledge
# ============================================================================

def build_kpi_context() -> str:
    """
    Build context string with all KPI knowledge.

    Returns:
        Formatted string describing all 7 KPIs
    """
    context = "\nKPI KNOWLEDGE:\n"
    context += "=" * 80 + "\n\n"

    # Load weights from config
    import yaml
    kpi_weights_path = os.path.join(os.path.dirname(__file__), "..", "config", "kpi_weights.yaml")
    with open(kpi_weights_path, 'r') as f:
        weights_config = yaml.safe_load(f)

    kpi_weights = weights_config['kpi_weights']

    for kpi_name, kpi_config in kpi_weights.items():
        context += f"{kpi_name}:\n"
        context += f"  Description: {kpi_config['description']}\n"
        context += f"  Weight: {kpi_config['weight']*100:.0f}% (Tier {kpi_config['tier']}, {kpi_config['priority']} priority)\n"
        context += f"  Target: {kpi_config['target']} {kpi_config['unit']}\n"
        context += f"  Thresholds:\n"
        for level, threshold in kpi_config['thresholds'].items():
            context += f"    - {level}: {threshold} {kpi_config['unit']}\n"
        context += "\n"

    return context


# ============================================================================
# CONTEXT BUILDER: Optimization Rules
# ============================================================================

def build_optimization_rules_context() -> str:
    """
    Build context string with all optimization rules.

    Returns:
        Formatted string describing all 10 optimization rules
    """
    context = "\nOPTIMIZATION RULES:\n"
    context += "=" * 80 + "\n\n"

    for rule_id, rule in OPTIMIZATION_RULES.items():
        context += f"{rule_id}: {rule.description}\n"
        context += f"  KPI Issue: {rule.kpi_issue}\n"
        context += f"  Parameter: {rule.parameter_name}\n"
        context += f"  Action: {rule.adjustment_direction.upper()} by {rule.adjustment_magnitude} amount\n"
        context += f"  Confidence: {rule.confidence*100:.0f}%\n"
        context += f"  Risk Level: {rule.risk_level}/10\n"
        context += f"  Expected Improvement: {rule.expected_improvement}\n"
        context += f"  Side Effects:\n"
        for effect in rule.side_effects:
            context += f"    - {effect}\n"
        context += "\n"

    return context


# ============================================================================
# CONTEXT BUILDER: Site Information
# ============================================================================

def build_site_context(site_name: str, kpis: Dict[str, float]) -> str:
    """
    Build context string for a specific site.

    Args:
        site_name: Site/eNodeB name
        kpis: Current KPI values

    Returns:
        Formatted string with site-specific context
    """
    context = f"\nCURRENT SITE INFORMATION:\n"
    context += "=" * 80 + "\n\n"

    context += f"Site Name: {site_name}\n"
    context += f"Cell ID: 1\n\n"

    context += "Current KPI Values:\n"
    for kpi_name, value in kpis.items():
        context += f"  - {kpi_name}: {value}\n"

    return context


# ============================================================================
# CONTEXT BUILDER: Full Agent Context
# ============================================================================

def build_full_agent_context(
    agent_name: str,
    site_name: Optional[str] = None,
    kpis: Optional[Dict[str, float]] = None,
    include_parameters: bool = True,
    include_kpis: bool = True,
    include_rules: bool = False
) -> str:
    """
    Build complete context for an agent.

    Args:
        agent_name: Name of agent
        site_name: Optional site name
        kpis: Optional current KPI values
        include_parameters: Include parameter knowledge
        include_kpis: Include KPI knowledge
        include_rules: Include optimization rules

    Returns:
        Complete formatted context string
    """
    context = f"\nAGENT CONTEXT FOR: {agent_name.upper()}\n"
    context += "=" * 80 + "\n"

    # Site-specific context
    if site_name and kpis:
        context += build_site_context(site_name, kpis)

    # Domain knowledge
    if include_parameters:
        context += build_parameter_context()

    if include_kpis:
        context += build_kpi_context()

    if include_rules:
        context += build_optimization_rules_context()

    return context


# ============================================================================
# CONTEXT BUILDER: Tool Usage Examples
# ============================================================================

def build_tool_examples(agent_name: str) -> str:
    """
    Build examples of how to use tools for a specific agent.

    Args:
        agent_name: Name of agent

    Returns:
        Formatted string with tool usage examples
    """
    examples = {
        "network_connector": """
TOOL USAGE EXAMPLES:

1. Query Parameter Value:
   query_huawei_parameter(parameter_name="reference_signal_power_pdschcfg", cell_id=1)

2. Query Live KPIs:
   query_huawei_kpi(site_name="MSH0013-Bindura-Zaoga", cell_id=1)

3. Fallback to Historical Data:
   execute_lz_kpi_sql(sql_query="SELECT * FROM kpi_data WHERE site_name='MSH0013-Bindura-Zaoga' ORDER BY timestamp DESC LIMIT 1")
""",

        "monitoring": """
TOOL USAGE EXAMPLES:

1. Query Current KPIs:
   execute_lz_kpi_sql(sql_query="SELECT network_access_success, download_speed, upload_speed FROM kpi_data WHERE site_name='Site1' ORDER BY timestamp DESC LIMIT 1")

2. Calculate Weighted Score:
   calc_weighted_kpi_score(network_access_success=96.0, download_speed=55.0, download_quality=97.0, upload_speed=22.0, upload_quality=96.0, control_channel_load=60.0, feedback_channel_load=30.0)

3. Analyze Trend:
   calc_kpi_trend(kpi_name="download_speed", current_value=50.0, historical_values="45.0,46.5,47.2,48.1,49.0", days=5)
""",

        "kpi_analytics": """
TOOL USAGE EXAMPLES:

1. Get KPI History:
   execute_lz_kpi_sql(sql_query="SELECT DATE(timestamp) as date, AVG(download_speed) as avg_dl FROM kpi_data WHERE site_name='Site1' AND timestamp >= date('now', '-7 days') GROUP BY date")

2. Calculate Weighted Score:
   calc_weighted_kpi_score(network_access_success=92.0, download_speed=42.0, download_quality=96.0, upload_speed=18.0, upload_quality=94.0, control_channel_load=70.0, feedback_channel_load=35.0)

3. Analyze Multiple KPI Trends:
   For each KPI, call: calc_kpi_trend(kpi_name="<kpi>", current_value=<value>, historical_values="<history>", days=7)
""",

        "configuration": """
TOOL USAGE EXAMPLES:

1. Query Current Parameter:
   query_huawei_parameter(parameter_name="reference_signal_power_pdschcfg", cell_id=1)

2. Validate Proposed Value:
   validate_parameter_range(parameter_name="reference_signal_power_pdschcfg", proposed_value=-180)

3. Query Historical Optimizations:
   execute_historical_sql(sql_query="SELECT * FROM optimization_history WHERE site_name='Site1' AND success=1 ORDER BY timestamp DESC LIMIT 5")
""",

        "validation": """
TOOL USAGE EXAMPLES:

1. Validate Parameter Range:
   validate_parameter_range(parameter_name="reference_signal_power_pdschcfg", proposed_value=-180)

2. Assess Individual Risk:
   assess_risk_score(parameter_name="reference_signal_power_pdschcfg", current_value=-200, proposed_value=-180, kpi_issue="low_download_speed")

3. Validate Complete Plan:
   validate_optimization_safety(parameter_changes_json='[{"parameter":"reference_signal_power_pdschcfg","current":-200,"proposed":-180,"kpi_issue":"low_download_speed"}]', site_name="Site1", max_risk_threshold=7)
""",

        "mml_executor": """
TOOL USAGE EXAMPLES:

1. Execute Parameter Change:
   modify_huawei_parameter(parameter_name="reference_signal_power_pdschcfg", new_value=-180, cell_id=1, reason="Improve download speed")

2. Execute MML Command:
   execute_mml_command(mml_command="LST CELL: LOCALCELLID=1;")

3. Verify KPIs After Change:
   query_huawei_kpi(site_name="MSH0013-Bindura-Zaoga", cell_id=1)

4. Log Change to Database:
   execute_historical_sql(sql_query="INSERT INTO parameter_changes ...")
"""
    }

    return examples.get(agent_name, "No tool examples available for this agent.")


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Build full context for Configuration Agent
    kpis = {
        'network_access_success': 94.2,
        'download_speed': 42.5,
        'download_quality': 96.1,
        'upload_speed': 22.0,
        'upload_quality': 95.8,
        'control_channel_load': 60.0,
        'feedback_channel_load': 30.0
    }

    context = build_full_agent_context(
        agent_name="configuration",
        site_name="MSH0013-Bindura-Zaoga",
        kpis=kpis,
        include_parameters=True,
        include_kpis=False,
        include_rules=True
    )

    print(context)
    print("\n\n")
    print(build_tool_examples("configuration"))
