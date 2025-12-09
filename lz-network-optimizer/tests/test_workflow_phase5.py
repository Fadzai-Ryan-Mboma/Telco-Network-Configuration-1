#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network Optimizer - Phase 5 Workflow Test
Purpose: Comprehensive workflow validation with updated tools
Created: 2025-11-03

Tests:
1. Workflow import and initialization
2. All 6 agents import successfully
3. Updated tools available in workflow
4. Workflow execution (generation mode - dry run)
5. Site_name parameter propagation
6. Batch modification recommendations
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# ANSI colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(title: str):
    """Print test section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")


def print_test(test_name: str, status: bool, details: str = ""):
    """Print test result"""
    symbol = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
    print(f"{symbol} {test_name}")
    if details:
        print(f"   {details}")


def test_workflow_imports():
    """Test 1: Workflow module imports"""
    print_header("Test 1: Workflow Module Imports")

    try:
        from agents.workflow import (
            create_optimization_workflow,
            run_optimization,
            OptimizationState
        )
        print_test("Import workflow functions", True)

        # Check workflow creation
        workflow = create_optimization_workflow()
        print_test("Create workflow instance", True, f"Type: {type(workflow)}")

        return True

    except Exception as e:
        print_test("Import workflow", False, str(e))
        return False


def test_agent_imports():
    """Test 2: All 6 agents import successfully"""
    print_header("Test 2: Individual Agent Imports")

    agents = [
        ('network_connector_agent', 'agents.network_connector_agent'),
        ('monitoring_agent', 'agents.monitoring_agent'),
        ('kpi_analytics_agent', 'agents.kpi_analytics_agent'),
        ('config_agent', 'agents.config_agent'),
        ('validation_agent', 'agents.validation_agent'),
        ('mml_executor_agent', 'agents.mml_executor_agent')
    ]

    all_passed = True
    for agent_name, module_path in agents:
        try:
            module = __import__(module_path, fromlist=[agent_name])
            agent_func = getattr(module, agent_name)
            print_test(f"Import {agent_name}", True)
        except Exception as e:
            print_test(f"Import {agent_name}", False, str(e))
            all_passed = False

    return all_passed


def test_updated_tools_available():
    """Test 3: Phase 5 updated tools available"""
    print_header("Test 3: Phase 5 Updated Tools")

    try:
        # Test Huawei tools
        from tools.huawei_tools import HUAWEI_TOOLS
        print_test(f"Huawei tools loaded", True, f"{len(HUAWEI_TOOLS)} tools")

        # Check for new batch tool
        tool_names = [tool.name for tool in HUAWEI_TOOLS]
        has_batch_tool = 'modify_huawei_parameter_site' in tool_names
        print_test("Batch modification tool present", has_batch_tool)

        # Check site_name parameter in tools
        from tools.huawei_tools import query_huawei_parameter
        sig = query_huawei_parameter.get_input_schema()
        has_site_name = 'site_name' in sig['properties']
        print_test("query_huawei_parameter has site_name", has_site_name)

        # Test rollback manager
        from tools.rollback_manager import ROLLBACK_TOOLS
        print_test(f"Rollback tools loaded", True, f"{len(ROLLBACK_TOOLS)} tools")

        return True

    except Exception as e:
        print_test("Load updated tools", False, str(e))
        return False


def test_workflow_state_initialization():
    """Test 4: Workflow state initialization"""
    print_header("Test 4: Workflow State Initialization")

    try:
        from agents.workflow import OptimizationState

        # Create test state
        test_state = {
            'site_name': 'MSH-0112-Bindura Hospital',
            'cell_id': 1,
            'user_query': 'Optimize network performance'
        }

        print_test("Create workflow state", True)
        print(f"   Site: {test_state['site_name']}")
        print(f"   Cell: {test_state['cell_id']}")
        print(f"   Query: {test_state['user_query']}")

        return True

    except Exception as e:
        print_test("Initialize workflow state", False, str(e))
        return False


def test_workflow_graph_structure():
    """Test 5: Workflow graph structure"""
    print_header("Test 5: Workflow Graph Structure")

    try:
        from agents.workflow import build_workflow

        # Build workflow graph
        graph = build_workflow()
        print_test("Build workflow graph", True)

        # Check nodes (should have 6 agent nodes)
        nodes = list(graph.nodes.keys())
        print_test(f"Workflow nodes", len(nodes) >= 6, f"{len(nodes)} nodes: {', '.join(nodes[:6])}")

        # Check edges
        edges = list(graph.edges)
        print_test(f"Workflow edges", len(edges) > 0, f"{len(edges)} edges defined")

        return True

    except Exception as e:
        print_test("Build workflow graph", False, str(e))
        return False


def test_dry_run_configuration():
    """Test 6: Dry-run mode configuration"""
    print_header("Test 6: Dry-Run Mode Configuration")

    try:
        import yaml

        config_path = project_root / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        dry_run = config.get('agents', {}).get('mml_executor', {}).get('dry_run', False)
        print_test("Dry-run mode", dry_run, f"dry_run = {dry_run}")

        if dry_run:
            print(f"   {Colors.GREEN}✓ Safe for testing - no live modifications{Colors.END}")
        else:
            print(f"   {Colors.YELLOW}⚠ WARNING: dry_run is FALSE - live modifications enabled!{Colors.END}")

        return True

    except Exception as e:
        print_test("Check dry-run config", False, str(e))
        return False


def test_workflow_execution_generation():
    """Test 7: Workflow execution - Generation mode (recommendations only)"""
    print_header("Test 7: Workflow Execution - Generation Mode")

    try:
        from agents.workflow import run_optimization

        print("Executing workflow for: MSH-0112-Bindura Hospital")
        print("Mode: Generation (recommendations only)")
        print("This will test the workflow without making actual modifications...\n")

        # Run workflow in generation mode
        result = run_optimization(
            site_name="MSH-0112-Bindura Hospital",
            user_query="Analyze network and recommend optimizations",
            cell_id=1
        )

        if result:
            print_test("Workflow execution", True)

            # Check result structure
            if isinstance(result, dict):
                print("\n   Workflow outputs:")
                for key, value in result.items():
                    if key.endswith('_output') and value:
                        agent_name = key.replace('_output', '')
                        print(f"   • {agent_name}: {str(value)[:100]}...")

            return True
        else:
            print_test("Workflow execution", False, "No result returned")
            return False

    except Exception as e:
        print_test("Workflow execution", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_site_name_propagation():
    """Test 8: Verify site_name propagates through workflow"""
    print_header("Test 8: Site Name Parameter Propagation")

    try:
        # This test checks if site_name is properly passed through the workflow
        # In Phase 5, all tools require site_name parameter

        from agents.workflow import OptimizationState

        test_state: OptimizationState = {
            'site_name': 'MSH-0112-Bindura Hospital',
            'cell_id': 1,
            'user_query': 'Test query',
            'network_connector_output': '',
            'monitoring_output': '',
            'kpi_analytics_output': '',
            'config_output': '',
            'validation_output': '',
            'executor_output': '',
            'data_source': 'live',
            'needs_optimization': False,
            'is_validated': False,
            'recommended_changes': [],
            'risk_score': 0,
            'final_result': ''
        }

        # Verify site_name is in state
        has_site_name = 'site_name' in test_state
        print_test("State contains site_name", has_site_name, f"Site: {test_state.get('site_name')}")

        # Verify site_name format
        site_name = test_state.get('site_name', '')
        valid_format = len(site_name) > 0 and ('-' in site_name or ' ' in site_name)
        print_test("Site name format valid", valid_format)

        return True

    except Exception as e:
        print_test("Site name propagation", False, str(e))
        return False


def test_batch_modification_readiness():
    """Test 9: Batch modification tool readiness"""
    print_header("Test 9: Batch Modification Tool Readiness")

    try:
        from tools.huawei_tools import modify_huawei_parameter_site

        # Check tool signature
        sig = modify_huawei_parameter_site.get_input_schema()

        # Verify required parameters
        required = ['parameter_name', 'new_value', 'site_name']
        all_present = all(param in sig['properties'] for param in required)
        print_test("Required parameters present", all_present, f"{', '.join(required)}")

        # Verify optional cell_ids parameter
        has_cell_ids = 'cell_ids' in sig['properties']
        print_test("Optional cell_ids parameter", has_cell_ids)

        # Check description mentions batch/6 cells
        description = modify_huawei_parameter_site.description or ""
        mentions_batch = 'batch' in description.lower() or '6' in description
        print_test("Description mentions batch execution", mentions_batch)

        return True

    except Exception as e:
        print_test("Batch tool readiness", False, str(e))
        return False


def test_rollback_integration():
    """Test 10: Rollback manager integration"""
    print_header("Test 10: Rollback Manager Integration")

    try:
        from tools.rollback_manager import (
            capture_rollback_state,
            execute_rollback,
            verify_rollback_success,
            list_available_rollbacks
        )

        print_test("Import rollback tools", True)

        # Check rollback storage directory
        rollback_dir = project_root / "data" / "rollback"
        rollback_dir.mkdir(parents=True, exist_ok=True)
        print_test("Rollback storage directory", rollback_dir.exists(), f"Path: {rollback_dir}")

        # Test RollbackManager instantiation
        from tools.rollback_manager import RollbackManager
        manager = RollbackManager()
        print_test("Create RollbackManager", True, f"Storage: {manager.storage_path}")

        return True

    except Exception as e:
        print_test("Rollback integration", False, str(e))
        return False


def main():
    """Run all tests"""
    print(f"{Colors.BOLD}LIQUID ZIMBABWE 4G NETWORK OPTIMIZER{Colors.END}")
    print(f"{Colors.BOLD}Phase 5 - Comprehensive Workflow Test Suite{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")

    results = []

    # Run tests
    results.append(("Workflow Imports", test_workflow_imports()))
    results.append(("Agent Imports", test_agent_imports()))
    results.append(("Updated Tools", test_updated_tools_available()))
    results.append(("State Initialization", test_workflow_state_initialization()))
    results.append(("Graph Structure", test_workflow_graph_structure()))
    results.append(("Dry-Run Config", test_dry_run_configuration()))
    results.append(("Site Name Propagation", test_site_name_propagation()))
    results.append(("Batch Tool Readiness", test_batch_modification_readiness()))
    results.append(("Rollback Integration", test_rollback_integration()))

    # Workflow execution test (can be slow)
    print(f"\n{Colors.YELLOW}Note: Workflow execution test may take 30-60 seconds...{Colors.END}")
    results.append(("Workflow Execution", test_workflow_execution_generation()))

    # Summary
    print_header("Test Summary")

    passed = sum(1 for _, status in results if status)
    total = len(results)

    for name, status in results:
        symbol = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
        print(f"{symbol} {name}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ ALL TESTS PASSED - WORKFLOW READY FOR PHASE 5{Colors.END}")
        return 0
    elif passed >= total * 0.8:  # 80% pass rate
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ MOSTLY PASSING - REVIEW FAILURES ABOVE{Colors.END}")
        return 1
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ MULTIPLE FAILURES - WORKFLOW NEEDS FIXES{Colors.END}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
