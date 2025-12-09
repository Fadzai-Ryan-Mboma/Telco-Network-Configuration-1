"""
Liquid Zimbabwe 4G Network Optimizer - Monitoring Agent
Purpose: Monitor KPIs and detect issues requiring optimization
Created: 2025-10-30
"""

from typing import Dict, Any
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.sql_tools import execute_lz_kpi_sql, get_latest_kpis_direct
from tools.calculation_tools import calc_weighted_kpi_score, calc_kpi_trend
from prompts.system_prompts import MONITORING_AGENT_PROMPT


def monitoring_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Monitoring Agent - Monitors KPIs and detects optimization needs.

    Args:
        state: Workflow state with network_connector_output

    Returns:
        Updated state with monitoring assessment
    """
    # Execute agent with fallback mechanism
    import logging
    logger = logging.getLogger('LZ-Agent')

    # Extract site_name and cell_id FIRST (handle case where state might be passed incorrectly)
    site_name_val = state.get("site_name", "Unknown")
    if isinstance(site_name_val, dict):
        # If site_name is a dict, it means the whole state was passed - extract the actual site_name
        site_name = site_name_val.get("site_name", "Unknown")
        cell_id = site_name_val.get("cell_id", 1)
    else:
        site_name = site_name_val
        cell_id = state.get("cell_id", 1)

    llm = ChatNVIDIA(
        model="meta/llama-3.1-70b-instruct",
        api_key=os.getenv("NVIDIA_API_KEY"),
        temperature=0.5
    )

    tools = [execute_lz_kpi_sql, calc_weighted_kpi_score, calc_kpi_trend]

    task = f"""
Site: {site_name}
Network Data: {state.get('network_connector_output', 'No data')}

YOUR TASK:
1. Query latest KPIs for site {site_name} using execute_lz_kpi_sql
   IMPORTANT: Use complete SQL syntax with proper quotes:
   Example: SELECT * FROM kpi_data WHERE site_name='{site_name}' ORDER BY timestamp DESC LIMIT 1
   DO NOT generate incomplete SQL like "WHERE site_name=" without a value!

2. Calculate weighted KPI score using calc_weighted_kpi_score with all 7 KPIs
3. Compare KPIs against thresholds:
   - network_access_success >= 95%
   - download_speed >= 50 Mbps
   - upload_speed >= 20 Mbps
   - quality >= 95%
4. Identify any KPIs below thresholds
5. Decide: OPTIMIZE (if issues found) or CONTINUE_MONITORING (if all good)
6. If OPTIMIZE, list specific KPI issues for KPI Analytics Agent
"""

    # Build system prompt with task
    system_prompt = MONITORING_AGENT_PROMPT + "\n\n" + task + "\n\nUSE TOOLS TO COMPLETE THIS TASK."

    # Create ReAct agent (LangGraph version)
    agent = create_react_agent(llm, tools, prompt=system_prompt)

    try:
        logger.info(f"🤖 MONITORING AGENT - Starting analysis for {site_name}")
        logger.info(f"📝 Task: {task[:200]}...")

        # Try LLM agent first
        try:
            # LangGraph create_react_agent expects messages in state
            result = agent.invoke({"messages": [{"role": "user", "content": task}]})

            # Extract output from messages
            if "messages" in result and len(result["messages"]) > 0:
                output = result["messages"][-1].content if hasattr(result["messages"][-1], 'content') else str(result["messages"][-1])
            else:
                output = str(result)

            # Check if agent failed with SQL error
            if "ERROR" in output.upper() and ("SQL" in output.upper() or "INCOMPLETE" in output.upper()):
                logger.warning(f"⚠️  LLM agent encountered SQL error, using direct fallback")
                raise Exception("SQL query generation failed")

            logger.info(f"💬 MONITORING AGENT OUTPUT:\n{output}")

        except Exception as agent_error:
            logger.warning(f"⚠️  Agent execution failed: {agent_error}")
            logger.info(f"🔄 Falling back to direct database query for {site_name}")

            # FALLBACK: Use direct database query
            kpis = get_latest_kpis_direct(site_name, cell_id)

            if kpis is None:
                raise Exception(f"No KPI data found for {site_name} in database")

            # Build output from direct query results
            output = f"""KPI Analysis for {site_name} (using direct database query):

Network Access Success: {kpis.get('network_access_success', 'N/A')}%
Download Speed: {kpis.get('download_speed', 'N/A')} Mbps
Upload Speed: {kpis.get('upload_speed', 'N/A')} Mbps
Download Quality: {kpis.get('download_quality', 'N/A')}%
Upload Quality: {kpis.get('upload_quality', 'N/A')}%
Control Channel Load: {kpis.get('control_channel_load', 'N/A')}%
Feedback Channel Load: {kpis.get('feedback_channel_load', 'N/A')}%

