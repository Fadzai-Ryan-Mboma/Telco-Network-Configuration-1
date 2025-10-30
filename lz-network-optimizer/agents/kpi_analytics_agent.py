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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.sql_tools import execute_lz_kpi_sql
from tools.calculation_tools import calc_weighted_kpi_score, calc_kpi_trend
from prompts.system_prompts import KPI_ANALYTICS_AGENT_PROMPT


def kpi_analytics_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """KPI Analytics Agent - Analyzes KPI issues and determines priorities."""
    site_name = state.get("site_name", "Unknown")

    llm = ChatNVIDIA(
        model="meta/llama-3.1-70b-instruct",
        api_key=os.getenv("NVIDIA_API_KEY"),
        temperature=0.5
    )

    tools = [execute_lz_kpi_sql, calc_weighted_kpi_score, calc_kpi_trend]

    task = f"""
Site: {site_name}
Monitoring Assessment: {state.get('monitoring_output', '')}

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

    # Execute agent
    try:
        # LangGraph create_react_agent expects messages in state
        result = agent.invoke({"messages": [{"role": "user", "content": task}]})

        # Extract output from messages
        if "messages" in result and len(result["messages"]) > 0:
            output = result["messages"][-1].content if hasattr(result["messages"][-1], 'content') else str(result["messages"][-1])
        else:
            output = str(result)

        # Update state
        state["kpi_analytics_output"] = output
        state["agent_outputs"] = state.get("agent_outputs", {})
        state["agent_outputs"]["kpi_analytics"] = output

        # Extract primary KPI issue (simplified - would need better parsing)
        output_lower = output.lower()
        if "download_speed" in output_lower and "low" in output_lower:
            state["primary_kpi_issue"] = "low_download_speed"
        elif "network_access" in output_lower and "low" in output_lower:
            state["primary_kpi_issue"] = "low_network_access_success"
        elif "upload_speed" in output_lower and "low" in output_lower:
            state["primary_kpi_issue"] = "low_upload_speed"
        else:
            state["primary_kpi_issue"] = "unknown"

    except Exception as e:
        state["kpi_analytics_output"] = f"ERROR: {str(e)}"
        state["primary_kpi_issue"] = "error"

    return state
