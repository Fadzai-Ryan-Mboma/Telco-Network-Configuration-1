"""
Liquid Zimbabwe 4G Network Optimizer - Configuration Agent
Purpose: Recommend parameter changes using few-shot learning
Created: 2025-10-30
"""

from typing import Dict, Any
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.huawei_tools import query_huawei_parameter, validate_parameter_range
from tools.sql_tools import execute_historical_sql
from prompts.system_prompts import CONFIGURATION_AGENT_PROMPT
from prompts.few_shot_examples import format_few_shot_examples


def config_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Configuration Agent - Recommends parameter changes using few-shot learning."""
    site_name = state.get("site_name", "Unknown")
    primary_kpi_issue = state.get("primary_kpi_issue", "unknown")

    llm = ChatNVIDIA(
        model="meta/llama-3.1-70b-instruct",
        api_key=os.getenv("NVIDIA_API_KEY"),
        temperature=0.7
    )

    tools = [query_huawei_parameter, validate_parameter_range, execute_historical_sql]

    # Get relevant few-shot examples
    few_shot_examples = format_few_shot_examples(primary_kpi_issue, top_n=2)

    task = f"""
Site: {site_name}
Primary KPI Issue: {primary_kpi_issue}
KPI Analytics: {state.get('kpi_analytics_output', '')}

YOUR TASK:
1. Query current parameter values for relevant parameters
2. Review few-shot examples below to learn from past successes
3. Match KPI issue to optimization rules
4. Recommend parameter changes following patterns from examples
5. Validate proposed values using validate_parameter_range
6. Provide clear recommendations in this format:

PARAMETER_RECOMMENDATIONS:
- parameter: <name>
  current: <value>
  recommended: <value>
  reason: <explanation>
  expected_improvement: <description>
  confidence: <0-100%>

{few_shot_examples}
"""

    prompt_template = CONFIGURATION_AGENT_PROMPT + "\n\n" + task
    prompt = PromptTemplate.from_template(prompt_template)

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=7)

    try:
        result = agent_executor.invoke({"task": task, "few_shot_examples": few_shot_examples})
        state["config_output"] = result.get("output", "")
        state["agent_outputs"]["configuration"] = result.get("output", "")

    except Exception as e:
        state["config_output"] = f"ERROR: {str(e)}"

    return state
