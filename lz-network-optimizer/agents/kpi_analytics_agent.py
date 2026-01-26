"""
Liquid Zimbabwe 4G Network Optimizer - KPI Analytics Agent
Purpose: Analyze KPI issues and recommend optimization priorities
Created: 2025-10-30
"""

from typing import Dict, Any
from utils.llm_factory import get_llm_client
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.sql_tools import execute_lz_kpi_sql, get_latest_kpis_direct
from tools.calculation_tools import calc_weighted_kpi_score, calc_kpi_trend
from tools.dummy_responses import get_kpi_analysis_dummy, DUMMY_KPI_ANALYSIS
from prompts.system_prompts import KPI_ANALYTICS_AGENT_PROMPT
from utils.timeout_handler import TimeoutHandler, TimeoutError as LLMTimeoutError, KPI_ANALYTICS_TIMEOUT

logger = logging.getLogger(__name__)


def kpi_analytics_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    KPI Analytics Agent - Analyzes KPI issues and determines priorities.

    3-TIER FALLBACK MECHANISM:
    Tier 1: LLM agent with SQL/calculation tools (with 45s timeout)
    Tier 2: Direct database query + rule-based analysis
    Tier 3: Dummy data based on monitoring output
    """
    logger.info(f"🤖 KPI ANALYTICS AGENT - Starting analysis")

    # Extract site_name and cell_id (handle malformed state)
    site_name_val = state.get("site_name", "Unknown")
    if isinstance(site_name_val, dict):
        site_name = site_name_val.get("site_name", "Unknown")
        cell_id = site_name_val.get("cell_id", 1)
        logger.warning(f"⚠️  Detected malformed state in KPI Analytics - extracting from dict")
    else:
        site_name = site_name_val
        cell_id = state.get("cell_id", 1)

    monitoring_output = state.get('monitoring_output', '')
    user_query = state.get('user_query', '')

    logger.info(f"📝 Task: Analysis for {site_name}, Cell {cell_id}")
    logger.info(f"📝 User Query: {user_query}")

    # ==========================================================================
    # TIER 1: Try LLM Agent with Pre-fetched Data (Primary - No Tool Calls)
    # ==========================================================================
    def try_llm_agent():
        """
        Attempt LLM-based analysis with pre-fetched data.
        WORKAROUND: Pre-fetch data to avoid NVIDIA tool calling issues.
        """
        logger.info("🔄 TIER 1: Attempting LLM agent analysis with pre-fetched data...")

        # PRE-FETCH DATA: Get KPI data directly (bypass tool calling issues)
        logger.info("📊 Pre-fetching KPI data from database...")

        try:
            # Fetch last 7 days of KPI data
            kpi_data = execute_lz_kpi_sql.invoke({
                "sql_query": f"SELECT * FROM kpi_data WHERE site_name='{site_name}' ORDER BY timestamp DESC LIMIT 7"
            })

            # Calculate weighted score from latest KPI
            latest_kpi_query = f"SELECT * FROM kpi_data WHERE site_name='{site_name}' ORDER BY timestamp DESC LIMIT 1"
            latest_kpi_data = execute_lz_kpi_sql.invoke({"sql_query": latest_kpi_query})

            # Calculate trends for key KPIs
            trend_analysis = "KPI Trend Analysis (7-day):\n"
            for kpi in ['network_access_success', 'download_speed', 'upload_speed', 'download_quality', 'upload_quality']:
                trend_query = f"SELECT AVG({kpi}) as avg FROM kpi_data WHERE site_name='{site_name}' AND timestamp >= date('now', '-7 days')"
                trend_result = execute_lz_kpi_sql.invoke({"sql_query": trend_query})
                trend_analysis += f"  - {kpi}: {trend_result}\n"

            logger.info("✅ Pre-fetched KPI data successfully")

        except Exception as e:
            logger.warning(f"⚠️  Failed to pre-fetch KPI data: {e}")
            kpi_data = "No historical KPI data available"
            latest_kpi_data = "No current KPI data available"
            trend_analysis = "Trend analysis unavailable"

        # Initialize LLM using factory (supports OpenAI, NVIDIA, etc.)
        llm = get_llm_client(temperature=0.5)

        # NO TOOLS - Direct prompting with pre-fetched data
        task = f"""
Analyze KPI data for site: {site_name}
Monitoring Assessment: {monitoring_output}

PRE-FETCHED KPI DATA (Last 7 Days):
{kpi_data}

LATEST KPI SNAPSHOT:
{latest_kpi_data}

TREND ANALYSIS:
{trend_analysis}

YOUR TASK:
1. Analyze the KPI data provided above
2. Calculate weighted KPI score (Foundation 25%, Revenue/Experience 50%, Efficiency 25%)
3. Identify PRIMARY KPI issue (worst performing with highest weight)
4. Analyze trends for degradation patterns
5. Provide root cause hypothesis

CRITICAL: Provide a complete detailed analysis following the FINAL ANSWER FORMAT in the system prompt. Include:
- WEIGHTED KPI SCORE with status (EXCELLENT/GOOD/FAIR/POOR/CRITICAL)
- Tier-by-tier breakdown with percentages
- PRIMARY ISSUE with specific metrics (Current: X, Target: Y, Gap: Z%)
- SECONDARY ISSUES list with details
- ROOT CAUSE HYPOTHESIS with technical analysis
- Specific metrics with values and trends

