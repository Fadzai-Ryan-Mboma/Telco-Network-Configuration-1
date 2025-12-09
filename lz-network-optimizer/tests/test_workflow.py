"""
Liquid Zimbabwe 4G Network Optimizer - Workflow Integration Test
Purpose: Test the complete 6-agent workflow end-to-end
Created: 2025-10-30
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / 'agents'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connectivity():
    """Test 1: Database connectivity and data availability."""
    print("\n" + "=" * 80)
    print("TEST 1: Database Connectivity")
    print("=" * 80)

    try:
        from network.kpi_collector import KPICollector

        collector = KPICollector()
        sites = collector.get_all_sites()

        print(f"✓ Database connection successful")
        print(f"✓ Found {len(sites)} sites in database:")
        for site in sites:
            print(f"  - {site}")

        if sites:
            # Test KPI collection for first site
            test_site = sites[0]
            kpis = collector.collect_kpis(test_site)
            print(f"\n✓ KPI collection test for {test_site}:")
            for kpi_name, value in kpis.items():
                print(f"  - {kpi_name}: {value}")

            return True, sites[0]
        else:
            print("✗ No sites found in database")
            return False, None

    except Exception as e:
        print(f"✗ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_tools():
    """Test 2: Individual tool functionality."""
    print("\n" + "=" * 80)
    print("TEST 2: Tool Functionality")
    print("=" * 80)

    try:
        # Test SQL tools
        from tools.sql_tools import execute_lz_kpi_sql

        print("\nTesting SQL tools...")
        result = execute_lz_kpi_sql.invoke({
            "sql_query": "SELECT COUNT(*) as total FROM kpi_data"
        })
        print(f"✓ SQL tool works: {result[:100]}...")

        # Test calculation tools
        from tools.calculation_tools import calc_weighted_kpi_score

        print("\nTesting calculation tools...")
        result = calc_weighted_kpi_score.invoke({
            "network_access_success": 96.0,
            "download_speed": 55.0,
            "download_quality": 97.0,
            "upload_speed": 22.0,
            "upload_quality": 96.0,
            "control_channel_load": 60.0,
            "feedback_channel_load": 30.0
        })
        print(f"✓ Calculation tool works")
        print(f"  Score preview: {result[:150]}...")

        # Test validation tools
        from tools.huawei_tools import validate_parameter_range
        from tools.validation_tools import assess_risk_score

        print("\nTesting validation tools...")
        result = validate_parameter_range.invoke({
            "parameter_name": "reference_signal_power_pdschcfg",
            "proposed_value": -180
        })
        print(f"✓ Parameter validation tool works: {result[:100]}...")

        result2 = assess_risk_score.invoke({
            "parameter_name": "reference_signal_power_pdschcfg",
            "current_value": -200,
            "proposed_value": -180,
            "kpi_issue": "low_download_speed"
        })
        print(f"✓ Risk assessment tool works")

        return True

    except Exception as e:
        print(f"✗ Tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompts():
    """Test 3: Prompt system."""
    print("\n" + "=" * 80)
    print("TEST 3: Prompt System")
    print("=" * 80)

    try:
        from prompts.system_prompts import build_agent_prompt
        from prompts.few_shot_examples import format_few_shot_examples
        from prompts.context_builders import build_parameter_context

        print("\nTesting system prompts...")
        prompt = build_agent_prompt("monitoring", "Test task")
        print(f"✓ System prompts work ({len(prompt)} chars)")

        print("\nTesting few-shot examples...")
        examples = format_few_shot_examples("low_download_speed", top_n=1)
        print(f"✓ Few-shot examples work ({len(examples)} chars)")

        print("\nTesting context builders...")
        context = build_parameter_context()
        print(f"✓ Context builders work ({len(context)} chars)")

        return True

    except Exception as e:
        print(f"✗ Prompt test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_dry_run(site_name):
    """Test 4: Complete workflow in offline mode."""
    print("\n" + "=" * 80)
    print("TEST 4: Workflow Dry Run (Offline Mode)")
    print("=" * 80)

    # Set offline mode
    os.environ['OFFLINE_MODE'] = 'true'

    # Check if NVIDIA API key is set
    if not os.getenv('NVIDIA_API_KEY'):
        print("⚠️  WARNING: NVIDIA_API_KEY not set")
        print("   Workflow test requires NVIDIA API key")
        print("   Set it with: export NVIDIA_API_KEY='your_key_here'")
        return False

    try:
        print(f"\nRunning workflow for site: {site_name}")
        print("Mode: OFFLINE (using historical data)")
        print("-" * 80)

        from agents.workflow import run_optimization

        result = run_optimization(
            site_name=site_name,
            user_query="Test optimization workflow",
            cell_id=1
        )

        print("\n✓ Workflow executed successfully!")
        print("\nWorkflow Results:")
        print(f"  Data Source: {result.get('data_source', 'Unknown')}")
        print(f"  Needs Optimization: {result.get('needs_optimization', False)}")

        if result.get('needs_optimization'):
            print(f"  Primary KPI Issue: {result.get('primary_kpi_issue', 'Unknown')}")
            print(f"  Validation Status: {result.get('validation_status', 'N/A')}")
            print(f"  Optimization Success: {result.get('optimization_success', False)}")

        print("\nAgent Execution Summary:")
        for agent_name in ['network_connector', 'monitoring', 'kpi_analytics',
                           'configuration', 'validation', 'mml_executor']:
            if agent_name in result.get('agent_outputs', {}):
                output = result['agent_outputs'][agent_name]
                status = "✓" if output and "ERROR" not in output.upper() else "✗"
                print(f"  {status} {agent_name}: {len(output)} chars output")

        return True

    except Exception as e:
        print(f"\n✗ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("\n" + "=" * 80)
    print("LIQUID ZIMBABWE 4G NETWORK OPTIMIZER - INTEGRATION TEST")
    print("=" * 80)

    results = {}
    test_site = None

    # Test 1: Database
    success, test_site = test_database_connectivity()
    results['database'] = success

    if not test_site:
        print("\n✗ Cannot proceed without database connectivity")
        print("  Run: python scripts/import_historical_data.py")
        return 1

    # Test 2: Tools
    results['tools'] = test_tools()

    # Test 3: Prompts
    results['prompts'] = test_prompts()

    # Test 4: Workflow (requires NVIDIA API key)
    results['workflow'] = test_workflow_dry_run(test_site)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name.upper()}")
        if not passed:
            all_passed = False

    print("=" * 80)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nSystem is ready for:")
        print("  1. Live API testing with Huawei network")
        print("  2. Phase 2.5: Docker containerization")
        print("  3. Checkpoint #2 demo")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nPlease fix the failing tests before proceeding")
        return 1


if __name__ == "__main__":
    sys.exit(main())
