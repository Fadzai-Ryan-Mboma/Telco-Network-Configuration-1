"""
Liquid Zimbabwe 4G Network Optimizer - Validation Agent
Purpose: Validate parameter changes and assess safety
Created: 2025-10-30
"""

from typing import Dict, Any
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
import sys
import os

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

    prompt = PromptTemplate.from_template(VALIDATION_AGENT_PROMPT)
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=6)

    try:
        result = agent_executor.invoke({"task": task})
        state["validation_output"] = result.get("output", "")
        state["agent_outputs"]["validation"] = result.get("output", "")

        # Determine approval status
        output = result.get("output", "").upper()
        if "APPROVED" in output:
            state["validation_status"] = "APPROVED"
        elif "REJECTED" in output:
            state["validation_status"] = "REJECTED"
        else:
            state["validation_status"] = "REVIEW"

    except Exception as e:
        state["validation_output"] = f"ERROR: {str(e)}"
        state["validation_status"] = "ERROR"

    return state
