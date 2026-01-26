"""
Test NVIDIA LLM tool calling with SQL query generation
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.llm_factory import get_llm_client
from tools.sql_tools import execute_lz_kpi_sql
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv()

def test_sql_tool_calling():
    """Test if NVIDIA LLM can generate complete SQL queries."""

    print("="*80)
    print("TESTING NVIDIA LLM TOOL CALLING WITH SQL")
    print("="*80)

    # Initialize NVIDIA LLM
    llm = get_llm_client(temperature=0.3)
    print(f"✅ LLM initialized")

    # Create agent with SQL tool
    tools = [execute_lz_kpi_sql]

    system_prompt = """You are a SQL query generator for network KPI data.

AVAILABLE TOOL:
- execute_lz_kpi_sql: Execute SQL queries on KPI data

TABLE SCHEMA (kpi_data):
- site_name (TEXT): Name of the site (e.g., 'MSH-0014-Chipadze')
- timestamp (TEXT): Date of measurement
- network_access_success (REAL): Percentage
- download_speed (REAL): Mbps
- upload_speed (REAL): Mbps

TASK: Generate and execute a SQL query to get the last 7 days of KPI data for site 'MSH-0014-Chipadze'.

CRITICAL: When calling execute_lz_kpi_sql, provide a COMPLETE SQL query with proper string quoting.

Example correct tool call:
execute_lz_kpi_sql(sql_query="SELECT * FROM kpi_data WHERE site_name='MSH-0014-Chipadze' ORDER BY timestamp DESC LIMIT 7")

DO NOT generate incomplete queries like:
SELECT * FROM kpi_data WHERE site_name=

USE THE TOOL NOW.
"""

    agent = create_react_agent(llm, tools, prompt=system_prompt)

    task = "Get the last 7 days of KPI data for site 'MSH-0014-Chipadze'"

    print(f"\n📝 Task: {task}")
    print(f"\n🤖 Invoking agent...")

    try:
        result = agent.invoke({"messages": [{"role": "user", "content": task}]})

        print(f"\n✅ Agent completed")
        print(f"\n📊 Messages returned: {len(result.get('messages', []))}")

        for i, msg in enumerate(result.get('messages', [])):
            msg_type = getattr(msg, 'type', '') or getattr(msg, '__class__', '').__name__.lower()
            content_preview = str(msg.content)[:300] if hasattr(msg, 'content') else "No content"
            print(f"\nMessage {i} [{msg_type}]:")
            print(f"  {content_preview}")

            # If it's a tool message, show full content
            if 'tool' in str(msg_type).lower():
                print(f"\n  FULL TOOL RESPONSE:")
                print(f"  {msg.content}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sql_tool_calling()
