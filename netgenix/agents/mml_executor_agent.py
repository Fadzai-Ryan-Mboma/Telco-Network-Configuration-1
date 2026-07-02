"""
Liquid Zimbabwe 4G Network Optimizer - MML Executor Agent
Purpose: Execute approved parameter changes
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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.huawei_tools import modify_huawei_parameter, execute_mml_command, query_huawei_kpi
from tools.sql_tools import execute_historical_sql
from tools.rollback_manager import capture_rollback_state, execute_rollback
from prompts.system_prompts import MML_EXECUTOR_AGENT_PROMPT
from utils.timeout_handler import TimeoutHandler, TimeoutError as LLMTimeoutError


def mml_executor_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """MML Executor Agent - Executes approved parameter changes."""
    site_name = state.get("site_name", "Unknown")
    cell_id = state.get("cell_id", 1)
    validation_status = state.get("validation_status", "REJECTED")

    # Initialize LLM using factory (supports OpenAI, NVIDIA, etc.)
    llm = get_llm_client(temperature=0.3)

    # CRITICAL: Include rollback tools for safety
    tools = [
        capture_rollback_state,  # Must capture BEFORE modifications
        modify_huawei_parameter,
        execute_mml_command,
        query_huawei_kpi,
        execute_rollback,  # For emergency rollback
        execute_historical_sql
    ]

    # Only execute if approved
    if validation_status not in ["APPROVED", "REVIEW"]:
        state["executor_output"] = f"EXECUTION SKIPPED: Validation status is {validation_status}"
        state["agent_outputs"]["mml_executor"] = state["executor_output"]
        state["optimization_success"] = False
        state["modify_results"] = []
        return state

    task = f"""
Site: {site_name}
Cell ID: {cell_id}
Validation Status: {validation_status}
Approved Changes: {state.get('validation_output', '')}

YOUR TASK - CRITICAL SAFETY PROCEDURE:

STEP 1: CAPTURE ROLLBACK STATE (MANDATORY)
   - BEFORE making ANY changes, you MUST call capture_rollback_state() for EACH parameter
   - Pass the parameter_name and site_name to the tool
   - Save the rollback_id returned - you'll need it if rollback is required
   - Example: capture_rollback_state("reference_signal_power_pdschcfg", "{site_name}")
   - This ensures we can undo changes if something goes wrong

STEP 2: EXECUTE PARAMETER CHANGES
   - Extract approved parameter changes from Validation Agent output
   - Execute EACH parameter change using modify_huawei_parameter
   - Execute changes sequentially, not all at once
   - Check for errors after each change
   - Log execution status (success/failure) for each change

STEP 3: VERIFY CHANGES
   - After all changes, query KPIs to verify impact
   - Compare with expected improvements

STEP 4: FINAL REPORT
   - Provide clear execution report
   - Include rollback_id(s) for reference
   - Report overall status (SUCCESS/PARTIAL SUCCESS/FAILURE)

CRITICAL RULES:
- NEVER skip rollback capture - it's a safety requirement
- If rollback capture fails, DO NOT proceed with modifications
- If any modification fails, report the rollback_id so changes can be undone
- Execute changes sequentially with error checking