Write your complete detailed KPI analysis NOW:
"""

        # Build system prompt with task
        system_prompt = KPI_ANALYTICS_AGENT_PROMPT + "\n\n" + task

        # Direct LLM call (no ReAct agent, no tool calling)
        from langchain_core.messages import HumanMessage, SystemMessage

        # Execute LLM with timeout protection (90s for complex analysis - NVIDIA API can be slow)
        timeout_handler = TimeoutHandler(timeout_seconds=90)

        try:
            with timeout_handler.timeout_context("KPI Analytics Agent LLM call"):
                # Direct invoke - no tool calling needed
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=task)
                ]
                result = llm.invoke(messages)

        except LLMTimeoutError as timeout_error:
            logger.error(f"❌ KPI ANALYTICS TIMEOUT: {timeout_error}")
            logger.error(f"⚠️  The LLM took longer than 90 seconds to respond")
            logger.error(f"⚠️  NVIDIA API is very slow - consider switching to Nemotron-4 340B or GPT-4o")
            raise Exception(f"LLM timeout - fallback will be attempted")

        # Extract output directly from LLM response (no agent wrapping)
        output = result.content if hasattr(result, 'content') else str(result)

        logger.info(f"✅ LLM response received: {len(output)} chars")
        logger.info(f"🔍 Response preview: {output[:300]}...")

        # Validate output quality
        if not output or len(output) < 100:
            logger.warning(f"⚠️  LLM response too short: {len(output)} chars")
            raise Exception(f"LLM output too short - falling back to Tier 2")

        # Check for error messages in output
        if "ERROR" in output.upper() and "error" in output.lower():
            logger.warning(f"⚠️  LLM generated error output")
            raise Exception(f"LLM generated error output: {output[:200]}")

        # Validate that we got actual analysis (not just echoing or incomplete)
        has_detailed_analysis = (
            'WEIGHTED KPI SCORE' in output.upper() or
            'PRIMARY' in output.upper() or
            'TIER' in output.upper() or
            'KPI ISSUE' in output.upper()
        )

        if not has_detailed_analysis:
            logger.warning(f"⚠️  LLM output incomplete (no detailed analysis sections)")
            raise Exception(f"LLM output incomplete - falling back to Tier 2")

        return output

    # ==========================================================================
    # TIER 2: Direct Database + Rule-Based Analysis (Fallback)
    # ==========================================================================
    def try_direct_analysis():
        """
        Fallback: DISABLED - No dummy data fallback.
        Raises explicit error if LLM fails - forces transparency.
        """
        logger.error("❌ KPI ANALYTICS AGENT LLM FAILED")
        logger.error("❌ Dummy fallbacks are DISABLED in production mode")
        logger.error("❌ Cannot analyze KPIs without LLM")

        raise Exception(
            "KPI Analytics Agent LLM failed. "
            "Dummy fallbacks are disabled. "
            "Check NVIDIA API connectivity and LLM configuration. "
            f"Site: {site_name}, Query: {user_query}"
        )

    # ==========================================================================
    # TIER 3: DISABLED - No Dummy Fallbacks
    # ==========================================================================
    def use_dummy_fallback():
        """
        TIER 3 Fallback: DISABLED - No dummy data fallback.
        Raises explicit error - forces transparency.
        """
        logger.error("❌ KPI ANALYTICS AGENT TIER 2 ALSO FAILED")
        logger.error("❌ All fallbacks are DISABLED in production mode")
        logger.error("❌ Workflow cannot continue without LLM")

        raise Exception(
            "KPI Analytics Agent failed completely (both Tier 1 and Tier 2). "
            "Dummy fallbacks are disabled. "
            "Check NVIDIA API connectivity and LLM configuration. "
            f"Site: {site_name}, Query: {user_query}"
        )

    # ==========================================================================
    # EXECUTION LOGIC: Try Tier 1 → Tier 2 (TIER 2 & 3 DISABLED)
    # ==========================================================================
    output = None
    primary_kpi_issue = "unknown"

    try:
        # TIER 1: Try LLM with timeout (ONLY TIER - NO FALLBACKS)
        output = try_llm_agent()

        if output is not None:
            logger.info("✅ TIER 1 SUCCESS: LLM analysis complete")

            # Extract primary KPI issue from LLM output
            output_lower = output.lower()
            if "download_speed" in output_lower and "low" in output_lower:
                primary_kpi_issue = "low_download_speed"
            elif "network_access" in output_lower and "low" in output_lower:
                primary_kpi_issue = "low_network_access_success"
            elif "upload_speed" in output_lower and "low" in output_lower:
                primary_kpi_issue = "low_upload_speed"
            elif "timing" in output_lower and "advance" in output_lower:
                primary_kpi_issue = "excessive_timing_advance_overshoot"
            elif "overshoot" in output_lower:
                primary_kpi_issue = "excessive_timing_advance_overshoot"
            else:
                primary_kpi_issue = "unknown"
        else:
            raise Exception("LLM returned None - workflow cannot continue (fallbacks disabled)")

    except Exception as e:
        logger.error(f"❌ KPI ANALYTICS AGENT FAILED: {e}")
        logger.error(f"❌ Dummy fallbacks are DISABLED - workflow will abort")
        logger.error(f"❌ Check NVIDIA API connectivity and LLM configuration")
        # Re-raise to abort workflow
        raise

    # ==========================================================================
    # UPDATE STATE
    # ==========================================================================
    state["kpi_analytics_output"] = output
    state["primary_kpi_issue"] = primary_kpi_issue
    state["agent_outputs"] = state.get("agent_outputs", {})
    state["agent_outputs"]["kpi_analytics"] = output

    logger.info(f"💬 KPI ANALYTICS OUTPUT:\n{output[:300]}...")
    logger.info(f"🎯 PRIMARY KPI ISSUE: {primary_kpi_issue}")

    return state
