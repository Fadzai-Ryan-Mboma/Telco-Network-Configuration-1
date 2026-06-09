"""
Liquid Zimbabwe 4G Network Optimizer - Rollback Manager
Purpose: Manage parameter change rollbacks for safe network modifications
Created: 2025-11-03 - Phase 5 Stage 5.4

This module provides rollback functionality for parameter modifications:
1. Capture pre-change state (all 6 cells)
2. Store rollback commands
3. Execute rollback if needed
4. Verify rollback success
"""

from langchain_core.tools import tool
from typing import Dict, Any, List, Optional, Annotated
import json
import os
import sys
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.mml_commands import build_query_command, build_modify_command_template
from network.huawei_api_client import HuaweiAPIClient

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# ROLLBACK STATE MANAGEMENT
# ============================================================================

class RollbackManager:
    """
    Manages rollback state for parameter modifications.

    Workflow:
    1. capture_state() - Query and store current values before change
    2. execute_modification() - Apply changes (handled by modify tools)
    3. rollback() - Restore previous values if needed
    4. verify_rollback() - Confirm restoration success
    """

    def __init__(self, storage_path: str = None):
        """
        Initialize rollback manager.

        Args:
            storage_path: Path to store rollback state files (default: data/rollback/)
        """
        if storage_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            storage_path = os.path.join(base_dir, "data", "rollback")

        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)

        logger.info(f"RollbackManager initialized with storage: {self.storage_path}")


    def capture_state(self,
                     parameter_name: str,
                     site_name: str,
                     cell_ids: List[int] = None,
                     api_client: HuaweiAPIClient = None) -> Dict[str, Any]:
        """
        Capture current parameter state for all cells at a site.

        Args:
            parameter_name: Parameter to capture (e.g., 'reference_signal_power_pdschcfg')
            site_name: Site name
            cell_ids: List of cell IDs (default: [1,2,3,4,5,6])
            api_client: Optional pre-initialized API client

        Returns:
            Dictionary with rollback state:
            {
                'rollback_id': str,
                'timestamp': str,
                'parameter_name': str,
                'site_name': str,
                'cell_states': [
                    {'cell_id': 1, 'current_value': -200},
                    {'cell_id': 2, 'current_value': -200},
                    ...
                ],
                'rollback_commands': [
                    'MOD PDSCHCFG: LOCALCELLID=1, REFERENCESIGNALPWR=-200;',
                    ...
                ]
            }
        """
        if cell_ids is None:
            cell_ids = [1, 2, 3, 4, 5, 6]

        rollback_id = f"{site_name}_{parameter_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Capturing state for rollback: {rollback_id}")

        # Initialize API client if not provided
        client_created = False
        if api_client is None:
            api_config = {
                'base_url': os.getenv('HUAWEI_API_URL'),
                'username': os.getenv('HUAWEI_USERNAME'),
                'password': os.getenv('HUAWEI_PASSWORD'),
                'timeout': 10,
                'retry_attempts': 2,
                'retry_delay': 3,
                'ssl_verify': False
            }
            api_client = HuaweiAPIClient(api_config)
            if not api_client.connect():
                raise Exception("Failed to authenticate with Huawei API")
            client_created = True

        # Query current values for all cells
        cell_states = []
        rollback_commands = []

        try:
            for cell_id in cell_ids:
                # Build query command
                query_command = build_query_command(parameter_name, cell_id)

                # Execute query
                response = api_client.execute_mml_command(query_command, [site_name])

                # Parse current value (simplified - would need proper parsing)
                # TODO: Implement proper MML response parsing
                current_value = self._parse_parameter_value(response, parameter_name)

                cell_states.append({
                    'cell_id': cell_id,
                    'current_value': current_value,
                    'query_response': str(response)[:500]  # Store partial response for debugging
                })

                # Build rollback command for this cell
                if current_value is not None:
                    rollback_cmd = build_modify_command_template(parameter_name, current_value)
                    rollback_commands.append(rollback_cmd.format(cell_id=cell_id))

            # Create rollback state
            rollback_state = {
                'rollback_id': rollback_id,
                'timestamp': datetime.now().isoformat(),
                'parameter_name': parameter_name,
                'site_name': site_name,
                'cell_states': cell_states,
                'rollback_commands': rollback_commands,
                'status': 'captured'
            }

            # Save to file
            self._save_state(rollback_id, rollback_state)

            logger.info(f"State captured successfully: {len(cell_states)} cells")
            return rollback_state

        finally:
            # Clean up client if we created it
            if client_created and hasattr(api_client, 'disconnect'):
                api_client.disconnect()


    def rollback(self,
                rollback_id: str,
                api_client: HuaweiAPIClient = None) -> Dict[str, Any]:
        """
        Execute rollback to restore previous parameter values.

        Args:
            rollback_id: Rollback ID from capture_state()
            api_client: Optional pre-initialized API client

        Returns:
            Dictionary with rollback results:
            {
                'rollback_id': str,
                'success': bool,
                'results': [
                    {'cell_id': 1, 'success': True, 'response': '...'},
                    ...
                ],
                'summary': str
            }
        """
        logger.info(f"Executing rollback: {rollback_id}")

        # Load rollback state
        rollback_state = self._load_state(rollback_id)
        if rollback_state is None:
            raise Exception(f"Rollback state not found: {rollback_id}")

        # Initialize API client if not provided
        client_created = False
        if api_client is None:
            api_config = {
                'base_url': os.getenv('HUAWEI_API_URL'),
                'username': os.getenv('HUAWEI_USERNAME'),
                'password': os.getenv('HUAWEI_PASSWORD'),
                'timeout': 30,
                'retry_attempts': 2,
                'retry_delay': 3,
                'ssl_verify': False
            }
            api_client = HuaweiAPIClient(api_config)
            if not api_client.connect():
                raise Exception("Failed to authenticate with Huawei API")
            client_created = True

        # Execute rollback commands
        results = []
        site_name = rollback_state['site_name']

        try:
            for i, cmd in enumerate(rollback_state['rollback_commands']):
                cell_id = rollback_state['cell_states'][i]['cell_id']

                try:
                    response = api_client.execute_mml_command(cmd, [site_name])

                    # Check success
                    response_str = str(response)
                    success = ("SUCCEED" in response_str.upper() or
                              "SUCCESS" in response_str.upper() or
                              "RETCODE = 0" in response_str)

                    results.append({
                        'cell_id': cell_id,
                        'success': success,
                        'command': cmd,
                        'response': response_str[:500]
                    })

                except Exception as e:
                    results.append({
                        'cell_id': cell_id,
                        'success': False,
                        'command': cmd,
                        'error': str(e)
                    })

            # Update rollback state
            successful = sum(1 for r in results if r['success'])
            rollback_state['status'] = 'completed' if successful == len(results) else 'partial'
            rollback_state['rollback_results'] = results
            rollback_state['rollback_timestamp'] = datetime.now().isoformat()

            self._save_state(rollback_id, rollback_state)

            logger.info(f"Rollback completed: {successful}/{len(results)} successful")

            return {
                'rollback_id': rollback_id,
                'success': successful == len(results),
                'results': results,
                'summary': f"Rollback {rollback_state['status']}: {successful}/{len(results)} cells restored"
            }

        finally:
            # Clean up client if we created it
            if client_created and hasattr(api_client, 'disconnect'):
                api_client.disconnect()


    def verify_rollback(self,
                       rollback_id: str,
                       api_client: HuaweiAPIClient = None) -> Dict[str, Any]:
        """
        Verify rollback was successful by querying current values.

        Args:
            rollback_id: Rollback ID to verify
            api_client: Optional pre-initialized API client

        Returns:
            Dictionary with verification results
        """
        logger.info(f"Verifying rollback: {rollback_id}")

        # Load rollback state
        rollback_state = self._load_state(rollback_id)
        if rollback_state is None:
            raise Exception(f"Rollback state not found: {rollback_id}")

        # Initialize API client if not provided
        client_created = False
        if api_client is None:
            api_config = {
                'base_url': os.getenv('HUAWEI_API_URL'),
                'username': os.getenv('HUAWEI_USERNAME'),
                'password': os.getenv('HUAWEI_PASSWORD'),
                'timeout': 10,
                'retry_attempts': 2,
                'retry_delay': 3,
                'ssl_verify': False
            }
            api_client = HuaweiAPIClient(api_config)
            if not api_client.connect():
                raise Exception("Failed to authenticate with Huawei API")
            client_created = True

        # Query current values and compare
        verification_results = []
        parameter_name = rollback_state['parameter_name']
        site_name = rollback_state['site_name']

        try:
            for cell_state in rollback_state['cell_states']:
                cell_id = cell_state['cell_id']
                expected_value = cell_state['current_value']

                # Query current value
                query_command = build_query_command(parameter_name, cell_id)
                response = api_client.execute_mml_command(query_command, [site_name])
                current_value = self._parse_parameter_value(response, parameter_name)

                # Compare
                matches = (current_value == expected_value)

                verification_results.append({
                    'cell_id': cell_id,
                    'expected_value': expected_value,
                    'current_value': current_value,
                    'verified': matches
                })

            verified_count = sum(1 for r in verification_results if r['verified'])

            return {
                'rollback_id': rollback_id,
                'verification_success': verified_count == len(verification_results),
                'results': verification_results,
                'summary': f"Verification: {verified_count}/{len(verification_results)} cells match expected values"
            }

        finally:
            # Clean up client if we created it
            if client_created and hasattr(api_client, 'disconnect'):
                api_client.disconnect()


    def list_rollbacks(self, site_name: str = None) -> List[Dict[str, Any]]:
        """
        List available rollback states.

        Args:
            site_name: Optional filter by site name

        Returns:
            List of rollback state summaries
        """
        rollbacks = []

        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                rollback_id = filename[:-5]  # Remove .json

                # Filter by site if specified
                if site_name and not rollback_id.startswith(site_name):
                    continue

                state = self._load_state(rollback_id)
                if state:
                    rollbacks.append({
                        'rollback_id': rollback_id,
                        'timestamp': state.get('timestamp'),
                        'site_name': state.get('site_name'),
                        'parameter_name': state.get('parameter_name'),
                        'status': state.get('status'),
                        'cell_count': len(state.get('cell_states', []))
                    })

        # Sort by timestamp (newest first)
        rollbacks.sort(key=lambda x: x['timestamp'], reverse=True)

        return rollbacks


    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _save_state(self, rollback_id: str, state: Dict[str, Any]) -> None:
        """Save rollback state to file"""
        filepath = os.path.join(self.storage_path, f"{rollback_id}.json")
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        logger.debug(f"Saved rollback state: {filepath}")


    def _load_state(self, rollback_id: str) -> Optional[Dict[str, Any]]:
        """Load rollback state from file"""
        filepath = os.path.join(self.storage_path, f"{rollback_id}.json")
        if not os.path.exists(filepath):
            return None

        with open(filepath, 'r') as f:
            state = json.load(f)
        logger.debug(f"Loaded rollback state: {filepath}")
        return state


    def _parse_parameter_value(self, response: Any, parameter_name: str) -> Optional[float]:
        """
        Parse parameter value from MML response.

        TODO: Implement proper MML response parsing based on parameter type.
        This is a simplified version - would need to parse actual MML output format.
        """
        # For now, return None to indicate parsing not implemented
        # Real implementation would extract value from response based on parameter_name

        response_str = str(response)

        # Try to extract value using simple pattern matching
        # This is a placeholder - real implementation needs proper MML parsing
        import re

        # Get parameter field name from mml_commands
        from domain.mml_commands import get_parameter_field_name
        try:
            field_name = get_parameter_field_name(parameter_name)

            # Look for "FIELD_NAME=value" pattern
            match = re.search(rf"{field_name}=([^,;\s]+)", response_str)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return None
        except:
            pass

        return None


