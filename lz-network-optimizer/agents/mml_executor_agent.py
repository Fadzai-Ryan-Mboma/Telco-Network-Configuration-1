"""
Liquid Zimbabwe 4G Network Optimizer - MML Executor Agent
Purpose: Execute approved parameter changes
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

from tools.huawei_tools import modify_huawei_parameter, execute_mml_command, query_huawei_kpi
from tools.sql_tools import execute_historical_sql
from prompts.system_prompts import MML_EXECUTOR_AGENT_PROMPT


def mml_executor_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """MML Executor Agent - Executes approved parameter changes."""
    site_name = state.get("site_name", "Unknown")
    cell_id = state.get("cell_id", 1)
    validation_status = state.get("validation_status", "REJECTED")

    llm = ChatNVIDIA(
        model="meta/llama-3.1-70b-instruct",
        api_key=os.getenv("NVIDIA_API_KEY"),
        temperature=0.3
    )

    tools = [modify_huawei_parameter, execute_mml_command, query_huawei_kpi, execute_historical_sql]

    # Only execute if approved
    if validation_status not in ["APPROVED", "REVIEW"]:
        state["executor_output"] = f"EXECUTION SKIPPED: Validation status is {validation_status}"
        state["agent_outputs"]["mml_executor"] = state["executor_output"]
        state["optimization_success"] = False
        return state

    task = f"""
Site: {site_name}
Cell ID: {cell_id}
Validation Status: {validation_status}
Approved Changes: {state.get('validation_output', '')}

YOUR TASK:
1. Extract approved parameter changes from Validation Agent output
2. Execute EACH parameter change using modify_huawei_parameter
3. Log execution status (success/failure) for each change
4. After all changes, query KPIs to verify impact
5. Report final status

IMPORTANT:
- Execute changes sequentially, not all at once
- Check for errors after each change
- Provide clear execution report at the end

If in DRY_RUN mode, simulate execution without making real changes.
"""

    # Build system prompt with task
    system_prompt = MML_EXECUTOR_AGENT_PROMPT + "\n\n" + task + "\n\nUSE TOOLS TO COMPLETE THIS TASK."

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
        state["executor_output"] = output
        state["agent_outputs"] = state.get("agent_outputs", {})
        state["agent_outputs"]["mml_executor"] = output

        # Determine success
        output_upper = output.upper()
        state["optimization_success"] = "SUCCESS" in output_upper and "FAILURE" not in output_upper

    except Exception as e:
        state["executor_output"] = f"ERROR: {str(e)}"
        state["optimization_success"] = False

    return state
