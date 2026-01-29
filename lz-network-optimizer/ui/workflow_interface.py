"""
Liquid Zimbabwe 4G Network Optimizer - Workflow Interface
Purpose: Bridge between Streamlit UI and agent workflow
"""

import logging
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List

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
        result = parse_workflow_results(result_state)

        # Log the optimization query to activity database
        try:
            from ui.database_helper import log_optimization_query
            log_optimization_query(
                site_name=site_name,
                user_query=user_query,
                status="approved" if result.get("status") == "success" else "incomplete",
                recommendation_summary=result.get("issue"),
                kpi_issue=result.get("issue"),
                parameters_recommended=json.dumps(result.get("recommendations", [])),
                validation_status=result.get("validation_status")
            )
            logger.info(f"Logged optimization query for {site_name}")
        except Exception as log_error:
            logger.warning(f"Failed to log optimization query: {log_error}")

        return result

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

    # Get all agent outputs
    kpi_output = state.get("kpi_output", "")
    validation_output = agent_outputs.get("validation", "")

    # ==========================================================================
    # RISK SCORE: Extract from validation OR calculate from recommendations
    # ==========================================================================
    risk_score = extract_risk_score(validation_output)

    # If extraction returned default (5.0) and we have recommendations, calculate real risk
    # This ensures we get a grounded risk score based on actual parameter changes
    if risk_score == 5.0 and recommendations:
        calculated_risk = calculate_risk_from_recommendations(recommendations)
        risk_score = calculated_risk
        logger.info(f"Using calculated risk score: {risk_score}/10 (based on {len(recommendations)} recommendations)")

    risk_level = categorize_risk(risk_score)

    # ==========================================================================
    # MML COMMANDS: Extract from text OR generate from recommendations
    # ==========================================================================
    mml_commands = extract_mml_commands(config_output, recommendations)

    # Extract expected impact
    expected_impact = extract_expected_impact(config_output)
    
    # Parse detailed sections from all agent outputs
    kpi_sections = parse_detailed_sections(kpi_output)
    config_sections = parse_detailed_sections(config_output)
    validation_sections = parse_detailed_sections(validation_output)

    # Combine sections - prefer more detailed output
    detailed_issue = kpi_sections.get("issue", "") or config_sections.get("issue", "") or issue_desc
    detailed_recommendations = config_sections.get("recommendations", "")
    detailed_risk = validation_sections.get("risk", "") or config_sections.get("risk", "")
    detailed_impact = (config_sections.get("impact", "") or 
                      validation_sections.get("impact", "") or 
                      expected_impact)

    return {
        "status": "success",
        "issue": issue_desc,
        "recommendations": recommendations,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "expected_impact": expected_impact,
        "mml_commands": mml_commands,
        "validation_status": validation_status,
        "detailed_issue": detailed_issue,
        "detailed_recommendations": detailed_recommendations,
        "detailed_risk": detailed_risk,
        "detailed_impact": detailed_impact
    }


