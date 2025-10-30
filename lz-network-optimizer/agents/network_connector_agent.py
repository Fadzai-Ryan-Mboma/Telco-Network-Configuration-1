"""
Liquid Zimbabwe 4G Network Optimizer - Network Connector Agent
Purpose: Establish connectivity and query network element data
Created: 2025-10-30
"""

from typing import Dict, Any
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.huawei_tools import query_huawei_parameter, query_huawei_kpi, execute_mml_command
from tools.sql_tools import execute_lz_kpi_sql
from prompts.system_prompts import NETWORK_CONNECTOR_PROMPT


def network_connector_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Network Connector Agent - Establishes connectivity and queries network data.

    Responsibilities:
    - Connect to Huawei iMaster MAE API
    - Query current parameter values
    - Query current KPI values
    - Handle API failures with fallback to database
    - Provide connectivity status

    Args:
        state: Current workflow state containing:
            - site_name: Site to query
            - cell_id: Cell ID (default: 1)
            - user_query: User's optimization request

    Returns:
        Updated state with network data
    """
    # Extract site information from state
    site_name = state.get("site_name", "Unknown")
    cell_id = state.get("cell_id", 1)
    user_query = state.get("user_query", "Query network status")

    # Initialize NVIDIA LLM
    llm = ChatNVIDIA(
        model="meta/llama-3.1-70b-instruct",
        api_key=os.getenv("NVIDIA_API_KEY"),
        temperature=0.7,
        max_tokens=2000
    )

    # Create agent tools list
    tools = [
        query_huawei_parameter,
        query_huawei_kpi,
        execute_mml_command,
        execute_lz_kpi_sql
    ]

    # Build prompt
    task = f"""
Site: {site_name}
Cell ID: {cell_id}
User Request: {user_query}

YOUR TASK:
1. Attempt to query live KPI data for site {site_name}
2. If API is available, use query_huawei_kpi
3. If API fails, fall back to execute_lz_kpi_sql to get latest historical data
4. Report data source (live or historical)
5. Provide all 7 KPI values for next agent

Retrieve these KPIs:
- network_access_success
- download_speed
- download_quality
- upload_speed
- upload_quality
- control_channel_load
- feedback_channel_load
"""

    prompt = PromptTemplate.from_template(
        NETWORK_CONNECTOR_PROMPT + "\n\nUSE TOOLS TO COMPLETE THIS TASK. Think step by step."
    )

    # Create ReAct agent
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True
    )

    # Execute agent
    try:
        result = agent_executor.invoke({"task": task})

        # Update state
        state["network_connector_output"] = result.get("output", "")
        state["data_source"] = "live" if "OFFLINE MODE" not in result.get("output", "") else "historical"
        state["agent_outputs"] = state.get("agent_outputs", {})
        state["agent_outputs"]["network_connector"] = result.get("output", "")

    except Exception as e:
        state["network_connector_output"] = f"ERROR: {str(e)}"
        state["data_source"] = "error"

    return state
