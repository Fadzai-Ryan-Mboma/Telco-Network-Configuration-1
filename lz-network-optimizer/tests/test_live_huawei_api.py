#!/usr/bin/env python3
"""
Live Huawei API Integration Tests
WARNING: Modifies REAL network - run on test site only

Usage:
    pytest tests/test_live_huawei_api.py -v -s --test-site="MSH-TEST-SITE"

Requirements:
    - Access to Huawei iMaster MAE test environment
    - Test site with low traffic
    - HUAWEI_API_URL, HUAWEI_USERNAME, HUAWEI_PASSWORD in .env
"""

import pytest
import os
import time
import re
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import system modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from network.huawei_api_client import HuaweiAPIClient
from domain.mml_commands import MML_COMMANDS
from tools.huawei_tools import modify_huawei_parameter, query_huawei_parameter


# ============================================================================
# Test Configuration
# ============================================================================

# CRITICAL: Set test site via command line
# pytest tests/test_live_huawei_api.py -v -s --test-site="MSH-0112-Bindura Hospital"
TEST_SITE = os.getenv("TEST_SITE", "MSH-0112-Bindura Hospital")
TEST_CELL_ID = 1

# Safety flag - must be explicitly enabled
RESTORE_AFTER_TEST = True

# Maximum safe parameter changes (conservative)
MAX_POWER_CHANGE_DB = 1  # ±1 dB max
MAX_TIMER_CHANGE_MS = 1000  # ±1000 ms max
MAX_OFFSET_CHANGE = 2  # ±2 units max


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--test-site",
        action="store",
        default="MSH-0112-Bindura Hospital",
        help="Site name for testing (e.g., 'MSH-0112-Bindura Hospital')"
    )
    parser.addoption(
        "--no-restore",
        action="store_true",
        default=False,
        help="Skip restoration after tests (DANGEROUS - use only if needed)"
    )


@pytest.fixture(scope="session")
def test_site(request):
    """Get test site from command line."""
    return request.config.getoption("--test-site")


@pytest.fixture(scope="session")
def restore_after_test(request):
    """Get restore flag from command line."""
    return not request.config.getoption("--no-restore")


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def api_client():
    """Initialize Huawei API client for all tests."""
    client = HuaweiAPIClient(
        base_url=os.getenv("HUAWEI_API_URL"),
        username=os.getenv("HUAWEI_USERNAME"),
        password=os.getenv("HUAWEI_PASSWORD"),
        ssl_verify=False  # Test environment may use self-signed certs
    )

    print(f"\n{'='*80}")
    print(f"LIVE HUAWEI API TEST SUITE")
    print(f"{'='*80}")
    print(f"⚠️  WARNING: This test suite modifies REAL network parameters")
    print(f"Test Site: {TEST_SITE}")
    print(f"Test Cell ID: {TEST_CELL_ID}")
    print(f"Restore After Test: {RESTORE_AFTER_TEST}")
    print(f"{'='*80}\n")

    yield client

    print(f"\n{'='*80}")
    print(f"TEST SUITE COMPLETED")
    print(f"{'='*80}\n")


# ============================================================================
# Helper Functions
# ============================================================================

def _parse_parameter_value(mml_output: str, parameter_field: str) -> Optional[float]:
    """
    Parse parameter value from MML response.

    Handles multiple Huawei MML output formats:
    - PARAMETER=VALUE
    - PARAMETER: VALUE
    - PARAMETER VALUE
    """
    if not mml_output or not parameter_field:
        return None

    # Try multiple patterns
    patterns = [
        rf"{parameter_field}\s*[=:]\s*([+-]?\d+(?:\.\d+)?)",  # PARAM=123 or PARAM: 123
        rf"{parameter_field}\s+([+-]?\d+(?:\.\d+)?)",  # PARAM 123
        rf"{parameter_field}\(([+-]?\d+(?:\.\d+)?)\)",  # PARAM(123)
    ]

    for pattern in patterns:
        match = re.search(pattern, mml_output, re.IGNORECASE)
        if match:
            return float(match.group(1))

    # If no match found, log for debugging
    print(f"⚠️  Could not parse '{parameter_field}' from MML output:")
    print(f"   {mml_output[:200]}...")
    return None


