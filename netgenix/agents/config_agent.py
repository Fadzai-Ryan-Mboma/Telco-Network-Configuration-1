"""
Liquid Zimbabwe 4G Network Optimizer - Configuration Agent
Purpose: Recommend parameter changes using few-shot learning
Created: 2025-10-30
"""

from typing import Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.huawei_tools import query_huawei_parameter, validate_parameter_range
from tools.sql_tools import execute_historical_sql
from backend.netgenix.services.database import get_site_parameters, check_api_status
from tools.dummy_responses import get_config_recommendation_dummy, DUMMY_CONFIG_RECOMMENDATIONS
from prompts.system_prompts import CONFIGURATION_AGENT_PROMPT
from prompts.few_shot_examples import format_few_shot_examples
from utils.timeout_handler import TimeoutHandler, TimeoutError as LLMTimeoutError, CONFIG_TIMEOUT
from utils.llm_factory import get_llm_client, message_to_text

logger = logging.getLogger(__name__)


def config_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Configuration Agent - Recommends parameter changes using few-shot learning.

    2-TIER FALLBACK MECHANISM:
    Tier 1: LLM agent with Huawei API tools (with 45s timeout)
    Tier 2: Rule-based recommendations from dummy data (always succeeds)
    """
    logger.info(f"🤖 CONFIGURATION AGENT - Starting parameter recommendation")

    # Extract parameters
    site_name = state.get("site_name", "Unknown")
    primary_kpi_issue = state.get("primary_kpi_issue", "unknown")
    kpi_analytics_output = state.get('kpi_analytics_output', '')

    logger.info(f"📝 Task: Recommendations for {site_name}, Issue: {primary_kpi_issue}")

    # ==========================================================================
    # TIER 1: Try LLM Agent with Pre-fetched Data (Primary - No Tool Calls)
    # ==========================================================================
    def try_llm_agent():
        """
        Attempt LLM-based configuration recommendations with pre-fetched data.
        WORKAROUND: Pre-fetch current parameters to avoid NVIDIA tool calling issues.
        """
        logger.info("🔄 TIER 1: Attempting LLM agent configuration with pre-fetched data...")

        # PRE-FETCH DATA: Get current parameter values
        # First check if Huawei API is reachable - if not, use database values
        api_status = check_api_status(site_name)
        use_live_api = "Connected" in api_status.get("api", "")

        if use_live_api:
            logger.info("📊 Pre-fetching current parameter values from Huawei API...")
        else:
            logger.info("📊 Huawei API unavailable - using database parameter values...")

        from domain.liquid_zimbabwe_parameters import LiquidZimbabweParameterManager
        param_manager = LiquidZimbabweParameterManager()

        current_params = {}

        if use_live_api:
            # Try live API
            try:
                for param_name in param_manager.parameter_config.keys():
                    try:
                        result = query_huawei_parameter.invoke({
                            "site_name": site_name,
                            "parameter_name": param_name,
                            "cell_id": state.get("cell_id", 1)
                        })
                        current_params[param_name] = result
                        logger.info(f"  ✅ {param_name}: {result}")
                    except Exception as e:
                        logger.warning(f"  ⚠️  Failed to query {param_name}: {e}")
                        current_params[param_name] = "Query failed"
                logger.info("✅ Pre-fetched current parameters from API")
            except Exception as e:
                logger.warning(f"⚠️  Failed to pre-fetch from API: {e}")
                use_live_api = False

        if not use_live_api:
            # Use database values
            try:
                db_params = get_site_parameters(site_name)
                if db_params:
                    current_params = {
                        "reference_signal_power_pdschcfg": db_params.get("reference_signal_power_pdschcfg", "N/A"),
                        "a3_event_offset": db_params.get("a3_event_offset", "N/A"),
                        "t310_timer": db_params.get("t310_timer", "N/A"),
                        "p0_nominal_pusch": db_params.get("p0_nominal_pusch", "N/A"),
                        "pdcch_aggregation_level": db_params.get("pdcch_aggregation_level", "N/A"),
                    }
                    logger.info("✅ Pre-fetched current parameters from database")
                else:
                    current_params = {"error": "No parameters found in database"}
            except Exception as e:
                logger.warning(f"⚠️  Failed to get database parameters: {e}")
                current_params = {"error": "Failed to query parameters"}

        # Format current parameters for LLM
        current_params_text = "CURRENT PARAMETER VALUES:\n"
        for param_name, value in current_params.items():
            current_params_text += f"  - {param_name}: {value}\n"

        # Use LLM factory to get client (supports OpenAI, NVIDIA, etc.)
        llm = get_llm_client()

        # Get relevant few-shot examples
        few_shot_examples = format_few_shot_examples(primary_kpi_issue, top_n=2)

        # NO TOOLS - Direct prompting with pre-fetched data
        task = f"""
Generate parameter recommendations for site: {site_name}
Primary KPI Issue: {primary_kpi_issue}
KPI Analytics: {kpi_analytics_output}

{current_params_text}

FEW-SHOT EXAMPLES (similar cases):
{few_shot_examples}

YOUR TASK:
1. Review the current parameter values provided above
2. Review the few-shot examples for similar KPI issues
3. Match the KPI issue to optimization rules:
   - Low network access → Increase reference signal power
   - Low download speed → Increase reference signal power
   - Low upload speed → Increase P0 nominal PUSCH
   - High handover failures → Adjust A3 offset
   - Radio link failures → Increase T310 timer