# ============================================================================
# LANGCHAIN TOOLS FOR AGENT USE
# ============================================================================

@tool
def capture_rollback_state(
    parameter_name: Annotated[str, "Parameter name (e.g., 'reference_signal_power_pdschcfg')"],
    site_name: Annotated[str, "Site name (e.g., 'MSH-0112-Bindura Hospital')"],
    cell_ids: Annotated[Optional[List[int]], "Cell IDs to capture (default: [1,2,3,4,5,6])"] = None
) -> str:
    """
    Capture current parameter state before modification for rollback.

    IMPORTANT: Call this tool BEFORE making any parameter modifications.
    It queries and stores current values for all cells so you can rollback if needed.

    Returns rollback_id that you must use for rollback operations.

    Args:
        parameter_name: Parameter to capture
        site_name: Site name
        cell_ids: Cell IDs to capture (default: all 6 cells)

    Returns:
        String with rollback_id and capture summary

    Example:
        capture_rollback_state("reference_signal_power_pdschcfg",
                              "MSH-0112-Bindura Hospital")
        Returns: "Rollback state captured: MSH-0112-Bindura Hospital_reference_signal_power_pdschcfg_20251103_143022"
    """
    try:
        manager = RollbackManager()
        state = manager.capture_state(parameter_name, site_name, cell_ids)

        return f"SUCCESS: Rollback state captured\nRollback ID: {state['rollback_id']}\nCells captured: {len(state['cell_states'])}\nUse this rollback_id if you need to restore previous values."

    except Exception as e:
        logger.error(f"Error capturing rollback state: {e}")
        return f"ERROR: Failed to capture rollback state: {str(e)}"