def parse_recommendations(config_output: str) -> List[Dict[str, Any]]:
    """
    Parse parameter recommendations from configuration output.

    Args:
        config_output: Raw output from configuration agent

    Returns:
        List of dicts with parameter changes including current and recommended values
    """
    recommendations = []

    # Parameter mappings with display names and units
    param_mappings = {
        "reference_signal_power": {"name": "Reference Signal Power", "unit": "dBm", "key": "reference_signal_power_pdschcfg"},
        "pdschcfg": {"name": "Reference Signal Power", "unit": "dBm", "key": "reference_signal_power_pdschcfg"},
        "referencesignalpower": {"name": "Reference Signal Power", "unit": "dBm", "key": "reference_signal_power_pdschcfg"},
        "a3_event_offset": {"name": "A3 Event Offset", "unit": "dB", "key": "a3_event_offset"},
        "a3offset": {"name": "A3 Event Offset", "unit": "dB", "key": "a3_event_offset"},
        "a3 offset": {"name": "A3 Event Offset", "unit": "dB", "key": "a3_event_offset"},
        "t310_timer": {"name": "T310 Timer", "unit": "ms", "key": "t310_timer"},
        "t310": {"name": "T310 Timer", "unit": "ms", "key": "t310_timer"},
        "p0_nominal_pusch": {"name": "P0 Nominal PUSCH", "unit": "dBm", "key": "p0_nominal_pusch"},
        "p0nominal": {"name": "P0 Nominal PUSCH", "unit": "dBm", "key": "p0_nominal_pusch"},
        "p0 nominal": {"name": "P0 Nominal PUSCH", "unit": "dBm", "key": "p0_nominal_pusch"},
        "pdcch_aggregation": {"name": "PDCCH Aggregation Level", "unit": "", "key": "pdcch_aggregation_level"},
        "aggregation_level": {"name": "PDCCH Aggregation Level", "unit": "", "key": "pdcch_aggregation_level"},
        "pdcch": {"name": "PDCCH Aggregation Level", "unit": "", "key": "pdcch_aggregation_level"}
    }

    # Track which parameters we've already added (by key)
    added_params = set()

    # FIRST: Try to extract from structured LLM output format
    # Format: "PRIMARY PARAMETER: ...\n  Current: X\n  Recommended: Y"
    structured_patterns = [
        # Match "Current: 152 (15.2 dBm)" or "Current: 152" followed by "Recommended: 172"
        r'(?:PRIMARY|SECONDARY)\s+PARAMETER[:\s]+[^\n]*?(reference.?signal|a3.?offset|t310|p0.?nominal|pdcch)[^\n]*\n[^\n]*?Current[:\s]+(\d+\.?\d*)[^\n]*\n[^\n]*?Recommended[:\s]+(\d+\.?\d*)',
        # Also try without the label
        r'(reference.?signal|a3.?offset|t310|p0.?nominal|pdcch)[^\n]*\n[^\n]*?Current[:\s]+(\d+\.?\d*)[^\n]*\n[^\n]*?Recommended[:\s]+(\d+\.?\d*)',
    ]

    for pattern in structured_patterns:
        matches = re.findall(pattern, config_output, re.IGNORECASE | re.DOTALL)
        for match in matches:
            param_text = match[0].lower().replace("_", "").replace(" ", "")
            current_val = match[1]
            new_val = match[2]

            # Find matching parameter
            for key_pattern, param_info in param_mappings.items():
                key_clean = key_pattern.replace("_", "").replace(" ", "")
                if key_clean in param_text or param_text in key_clean:
                    if param_info["key"] not in added_params:
                        recommendations.append({
                            "parameter": param_info["name"],
                            "current_value": current_val,
                            "recommended_value": new_val,
                            "unit": param_info["unit"],
                            "description": f"Adjust {param_info['name']} to optimize performance"
                        })
                        added_params.add(param_info["key"])
                    break

    # SECOND: Try inline patterns like "param: 100 → 120" or "param from 100 to 120"
    value_patterns = [
        r'(\w+)[:\s]+(-?\d+\.?\d*)\s*(?:→|->|to)\s*(-?\d+\.?\d*)',  # param: 100 → 120
        r'(\w+)\s+from\s+(-?\d+\.?\d*)\s+to\s+(-?\d+\.?\d*)',  # param from 100 to 120
    ]

    config_lower = config_output.lower()

    for pattern in value_patterns:
        matches = re.findall(pattern, config_lower, re.IGNORECASE)
        for match in matches:
            param_text = match[0].lower().replace("_", "").replace("-", "").replace(" ", "")

            # Find matching parameter
            for key_pattern, param_info in param_mappings.items():
                key_clean = key_pattern.replace("_", "").replace(" ", "")
                if key_clean in param_text or param_text in key_clean:
                    if param_info["key"] not in added_params:
                        current_val = match[1]
                        new_val = match[2]

                        recommendations.append({
                            "parameter": param_info["name"],
                            "current_value": current_val,
                            "recommended_value": new_val,
                            "unit": param_info["unit"],
                            "description": f"Adjust {param_info['name']} to optimize performance"
                        })
                        added_params.add(param_info["key"])
                    break

    # THIRD: Look for Current/Recommended pairs anywhere in the text for any parameter
    if not recommendations:
        # Generic extraction: find any "Current: X" followed by "Recommended: Y"
        current_rec_pattern = r'Current[:\s]+(\d+\.?\d*)[^\n]*(?:\n[^\n]*)*?Recommended[:\s]+(\d+\.?\d*)'
        matches = re.findall(current_rec_pattern, config_output, re.IGNORECASE)

        for i, match in enumerate(matches):
            if i < len(param_mappings):  # Limit to reasonable number
                recommendations.append({
                    "parameter": f"Parameter {i+1}",
                    "current_value": match[0],
                    "recommended_value": match[1],
                    "unit": "",
                    "description": "Parameter adjustment based on KPI analysis"
                })

    # FOURTH: Check for parameter mentions without specific values (with fallback values)
    if not recommendations:
        for key_pattern, param_info in param_mappings.items():
            if param_info["key"] not in added_params:
                if key_pattern in config_lower or key_pattern.replace("_", " ") in config_lower:
                    # Try to find ANY numbers near this parameter mention
                    param_section = re.search(
                        rf'{key_pattern}[^\n]*?(\d+\.?\d*)[^\n]*?(\d+\.?\d*)?',
                        config_lower, re.IGNORECASE
                    )
                    if param_section and param_section.group(1):
                        current_val = param_section.group(1)
                        new_val = param_section.group(2) if param_section.group(2) else "optimized"
                    else:
                        current_val = "current"
                        new_val = "optimized"

                    recommendations.append({
                        "parameter": param_info["name"],
                        "current_value": current_val,
                        "recommended_value": new_val,
                        "unit": param_info["unit"],
                        "description": f"Adjust {param_info['name']} based on KPI analysis"
                    })
                    added_params.add(param_info["key"])

    # Final fallback - but with better message
    if not recommendations:
        recommendations.append({
            "parameter": "Network Optimization",
            "current_value": "current",
            "recommended_value": "optimized",
            "unit": "",
            "description": "See detailed analysis for specific parameter recommendations"
        })

    return recommendations


