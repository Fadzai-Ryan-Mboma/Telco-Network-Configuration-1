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
   validate_parameter_range(parameter_name="reference_signal_power_pdschcfg", proposed_value=172)

2. Assess Individual Risk (using Bindura Zaoga baseline):
   assess_risk_score(parameter_name="reference_signal_power_pdschcfg", current_value=152, proposed_value=172, kpi_issue="low_download_speed")

3. Validate Complete Plan:
   validate_optimization_safety(parameter_changes_json='[{"parameter":"reference_signal_power_pdschcfg","current":152,"proposed":172,"kpi_issue":"low_download_speed"}]', site_name="Site1", max_risk_threshold=7)
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


# ============================================================================
# CONTEXT BUILDER: TA Distribution (NEW)
# ============================================================================

def build_ta_context(site_name: str, cell_id: Optional[int] = None, days: int = 7) -> str:
    """
    Build TA distribution context for LLM prompts.

    Args:
        site_name: Site identifier
        cell_id: Optional cell ID (None = aggregate all cells)
        days: Days of history to retrieve

    Returns:
        Formatted TA context string with distribution and coverage assessment
    """
    try:
        from tools.sql_tools import get_ta_metrics_direct

        ta_data = get_ta_metrics_direct(site_name, cell_id, days)

        if not ta_data or len(ta_data) == 0:
            return "\nTA DISTRIBUTION: Not available for this site\n"

        # Latest TA record
        latest = ta_data[0]

        context = "\n" + "=" * 80 + "\n"
        context += "TIMING ADVANCE DISTRIBUTION ANALYSIS\n"
        context += "=" * 80 + "\n\n"

        context += f"**Site**: {site_name}\n"
        context += f"**Cell**: {cell_id if cell_id else 'All cells (aggregated)'}\n"
        context += f"**Last Update**: {latest.get('timestamp')}\n"
        context += f"**Data Integrity**: {latest.get('integrity', 100):.1f}%\n\n"

        # Key Metrics
        context += "### Key Coverage Metrics\n"
        context += f"- **Total UEs**: {latest.get('total_ues', 0):,}\n"
        context += f"- **Avg TA Index**: {latest.get('avg_ta_index', 0):.2f} "
        context += f"(Typical distance: {_get_distance_range(latest.get('avg_ta_index', 0))})\n"

        overshoot = latest.get('overshoot_percentage', 0)
        context += f"- **Overshoot %**: {overshoot:.1f}% "
        context += "⚠️ HIGH\n" if overshoot > 10 else "✓ Healthy\n"

        cell_edge = latest.get('cell_edge_percentage', 0)
        context += f"- **Cell Edge %**: {cell_edge:.1f}% "
        context += "⚠️ HIGH\n" if cell_edge > 20 else "✓ Healthy\n"

        rach = latest.get('rach_success_rate')
        if rach:
            context += f"- **RACH Success**: {rach:.1f}%\n"
        context += "\n"

        # UE Distance Distribution Table
        context += "### UE Distance Distribution\n"
        context += "```\n"
        context += "Index | Distance Range    | UE Count | Percentage | Assessment\n"
        context += "------|-------------------|----------|------------|------------------\n"

        total_ues = latest.get('total_ues', 1)  # Avoid division by zero

        for i in range(12):
            ue_count = latest.get(f'ta_index_{i}', 0)
            percentage = (ue_count / total_ues * 100) if total_ues > 0 else 0
            distance_range = _get_ta_distance_range(i)
            assessment = _assess_ta_index(i, percentage)

            context += f"{i:5} | {distance_range:17} | {ue_count:8,} | {percentage:9.1f}% | {assessment}\n"

        context += "```\n\n"

        # Coverage Assessment
        context += "### Coverage Assessment\n"
        context += _assess_ta_distribution(latest)
        context += "\n"

        # Recommendations
        context += "### TA-Based Recommendations\n"
        recommendations = _generate_ta_recommendations(latest)
        if recommendations:
            for rec in recommendations:
                context += f"- {rec}\n"
        else:
            context += "- ✅ Coverage distribution is healthy - no TA-based issues detected.\n"
        context += "\n"

        return context

    except Exception as e:
        return f"\nTA DISTRIBUTION: Error loading data - {str(e)}\n"


def _get_distance_range(avg_index: float) -> str:
    """Get distance range description for average TA index."""
    if avg_index < 2:
        return "<312m (Very close, possible overshoot)"
    elif avg_index < 4:
        return "312-781m (Close, healthy coverage)"
    elif avg_index < 7:
        return "781-2344m (Optimal coverage)"
    elif avg_index < 9:
        return "2344-7813m (Far, cell edge approaching)"
    else:
        return ">7813m (Excessive overshoot)"


