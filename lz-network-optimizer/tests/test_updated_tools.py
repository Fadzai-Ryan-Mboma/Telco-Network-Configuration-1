#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network Optimizer - Test Updated Tools
Purpose: Verify Phase 5 tool updates work correctly with API
Created: 2025-11-03

Tests:
1. Import updated tools successfully
2. Verify site_name parameter exists in all tools
3. Test query_huawei_parameter with site_name
4. Test new modify_huawei_parameter_site tool
5. Test rollback_manager functionality
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


def test_tool_imports():
    """Test 1: Import updated tools"""
    print_header("Test 1: Tool Imports")

    try:
        from tools.huawei_tools import (
            query_huawei_parameter,
            modify_huawei_parameter,
            modify_huawei_parameter_site,
            execute_mml_command,
            query_huawei_kpi,
            validate_parameter_range,
            HUAWEI_TOOLS
        )
        print_test("Import huawei_tools", True)

        # Check tool count
        expected_count = 6
        actual_count = len(HUAWEI_TOOLS)
        print_test(f"Tool count: {actual_count}", actual_count == expected_count,
                  f"Expected {expected_count}, got {actual_count}")

        # Check new tool exists
        has_batch_tool = any(tool.name == "modify_huawei_parameter_site" for tool in HUAWEI_TOOLS)
        print_test("New batch modification tool exists", has_batch_tool)

        return True

    except Exception as e:
        print_test("Import huawei_tools", False, str(e))
        return False


def test_tool_signatures():
    """Test 2: Verify tool signatures have site_name parameter"""
    print_header("Test 2: Tool Signatures")

    try:
        from tools.huawei_tools import (
            query_huawei_parameter,
            modify_huawei_parameter,
            modify_huawei_parameter_site,
            execute_mml_command,
            query_huawei_kpi
        )

        # Check query_huawei_parameter
        sig = query_huawei_parameter.get_input_schema()
        has_site = 'site_name' in sig['properties']
        print_test("query_huawei_parameter has site_name", has_site)

        # Check modify_huawei_parameter
        sig = modify_huawei_parameter.get_input_schema()
        has_site = 'site_name' in sig['properties']
        print_test("modify_huawei_parameter has site_name", has_site)

        # Check modify_huawei_parameter_site
        sig = modify_huawei_parameter_site.get_input_schema()
        has_site = 'site_name' in sig['properties']
        has_cells = 'cell_ids' in sig['properties']
        print_test("modify_huawei_parameter_site has site_name and cell_ids", has_site and has_cells)

        # Check execute_mml_command
        sig = execute_mml_command.get_input_schema()
        has_site = 'site_name' in sig['properties']
        print_test("execute_mml_command has site_name", has_site)

        # Check query_huawei_kpi
        sig = query_huawei_kpi.get_input_schema()
        has_site = 'site_name' in sig['properties']
        print_test("query_huawei_kpi has site_name", has_site)

        return True

    except Exception as e:
        print_test("Check tool signatures", False, str(e))
        return False


def test_rollback_manager_import():
    """Test 3: Import rollback manager"""
    print_header("Test 3: Rollback Manager Import")

    try:
        from tools.rollback_manager import (
            RollbackManager,
            capture_rollback_state,
            execute_rollback,
            verify_rollback_success,
            list_available_rollbacks,
            ROLLBACK_TOOLS
        )
        print_test("Import rollback_manager", True)

        # Check tool count
        expected_count = 4
        actual_count = len(ROLLBACK_TOOLS)
        print_test(f"Rollback tool count: {actual_count}", actual_count == expected_count,
                  f"Expected {expected_count}, got {actual_count}")

        # Create RollbackManager instance
        manager = RollbackManager()
        print_test("Create RollbackManager instance", True,
                  f"Storage path: {manager.storage_path}")

        return True

    except Exception as e:
        print_test("Import rollback_manager", False, str(e))
        return False


