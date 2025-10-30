"""
Liquid Zimbabwe 4G Network Optimizer - Monitoring Agent
Purpose: Monitor KPIs and detect issues requiring optimization
Created: 2025-10-30
"""

from typing import Dict, Any
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.sql_tools import execute_lz_kpi_sql
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
    site_name = state.get("site_name", "Unknown")

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

    prompt = PromptTemplate.from_template(MONITORING_AGENT_PROMPT)
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)

    try:
        result = agent_executor.invoke({"task": task})
        state["monitoring_output"] = result.get("output", "")
        state["agent_outputs"]["monitoring"] = result.get("output", "")

        # Determine if optimization needed
        output = result.get("output", "").upper()
        state["needs_optimization"] = "OPTIMIZE" in output or "CRITICAL" in output or "POOR" in output

    except Exception as e:
        state["monitoring_output"] = f"ERROR: {str(e)}"
        state["needs_optimization"] = False

    return state