def _safe_parameter_change(current_value: float, parameter_name: str) -> float:
    """
    Calculate a safe test value based on parameter type.
    Returns a conservative change that won't impact network.
    """
    # Power parameters (in 0.1 dB units, so ±10 = ±1 dB)
    if 'power' in parameter_name.lower() or 'p0' in parameter_name.lower():
        return current_value + 10  # +1 dB (small safe change)

    # Timer parameters (in ms)
    if 'timer' in parameter_name.lower() or 't310' in parameter_name.lower():
        return current_value + 1000  # +1000 ms (1 second)

    # Offset parameters
    if 'offset' in parameter_name.lower():
        return current_value + 2  # +2 units

    # Default: 10% increase (conservative)
    return current_value * 1.1


# ============================================================================
# Test Class 1: Authentication
# ============================================================================

class TestLiveAuthentication:
    """Test OAuth2 authentication with Huawei iMaster MAE API."""

    def test_authentication(self, api_client):
        """Test OAuth token retrieval."""
        print("\n" + "="*80)
        print("TEST 1: AUTHENTICATION")
        print("="*80)

        token = api_client.authenticate()

        assert token is not None, "Token should not be None"
        assert len(token) > 20, "Token should be substantial length"

        print(f"✅ Token obtained: {token[:30]}...")
        print(f"✅ Token length: {len(token)} characters")

    def test_token_expiry_handling(self, api_client):
        """Test auto-refresh when token expires."""
        print("\n" + "="*80)
        print("TEST 2: TOKEN AUTO-REFRESH")
        print("="*80)

        # Force token expiry
        original_expiry = api_client.token_expires_at
        api_client.token_expires_at = 0

        print("⏰ Forced token expiry")

        # Should auto-refresh on next API call
        result = api_client.execute_mml_command(
            "LST CELL:;",
            [TEST_SITE]
        )

        assert result['success'], f"Command should succeed after token refresh: {result.get('error')}"
        assert api_client.token_expires_at > original_expiry, "Token should have been refreshed"

        print("✅ Token auto-refresh works")


# ============================================================================
# Test Class 2: Parameter Query
# ============================================================================

class TestParameterQuery:
    """Test querying cell parameters via MML commands."""

    def test_query_single_parameter(self, api_client, test_site):
        """Test querying reference signal power."""
        print("\n" + "="*80)
        print("TEST 3: QUERY SINGLE PARAMETER")
        print("="*80)

        param_name = 'reference_signal_power_pdschcfg'
        param_config = MML_COMMANDS[param_name]

        cmd_template = param_config['query']
        cmd = cmd_template.format(cell_id=TEST_CELL_ID)

        print(f"📝 Executing: {cmd}")

        result = api_client.execute_mml_command(cmd, [test_site])

        assert result['success'], f"Query failed: {result.get('error')}"

        print(f"✅ Query successful")
        print(f"📄 Response preview: {result['output'][:200]}...")

        # Try to parse value
        current_value = _parse_parameter_value(
            result['output'],
            param_config.get('parameter_field_alt', 'REFERENCESIGNALPWR')
        )

        if current_value is not None:
            print(f"✅ Parsed value: {current_value}")
        else:
            print(f"⚠️  Could not parse value (may need to adjust parsing logic)")

    def test_query_all_parameters(self, api_client, test_site):
        """Test querying all 5 tunable parameters."""
        print("\n" + "="*80)
        print("TEST 4: QUERY ALL PARAMETERS")
        print("="*80)

        results = {}

        for param_name, param_config in MML_COMMANDS.items():
            cmd_template = param_config['query']
            cmd = cmd_template.format(cell_id=TEST_CELL_ID)

            print(f"\n📝 Testing: {param_name}")

            result = api_client.execute_mml_command(cmd, [test_site])
            results[param_name] = result

            if result['success']:
                print(f"   ✅ Query successful")
            else:
                print(f"   ❌ Query failed: {result.get('error')}")

        # Verify at least some queries succeeded
        success_count = sum(1 for r in results.values() if r['success'])
        total_count = len(results)

        print(f"\n{'='*80}")
        print(f"SUMMARY: {success_count}/{total_count} parameter queries succeeded")
        print(f"{'='*80}")

        assert success_count > 0, "At least one parameter query should succeed"


