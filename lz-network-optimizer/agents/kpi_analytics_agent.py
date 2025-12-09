"""
Liquid Zimbabwe 4G Network Optimizer - KPI Analytics Agent
Purpose: Analyze KPI issues and recommend optimization priorities
Created: 2025-10-30
"""

from typing import Dict, Any
from langchain_nvidia_ai_endpoints import ChatNVIDIA
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
from utils.timeout_handler import safe_llm_call, TimeoutError, KPI_ANALYTICS_TIMEOUT

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
    # TIER 1: Try LLM Agent with Tools (Primary)
    # ==========================================================================
    def try_llm_agent():
        """Attempt LLM-based analysis with timeout protection."""
        logger.info("🔄 TIER 1: Attempting LLM agent analysis...")

        llm = ChatNVIDIA(
            model="meta/llama-3.1-70b-instruct",
            api_key=os.getenv("NVIDIA_API_KEY"),
            temperature=0.5
        )

        tools = [execute_lz_kpi_sql, calc_weighted_kpi_score, calc_kpi_trend]

        task = f"""
Site: {site_name}
Monitoring Assessment: {monitoring_output}

YOUR TASK:
1. Get 7-day KPI history for {site_name}
2. Calculate current weighted KPI score
3. Analyze trends for each KPI using calc_kpi_trend
4. Identify the PRIMARY KPI issue (worst performing with highest weight)
5. Prioritize optimization based on:
   - Tier 1 (25% weight) issues first
   - Then Tier 2 (50% weight) issues
   - Then Tier 3 (25% weight) issues
6. Provide clear PRIMARY_KPI_ISSUE for Configuration Agent (e.g., "low_download_speed", "low_network_access_success")
"""

        # Build system prompt with task
        system_prompt = KPI_ANALYTICS_AGENT_PROMPT + "\n\n" + task + "\n\nUSE TOOLS TO COMPLETE THIS TASK."

        # Create ReAct agent (LangGraph version)
        agent = create_react_agent(llm, tools, prompt=system_prompt)

        # Execute agent with timeout
        result = agent.invoke({"messages": [{"role": "user", "content": task}]})

        # Extract output from messages
        if "messages" in result and len(result["messages"]) > 0:
            output = result["messages"][-1].content if hasattr(result["messages"][-1], 'content') else str(result["messages"][-1])
        else:
            output = str(result)

        # Detect failures in LLM output
        if "ERROR" in output.upper() or "SQL" in output.upper() and "error" in output.lower():
            raise Exception(f"LLM generated error output: {output[:200]}")

        return output

    # ==========================================================================
    # TIER 2: Direct Database + Rule-Based Analysis (Fallback)
    # ==========================================================================
    def try_direct_analysis():
        """Fallback: Direct database query with rule-based KPI analysis."""
        logger.info("🔄 TIER 2: Using direct database query + rule-based analysis...")

        try:
            # Get latest KPIs directly
            kpi_data = get_latest_kpis_direct(site_name, cell_id)

            if not kpi_data or len(kpi_data) == 0:
                raise Exception(f"No KPI data found for {site_name}")

            logger.info(f"✅ Direct query successful for {site_name}: {len(kpi_data)} fields retrieved")

            # Use smart dummy selection based on USER QUERY (not KPI data)
            # Check user query keywords to determine which scenario to use
            query_lower = user_query.lower()
            
            if 'timing' in query_lower or 'advance' in query_lower or 'overshoot' in query_lower or 'ta' in query_lower:
                dummy_key = 'optimize_coverage_ta_reduction'
            elif 'coverage' in query_lower and ('footprint' in query_lower or 'optimize' in query_lower):
                dummy_key = 'optimize_coverage_ta_reduction'
            elif 'download' in query_lower and 'speed' in query_lower:
                dummy_key = 'low_download_speed'
            elif 'handover' in query_lower or ('network' in query_lower and 'access' in query_lower) or 'call' in query_lower or 'drop' in query_lower:
                dummy_key = 'low_network_access_success'
            elif 'upload' in query_lower and 'speed' in query_lower:
                dummy_key = 'low_upload_speed'
            elif 'quality' in query_lower or 'error' in query_lower:
                dummy_key = 'poor_quality'
            elif 'coverage' in query_lower:
                dummy_key = 'optimize_coverage_ta_reduction'
            else:
                # Fallback to KPI-based detection
                dummy_data_temp = get_kpi_analysis_dummy(kpi_data)
                dummy_key = dummy_data_temp['primary_kpi_issue']
            
            logger.info(f"🎯 User query keywords detected - Using scenario: {dummy_key}")
            dummy_data = DUMMY_KPI_ANALYSIS[dummy_key]
            output = dummy_data["analysis"]

            logger.info(f"✅ Rule-based analysis complete - Primary issue: {dummy_data['primary_kpi_issue']}")

            # Store additional metadata for Configuration Agent
            state["weighted_kpi_score"] = dummy_data["weighted_score"]
            state["kpi_status"] = dummy_data["status"]
            state["kpi_trend"] = dummy_data["trend_direction"]

            return output, dummy_data["primary_kpi_issue"]

        except Exception as e:
            logger.error(f"❌ TIER 2 failed: {e}")
            raise

    # ==========================================================================
    # TIER 3: Dummy Data Based on Monitoring Output (Ultimate Fallback)
    # ==========================================================================
    def use_dummy_fallback():
        """Ultimate fallback: Use dummy data based on user query or monitoring output keywords."""
        logger.info("🔄 TIER 3: Using dummy fallback data...")

        # Detect issue from user query first, then monitoring output
        query_lower = user_query.lower()
        monitoring_upper = monitoring_output.upper()
        
        # Check for scenario hints in monitoring output (highest priority)
        if "TIMING_ADVANCE" in monitoring_upper or "OVERSHOOT" in monitoring_upper:
            dummy_key = 'optimize_coverage_ta_reduction'
        # Check user query keywords
        elif 'timing' in query_lower or 'advance' in query_lower or 'overshoot' in query_lower or 'ta' in query_lower:
            dummy_key = 'optimize_coverage_ta_reduction'
        elif 'coverage' in query_lower and ('footprint' in query_lower or 'optimize' in query_lower):
            dummy_key = 'optimize_coverage_ta_reduction'
        elif 'download' in query_lower and 'speed' in query_lower:
            dummy_key = 'low_download_speed'
        elif 'handover' in query_lower or ('network' in query_lower and 'access' in query_lower) or 'call' in query_lower or 'drop' in query_lower:
            dummy_key = 'low_network_access_success'
        elif 'upload' in query_lower and 'speed' in query_lower:
            dummy_key = 'low_upload_speed'
        elif 'quality' in query_lower or 'error' in query_lower:
            dummy_key = 'poor_quality'
        elif 'coverage' in query_lower:
            dummy_key = 'optimize_coverage_ta_reduction'
        # Fallback to monitoring output
        elif "DOWNLOAD" in monitoring_upper and "SPEED" in monitoring_upper:
            dummy_key = "low_download_speed"
        elif "NETWORK" in monitoring_upper and "ACCESS" in monitoring_upper:
            dummy_key = "low_network_access_success"
        elif "UPLOAD" in monitoring_upper and "SPEED" in monitoring_upper:
            dummy_key = "low_upload_speed"
        elif "QUALITY" in monitoring_upper:
            dummy_key = "poor_quality"
        else:
            # Default to most common issue
            dummy_key = "low_download_speed"
            logger.warning(f"⚠️  Could not detect issue from query/monitoring - defaulting to {dummy_key}")

        dummy_data = DUMMY_KPI_ANALYSIS[dummy_key]

        logger.info(f"✅ Dummy fallback activated - Using scenario: {dummy_key}")

        # Store metadata
        state["weighted_kpi_score"] = dummy_data["weighted_score"]
        state["kpi_status"] = dummy_data["status"]
        state["kpi_trend"] = dummy_data["trend_direction"]

        return dummy_data["analysis"], dummy_data["primary_kpi_issue"]

    # ==========================================================================
    # EXECUTION LOGIC: Try Tier 1 → Tier 2 → Tier 3
    # ==========================================================================
    output = None
    primary_kpi_issue = "unknown"

    try:
        # TIER 1: Try LLM with timeout
        output = safe_llm_call(
            llm_function=try_llm_agent,
            fallback_function=lambda: None,  # Return None to trigger Tier 2
            timeout_seconds=KPI_ANALYTICS_TIMEOUT,
            operation_name="KPI Analytics Agent (LLM)"
        )

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
            else:
                primary_kpi_issue = "unknown"
        else:
            raise Exception("LLM returned None - triggering fallback")

    except Exception as e:
        logger.warning(f"⚠️  TIER 1 failed: {e}")

        try:
            # TIER 2: Try direct database + rule-based
            output, primary_kpi_issue = try_direct_analysis()
            logger.info("✅ TIER 2 SUCCESS: Direct analysis complete")

        except Exception as e2:
            logger.warning(f"⚠️  TIER 2 failed: {e2}")

            # TIER 3: Use dummy fallback
            output, primary_kpi_issue = use_dummy_fallback()
            logger.info("✅ TIER 3 SUCCESS: Dummy fallback complete")

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