@tool
def execute_rollback(
    rollback_id: Annotated[str, "Rollback ID from capture_rollback_state"]
) -> str:
    """
    Execute rollback to restore previous parameter values.

    Use this if a parameter modification caused issues and you need to
    restore the previous configuration.

    Args:
        rollback_id: Rollback ID from capture_rollback_state

    Returns:
        String with rollback results

    Example:
        execute_rollback("MSH-0112-Bindura Hospital_reference_signal_power_pdschcfg_20251103_143022")
        Returns: "Rollback completed: 6/6 cells restored"
    """
    try:
        manager = RollbackManager()
        result = manager.rollback(rollback_id)

        if result['success']:
            return f"SUCCESS: {result['summary']}"
        else:
            failed_cells = [r['cell_id'] for r in result['results'] if not r['success']]
            return f"PARTIAL SUCCESS: {result['summary']}\nFailed cells: {failed_cells}"

    except Exception as e:
        logger.error(f"Error executing rollback: {e}")
        return f"ERROR: Failed to execute rollback: {str(e)}"


@tool
def verify_rollback_success(
    rollback_id: Annotated[str, "Rollback ID to verify"]
) -> str:
    """
    Verify rollback was successful by querying current values.

    Use this after execute_rollback to confirm all cells were restored correctly.

    Args:
        rollback_id: Rollback ID to verify

    Returns:
        String with verification results
    """
    try:
        manager = RollbackManager()
        result = manager.verify_rollback(rollback_id)

        if result['verification_success']:
            return f"SUCCESS: {result['summary']}\nAll cells restored correctly."
        else:
            mismatches = [r for r in result['results'] if not r['verified']]
            return f"VERIFICATION FAILED: {result['summary']}\nMismatches: {mismatches}"

    except Exception as e:
        logger.error(f"Error verifying rollback: {e}")
        return f"ERROR: Failed to verify rollback: {str(e)}"