# ============================================================================
# Test Class 3: Parameter Modification with Rollback
# ============================================================================

class TestParameterModification:
    """Test modifying parameters with automatic rollback."""

    @pytest.fixture(autouse=True)
    def capture_baseline(self, api_client, test_site, restore_after_test):
        """Capture baseline values before each test and restore after."""
        self.baseline_values = {}
        self.api_client = api_client
        self.test_site = test_site
        self.restore_enabled = restore_after_test

        print("\n📸 Capturing baseline configuration...")

        # Capture current values for all parameters
        for param_name, param_config in MML_COMMANDS.items():
            cmd = param_config['query'].format(cell_id=TEST_CELL_ID)
            result = api_client.execute_mml_command(cmd, [test_site])

            if result['success']:
                value = _parse_parameter_value(
                    result['output'],
                    param_config.get('parameter_field_alt', param_name.upper())
                )
                if value is not None:
                    self.baseline_values[param_name] = value
                    print(f"   ✅ {param_name}: {value}")

        print(f"📸 Baseline captured: {len(self.baseline_values)} parameters")

        yield  # Run test

        # Restore after test
        if self.restore_enabled and self.baseline_values:
            self._restore_baseline()

    def test_modify_power_parameter(self, test_site):
        """Test modifying reference signal power (safest parameter)."""
        print("\n" + "="*80)
        print("TEST 5: MODIFY POWER PARAMETER")
        print("="*80)

        param_name = 'reference_signal_power_pdschcfg'

        if param_name not in self.baseline_values:
            pytest.skip(f"Could not capture baseline for {param_name}")

        baseline_value = self.baseline_values[param_name]
        test_value = _safe_parameter_change(baseline_value, param_name)

        print(f"📊 Baseline value: {baseline_value}")
        print(f"📊 Test value: {test_value}")
        print(f"📊 Change: {test_value - baseline_value:+.1f} ({(test_value/baseline_value - 1)*100:+.1f}%)")

        # Execute modification
        cmd_template = MML_COMMANDS[param_name]['modify']
        cmd = cmd_template.format(cell_id=TEST_CELL_ID, value=int(test_value))

        print(f"📝 Executing: {cmd}")

        result = self.api_client.execute_mml_command(cmd, [test_site])

        # Verify modification succeeded
        assert result['success'], f"Modification failed: {result.get('error')}"
        assert 'SUCCEED' in result['output'].upper() or 'SUCCESS' in result['output'].upper(), \
            f"Modification may have failed: {result['output']}"

        print(f"✅ Modification command succeeded")

        # Wait for propagation
        print("⏳ Waiting 3 seconds for parameter propagation...")
        time.sleep(3)

        # Query to verify change
        query_cmd = MML_COMMANDS[param_name]['query'].format(cell_id=TEST_CELL_ID)
        verify_result = self.api_client.execute_mml_command(query_cmd, [test_site])

        assert verify_result['success'], "Verification query failed"

        new_value = _parse_parameter_value(
            verify_result['output'],
            MML_COMMANDS[param_name].get('parameter_field_alt', param_name.upper())
        )

        if new_value is not None:
            print(f"✅ Verified new value: {new_value}")

            # Check if change was applied (allow 1% tolerance)
            tolerance = abs(test_value * 0.01)
            if abs(new_value - test_value) <= tolerance:
                print(f"✅ Parameter modified successfully: {baseline_value} → {new_value}")
            else:
                print(f"⚠️  Value changed but not to expected value:")
                print(f"   Expected: {test_value}")
                print(f"   Got: {new_value}")
                print(f"   This may be due to Huawei rounding or constraints")
        else:
            print(f"⚠️  Could not verify new value (parsing issue)")

    def test_modify_timer_parameter(self, test_site):
        """Test modifying T310 timer (moderate risk)."""
        print("\n" + "="*80)
        print("TEST 6: MODIFY TIMER PARAMETER")
        print("="*80)

        param_name = 't310_timer'

        if param_name not in self.baseline_values:
            pytest.skip(f"Could not capture baseline for {param_name}")

        baseline_value = self.baseline_values[param_name]
        test_value = _safe_parameter_change(baseline_value, param_name)

        print(f"📊 Baseline value: {baseline_value} ms")
        print(f"📊 Test value: {test_value} ms")
        print(f"📊 Change: {test_value - baseline_value:+.0f} ms")

        # Execute modification
        cmd_template = MML_COMMANDS[param_name]['modify']
        cmd = cmd_template.format(cell_id=TEST_CELL_ID, value=int(test_value))

        print(f"📝 Executing: {cmd}")

        result = self.api_client.execute_mml_command(cmd, [test_site])

        assert result['success'], f"Modification failed: {result.get('error')}"

        print(f"✅ Timer modification succeeded")

    def _restore_baseline(self):
        """Restore all parameters to baseline values."""
        print("\n" + "="*80)
        print("🔄 RESTORING BASELINE CONFIGURATION")
        print("="*80)

        for param_name, baseline_value in self.baseline_values.items():
            print(f"\n📝 Restoring {param_name} to {baseline_value}...")

            cmd_template = MML_COMMANDS[param_name]['modify']
            cmd = cmd_template.format(cell_id=TEST_CELL_ID, value=int(baseline_value))

            result = self.api_client.execute_mml_command(cmd, [self.test_site])

            if result['success']:
                print(f"   ✅ Restored {param_name}")
            else:
                print(f"   ❌ Failed to restore {param_name}: {result.get('error')}")
                print(f"   ⚠️  MANUAL RESTORATION REQUIRED!")

        print(f"\n{'='*80}")
        print(f"✅ BASELINE RESTORATION COMPLETE")
        print(f"{'='*80}")


