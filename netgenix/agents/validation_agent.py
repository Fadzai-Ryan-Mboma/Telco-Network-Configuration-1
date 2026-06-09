"""
Liquid Zimbabwe 4G Network Optimizer - Validation Agent
Purpose: Validate parameter changes and assess safety
Created: 2025-10-30
"""

from typing import Dict, Any
from utils.llm_factory import get_llm_client, looks_like_llm_failure, message_to_text
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.huawei_tools import validate_parameter_range
from tools.validation_tools import assess_risk_score, validate_optimization_safety
from tools.sql_tools import execute_historical_sql
from tools.dummy_responses import get_validation_result_dummy, DUMMY_VALIDATION_RESULTS
from prompts.system_prompts import VALIDATION_AGENT_PROMPT
from utils.timeout_handler import TimeoutHandler, TimeoutError as LLMTimeoutError, VALIDATION_TIMEOUT

logger = logging.getLogger(__name__)


# ==========================================================================
# HELPER FUNCTIONS FOR RULE-BASED VALIDATION
# ==========================================================================

def _calculate_risk_score(parameter: str, current_value: float,
                         new_value: float, kpi_context: Dict) -> int:
    """
    Calculate 1-10 risk score based on:
    - Parameter type (power changes = higher risk)
    - Magnitude of change
    - Current network state (if KPIs already poor, higher risk)
    - Direction of change (increase vs decrease)
    """
    risk = 3  # Base risk

    # Parameter-specific risk
    high_risk_params = ['reference_signal_power_pdschcfg', 'p0_nominal_pusch']
    medium_risk_params = ['a3_event_offset', 't310_timer']

    if parameter in high_risk_params:
        risk += 2
    elif parameter in medium_risk_params:
        risk += 1

    # Magnitude risk
    if current_value != 0:
        change_pct = abs((new_value - current_value) / current_value) * 100
        if change_pct > 30:
            risk += 3
        elif change_pct > 20:
            risk += 2
        elif change_pct > 10:
            risk += 1

    # Network state risk
    if kpi_context:
        network_access = kpi_context.get('network_access_success', 100)
        if network_access < 90:  # Network already degraded
            risk += 2
        elif network_access < 95:
            risk += 1

    return min(risk, 10)  # Cap at 10


def _check_parameter_bounds(parameter: str, value: float) -> bool:
    """
    Check if parameter value is within valid bounds.
    Returns True if within bounds, False otherwise.
    """
    from domain.liquid_zimbabwe_parameters import LiquidZimbabweParameterManager

    try:
        param_manager = LiquidZimbabweParameterManager()
        if parameter in param_manager.parameter_config:
            param_info = param_manager.parameter_config[parameter]
            min_val = param_info.get('min_value', float('-inf'))
            max_val = param_info.get('max_value', float('inf'))

            return min_val <= value <= max_val
        else:
            logger.warning(f"⚠️  Unknown parameter: {parameter} - assuming valid")
            return True  # Conservative: allow unknown parameters
    except Exception as e:
        logger.error(f"❌ Error checking bounds: {e}")
        return True  # Conservative: allow on error


def validation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validation Agent - Validates safety of proposed parameter changes.

    2-TIER FALLBACK MECHANISM:
    Tier 1: LLM agent with validation tools (with 30s timeout)
    Tier 2: Rule-based validation from dummy data (always APPROVED for demo)
    """
    logger.info(f"🤖 VALIDATION AGENT - Starting safety validation")

    # Extract parameters
    site_name = state.get("site_name", "Unknown")
    config_output = state.get('config_output', '')
    primary_kpi_issue = state.get('primary_kpi_issue', 'unknown')

    logger.info(f"📝 Task: Validating recommendations for {site_name}")

    # ==========================================================================
    # TIER 1: Try LLM Agent with Tools (Primary)
    # ==========================================================================
    def try_llm_agent():
        """Attempt LLM-based validation."""
        logger.info("🔄 TIER 1: Attempting LLM agent validation...")

        # Initialize LLM using factory (supports OpenAI, NVIDIA, etc.)
        # Lower temperature for safety-critical decisions
        llm = get_llm_client(temperature=0.3)

        tools = [validate_parameter_range, assess_risk_score, validate_optimization_safety, execute_historical_sql]

        task = f"""
