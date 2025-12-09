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

        # Run the workflow with individual arguments (not a dict!)
        # The workflow function expects: site_name: str, user_query: str, cell_id: int
        logger.info(f"Starting optimization workflow for {site_name}")
        logger.info(f"User query: {user_query}")
        result_state = run_workflow(
            site_name=site_name,
            user_query=user_query,
            cell_id=cell_id
        )

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
    
    # Parse detailed sections from config_output
    detailed_sections = parse_detailed_sections(config_output)

    return {
        "status": "success",
        "issue": issue_desc,
        "recommendations": recommendations,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "expected_impact": expected_impact,
        "mml_commands": mml_commands,
        "validation_status": validation_status,
        "detailed_issue": detailed_sections.get("issue", issue_desc),
        "detailed_recommendations": detailed_sections.get("recommendations", ""),
        "detailed_risk": detailed_sections.get("risk", ""),
        "detailed_impact": detailed_sections.get("impact", expected_impact)
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


def parse_detailed_sections(config_output: str) -> Dict[str, str]:
    """
    Parse the detailed technical sections from configuration output.
    
    Extracts content from:
    - ISSUE IDENTIFIED
    - RECOMMENDED CHANGES
    - RISK ASSESSMENT
    - EXPECTED IMPACT
    
    Args:
        config_output: Raw configuration output with technical sections
        
    Returns:
        Dictionary with parsed sections
    """
    sections = {
        "issue": "",
        "recommendations": "",
        "risk": "",
        "impact": ""
    }
    
    if not config_output:
        return sections
    
    lines = config_output.split('\n')
    current_section = None
    section_content = []
    
    for line in lines:
        # Check for section headers
        if "ISSUE IDENTIFIED" in line:
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            current_section = "issue"
            section_content = []
        elif "RECOMMENDED CHANGES" in line:
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            current_section = "recommendations"
            section_content = []
        elif "RISK ASSESSMENT" in line:
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            current_section = "risk"
            section_content = []
        elif "EXPECTED IMPACT" in line:
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            current_section = "impact"
            section_content = []
        elif "EXECUTION MODE" in line or "NEXT STEP" in line:
            # End of impact section
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            break
        elif current_section and line.strip() and not line.startswith('━'):
            # Add content to current section (skip separator lines)
            section_content.append(line)
    
    # Capture last section if any
    if current_section and section_content:
        sections[current_section] = '\n'.join(section_content).strip()
    
    return sections


def execute_optimization(site_name: str, recommendations: list, mml_commands: list) -> Dict[str, Any]:
    """
    Execute approved optimization recommendations.

    Args:
        site_name: Name of the site
        recommendations: List of approved parameter changes
        mml_commands: List of MML commands to execute

    Returns:
        Dict with execution results:
        - status: "success", "partial", "error"
        - executed: Number of commands executed
        - failed: Number of commands failed
        - details: List of execution details per command
        - message: Summary message
    """
    try:
        # Import tools
        from tools.rollback_manager import capture_rollback_state
        from agents.mml_executor_agent import mml_executor_agent

        logger.info(f"Executing optimization for {site_name}")
        logger.info(f"Commands to execute: {len(mml_commands)}")

        # Check if in dry-run mode
        import yaml
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        dry_run = config.get('agents', {}).get('mml_executor', {}).get('dry_run', False)

        if dry_run:
            logger.info("DRY RUN MODE - Simulating execution")
            return {
                "status": "success",
                "executed": len(mml_commands),
                "failed": 0,
                "details": [
                    {"command": cmd, "status": "simulated", "message": "[DRY RUN] Would execute command"}
                    for cmd in mml_commands
                ],
                "message": f"[DRY RUN] Would execute {len(mml_commands)} commands. No actual changes made.",
                "dry_run": True
            }

        # Execute with MML executor agent
        execution_state = {
            "site_name": site_name,
            "cell_id": 1,  # Will be handled by batch execution
            "user_query": "Execute approved optimizations",
            "config_output": "\n".join(mml_commands),
            "validation_status": "APPROVED",
            "is_validated": True,
            "recommended_changes": recommendations
        }

        result_state = mml_executor_agent(execution_state)

        # Parse execution results
        executor_output = result_state.get("executor_output", "")

        # Count successes and failures
        executed = executor_output.lower().count("success")
        failed = executor_output.lower().count("fail")

        if failed == 0:
            status = "success"
            message = f"Successfully executed {executed} commands"
        elif executed > 0:
            status = "partial"
            message = f"Executed {executed} commands, {failed} failed"
        else:
            status = "error"
            message = f"Failed to execute commands: {executor_output[:200]}"

        return {
            "status": status,
            "executed": executed,
            "failed": failed,
            "details": parse_execution_details(executor_output),
            "message": message,
            "dry_run": False
        }

    except Exception as e:
        logger.error(f"Execution error: {e}")
        return {
            "status": "error",
            "executed": 0,
            "failed": len(mml_commands),
            "details": [],
            "message": f"Execution failed: {str(e)}",
            "dry_run": False
        }


def parse_execution_details(executor_output: str) -> list:
    """Parse execution details from executor output"""
    details = []

    # Simple parsing - look for command results in output
    for line in executor_output.split('\n'):
        if 'MOD' in line or 'ADD' in line or 'SET' in line:
            status = "success" if "success" in line.lower() else "failed"
            details.append({
                "command": line[:100],
                "status": status,
                "message": line
            })

    return details