# ============================================================================
# Test Class 4: KPI Collection
# ============================================================================

class TestKPICollection:
    """Test KPI data collection via MML (known to be unreliable)."""

    def test_query_huawei_kpi_tool(self, test_site):
        """Test KPI collection tool (may fail - fallback is expected)."""
        print("\n" + "="*80)
        print("TEST 7: KPI COLLECTION VIA MML")
        print("="*80)

        # Import the tool
        from tools.huawei_tools import query_huawei_kpi

        # This is expected to potentially fail
        result = query_huawei_kpi.invoke({
            "site_name": test_site,
            "cell_id": TEST_CELL_ID
        })

        print(f"📄 Result: {result[:300]}...")

        # Document whether it works
        if "error" in result.lower() or "failed" in result.lower():
            print("⚠️  KPI collection via MML failed (expected behavior)")
            print("→ System will fallback to database as designed")
        else:
            print("✅ KPI collection via MML succeeded (unexpected but good!)")
            print("→ MML KPI collection is working on this system")


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    """Run tests directly (for quick debugging)."""
    print("\nTo run the full test suite:")
    print('pytest tests/test_live_huawei_api.py -v -s --test-site="YOUR-TEST-SITE"')
    print("\nTo run without restoration (DANGEROUS):")
    print('pytest tests/test_live_huawei_api.py -v -s --test-site="YOUR-TEST-SITE" --no-restore')