If in DRY_RUN mode, simulate execution without making real changes.
"""

    # Build system prompt with task
    system_prompt = MML_EXECUTOR_AGENT_PROMPT + "\n\n" + task + "\n\nUSE TOOLS TO COMPLETE THIS TASK."

    # Create ReAct agent (LangGraph version)
    agent = create_react_agent(llm, tools, prompt=system_prompt)

    # Execute agent with timeout protection
    import logging
    logger = logging.getLogger('LZ-Agent')

    try:
        logger.info(f"🤖 MML EXECUTOR AGENT - Starting execution for {site_name}")

        # Create timeout handler (60s for execution + verification)
        timeout_handler = TimeoutHandler(timeout_seconds=60)

        # Wrap agent.invoke() with timeout
        try:
            with timeout_handler.timeout_context("MML Executor Agent LLM call"):
                result = agent.invoke({"messages": [{"role": "user", "content": task}]})

        except LLMTimeoutError as timeout_error:
            logger.error(f"❌ MML EXECUTOR TIMEOUT: {timeout_error}")
            logger.error(f"⚠️  The LLM took longer than 60 seconds to respond")
            state["executor_output"] = f"ERROR: Agent timed out after 60 seconds. No changes were made."
            state["optimization_success"] = False
            state["modify_results"] = []
            return state

        # Extract structured outcomes from the actual modify-tool calls (ToolMessages),
        # rather than relying on the agent's freeform final report. huawei_tools'
        # modify_huawei_parameter(_site) always return a string that starts with
        # SUCCESS:/PARTIAL SUCCESS:/FAILURE:/ERROR:, which is reliable to parse;
        # the agent's prose summary is not (it can say "no failures" or discuss a
        # failure hypothetically, which naive substring counts miscount).
        modify_tool_names = {"modify_huawei_parameter", "modify_huawei_parameter_site"}
        modify_results = []
        for msg in result.get("messages", []):
            msg_type = str(getattr(msg, 'type', '') or getattr(msg, '__class__', '').__name__).lower()
            if 'tool' not in msg_type:
                continue
            tool_name = getattr(msg, 'name', '')
            if tool_name not in modify_tool_names:
                continue
            content = message_to_text(msg)
            content_upper = content.upper()
            if content_upper.startswith("SUCCESS"):
                outcome = "success"
            elif content_upper.startswith("PARTIAL SUCCESS"):
                outcome = "partial"
            elif content_upper.startswith(("FAILURE", "ERROR")):
                outcome = "failed"
            else:
                outcome = "unknown"
            modify_results.append({"tool": tool_name, "outcome": outcome, "message": content})

        state["modify_results"] = modify_results

        # Extract output from AI messages only (not tool calls)
        ai_responses = []
        if "messages" in result and len(result["messages"]) > 0:
            for msg in result["messages"]:
                msg_type = getattr(msg, 'type', '') or getattr(msg, '__class__', '').__name__.lower()
                if 'ai' in str(msg_type).lower() and hasattr(msg, 'content') and msg.content:
                    content = message_to_text(msg)
                    # Skip tool calls
                    if '<function' not in content and len(content) > 100:
                        ai_responses.append(content)
        
        # If no final text found, force LLM to generate execution report
        if not ai_responses:
            followup_prompt = """
Based on the tool executions above, now provide your FINAL EXECUTION REPORT:

Include:
- Summary of each parameter change executed (parameter name, old value → new value, status)
- Any errors encountered
- Post-change KPI verification results
- Overall execution status (SUCCESS/PARTIAL SUCCESS/FAILURE)
- Specific details about what was changed and what happened

Write your complete detailed execution report NOW:
"""
            messages = result.get("messages", [])
            messages.append({"role": "user", "content": followup_prompt})
            result = agent.invoke({"messages": messages})
            
            # Extract AI response from follow-up
            for msg in reversed(result.get("messages", [])):
                msg_type = str(getattr(msg, 'type', '') or getattr(msg, '__class__', '').__name__).lower()
                if 'ai' in msg_type and hasattr(msg, 'content'):
                    content = message_to_text(msg)
                    if '<function' not in content and len(content) > 100:
                        ai_responses.append(content)
                        break
        
        # Get output
        if ai_responses:
            output = "\n\n".join(ai_responses)
        else:
            output = str(result.get("messages", [])[-1].content) if result.get("messages") else "No execution output"

        # Update state
        state["executor_output"] = output
        state["agent_outputs"] = state.get("agent_outputs", {})
        state["agent_outputs"]["mml_executor"] = output

        # Determine success from the structured modify-tool results when any
        # modify calls were made; fall back to the prose report only if the
        # agent never called a modify tool (e.g. it aborted after rollback
        # capture failed).
        if modify_results:
            state["optimization_success"] = all(r["outcome"] == "success" for r in modify_results)
        else:
            output_upper = output.upper()
            state["optimization_success"] = "SUCCESS" in output_upper and "FAILURE" not in output_upper

    except Exception as e:
        state["executor_output"] = f"ERROR: {str(e)}"
        state["optimization_success"] = False
        state["modify_results"] = []

    return state
