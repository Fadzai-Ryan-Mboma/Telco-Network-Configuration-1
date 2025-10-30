"""
Liquid Zimbabwe 4G Network Optimizer - Validation Agent
Purpose: Validate parameter changes and assess safety
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

from tools.huawei_tools import validate_parameter_range
from tools.validation_tools import assess_risk_score, validate_optimization_safety
from tools.sql_tools import execute_historical_sql
from prompts.system_prompts import VALIDATION_AGENT_PROMPT


def validation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Validation Agent - Validates safety of proposed parameter changes."""
    site_name = state.get("site_name", "Unknown")

    llm = ChatNVIDIA(
        model="meta/llama-3.1-70b-instruct",
        api_key=os.getenv("NVIDIA_API_KEY"),
        temperature=0.3  # Lower temperature for safety-critical decisions
    )

    tools = [validate_parameter_range, assess_risk_score, validate_optimization_safety, execute_historical_sql]

    task = f"""
Site: {site_name}
Parameter Recommendations: {state.get('config_output', '')}

YOUR TASK:
1. Extract parameter change recommendations from Configuration Agent output
2. For EACH parameter change:
   - Validate range using validate_parameter_range
   - Assess individual risk using assess_risk_score
3. If multiple changes, validate combined safety using validate_optimization_safety
4. Make decision: APPROVED, REVIEW, or REJECTED
5. If APPROVED or REVIEW, proceed to execution
6. If REJECTED, explain why and recommend alternatives

Maximum acceptable risk threshold: 7/10

Provide clear safety decision at the end of your analysis.
"""

    # Build system prompt with task
    system_prompt = VALIDATION_AGENT_PROMPT + "\n\n" + task + "\n\nUSE TOOLS TO COMPLETE THIS TASK."

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
        state["validation_output"] = output
        state["agent_outputs"] = state.get("agent_outputs", {})
        state["agent_outputs"]["validation"] = output

        # Determine approval status
        output_upper = output.upper()
        if "APPROVED" in output_upper:
            state["validation_status"] = "APPROVED"
        elif "REJECTED" in output_upper:
            state["validation_status"] = "REJECTED"
        else:
            state["validation_status"] = "REVIEW"

    except Exception as e:
        state["validation_output"] = f"ERROR: {str(e)}"
        state["validation_status"] = "ERROR"

    return state