@tool
def list_available_rollbacks(
    site_name: Annotated[Optional[str], "Optional site name filter"] = None
) -> str:
    """
    List available rollback states.

    Use this to see what rollbacks are available for a site.

    Args:
        site_name: Optional site name to filter results

    Returns:
        String with list of available rollbacks
    """
    try:
        manager = RollbackManager()
        rollbacks = manager.list_rollbacks(site_name)

        if not rollbacks:
            return "No rollback states found"

        result = f"Found {len(rollbacks)} rollback states:\n\n"
        for rb in rollbacks:
            result += f"- {rb['rollback_id']}\n"
            result += f"  Site: {rb['site_name']}\n"
            result += f"  Parameter: {rb['parameter_name']}\n"
            result += f"  Status: {rb['status']}\n"
            result += f"  Cells: {rb['cell_count']}\n"
            result += f"  Created: {rb['timestamp']}\n\n"

        return result

    except Exception as e:
        logger.error(f"Error listing rollbacks: {e}")
        return f"ERROR: Failed to list rollbacks: {str(e)}"


    # ========================================================================
    # AUTO-ROLLBACK MONITORING (PRODUCTION FEATURE)
    # ========================================================================

    async def monitor_and_rollback(self,
                                   site_name: str,
                                   cell_id: int,
                                   optimization_id: int,
                                   monitoring_duration: int = 15,
                                   rollback_threshold: float = -3.0) -> Dict[str, Any]:
        """
        Monitor KPIs after optimization and auto-rollback if degradation detected.

        This function implements the auto-rollback feature for production mode:
        1. Wait for monitoring_duration minutes after optimization
        2. Query current KPIs and calculate weighted score
        3. Compare with baseline (weighted_score_before)
        4. If degradation > threshold: Trigger automatic rollback
        5. Log rollback reason and update optimization_history

        Args:
            site_name: Site identifier
            cell_id: Cell ID
            optimization_id: ID from optimization_history table
            monitoring_duration: Minutes to monitor before decision (default: 15)
            rollback_threshold: Negative delta threshold to trigger rollback (default: -3.0)

        Returns:
            {
                "rollback_triggered": bool,
                "reason": str,
                "kpi_delta": float,
                "baseline_score": float,
                "current_score": float
            }
        """
        import asyncio
        import sqlite3

        logger.info(f"Starting post-optimization monitoring for {site_name} cell {cell_id}")
        logger.info(f"Monitoring duration: {monitoring_duration} minutes, Threshold: {rollback_threshold}%")

        # Step 1: Get baseline KPI (before optimization)
        baseline = self._get_optimization_baseline(optimization_id)
        if not baseline:
            logger.error(f"Cannot find optimization record {optimization_id}")
            return {
                "rollback_triggered": False,
                "reason": "Baseline not found",
                "kpi_delta": 0.0
            }

        baseline_score = baseline['weighted_score_before']
        logger.info(f"Baseline weighted score: {baseline_score:.2f}")

        # Step 2: Wait for monitoring duration
        logger.info(f"Waiting {monitoring_duration} minutes before checking KPIs...")
        await asyncio.sleep(monitoring_duration * 60)

        # Step 3: Fetch current KPIs
        try:
            from tools.sql_tools import get_latest_kpis_direct
            from tools.calculation_tools import calc_weighted_kpi_score

            current_kpis = get_latest_kpis_direct(site_name, cell_id)
            if not current_kpis:
                logger.warning("Cannot fetch current KPIs - monitoring failed")
                return {
                    "rollback_triggered": False,
                    "reason": "Current KPIs unavailable",
                    "kpi_delta": 0.0
                }

            # Calculate current weighted score
            current_score = calc_weighted_kpi_score.invoke({"kpis": current_kpis})
            if isinstance(current_score, str):
                # Parse score from string response
                import re
                match = re.search(r'Weighted Score:\s*(\d+\.?\d*)', current_score)
                if match:
                    current_score = float(match.group(1))
                else:
                    logger.error("Failed to parse weighted score")
                    return {
                        "rollback_triggered": False,
                        "reason": "Score parsing failed",
                        "kpi_delta": 0.0
                    }

            logger.info(f"Current weighted score: {current_score:.2f}")

            # Step 4: Check for degradation
            kpi_delta = current_score - baseline_score
            logger.info(f"KPI delta: {kpi_delta:+.2f}%")

            if kpi_delta < rollback_threshold:
                # Trigger rollback
                logger.warning(f"🔴 ROLLBACK TRIGGERED: KPI degradation {kpi_delta:.2f}% exceeds threshold {rollback_threshold}%")

                # Execute rollback
                rollback_result = await self._execute_automatic_rollback(
                    optimization_id=optimization_id,
                    reason=f"Automatic rollback due to KPI degradation: {kpi_delta:.2f}% (threshold: {rollback_threshold}%)"
                )

                return {
                    "rollback_triggered": True,
                    "reason": f"KPI degradation detected: {kpi_delta:.2f}%",
                    "kpi_delta": kpi_delta,
                    "baseline_score": baseline_score,
                    "current_score": current_score,
                    "rollback_success": rollback_result['success']
                }
            else:
                logger.info(f"✅ KPIs stable - no rollback needed (delta: {kpi_delta:+.2f}%)")
                return {
                    "rollback_triggered": False,
                    "reason": "KPIs stable or improved",
                    "kpi_delta": kpi_delta,
                    "baseline_score": baseline_score,
                    "current_score": current_score
                }

        except Exception as e:
            logger.error(f"Error during monitoring: {e}")
            return {
                "rollback_triggered": False,
                "reason": f"Monitoring error: {str(e)}",
                "kpi_delta": 0.0
            }


    def _get_optimization_baseline(self, optimization_id: int) -> Optional[Dict]:
        """Retrieve baseline KPIs from optimization_history."""
        import sqlite3

        try:
            # Determine database path
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "data", "lz_network.db")

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT site_name, cell_id, weighted_score_before, kpi_before, parameters_changed
                FROM optimization_history
                WHERE id = ?
            """, (optimization_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return {
                "site_name": row[0],
                "cell_id": row[1],
                "weighted_score_before": row[2],
                "kpi_before": json.loads(row[3]) if row[3] else {},
                "parameters_changed": json.loads(row[4]) if row[4] else {}
            }

        except Exception as e:
            logger.error(f"Error retrieving optimization baseline: {e}")
            return None


    async def _execute_automatic_rollback(self, optimization_id: int, reason: str) -> Dict[str, Any]:
        """Execute automatic rollback and update database."""
        import sqlite3

        try:
            # Get optimization details
            baseline = self._get_optimization_baseline(optimization_id)
            if not baseline:
                return {"success": False, "error": "Baseline not found"}

            site_name = baseline["site_name"]
            parameters_changed = baseline["parameters_changed"]

            logger.info(f"Executing automatic rollback for optimization {optimization_id}")
            logger.info(f"Reverting parameters: {list(parameters_changed.keys())}")

            # Execute rollback for each changed parameter
            rollback_success = True
            for param_name, param_info in parameters_changed.items():
                original_value = param_info.get("old_value")
                if original_value is None:
                    logger.warning(f"No original value for {param_name}, skipping")
                    continue

                # Build rollback_id
                rollback_id = f"{site_name}_{param_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                # Execute rollback
                result = execute_rollback.invoke({"rollback_id": rollback_id})

                if "ERROR" in result:
                    logger.error(f"Rollback failed for {param_name}: {result}")
                    rollback_success = False
                else:
                    logger.info(f"✅ Rolled back {param_name} to {original_value}")

            # Update optimization_history
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "data", "lz_network.db")

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE optimization_history
                SET rolled_back = 1,
                    rollback_reason = ?,
                    rollback_timestamp = ?
                WHERE id = ?
            """, (reason, datetime.now().isoformat(), optimization_id))

            conn.commit()
            conn.close()

            logger.info(f"Updated optimization_history: optimization {optimization_id} marked as rolled back")

            return {
                "success": rollback_success,
                "optimization_id": optimization_id,
                "reason": reason
            }

        except Exception as e:
            logger.error(f"Error executing automatic rollback: {e}")
            return {"success": False, "error": str(e)}


# ============================================================================
# Tool List for Agent Registration
# ============================================================================

ROLLBACK_TOOLS = [
    capture_rollback_state,
    execute_rollback,
    verify_rollback_success,
    list_available_rollbacks
]


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Capture state
    manager = RollbackManager()

    print("Testing RollbackManager...")
    print("Note: This requires active Huawei API connection")

    # Example workflow
    print("\n1. Capture state before modification")
    print("   result = capture_rollback_state.invoke({")
    print("       'parameter_name': 'reference_signal_power_pdschcfg',")
    print("       'site_name': 'MSH-0112-Bindura Hospital'")
    print("   })")

    print("\n2. Make modifications (using modify_huawei_parameter_site)")

    print("\n3. If issues occur, execute rollback")
    print("   result = execute_rollback.invoke({")
    print("       'rollback_id': 'MSH-0112-Bindura Hospital_reference_signal_power_pdschcfg_20251103_143022'")
    print("   })")

    print("\n4. Verify rollback success")
    print("   result = verify_rollback_success.invoke({")
    print("       'rollback_id': 'MSH-0112-Bindura Hospital_reference_signal_power_pdschcfg_20251103_143022'")
    print("   })")
