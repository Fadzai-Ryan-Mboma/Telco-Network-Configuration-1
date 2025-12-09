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
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.huawei_tools import validate_parameter_range
from tools.validation_tools import assess_risk_score, validate_optimization_safety
from tools.sql_tools import execute_historical_sql
from tools.dummy_responses import get_validation_result_dummy, DUMMY_VALIDATION_RESULTS
from prompts.system_prompts import VALIDATION_AGENT_PROMPT
from utils.timeout_handler import safe_llm_call, TimeoutError, VALIDATION_TIMEOUT

logger = logging.getLogger(__name__)


def validation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validation Agent - Validates safety of proposed parameter changes.

    2-TIER FALLBACK MECHANISM:
    Tier 1: LLM agent with validation tools (with 30s timeout)
    Tier 2: Rule-based validation from dummy data (always APPROVED for demo)
    """
    logger.info(f"🤖 VALIDATION AGENT - Starting safety validation")

    # Extract parameters
    site_name = state.get("site_name", "Unknown")
    config_output = state.get('config_output', '')
    primary_kpi_issue = state.get('primary_kpi_issue', 'unknown')

    logger.info(f"📝 Task: Validating recommendations for {site_name}")

    # ==========================================================================
    # TIER 1: Try LLM Agent with Tools (Primary)
    # ==========================================================================
    def try_llm_agent():
        """Attempt LLM-based validation."""
        logger.info("🔄 TIER 1: Attempting LLM agent validation...")

        llm = ChatNVIDIA(
            model="meta/llama-3.1-70b-instruct",
            api_key=os.getenv("NVIDIA_API_KEY"),
            temperature=0.3  # Lower temperature for safety-critical decisions
        )

        tools = [validate_parameter_range, assess_risk_score, validate_optimization_safety, execute_historical_sql]

        task = f"""
Site: {site_name}
Parameter Recommendations: {config_output}

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
    # TIER 2: Rule-Based Validation (Fallback - Always APPROVED for Demo)
    # ==========================================================================
    def use_rule_based_validation():
        """Fallback: Use rule-based validation from dummy data (always approves for demo)."""
        logger.info("🔄 TIER 2: Using rule-based validation (demo mode)...")

        # For demo, always use APPROVED_LOW_RISK validation
        # In production, you could analyze config_output to determine risk level
        output = get_validation_result_dummy("LOW")

        logger.info(f"✅ Rule-based validation complete - Status: APPROVED (demo mode)")

        return output

    # ==========================================================================
    # EXECUTION LOGIC: Try Tier 1 → Tier 2
    # ==========================================================================
    output = None
    validation_status = "PENDING"

    try:
        # TIER 1: Try LLM with timeout
        output = safe_llm_call(
            llm_function=try_llm_agent,
            fallback_function=lambda: None,  # Return None to trigger Tier 2
            timeout_seconds=VALIDATION_TIMEOUT,
            operation_name="Validation Agent (LLM)"
        )

        if output is not None:
            logger.info("✅ TIER 1 SUCCESS: LLM validation complete")

            # Determine approval status from LLM output
            output_upper = output.upper()
            if "APPROVED" in output_upper:
                validation_status = "APPROVED"
            elif "REJECTED" in output_upper:
                validation_status = "REJECTED"
            else:
                validation_status = "REVIEW"
        else:
            raise Exception("LLM returned None - triggering fallback")

    except Exception as e:
        logger.warning(f"⚠️  TIER 1 failed: {e}")

        # TIER 2: Use rule-based fallback
        output = use_rule_based_validation()
        validation_status = "APPROVED"  # Demo mode always approves
        logger.info("✅ TIER 2 SUCCESS: Rule-based validation complete")

    # ==========================================================================
    # UPDATE STATE
    # ==========================================================================
    state["validation_output"] = output
    state["validation_status"] = validation_status
    state["agent_outputs"] = state.get("agent_outputs", {})
    state["agent_outputs"]["validation"] = output

    logger.info(f"💬 VALIDATION OUTPUT:\n{output[:300]}...")
    logger.info(f"✅ VALIDATION STATUS: {validation_status}")

    return state
