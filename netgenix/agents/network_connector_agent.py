"""
Liquid Zimbabwe 4G Network Optimizer - Network Connector Agent
Purpose: Establish connectivity and query network element data
Created: 2025-10-30
"""

from typing import Dict, Any
from utils.llm_factory import get_llm_client, message_to_text
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

    # Initialize LLM using factory (supports OpenAI, NVIDIA, etc.)
    llm = get_llm_client(max_tokens=2000)

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
1. **ALWAYS TRY query_huawei_kpi FIRST** to get live network data
2. **ONLY if query_huawei_kpi explicitly says [API UNAVAILABLE]**, then use execute_lz_kpi_sql
3. If query_huawei_kpi returns KPI data (even with errors), use that data - DO NOT fall back to database unnecessarily
4. Report data source (live or historical)
5. Provide all 7 KPI values for next agent

Retrieve these KPIs:
- network_access_success (RACH Setup Success Rate %)
- download_speed (DL PDCP Throughput kbit/s)  
- download_quality (100 - DL IBLER %)
- upload_speed (UL PDCP Throughput kbit/s)
- upload_quality (100 - UL IBLER %)
- control_channel_load (PDCCH CCE Usage %)
- feedback_channel_load (PUCCH Usage %)

**CRITICAL: Try live API first! Only use database if API completely unavailable!**
"""

    # Build system prompt with task
    system_prompt = NETWORK_CONNECTOR_PROMPT + "\n\n" + task + "\n\nUSE TOOLS TO COMPLETE THIS TASK. Think step by step."

    # Create ReAct agent (LangGraph version - simpler API)
    agent = create_react_agent(llm, tools, prompt=system_prompt)

    # Execute agent
    try:
        # LangGraph create_react_agent expects messages in state
        result = agent.invoke({"messages": [{"role": "user", "content": task}]})

        # Extract output from messages
        if "messages" in result and len(result["messages"]) > 0:
            output = message_to_text(result["messages"][-1])
        else:
            output = str(result)

        # Update state
        state["network_connector_output"] = output
        state["data_source"] = "live" if "OFFLINE MODE" not in output else "historical"
        state["agent_outputs"] = state.get("agent_outputs", {})
        state["agent_outputs"]["network_connector"] = output

    except Exception as e:
        state["network_connector_output"] = f"ERROR: {str(e)}"
        state["data_source"] = "error"

    return state