4. Recommend specific parameter changes with exact values
5. Calculate expected KPI improvements

CRITICAL: Provide complete detailed recommendations following the FINAL ANSWER FORMAT. Include:
- ISSUE IDENTIFIED with context
- PRIMARY PARAMETER with exact current/recommended values (e.g., 150 → 160 for power, MS1000_T310 → MS2000_T310 for timer)
- Exact change with unit (+10 units = +1.0 dBm, +1000 ms)
- Detailed reasoning with projections (current% → target%)
- Expected KPI improvements with specific numbers
- Risk assessment with scores
- Technical effects

Write your complete detailed recommendations NOW:
"""

        # Build system prompt with task
        system_prompt = CONFIGURATION_AGENT_PROMPT + "\n\n" + task

        # Direct LLM call (no ReAct agent, no tool calling)
        from langchain_core.messages import HumanMessage, SystemMessage

        # Execute LLM with timeout protection (90s for recommendation generation - NVIDIA API can be slow)
        timeout_handler = TimeoutHandler(timeout_seconds=90)

        try:
            with timeout_handler.timeout_context("Configuration Agent LLM call"):
                # Direct invoke - no tool calling needed
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=task)
                ]
                result = llm.invoke(messages)

        except LLMTimeoutError as timeout_error:
            logger.error(f"❌ CONFIGURATION AGENT TIMEOUT: {timeout_error}")
            logger.error(f"⚠️  The LLM took longer than 90 seconds to respond")
            logger.error(f"⚠️  NVIDIA API is very slow - consider switching to Nemotron-4 340B or GPT-4o")
            raise Exception(f"LLM timeout - fallback will be attempted")

        # Extract output directly from LLM response (no agent wrapping)
        output = message_to_text(result)

        logger.info(f"✅ LLM response received: {len(output)} chars")
        logger.info(f"🔍 Response preview: {output[:300]}...")

        # Validate output quality
        if not output or len(output) < 100:
            logger.warning(f"⚠️  LLM response too short: {len(output)} chars")
            raise Exception(f"LLM output too short - falling back to Tier 2")

        # Check for critical LLM errors (not parameter fetch errors which are expected when Huawei API is down)
        # Only flag as error if the LLM itself failed to generate recommendations
        llm_error_indicators = [
            "I CANNOT GENERATE",
            "I'M UNABLE TO",
            "UNABLE TO PROCESS",
            "CANNOT PROVIDE RECOMMENDATIONS",
            "NO RECOMMENDATIONS POSSIBLE"
        ]
        if any(indicator in output.upper() for indicator in llm_error_indicators):
            logger.warning(f"⚠️  LLM could not generate recommendations")
            raise Exception(f"LLM could not generate recommendations: {output[:200]}")

        # Validate that we got actual recommendations (not just echoing)
        has_detailed_sections = (
            'PARAMETER' in output.upper() or
            'RECOMMENDED' in output.upper() or
            'ISSUE' in output.upper() or
            'CHANGE' in output.upper()
        )

        if not has_detailed_sections:
            logger.warning(f"⚠️  LLM output incomplete (no detailed recommendation sections)")
            raise Exception(f"LLM output incomplete - falling back to Tier 2")

        return output

    # ==========================================================================
    # TIER 2: Rule-Based Recommendations (Fallback - Always Succeeds)
    # ==========================================================================
    def use_rule_based_config():
        """
        Fallback: DISABLED - No dummy data fallback.
        Raises explicit error if LLM fails - forces transparency.
        """
        logger.error("❌ CONFIGURATION AGENT LLM FAILED")
        logger.error("❌ Dummy fallbacks are DISABLED in production mode")
        logger.error("❌ Cannot generate recommendations without LLM")

        raise Exception(
            "Configuration Agent LLM failed. "
            "Dummy fallbacks are disabled. "
            "Check NVIDIA API connectivity and LLM configuration. "
            f"Site: {site_name}, Issue: {primary_kpi_issue}"
        )

    # ==========================================================================
    # EXECUTION LOGIC: Try Tier 1 → Tier 2
    # ==========================================================================
    output = None

    try:
        # TIER 1: Try LLM with timeout
        output = try_llm_agent()

        if output is not None:
            logger.info("✅ TIER 1 SUCCESS: LLM configuration recommendations complete")
        else:
            raise Exception("LLM returned None - triggering fallback")

    except Exception as e:
        logger.warning(f"⚠️  TIER 1 failed: {e}")
        logger.warning("⚠️  WARNING: Falling back to DUMMY recommendations!")
        logger.warning("⚠️  Dummy values (e.g., 152 for power) may not match actual network!")

        # TIER 2: Use rule-based fallback
        output = use_rule_based_config()
        logger.info("✅ TIER 2 SUCCESS: Rule-based configuration complete")

    # ==========================================================================
    # UPDATE STATE
    # ==========================================================================
    state["config_output"] = output
    state["agent_outputs"] = state.get("agent_outputs", {})
    state["agent_outputs"]["configuration"] = output

    logger.info(f"💬 CONFIGURATION OUTPUT:\n{output[:300]}...")

    return state