def calculate_risk_from_recommendations(recommendations: List[Dict[str, Any]]) -> float:
    """
    Calculate risk score based on actual parameter changes.
    Uses same logic as validation_agent.py TIER 2 for consistency.

    Args:
        recommendations: List of parameter recommendations with current/new values

    Returns:
        Risk score (0-10) based on:
        - Parameter type (power changes = higher risk)
        - Magnitude of change
        - Base risk of 3 points
    """
    if not recommendations:
        return 5.0  # Medium risk default when no recommendations

    risk = 3  # Base risk (same as validation_agent.py)

    high_risk_params = ['reference_signal_power', 'p0_nominal', 'p0nominal', 'pdschcfg']
    medium_risk_params = ['a3_event_offset', 'a3_offset', 'a3offset', 't310', 'timer']

    for rec in recommendations:
        param_lower = rec.get("parameter", "").lower().replace(" ", "_")
        current = rec.get("current_value")
        new = rec.get("recommended_value")

        # Skip non-numeric recommendations
        if new in ["optimized", "current", None, ""]:
            continue

        # Parameter type risk
        if any(p in param_lower for p in high_risk_params):
            risk += 2
        elif any(p in param_lower for p in medium_risk_params):
            risk += 1

        # Magnitude risk (if we have numeric values)
        try:
            # Clean numeric values
            current_str = str(current).replace('dBm', '').replace('dB', '').replace('ms', '').replace('MS', '').strip()
            new_str = str(new).replace('dBm', '').replace('dB', '').replace('ms', '').replace('MS', '').strip()

            # Handle T310 timer format like "MS1000_T310" -> extract 1000
            if 'MS' in str(current).upper():
                import re
                match = re.search(r'(\d+)', str(current))
                if match:
                    current_str = match.group(1)
            if 'MS' in str(new).upper():
                import re
                match = re.search(r'(\d+)', str(new))
                if match:
                    new_str = match.group(1)

            current_float = float(current_str)
            new_float = float(new_str)

            if current_float != 0:
                change_pct = abs((new_float - current_float) / current_float) * 100
                if change_pct > 30:
                    risk += 3
                elif change_pct > 20:
                    risk += 2
                elif change_pct > 10:
                    risk += 1

                logger.debug(f"Risk calc for {param_lower}: {current_float} -> {new_float} ({change_pct:.1f}% change)")
        except (ValueError, TypeError) as e:
            logger.debug(f"Could not calculate magnitude risk for {param_lower}: {e}")

    final_risk = min(risk, 10.0)
    logger.info(f"Calculated risk score from recommendations: {final_risk}/10")
    return final_risk