KPI Threshold Assessment:
"""

            # Check thresholds and add assessment
            issues = []
            if kpis.get('network_access_success', 100) < 95:
                issues.append(f"- Network access success BELOW threshold: {kpis['network_access_success']}% < 95%")
            if kpis.get('download_speed', 100) < 50:
                issues.append(f"- Download speed BELOW threshold: {kpis['download_speed']} Mbps < 50 Mbps")
            if kpis.get('upload_speed', 100) < 20:
                issues.append(f"- Upload speed BELOW threshold: {kpis['upload_speed']} Mbps < 20 Mbps")
            if kpis.get('download_quality', 100) < 95:
                issues.append(f"- Download quality BELOW threshold: {kpis['download_quality']}% < 95%")
            if kpis.get('upload_quality', 100) < 95:
                issues.append(f"- Upload quality BELOW threshold: {kpis['upload_quality']}% < 95%")
            if kpis.get('control_channel_load', 0) > 80:
                issues.append(f"- Control channel load ABOVE threshold: {kpis['control_channel_load']}% > 80%")
            if kpis.get('feedback_channel_load', 0) > 80:
                issues.append(f"- Feedback channel load ABOVE threshold: {kpis['feedback_channel_load']}% > 80%")

            if issues:
                output += "\n".join(issues)
                output += "\n\nRecommendation: OPTIMIZE - Issues detected requiring attention"
            else:
                output += "All KPIs within acceptable thresholds.\n\nRecommendation: CONTINUE_MONITORING - No optimization needed"

            logger.info(f"✅ Fallback successful - analysis complete")
            logger.info(f"💬 MONITORING AGENT OUTPUT (Fallback):\n{output}")

        # DEMO FIX: Add scenario hints to monitoring output based on user query
        user_query_lower = state.get("user_query", "").lower()
        scenario_hint = ""
        
        if 'timing' in user_query_lower or 'advance' in user_query_lower or 'overshoot' in user_query_lower or 'ta' in user_query_lower:
            scenario_hint = " [TIMING_ADVANCE OVERSHOOT COVERAGE]"
        elif 'coverage' in user_query_lower and ('footprint' in user_query_lower or 'optimize' in user_query_lower):
            scenario_hint = " [TIMING_ADVANCE OVERSHOOT COVERAGE]"
        elif 'download' in user_query_lower and 'speed' in user_query_lower:
            scenario_hint = " [DOWNLOAD SPEED]"
        elif 'handover' in user_query_lower or ('network' in user_query_lower and 'access' in user_query_lower) or 'call' in user_query_lower or 'drop' in user_query_lower:
            scenario_hint = " [NETWORK ACCESS]"
        elif 'upload' in user_query_lower and 'speed' in user_query_lower:
            scenario_hint = " [UPLOAD SPEED]"
        elif 'quality' in user_query_lower or 'error' in user_query_lower:
            scenario_hint = " [QUALITY]"
        elif 'coverage' in user_query_lower:
            scenario_hint = " [TIMING_ADVANCE OVERSHOOT COVERAGE]"
        
        if scenario_hint:
            output = output + scenario_hint
            logger.info(f"🎯 Added scenario hint: {scenario_hint}")

        # Update state
        state["monitoring_output"] = output
        state["agent_outputs"] = state.get("agent_outputs", {})
        state["agent_outputs"]["monitoring"] = output

        # Determine if optimization needed - CHECK USER QUERY TOO
        output_upper = output.upper()
        user_query_upper = state.get("user_query", "").upper()

        # Trigger optimization if:
        # 1. Agent says OPTIMIZE or CRITICAL or POOR or BELOW
        # 2. User query mentions optimization/improve/fix/enhance
        # 3. User query mentions specific issues (coverage, speed, quality)
        needs_opt = (
            "OPTIMIZE" in output_upper or
            "CRITICAL" in output_upper or
            "POOR" in output_upper or
            "BELOW" in output_upper or
            "OPTIM" in user_query_upper or
            "IMPROVE" in user_query_upper or
            "FIX" in user_query_upper or
            "ENHANCE" in user_query_upper or
            "COVERAGE" in user_query_upper or
            "SPEED" in user_query_upper or
            "QUALITY" in user_query_upper
        )

        state["needs_optimization"] = needs_opt
        logger.info(f"⚖️  DECISION: needs_optimization = {needs_opt}")
        logger.info(f"   - User query: '{state.get('user_query', 'N/A')}'")
        logger.info(f"   - Keyword match in query: {'Yes' if any(kw in user_query_upper for kw in ['OPTIM', 'IMPROVE', 'FIX', 'ENHANCE', 'SPEED', 'QUALITY', 'COVERAGE']) else 'No'}")
        logger.info(f"   - Keyword match in output: {'Yes' if any(kw in output_upper for kw in ['OPTIMIZE', 'CRITICAL', 'POOR', 'BELOW']) else 'No'}")

        if needs_opt:
            logger.info(f"✅ Proceeding to KPI Analytics Agent")
        else:
            logger.info(f"⏹️  No optimization needed - workflow will end")

    except Exception as e:
        logger.error(f"❌ MONITORING AGENT FATAL ERROR: {str(e)}")
        logger.error(f"   This should not happen with fallback mechanism")

        # Even in fatal error, check user query for optimization keywords
        user_query_upper = state.get("user_query", "").upper()
        force_optimization = any(kw in user_query_upper for kw in ['OPTIM', 'IMPROVE', 'FIX', 'ENHANCE', 'SPEED', 'QUALITY', 'COVERAGE'])

        state["monitoring_output"] = f"ERROR: {str(e)}"
        state["needs_optimization"] = force_optimization  # Changed: use user intent as fallback

        if force_optimization:
            logger.warning(f"⚠️  Despite error, forcing optimization=True based on user query keywords")

    return state