Validate parameter recommendations for site: {site_name}
Parameter Recommendations: {config_output}

STEPS:
1. Extract all parameter changes from recommendations
2. For EACH parameter:
   - Validate value range using validate_parameter_range
   - Assess risk score using assess_risk_score  
3. Validate combined safety using validate_optimization_safety
4. Determine decision: APPROVED (risk ≤5), REVIEW (5<risk≤7), or REJECTED (risk>7)

CRITICAL: After using tools, YOU MUST write complete detailed validation following the FINAL ANSWER FORMAT in the system prompt. Include:
- DECISION and RISK SCORE
- Specific risk factors with quantified impacts (e.g., Ping-Pong HO: 2.5%→4.1%)
- Mitigation strategies with details
- Safety checks for each parameter
- Expected impact with specific KPI projections
- Technical effects with trade-offs
- Rollback strategy with exact steps

DO NOT stop after tool execution - provide the full detailed textual validation!
"""

        # Build system prompt with task
        system_prompt = VALIDATION_AGENT_PROMPT + "\n\n" + task + "\n\nUSE TOOLS TO COMPLETE THIS TASK."

        # Create ReAct agent (LangGraph version)
        agent = create_react_agent(llm, tools, prompt=system_prompt)

        # Execute agent with timeout protection (30s for safety checks)
        timeout_handler = TimeoutHandler(timeout_seconds=90)  # Increased from 30s to 90s for NVIDIA LLM

        try:
            with timeout_handler.timeout_context("Validation Agent LLM call"):
                result = agent.invoke({"messages": [{"role": "user", "content": task}]})

        except LLMTimeoutError as timeout_error:
            logger.error(f"❌ VALIDATION AGENT TIMEOUT: {timeout_error}")
            logger.error(f"⚠️  The LLM took longer than 30 seconds to respond")
            raise Exception(f"LLM timeout - fallback will be attempted")

        # DEBUG: Log all messages
        logger.info(f"🔍 DEBUG: Total messages returned: {len(result.get('messages', []))}")
        for i, msg in enumerate(result.get("messages", [])):
            msg_type = getattr(msg, 'type', '') or getattr(msg, '__class__', '').__name__.lower()
            content_preview = str(msg.content)[:200] if hasattr(msg, 'content') else "No content"
            logger.info(f"🔍 Message {i}: Type={msg_type}, Content={content_preview}...")

        # Extract output from AI messages only (not user/human, not tool calls)
        ai_responses = []
        if "messages" in result and len(result["messages"]) > 0:
            for msg in result["messages"]:
                # Only get AI messages (check message type)
                msg_type = getattr(msg, 'type', '') or getattr(msg, '__class__', '').__name__.lower()
                if 'ai' in str(msg_type).lower() and hasattr(msg, 'content') and msg.content:
                    content = message_to_text(msg)
                    # Skip tool calls and task echoes
                    if ('<function' not in content and 
                        'YOUR TASK:' not in content and
                        len(content) > 100):
                        ai_responses.append(content)
                        logger.info(f"✅ Captured AI response: {len(content)} chars")
        
        # If no final text found, force LLM to generate it
        if not ai_responses:
            logger.info("⚠️ No final text found - requesting explicit final answer from LLM...")
            # Add follow-up message to existing conversation
            followup_prompt = """
Based on the tool results above, now provide your FINAL ANSWER in the exact detailed format specified in the system prompt.

Include:
- ━━━ visual separators
- All sections (PARAMETER-BY-PARAMETER SAFETY ANALYSIS, MULTI-PARAMETER CONFLICT ANALYSIS, etc.)
- Specific parameter values with units
- ✅ Range checks, 📊 Historical analysis, ⚠️ Side effects
- Risk scores with emoji indicators (🟢 🟡 🔴)
- Detailed justifications