def extract_risk_score(validation_output: str) -> float:
    """
    Extract risk score from validation output.

    Args:
        validation_output: Output from validation agent

    Returns:
        Risk score (0-10)
    """
    if not validation_output:
        return 5.0  # Default to medium risk if no output

    # Patterns ordered from most specific to least specific
    patterns = [
        r'(?:Maximum\s+)?Risk\s+Score[:\s]+(\d+\.?\d*)\s*/\s*10',  # "Maximum Risk Score: 7/10"
        r'Risk\s+Score[:\s]+(\d+\.?\d*)',  # "Risk Score: 7"
        r'risk[:\s]+(\d+\.?\d*)\s*/\s*10',  # "risk: 7/10"
        r'risk.*?(\d+\.?\d*)\s*out\s*of\s*10',  # "risk 7 out of 10"
        r'risk.*?(\d+)\s*/\s*10',  # "risk 7/10"
        r'risk.*?score.*?(\d+\.?\d*)',  # "risk score 7"
        r'score.*?(\d+\.?\d*)\s*/\s*10',  # "score: 7/10"
        r'(\d+\.?\d*)\s*/\s*10\s*risk',  # "7/10 risk"
        r'risk.*?(\d+\.?\d*)',  # generic "risk: 7"
        r'score.*?(\d+\.?\d*)',  # generic "score: 7"
    ]

    validation_lower = validation_output.lower()

    for pattern in patterns:
        match = re.search(pattern, validation_lower)
        if match:
            try:
                score = float(match.group(1))
                # Validate it's a reasonable risk score (0-10)
                if 0.0 <= score <= 10.0:
                    return score
                # If score > 10, might be percentage or other format
                elif score <= 100:
                    return score / 10.0  # Convert percentage to 0-10
            except (ValueError, IndexError):
                pass

    # Try to infer from risk level keywords
    if "high risk" in validation_lower or "critical" in validation_lower:
        return 8.0
    elif "medium risk" in validation_lower or "moderate" in validation_lower:
        return 5.0
    elif "low risk" in validation_lower or "minimal" in validation_lower:
        return 3.0

    # Default to medium risk if can't extract - this is a safe default
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