def _get_ta_distance_range(index: int) -> str:
    """Get distance range for specific TA index."""
    ranges = {
        0: "0-78m",
        1: "78-156m",
        2: "156-312m",
        3: "312-547m",
        4: "547-781m",
        5: "781-1172m",
        6: "1172-1563m",
        7: "1563-2344m",
        8: "2344-3906m",
        9: "3906-7813m",
        10: "7813-15625m",
        11: "15625-31250m"
    }
    return ranges.get(index, "Unknown")


def _assess_ta_index(index: int, percentage: float) -> str:
    """Assess individual TA index percentage."""
    if index == 0 and percentage > 5:
        return "⚠️ Overshoot"
    elif index in [10, 11] and percentage > 3:
        return "⚠️ Far overshoot"
    elif index == 9 and percentage > 10:
        return "⚠️ Cell edge"
    elif index in [5, 6] and percentage > 10:
        return "✓ Optimal"
    else:
        return ""


def _assess_ta_distribution(ta_record: dict) -> str:
    """Assess TA distribution and provide coverage analysis."""
    overshoot = ta_record.get('overshoot_percentage', 0)
    cell_edge = ta_record.get('cell_edge_percentage', 0)
    avg_ta = ta_record.get('avg_ta_index', 0)

    issues = []

    if overshoot > 15:
        issues.append("🔴 **CRITICAL**: Overshoot >15% - immediate action required")
        issues.append("   Recommendation: Reduce reference_signal_power by 1-2 dB AND alert engineer for manual antenna downtilt")
    elif overshoot > 10:
        issues.append("⚠️ **WARNING**: Elevated overshoot (>10%)")
        issues.append("   Recommendation: Reduce reference_signal_power by 1 dB or consider antenna downtilt")

    if cell_edge > 25:
        issues.append("🔴 **CRITICAL**: Cell edge loading >25% - power increase required")
        issues.append("   Recommendation: Increase reference_signal_power by 2-3 dB to extend coverage")
    elif cell_edge > 20:
        issues.append("⚠️ **WARNING**: Elevated cell edge loading (>20%)")
        issues.append("   Recommendation: Consider increasing reference_signal_power by 1-2 dB")

    if avg_ta < 3:
        issues.append("⚠️ **WARNING**: Average TA too low (<3.0) - overshooting detected")
        issues.append("   Recommendation: MANUAL ANTENNA ADJUSTMENT required (automated parameter changes not recommended)")
    elif avg_ta > 8:
        issues.append("⚠️ **WARNING**: Average TA too high (>8.0) - undershooting or coverage gap")
        issues.append("   Recommendation: Increase reference_signal_power to improve coverage")

    if not issues:
        return "✅ Coverage distribution is **HEALTHY** - no TA-based issues detected.\n" + \
               "   - Overshoot percentage within target (<5%)\n" + \
               "   - Cell edge loading acceptable (<20%)\n" + \
               "   - Average TA index in optimal range (4-7)"

    return "\n".join(issues)


def _generate_ta_recommendations(ta_record: dict) -> List[str]:
    """Generate actionable recommendations based on TA data."""
    recommendations = []

    overshoot = ta_record.get('overshoot_percentage', 0)
    cell_edge = ta_record.get('cell_edge_percentage', 0)
    avg_ta = ta_record.get('avg_ta_index', 0)

    # High overshoot recommendations
    if overshoot > 10:
        recommendations.append(f"Apply **Rule 11**: High overshoot ({overshoot:.1f}%) → Reduce reference_signal_power by 1-2 dB")
        if overshoot > 15:
            recommendations.append("🚨 Alert engineer for **manual antenna downtilt** inspection")

    # High cell edge recommendations
    if cell_edge > 20:
        recommendations.append(f"Apply **Rule 12**: High cell edge ({cell_edge:.1f}%) → Increase reference_signal_power by 1-3 dB")
        recommendations.append("Monitor neighbor cells for increased interference after power increase")

    # Low avg TA recommendations
    if avg_ta < 3:
        recommendations.append(f"Apply **Rule 13**: Low avg TA ({avg_ta:.2f}) → ALERT ONLY - Manual antenna adjustment needed")
        recommendations.append("Do NOT attempt automated parameter optimization for this issue")

    # Conflicting recommendations check
    if overshoot > 10 and cell_edge > 20:
        recommendations.append("⚠️ **CONFLICT DETECTED**: High overshoot AND high cell edge present")
        recommendations.append("Priority: Address overshoot first (higher immediate risk), then monitor cell edge")

    return recommendations
