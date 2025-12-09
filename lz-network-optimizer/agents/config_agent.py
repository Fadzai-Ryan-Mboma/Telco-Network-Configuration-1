"""
Liquid Zimbabwe 4G Network Optimizer - Configuration Agent
Purpose: Recommend parameter changes using few-shot learning
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

from tools.huawei_tools import query_huawei_parameter, validate_parameter_range
from tools.sql_tools import execute_historical_sql
from tools.dummy_responses import get_config_recommendation_dummy, DUMMY_CONFIG_RECOMMENDATIONS
from prompts.system_prompts import CONFIGURATION_AGENT_PROMPT
from prompts.few_shot_examples import format_few_shot_examples
from utils.timeout_handler import safe_llm_call, TimeoutError, CONFIG_TIMEOUT

logger = logging.getLogger(__name__)


def config_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Configuration Agent - Recommends parameter changes using few-shot learning.

    2-TIER FALLBACK MECHANISM:
    Tier 1: LLM agent with Huawei API tools (with 45s timeout)
    Tier 2: Rule-based recommendations from dummy data (always succeeds)
    """
    logger.info(f"🤖 CONFIGURATION AGENT - Starting parameter recommendation")

    # Extract parameters
    site_name = state.get("site_name", "Unknown")
    primary_kpi_issue = state.get("primary_kpi_issue", "unknown")
    kpi_analytics_output = state.get('kpi_analytics_output', '')

    logger.info(f"📝 Task: Recommendations for {site_name}, Issue: {primary_kpi_issue}")

    # ==========================================================================
    # TIER 1: Try LLM Agent with Tools (Primary)
    # ==========================================================================
    def try_llm_agent():
        """Attempt LLM-based configuration recommendations."""
        logger.info("🔄 TIER 1: Attempting LLM agent configuration...")

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
KPI Analytics: {kpi_analytics_output}

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

        # Build system prompt with task
        system_prompt = CONFIGURATION_AGENT_PROMPT + "\n\n" + task + "\n\nUSE TOOLS TO COMPLETE THIS TASK."

        # Create ReAct agent (LangGraph version)
        agent = create_react_agent(llm, tools, prompt=system_prompt)

        # Execute agent
        result = agent.invoke({"messages": [{"role": "user", "content": task}]})

        # Extract output from messages
        if "messages" in result and len(result["messages"]) > 0:
            output = result["messages"][-1].content if hasattr(result["messages"][-1], 'content') else str(result["messages"][-1])
        else:
            output = str(result)

        # Detect failures in LLM output
        if "ERROR" in output.upper():
            raise Exception(f"LLM generated error output: {output[:200]}")

        return output

    # ==========================================================================
    # TIER 2: Rule-Based Recommendations (Fallback - Always Succeeds)
    # ==========================================================================
    def use_rule_based_config():
        """Fallback: Use rule-based configuration recommendations from dummy data."""
        logger.info("🔄 TIER 2: Using rule-based configuration recommendations...")

        # Get dummy recommendation based on primary KPI issue
        output = get_config_recommendation_dummy(primary_kpi_issue)

        logger.info(f"✅ Rule-based recommendations generated for issue: {primary_kpi_issue}")

        return output

    # ==========================================================================
    # EXECUTION LOGIC: Try Tier 1 → Tier 2
    # ==========================================================================
    output = None

    try:
        # TIER 1: Try LLM with timeout
        output = safe_llm_call(
            llm_function=try_llm_agent,
            fallback_function=lambda: None,  # Return None to trigger Tier 2
            timeout_seconds=CONFIG_TIMEOUT,
            operation_name="Configuration Agent (LLM)"
        )

        if output is not None:
            logger.info("✅ TIER 1 SUCCESS: LLM configuration recommendations complete")
        else:
            raise Exception("LLM returned None - triggering fallback")

    except Exception as e:
        logger.warning(f"⚠️  TIER 1 failed: {e}")

        # TIER 2: Use rule-based fallback
        output = use_rule_based_config()
        logger.info("✅ TIER 2 SUCCESS: Rule-based configuration complete")

    # ==========================================================================
    # UPDATE STATE
    # ==========================================================================
    state["config_output"] = output
    state["agent_outputs"] = state.get("agent_outputs", {})
    state["agent_outputs"]["configuration"] = output

    logger.info(f"💬 CONFIGURATION OUTPUT:\n{output[:300]}...")

    return state