def test_api_connectivity():
    """Test 4: API connectivity with updated client"""
    print_header("Test 4: API Connectivity")

    try:
        from network.huawei_api_client import HuaweiAPIClient

        # Check environment variables
        api_url = os.getenv('HUAWEI_API_URL')
        username = os.getenv('HUAWEI_USERNAME')
        password = os.getenv('HUAWEI_PASSWORD')

        if not all([api_url, username, password]):
            print_test("Environment variables", False,
                      "Missing HUAWEI_API_URL, HUAWEI_USERNAME, or HUAWEI_PASSWORD")
            return False

        print_test("Environment variables", True)

        # Initialize client
        api_config = {
            'base_url': api_url,
            'username': username,
            'password': password,
            'timeout': 10,
            'retry_attempts': 2,
            'retry_delay': 3,
            'ssl_verify': False
        }
        client = HuaweiAPIClient(api_config)
        print_test("Initialize HuaweiAPIClient", True)

        # Test authentication
        connected = client.connect()
        print_test("Authenticate with API", connected)

        if connected:
            print_test("Access token received", True,
                      f"Token length: {len(client.access_token)}")

        return connected

    except Exception as e:
        print_test("API connectivity", False, str(e))
        return False


def test_query_with_site_name():
    """Test 5: Query parameter with site_name"""
    print_header("Test 5: Query Parameter with site_name")

    try:
        from tools.huawei_tools import query_huawei_parameter

        # Test site
        test_site = "MSH-0112-Bindura Hospital"

        print(f"   Testing query on site: {test_site}")
        print(f"   Parameter: reference_signal_power_pdschcfg")
        print(f"   Cell: 1")

        # Execute query
        result = query_huawei_parameter.invoke({
            "parameter_name": "reference_signal_power_pdschcfg",
            "site_name": test_site,
            "cell_id": 1
        })

        print(f"\n   Result:\n   {result}\n")

        # Check result
        success = "ERROR" not in result and "OFFLINE" not in result
        print_test("Query executed successfully", success)

        return success

    except Exception as e:
        print_test("Query with site_name", False, str(e))
        return False


def test_batch_tool_dry_run():
    """Test 6: Batch modification tool (dry-run mode)"""
    print_header("Test 6: Batch Modification Tool (Dry-Run)")

    try:
        # First, check if dry-run mode is enabled
        import yaml
        config_path = project_root / "config" / "config.yaml"

        # Load config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Ensure dry-run is enabled
        if not config.get('agents', {}).get('mml_executor', {}).get('dry_run', False):
            print_test("Dry-run mode check", False,
                      "WARNING: dry_run is disabled in config.yaml. Skipping to prevent actual modifications.")
            return False

        print_test("Dry-run mode enabled", True)

        from tools.huawei_tools import modify_huawei_parameter_site

        # Test site
        test_site = "MSH-0112-Bindura Hospital"

        print(f"   Testing batch modification on site: {test_site}")
        print(f"   Parameter: reference_signal_power_pdschcfg")
        print(f"   Value: -180")
        print(f"   Cells: [1, 2, 3]")  # Test with 3 cells only

        # Execute batch modification (dry-run)
        result = modify_huawei_parameter_site.invoke({
            "parameter_name": "reference_signal_power_pdschcfg",
            "new_value": -180,
            "site_name": test_site,
            "cell_ids": [1, 2, 3],
            "reason": "Phase 5 testing - dry run"
        })

        print(f"\n   Result:\n   {result}\n")

        # Check result
        success = "DRY RUN" in result or "Would modify" in result
        print_test("Batch tool executed in dry-run mode", success)

        return success

    except Exception as e:
        print_test("Batch modification tool", False, str(e))
        return False


def main():
    """Run all tests"""
    print(f"{Colors.BOLD}LIQUID ZIMBABWE 4G NETWORK OPTIMIZER{Colors.END}")
    print(f"{Colors.BOLD}Phase 5 - Updated Tools Test Suite{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")

    results = []

    # Run tests
    results.append(("Tool Imports", test_tool_imports()))
    results.append(("Tool Signatures", test_tool_signatures()))
    results.append(("Rollback Manager Import", test_rollback_manager_import()))
    results.append(("API Connectivity", test_api_connectivity()))

    # Only run API tests if connectivity succeeds
    if results[-1][1]:
        results.append(("Query with site_name", test_query_with_site_name()))
        results.append(("Batch Tool (Dry-Run)", test_batch_tool_dry_run()))

    # Summary
    print_header("Test Summary")

    passed = sum(1 for _, status in results if status)
    total = len(results)

    for name, status in results:
        symbol = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
        print(f"{symbol} {name}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ ALL TESTS PASSED - TOOLS READY FOR PHASE 5{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ SOME TESTS FAILED - REVIEW ERRORS ABOVE{Colors.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
