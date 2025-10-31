"""
Liquid Zimbabwe 4G Network Optimizer - Workflow Interface
Purpose: Bridge between Streamlit UI and agent workflow
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Add parent directory to path so we can import agents
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_optimization(site_name: str, cell_id: int, user_query: str) -> Dict[str, Any]:
    """
    Run the complete optimization workflow for a site.

    Args:
        site_name: Name of the site to optimize
        cell_id: Cell ID for the site
        user_query: Natural language query from user

    Returns:
        Dict with workflow results including:
        - status: "success", "error", "rejected"
        - issue: Description of identified issue
        - recommendations: List of parameter changes
        - risk_level: "LOW", "MEDIUM", "HIGH"
        - risk_score: Float 0-10
        - expected_impact: Description of expected improvement
        - mml_commands: List of MML commands to execute
        - error_message: Error description if status is "error"
    """
    try:
        # Import workflow (inside function to avoid issues if not in path)
        from agents.workflow import run_optimization as run_workflow

        # Prepare initial state
        initial_state = {
            "site_name": site_name,
            "cell_id": cell_id,
            "user_query": user_query,
            "agent_outputs": {},
            "data_source": "unknown",
            "needs_optimization": False,
            "primary_kpi_issue": None,
            "config_output": "",
            "validation_status": "PENDING",
            "optimization_success": False
        }

        # Run the workflow
        logger.info(f"Starting optimization workflow for {site_name}")
        result_state = run_workflow(initial_state)

        # Parse results into UI-friendly format
        return parse_workflow_results(result_state)

    except ImportError as e:
        logger.error(f"Failed to import workflow: {e}")
        return {
            "status": "error",
            "error_message": f"Workflow import error: {str(e)}. Make sure agents are properly configured."
        }

    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        return {
            "status": "error",
            "error_message": f"Optimization failed: {str(e)}"
        }


def parse_workflow_results(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse workflow state into UI-friendly format.

    Args:
        state: Final workflow state from agents

    Returns:
        Formatted results dict
    """
    # Extract agent outputs
    agent_outputs = state.get("agent_outputs", {})

    # Determine if optimization is needed
    needs_optimization = state.get("needs_optimization", False)

    if not needs_optimization:
        return {
            "status": "success",
            "issue": "No optimization needed",
            "message": "All KPIs are within acceptable thresholds. Network performance is good.",
            "recommendations": [],
            "risk_level": "NONE",
            "risk_score": 0.0,
            "expected_impact": "No changes recommended",
            "mml_commands": []
        }

    # Get primary issue
    primary_issue = state.get("primary_kpi_issue", "unknown")
    issue_descriptions = {
        "low_download_speed": "Low download speed detected",
        "low_network_access_success": "Low network access success rate",
        "low_upload_speed": "Low upload speed detected",
        "poor_quality": "Poor signal quality detected",
        "high_channel_load": "High channel load detected"
    }
    issue_desc = issue_descriptions.get(primary_issue, "Performance issue detected")

    # Parse configuration output for recommendations
    config_output = state.get("config_output", "")
    recommendations = parse_recommendations(config_output)

    # Get validation status
    validation_status = state.get("validation_status", "PENDING")

    if validation_status == "REJECTED":
        return {
            "status": "rejected",
            "issue": issue_desc,
            "message": "Proposed changes were rejected due to safety concerns.",
            "recommendations": recommendations,
            "risk_level": "HIGH",
            "risk_score": 9.0,
            "expected_impact": "Changes not approved",
            "mml_commands": []
        }

    # Determine risk level from validation
    risk_score = extract_risk_score(agent_outputs.get("validation", ""))
    risk_level = categorize_risk(risk_score)

    # Extract MML commands from executor output
    mml_commands = extract_mml_commands(config_output)

    # Extract expected impact
    expected_impact = extract_expected_impact(config_output)

    return {
        "status": "success",
        "issue": issue_desc,
        "recommendations": recommendations,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "expected_impact": expected_impact,
        "mml_commands": mml_commands,
        "validation_status": validation_status
    }


def parse_recommendations(config_output: str) -> list:
    """
    Parse parameter recommendations from configuration output.

    Args:
        config_output: Raw output from configuration agent

    Returns:
        List of dicts with parameter changes
    """
    recommendations = []

    # Simple parsing - look for parameter names and values
    # In production, would use more robust parsing

    param_keywords = {
        "reference_signal_power": "Reference Signal Power",
        "a3_event_offset": "A3 Event Offset",
        "t310_timer": "T310 Timer",
        "p0_nominal_pusch": "P0 Nominal PUSCH",
        "pdcch_aggregation_level": "PDCCH Aggregation Level"
    }

    for param_key, param_name in param_keywords.items():
        if param_key in config_output.lower():
            # Try to extract old and new values
            # This is simplified - production would use regex or structured parsing
            recommendations.append({
                "parameter": param_name,
                "description": f"Adjust {param_name} to optimize performance",
                "change": "Recommended adjustment based on KPI analysis"
            })

    # If no specific recommendations found, add generic one
    if not recommendations:
        recommendations.append({
            "parameter": "Network Parameters",
            "description": "Optimization recommendations available",
            "change": "See detailed output for specific parameter adjustments"
        })

    return recommendations


def extract_risk_score(validation_output: str) -> float:
    """
    Extract risk score from validation output.

    Args:
        validation_output: Output from validation agent

    Returns:
        Risk score (0-10)
    """
    # Simple extraction - look for numbers that could be risk scores
    # In production, would use structured output

    import re

    # Look for patterns like "risk: 5/10" or "score: 5"
    patterns = [r'risk.*?(\d+)/10', r'risk.*?(\d+\.?\d*)', r'score.*?(\d+\.?\d*)']

    for pattern in patterns:
        match = re.search(pattern, validation_output.lower())
        if match:
            try:
                score = float(match.group(1))
                return min(max(score, 0.0), 10.0)  # Clamp to 0-10
            except:
                pass

    # Default to medium risk if can't extract
    return 5.0


def categorize_risk(risk_score: float) -> str:
    """
    Categorize numeric risk score into level.

    Args:
        risk_score: Numeric score 0-10

    Returns:
        Risk level: "LOW", "MEDIUM", "HIGH"
    """
    if risk_score <= 3.0:
        return "LOW"
    elif risk_score <= 7.0:
        return "MEDIUM"
    else:
        return "HIGH"


def extract_mml_commands(config_output: str) -> list:
    """
    Extract MML commands from configuration output.

    Args:
        config_output: Output from configuration agent

    Returns:
        List of MML command strings
    """
    commands = []

    # Look for lines that look like MML commands
    # MML commands typically start with MOD, ADD, LST, etc.
    for line in config_output.split('\n'):
        line = line.strip()
        if any(line.upper().startswith(cmd) for cmd in ['MOD', 'ADD', 'LST', 'SET', 'ALM']):
            commands.append(line)

    return commands


def extract_expected_impact(config_output: str) -> str:
    """
    Extract expected impact description from output.

    Args:
        config_output: Output from configuration agent

    Returns:
        Impact description string
    """
    # Look for impact-related keywords
    impact_keywords = ['improve', 'increase', 'decrease', 'enhance', 'optimize', 'mbps', 'performance']

    for line in config_output.split('\n'):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in impact_keywords):
            if len(line) > 10 and len(line) < 200:  # Reasonable length
                return line.strip()

    # Default impact message
    return "Expected improvement in network KPIs based on parameter optimization"