def extract_mml_commands(config_output: str, recommendations: List[Dict[str, Any]] = None) -> List[str]:
    """
    Extract MML commands from configuration output, or GENERATE them from recommendations.

    Args:
        config_output: Output from configuration agent
        recommendations: Optional list of parameter recommendations to generate MML from

    Returns:
        List of MML command strings
    """
    commands = []

    # First, strip markdown code block markers
    cleaned_output = config_output if config_output else ""
    cleaned_output = re.sub(r'```\w*\n?', '', cleaned_output)  # Remove ```python, ```mml, etc.
    cleaned_output = re.sub(r'`([^`]+)`', r'\1', cleaned_output)  # Remove inline code markers

    # MML command prefixes (Huawei format)
    mml_prefixes = ['MOD', 'ADD', 'LST', 'SET', 'ALM', 'DSP', 'DEL', 'ACT', 'DEA', 'BLK', 'UBL']

    # Look for lines that look like MML commands
    for line in cleaned_output.split('\n'):
        line = line.strip()

        # Skip empty lines and comment lines
        if not line or line.startswith('#') or line.startswith('//'):
            continue

        # Remove leading numbers/bullets (e.g., "1. MOD..." or "- MOD...")
        line = re.sub(r'^[\d\.\-\*\s]+', '', line).strip()

        # Check if line starts with MML command prefix
        line_upper = line.upper()
        for prefix in mml_prefixes:
            if line_upper.startswith(prefix):
                # Clean up the command
                clean_cmd = line.strip()
                if clean_cmd and clean_cmd not in commands:
                    commands.append(clean_cmd)
                break

    # Also look for commands in code block format that might have been missed
    code_block_match = re.findall(r'(?:MOD|ADD|SET|LST)[A-Z0-9_]+:[^;]+;', config_output or "", re.IGNORECASE)
    for cmd in code_block_match:
        cmd = cmd.strip()
        if cmd and cmd not in commands:
            commands.append(cmd)

    # ==========================================================================
    # GENERATE MML COMMANDS FROM RECOMMENDATIONS (if none found in text)
    # ==========================================================================
    if not commands and recommendations:
        logger.info("No MML commands found in text - generating from recommendations...")

        try:
            from domain.mml_commands import build_modify_command, MML_COMMANDS
        except ImportError:
            logger.warning("Could not import mml_commands module for MML generation")
            return commands

        # Map display names back to internal parameter keys
        param_name_map = {
            "Reference Signal Power": "reference_signal_power_pdschcfg",
            "reference signal power": "reference_signal_power_pdschcfg",
            "A3 Event Offset": "a3_event_offset",
            "a3 event offset": "a3_event_offset",
            "A3 Offset": "a3_event_offset",
            "T310 Timer": "t310_timer",
            "t310 timer": "t310_timer",
            "T310": "t310_timer",
            "P0 Nominal PUSCH": "p0_nominal_pusch",
            "p0 nominal pusch": "p0_nominal_pusch",
            "P0 Nominal": "p0_nominal_pusch",
            "PDCCH Aggregation Level": "pdcch_aggregation_level",
            "pdcch aggregation level": "pdcch_aggregation_level",
        }

        for rec in recommendations:
            param_name = rec.get("parameter", "")
            new_value = rec.get("recommended_value")

            # Skip non-actionable recommendations
            if new_value in ["optimized", "current", None, ""]:
                logger.debug(f"Skipping non-numeric recommendation: {param_name} = {new_value}")
                continue

            # Map display name to internal name
            internal_name = param_name_map.get(param_name)
            if not internal_name:
                # Try case-insensitive match
                internal_name = param_name_map.get(param_name.lower())
            if not internal_name:
                # Try converting display name to snake_case
                internal_name = param_name.lower().replace(" ", "_")

            # Check if this parameter is supported for modification
            if internal_name not in MML_COMMANDS:
                logger.warning(f"Parameter '{internal_name}' not found in MML_COMMANDS")
                continue

            if MML_COMMANDS[internal_name].get("modify") is None:
                logger.warning(f"Parameter '{internal_name}' is read-only (no modify command)")
                continue

            try:
                # Clean the value for MML command
                clean_value = str(new_value).strip()

                # Handle T310 timer format - needs to be like "MS1000_T310"
                if internal_name == "t310_timer":
                    if not clean_value.upper().startswith("MS"):
                        # Extract numeric value and format correctly
                        match = re.search(r'(\d+)', clean_value)
                        if match:
                            ms_value = match.group(1)
                            clean_value = f"MS{ms_value}_T310"

                # Generate commands for all 6 cells at the site
                for cell_id in [1, 2, 3, 4, 5, 6]:
                    cmd = build_modify_command(internal_name, clean_value, cell_id)
                    if cmd and cmd not in commands:
                        commands.append(cmd)

                logger.info(f"Generated 6 MML commands for {internal_name} = {clean_value}")

            except Exception as e:
                logger.warning(f"Could not generate MML for {param_name}: {e}")

    if commands:
        logger.info(f"Total MML commands: {len(commands)}")
    else:
        logger.warning("No MML commands extracted or generated")

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
    - PRIMARY ISSUE / Issue Identified
    - PRIMARY PARAMETER / SECONDARY PARAMETER / Recommended Changes
    - Risk Factors / Risk Assessment
    - Expected Impact / Expected KPI Improvements
    
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
        line_upper = line.upper()
        
        # Check for section headers (support both old and new formats)
        if ("PRIMARY ISSUE:" in line_upper or "ISSUE IDENTIFIED" in line_upper):
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            current_section = "issue"
            section_content = [line]  # Include the header
            
        elif ("PRIMARY PARAMETER:" in line_upper or "SECONDARY PARAMETER:" in line_upper or 
              "RECOMMENDED CHANGES" in line_upper or "💡 RECOMMENDED CHANGES" in line_upper):
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            current_section = "recommendations"
            if not section_content:  # Only add if starting fresh
                section_content = [line]
            else:
                section_content.append(line)
            
        elif ("RISK FACTORS:" in line_upper or "RISK ASSESSMENT" in line_upper or 
              "⚠️ RISK ASSESSMENT" in line_upper):
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            current_section = "risk"
            section_content = [line]
            
        elif ("EXPECTED IMPACT" in line_upper or "EXPECTED KPI IMPROVEMENTS" in line_upper or
              "📈 EXPECTED IMPACT" in line_upper or "PERFORMANCE IMPROVEMENTS:" in line_upper):
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            current_section = "impact"
            section_content = [line]
            
        elif "EXECUTION MODE" in line_upper or "NEXT STEP" in line_upper or "=====" in line:
            # End of section - save and stop
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            if "=====" in line and "CONFIGURATION RECOMMENDATIONS" not in line_upper:
                break
            
        elif current_section and line.strip() and not line.startswith('━'):
            # Stop impact section when hitting other major sections
            if current_section == "impact":
                stop_keywords = [
                    "RISK MITIGATION", "MITIGATION PLAN", "MONITORING PLAN",
                    "ROLLBACK", "DECISION:", "OVERALL DECISION", "RECOMMENDATION:",
                    "SAFETY CHECK", "VALIDATION", "METHOD:", "PARAMETER #",
                    "MULTI-PARAMETER", "CONFLICT ANALYSIS"
                ]
                if any(kw in line.upper() for kw in stop_keywords):
                    sections[current_section] = '\n'.join(section_content).strip()
                    current_section = None
                    section_content = []
                    continue

            # Add content to current section (skip separator lines)
            section_content.append(line)

    # Capture last section if any
    if current_section and section_content:
        sections[current_section] = '\n'.join(section_content).strip()

    # ==========================================================================
    # POST-PROCESSING: Clean up and limit impact section
    # ==========================================================================
    if sections.get("impact"):
        lines = sections["impact"].split('\n')
        # Keep only lines that look like impact statements (contain improvement keywords)
        impact_lines = []
        impact_keywords = ['improve', 'increase', 'decrease', 'reduce', 'enhance',
                          '%', 'mbps', 'ms', 'db', 'kpi', 'throughput', 'latency',
                          'speed', 'access', 'success', 'rate', 'quality']

        for line in lines:
            if len(impact_lines) >= 10:  # Max 10 lines
                break
            line_clean = line.strip()
            if not line_clean:
                continue
            # Skip header/separator lines
            if line_clean.startswith('━') or line_clean.startswith('=') or line_clean.startswith('-'*5):
                continue
            # Skip lines that are just headers
            if line_clean.upper() in ['EXPECTED IMPACT', 'EXPECTED KPI IMPROVEMENTS', 'PERFORMANCE IMPROVEMENTS:']:
                continue
            # Include lines that have impact-related keywords
            if any(kw in line_clean.lower() for kw in impact_keywords):
                # Clean up bullet points
                line_clean = re.sub(r'^[•\-\*\d\.]+\s*', '', line_clean)
                if line_clean:
                    impact_lines.append(line_clean)

        sections["impact"] = '\n'.join(impact_lines[:10]) if impact_lines else ""
        logger.debug(f"Impact section limited to {len(impact_lines)} lines")

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