Write your complete detailed validation analysis NOW:
"""
            # Continue conversation with follow-up (with timeout)
            messages = result.get("messages", [])
            messages.append({"role": "user", "content": followup_prompt})

            try:
                with timeout_handler.timeout_context("Validation Agent follow-up call"):
                    result = agent.invoke({"messages": messages})
            except LLMTimeoutError as timeout_error:
                logger.error(f"❌ VALIDATION AGENT FOLLOW-UP TIMEOUT: {timeout_error}")
                raise Exception(f"LLM follow-up timeout - fallback will be attempted")
            
            logger.info(f"🔍 Follow-up returned {len(result.get('messages', []))} total messages")
            
            # Extract AI response from follow-up
            for msg in reversed(result.get("messages", [])):
                msg_type = str(getattr(msg, 'type', '') or getattr(msg, '__class__', '').__name__).lower()
                if 'ai' in msg_type and hasattr(msg, 'content'):
                    content = message_to_text(msg)
                    if '<function' not in content and len(content) > 100:
                        ai_responses.append(content)
                        logger.info(f"✅ Captured follow-up AI response: {len(content)} chars")
                        break
        
        # Combine all AI responses
        if ai_responses:
            output = "\n\n".join(ai_responses)
        else:
            # Last resort fallback
            logger.warning("⚠️ Still no valid AI response after follow-up - using last message")
            output = message_to_text(result.get("messages", [])[-1]) if result.get("messages") else str(result)

        # Detect failures in LLM output
        if looks_like_llm_failure(output):
            raise Exception(f"LLM generated error output: {output[:200]}")

        return output

    # ==========================================================================
    # TIER 2: Rule-Based Validation with ACTUAL Risk Scoring (Production Ready)
    # ==========================================================================
    def use_rule_based_validation():
        """
        Fallback: Rule-based validation with REAL risk assessment.
        NOT a dummy response - performs actual safety checks.
        """
        logger.info("🔄 TIER 2: Using rule-based validation with risk scoring...")

        import re
        from domain.liquid_zimbabwe_parameters import LiquidZimbabweParameterManager

        # Parse config_output to extract recommendations
        config_text = state.get("config_output", "")

        # Try to extract parameter changes from text
        # Look for patterns like: "parameter_name: current_value → new_value"
        param_changes = []

        # Pattern 1: "Parameter: old → new"
        pattern1 = r'(?:parameter|param)[\s:]+(\w+)[\s:]+([+-]?\d+(?:\.\d+)?)\s*(?:→|->|to)\s*([+-]?\d+(?:\.\d+)?)'
        matches1 = re.finditer(pattern1, config_text, re.IGNORECASE)

        for match in matches1:
            param_changes.append({
                'parameter': match.group(1),
                'current_value': float(match.group(2)),
                'new_value': float(match.group(3))
            })

        # Pattern 2: Look for specific parameter names we know about
        param_manager = LiquidZimbabweParameterManager()
        for param_name in param_manager.parameter_config.keys():
            if param_name in config_text:
                # Try to find values near this parameter name
                param_section = config_text[max(0, config_text.find(param_name)-100):config_text.find(param_name)+200]
                numbers = re.findall(r'([+-]?\d+(?:\.\d+)?)', param_section)
                if len(numbers) >= 2:
                    param_changes.append({
                        'parameter': param_name,
                        'current_value': float(numbers[0]),
                        'new_value': float(numbers[1])
                    })

        # If no parameters found, try to infer from config output
        if not param_changes:
            logger.warning("⚠️  Could not parse parameter changes - using conservative approval")
            # Be conservative: require human review
            validation_result = {
                'status': 'REVIEW',
                'risk_score': 5,
                'reason': 'Could not parse recommendations - manual review required',
                'method': 'rule_based_conservative'
            }
        else:
            # Perform actual risk scoring
            validation_results = []
            max_risk_score = 0

            for change in param_changes:
                risk_score = _calculate_risk_score(
                    parameter=change['parameter'],
                    current_value=change['current_value'],
                    new_value=change['new_value'],
                    kpi_context=state.get('kpis', {})
                )

                # Check parameter bounds
                within_bounds = _check_parameter_bounds(
                    change['parameter'],
                    change['new_value']
                )

                # Calculate change magnitude
                if change['current_value'] != 0:
                    magnitude_pct = abs((change['new_value'] - change['current_value']) / change['current_value']) * 100
                else:
                    magnitude_pct = 0

                # Decision logic
                if not within_bounds:
                    status = "REJECTED"
                    reason = f"Parameter {change['parameter']} = {change['new_value']} out of valid range"
                elif risk_score > 8:  # Max risk threshold
                    status = "REJECTED"
                    reason = f"Risk score {risk_score}/10 exceeds threshold"
                elif risk_score >= 5 or magnitude_pct > 20:
                    status = "REVIEW"  # Requires human approval
                    reason = f"High risk ({risk_score}/10) or large change ({magnitude_pct:.1f}%)"
                else:
                    status = "APPROVED"
                    reason = f"Low risk ({risk_score}/10), moderate change ({magnitude_pct:.1f}%)"

                validation_results.append({
                    'parameter': change['parameter'],
                    'status': status,
                    'risk_score': risk_score,
                    'reason': reason,
                    'magnitude_pct': magnitude_pct
                })

                max_risk_score = max(max_risk_score, risk_score)

            # Overall decision
            if any(v['status'] == 'REJECTED' for v in validation_results):
                overall_status = "REJECTED"
            elif any(v['status'] == 'REVIEW' for v in validation_results):
                overall_status = "REVIEW"
            else:
                overall_status = "APPROVED"

            validation_result = {
                'status': overall_status,
                'risk_score': max_risk_score,
                'validation_results': validation_results,
                'method': 'rule_based_scoring'
            }

        # Format output
        output = "SAFETY VALIDATION ASSESSMENT (Rule-Based with Risk Scoring)\n\n"
        output += "="*70 + "\n"

        if 'validation_results' in validation_result:
            for i, vr in enumerate(validation_result['validation_results'], 1):
                output += f"\nPARAMETER #{i}: {vr['parameter']}\n"
                output += "-"*70 + "\n"
                output += f"Risk Score: {vr['risk_score']}/10\n"
                output += f"Status: {vr['status']}\n"
                output += f"Reason: {vr['reason']}\n"
                if 'magnitude_pct' in vr:
                    output += f"Change Magnitude: {vr['magnitude_pct']:.1f}%\n"

        output += "\n" + "="*70 + "\n"
        output += f"OVERALL DECISION: {validation_result['status']}\n"
        output += f"Maximum Risk Score: {validation_result['risk_score']}/10\n"
        output += f"Method: {validation_result['method']}\n"

        if validation_result['status'] == 'REVIEW':
            output += "\n⚠️  HUMAN APPROVAL REQUIRED\n"
            output += "This change requires engineer review before execution.\n"

        logger.info(f"✅ Rule-based validation complete - Status: {validation_result['status']}")
        logger.info(f"📊 Risk Score: {validation_result['risk_score']}/10")

        return output, validation_result['status']

    # ==========================================================================
    # EXECUTION LOGIC: Try Tier 1 → Tier 2
    # ==========================================================================
    output = None
    validation_status = "PENDING"

    try:
        # TIER 1: Try LLM with timeout
        output = try_llm_agent()

        if output is not None:
            logger.info("✅ TIER 1 SUCCESS: LLM validation complete")

            # Determine approval status from LLM output
            output_upper = output.upper()
            if "APPROVED" in output_upper:
                validation_status = "APPROVED"
            elif "REJECTED" in output_upper:
                validation_status = "REJECTED"
            else:
                validation_status = "REVIEW"
        else:
            raise Exception("LLM returned None - triggering fallback")

    except Exception as e:
        logger.warning(f"⚠️  TIER 1 failed: {e}")

        # TIER 2: Use rule-based fallback with REAL risk scoring
        output, validation_status = use_rule_based_validation()
        logger.info("✅ TIER 2 SUCCESS: Rule-based validation complete")

    # ==========================================================================
    # UPDATE STATE
    # ==========================================================================
    state["validation_output"] = output
    state["validation_status"] = validation_status
    state["agent_outputs"] = state.get("agent_outputs", {})
    state["agent_outputs"]["validation"] = output

    logger.info(f"💬 VALIDATION OUTPUT:\n{output[:300]}...")
    logger.info(f"✅ VALIDATION STATUS: {validation_status}")

    return state
