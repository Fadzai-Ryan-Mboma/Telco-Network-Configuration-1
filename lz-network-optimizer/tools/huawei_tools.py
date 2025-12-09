"""
Liquid Zimbabwe 4G Network Optimizer - Huawei API Tools (Updated for Phase 5)
Purpose: LangChain tools for interacting with Huawei iMaster MAE API
Updated: 2025-11-03 - Phase 5 cell-by-cell modifications support

These tools allow agents to query and modify Huawei 4G parameters via MML commands.

CRITICAL UPDATES (Phase 5):
- All tools now require site_name parameter
- New tool: modify_huawei_parameter_site() for batch cell modifications
- API calls updated to include neNames (site name list)
"""

from langchain_core.tools import tool
from typing import Dict, Any, Optional, Annotated, List
import sys
import os
import logging
import yaml

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.mml_commands import (
    build_query_command,
    build_modify_command,
    build_modify_command_template,
    validate_command_syntax,
    format_command_response,
    build_query_all_cells,
    is_global_query
)
from domain.liquid_zimbabwe_parameters import PARAMETERS
from network.huawei_api_client import HuaweiAPIClient

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# TOOL 1: query_huawei_parameter (UPDATED - added site_name)
# ============================================================================

@tool
def query_huawei_parameter(
    parameter_name: Annotated[str, "The name of the parameter to query (e.g., 'reference_signal_power_pdschcfg')"],
    site_name: Annotated[str, "The site name (e.g., 'MSH-0112-Bindura Hospital')"],
    cell_id: Annotated[int, "The cell ID to query (1-6, default: 1)"] = 1
) -> str:
    """
    Query the current value of a Huawei 4G parameter via MML command.

    This tool queries the live Huawei iMaster MAE API to get the current value
    of a specific parameter for a cell at a site. If the API is unavailable,
    it returns an error message.

    UPDATED: Now requires site_name parameter for API neNames field.

    Available parameters:
    - reference_signal_power_pdschcfg: Reference signal power configuration
    - a3_event_offset: A3 handover event offset
    - t310_timer: Radio link failure detection timer
    - p0_nominal_pusch: Uplink power control parameter
    - pdcch_aggregation_level: Control channel aggregation level

    Args:
        parameter_name: Name of parameter to query
        site_name: Target site name
        cell_id: Cell ID (1-6, default: 1)

    Returns:
        String containing current parameter value or error message

    Example:
        query_huawei_parameter("reference_signal_power_pdschcfg",
                              "MSH-0112-Bindura Hospital", 1)
        Returns: "Current value of reference_signal_power_pdschcfg for cell 1: -200 (0.1 dBm units)"
    """
    try:
        # Validate parameter name
        if parameter_name not in PARAMETERS:
            available = ", ".join(PARAMETERS.keys())
            return f"ERROR: Unknown parameter '{parameter_name}'. Available parameters: {available}"

        # Build MML query command
        mml_command = build_query_command(parameter_name, cell_id)
        logger.info(f"Querying {parameter_name} for {site_name} cell {cell_id}: {mml_command}")

        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check if in offline/test mode
        if config.get('system', {}).get('offline_mode', False):
            param_info = PARAMETERS[parameter_name]
            default_value = param_info.get('default', 'N/A')
            return f"[OFFLINE MODE] Current value of {parameter_name} for {site_name} cell {cell_id}: {default_value} (using default value)"

        # Initialize Huawei API client
        try:
            api_config = {
                'base_url': os.getenv('HUAWEI_API_URL'),
                'username': os.getenv('HUAWEI_USERNAME'),
                'password': os.getenv('HUAWEI_PASSWORD'),
                'timeout': 10,
                'retry_attempts': 2,
                'retry_delay': 3,
                'ssl_verify': False
            }
            client = HuaweiAPIClient(api_config)

            # Connect to API
            if not client.connect():
                return f"ERROR: Failed to authenticate with Huawei API"

            # Execute MML command with site_name
            response = client.execute_mml_command(mml_command, [site_name])

            # Parse response
            parsed = format_command_response(response, parameter_name)

            if parsed['success'] and parsed['value']:
                param_info = PARAMETERS[parameter_name]
                units = param_info.get('units', '')
                return f"Current value of {parameter_name} for {site_name} cell {cell_id}: {parsed['value']} {units}"
            else:
                error_msg = parsed.get('error', 'Unknown error')
                return f"ERROR: Failed to query {parameter_name}: {error_msg}\nRaw response: {response}"

        except Exception as api_error:
            logger.warning(f"Huawei API error: {api_error}. Falling back to database.")
            return f"ERROR: Huawei API unavailable ({str(api_error)}). Use execute_lz_kpi_sql to query historical data instead."

    except Exception as e:
        logger.error(f"Error querying parameter: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# TOOL 1b: query_huawei_parameter_site (NEW - query all cells at once)
# ============================================================================

@tool
def query_huawei_parameter_site(
    parameter_name: Annotated[str, "The name of the parameter to query (e.g., 'reference_signal_power_pdschcfg')"],
    site_name: Annotated[str, "The site name (e.g., 'MSH-0112-Bindura Hospital')"]
) -> str:
    """
    Query the current value of a Huawei 4G parameter for ALL cells at a site.

    This tool queries the live Huawei iMaster MAE API to get the current value
    of a specific parameter for all 6 cells at a site. For global parameters
    (like a3_event_offset, t310_timer), it executes one query. For cell-specific
    parameters, it queries all 6 cells.

    Available parameters:
    - reference_signal_power_pdschcfg: Reference signal power configuration (cell-specific)
    - a3_event_offset: A3 handover event offset (global)
    - t310_timer: Radio link failure detection timer (global)
    - p0_nominal_pusch: Uplink power control parameter (cell-specific)
    - pdcch_aggregation_level: Control channel aggregation level (cell-specific)

    Args:
        parameter_name: Name of parameter to query
        site_name: Target site name

    Returns:
        String containing current parameter values for all cells or error message

    Example:
        query_huawei_parameter_site("reference_signal_power_pdschcfg", "MSH-0014-Chipadze")
        Returns: "Parameter reference_signal_power_pdschcfg for MSH-0014-Chipadze:
                  Cell 1: 49, Cell 2: 49, Cell 3: 49, Cell 4: 57, Cell 5: 57, Cell 6: 57"
    """
    try:
        # Validate parameter name
        if parameter_name not in PARAMETERS:
            available = ", ".join(PARAMETERS.keys())
            return f"ERROR: Unknown parameter '{parameter_name}'. Available parameters: {available}"

        # Build MML query commands for all cells
        cell_ids = [1, 2, 3, 4, 5, 6]
        commands = build_query_all_cells(parameter_name, cell_ids=cell_ids)
        is_global = is_global_query(parameter_name)
        
        logger.info(f"Querying {parameter_name} for {site_name} ({'global' if is_global else '6 cells'})")

        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check if in offline/test mode
        if config.get('system', {}).get('offline_mode', False):
            param_info = PARAMETERS[parameter_name]
            default_value = param_info.get('default', 'N/A')
            return f"[OFFLINE MODE] Parameter {parameter_name} for {site_name}: {default_value} (using default value for all cells)"

        # Initialize Huawei API client
        try:
            api_config = {
                'base_url': os.getenv('HUAWEI_API_URL'),
                'username': os.getenv('HUAWEI_USERNAME'),
                'password': os.getenv('HUAWEI_PASSWORD'),
                'timeout': 30,
                'retry_attempts': 2,
                'retry_delay': 3,
                'ssl_verify': False
            }
            client = HuaweiAPIClient(api_config)

            # Connect to API
            if not client.connect():
                return f"ERROR: Failed to authenticate with Huawei API"

            results = {}
            errors = []
            
            # For global queries, there's only 1 command; for cell-specific, 6 commands
            for i, mml_command in enumerate(commands):
                cell_id = 0 if is_global else cell_ids[i]
                
                # Execute MML command with site_name
                response = client.execute_mml_command(mml_command, [site_name])

                # Parse response
                parsed = format_command_response(response, parameter_name)

                if parsed['success'] and parsed['value']:
                    results[cell_id] = parsed['value']
                else:
                    error_msg = parsed.get('error', 'Unknown error')
                    errors.append(f"Cell {cell_id}: {error_msg}")

            # Format output
            param_info = PARAMETERS[parameter_name]
            units = param_info.get('units', '')
            
            if results:
                if is_global:
                    # Global query - just one value
                    value = list(results.values())[0]
                    result_str = f"Parameter {parameter_name} for {site_name}: {value} {units} (global)"
                else:
                    # Cell-specific - list all values
                    values = [f"Cell {cell_id}: {value}" for cell_id, value in sorted(results.items())]
                    result_str = f"Parameter {parameter_name} for {site_name}:\n  " + "\n  ".join(values)
                    if units:
                        result_str += f"\n  Units: {units}"
                
                if errors:
                    result_str += f"\n  Errors: {', '.join(errors)}"
                
                return result_str
            else:
                return f"ERROR: Failed to query {parameter_name} for all cells. Errors: {', '.join(errors)}"

        except Exception as api_error:
            logger.warning(f"Huawei API error: {api_error}.")
            return f"ERROR: Huawei API unavailable ({str(api_error)}). Use execute_lz_kpi_sql to query historical data instead."

    except Exception as e:
        logger.error(f"Error querying parameter site: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# TOOL 2: modify_huawei_parameter (UPDATED - added site_name)
# ============================================================================

@tool
def modify_huawei_parameter(
    parameter_name: Annotated[str, "The name of the parameter to modify"],
    new_value: Annotated[float, "The new value to set"],
    site_name: Annotated[str, "The site name (e.g., 'MSH-0112-Bindura Hospital')"],
    cell_id: Annotated[int, "The cell ID to modify (1-6, default: 1)"] = 1,
    reason: Annotated[str, "Reason for the change"] = "Agent optimization"
) -> str:
    """
    Modify a Huawei 4G parameter for a SINGLE CELL via MML command.

    IMPORTANT: This modifies ONE cell only. For site-wide changes across all 6 cells,
    use modify_huawei_parameter_site() instead.

    This tool sends an MML modify command to the Huawei iMaster MAE API to change
    a parameter value. It validates the new value is within acceptable range before
    sending the command.

    CRITICAL: Parameter modifications require:
    - LOCALCELLID specified (cell-specific)
    - Site name in neNames (e.g., "MSH-0112-Bindura Hospital")

    Args:
        parameter_name: Name of parameter to modify
        new_value: New value to set
        site_name: Target site name
        cell_id: Cell ID (1-6, default: 1)
        reason: Reason for the change (for logging)

    Returns:
        String containing success/failure message

    Example:
        modify_huawei_parameter("reference_signal_power_pdschcfg", -180,
                               "MSH-0112-Bindura Hospital", 1, "Improve coverage")
        Returns: "SUCCESS: Modified reference_signal_power_pdschcfg for cell 1 to -180"
    """
    try:
        # Validate parameter name
        if parameter_name not in PARAMETERS:
            available = ", ".join(PARAMETERS.keys())
            return f"ERROR: Unknown parameter '{parameter_name}'. Available parameters: {available}"

        param_info = PARAMETERS[parameter_name]

        # Validate value is within range
        param_range = param_info.get('range', (None, None))
        if param_range[0] is not None and new_value < param_range[0]:
            return f"ERROR: Value {new_value} is below minimum {param_range[0]} for {parameter_name}"
        if param_range[1] is not None and new_value > param_range[1]:
            return f"ERROR: Value {new_value} is above maximum {param_range[1]} for {parameter_name}"

        # Build MML modify command
        mml_command = build_modify_command(parameter_name, new_value, cell_id)
        logger.info(f"Modifying {parameter_name} for {site_name} cell {cell_id} to {new_value}: {mml_command}")
        logger.info(f"Reason: {reason}")

        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check if in dry-run mode
        if config.get('agents', {}).get('mml_executor', {}).get('dry_run', False):
            return f"[DRY RUN] Would modify {parameter_name} for {site_name} cell {cell_id} to {new_value}. Command: {mml_command}"

        # Check if in offline/test mode
        if config.get('system', {}).get('offline_mode', False):
            return f"[OFFLINE MODE] Cannot modify parameters in offline mode. Would execute: {mml_command}"

        # Initialize Huawei API client
        try:
            api_config = {
                'base_url': os.getenv('HUAWEI_API_URL'),
                'username': os.getenv('HUAWEI_USERNAME'),
                'password': os.getenv('HUAWEI_PASSWORD'),
                'timeout': 30,
                'retry_attempts': 2,
                'retry_delay': 3,
                'ssl_verify': False
            }
            client = HuaweiAPIClient(api_config)

            # Connect to API
            if not client.connect():
                return f"ERROR: Failed to authenticate with Huawei API"

            # Execute MML command with site_name
            response = client.execute_mml_command(mml_command, [site_name])

            # Check for success
            response_str = str(response)
            if "SUCCEED" in response_str.upper() or "SUCCESS" in response_str.upper() or "RETCODE = 0" in response_str:
                return f"SUCCESS: Modified {parameter_name} for {site_name} cell {cell_id} to {new_value}. Response: {response_str[:200]}"
            else:
                return f"FAILURE: Failed to modify {parameter_name}. Response: {response_str[:500]}"

        except Exception as api_error:
            logger.error(f"Huawei API error: {api_error}")
            return f"ERROR: Huawei API unavailable ({str(api_error)}). Cannot modify parameter."

    except Exception as e:
        logger.error(f"Error modifying parameter: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# TOOL 3: modify_huawei_parameter_site (NEW - batch cell modifications)
# ============================================================================

@tool
def modify_huawei_parameter_site(
    parameter_name: Annotated[str, "The name of the parameter to modify"],
    new_value: Annotated[float, "The new value to set"],
    site_name: Annotated[str, "The site name (e.g., 'MSH-0112-Bindura Hospital')"],
    cell_ids: Annotated[Optional[List[int]], "List of cell IDs (default: [1,2,3,4,5,6])"] = None,
    reason: Annotated[str, "Reason for the change"] = "Agent optimization"
) -> str:
    """
    Modify a Huawei 4G parameter across ALL CELLS at a site.

    CRITICAL: This executes 6 separate MML commands (one per cell) to modify
    the parameter at all cells of a site. This is required by Huawei API -
    parameter modifications must be done cell-by-cell.

    Use this tool when you want to apply the same parameter change to all cells
    at a site (typical for site-wide optimizations).

    Args:
        parameter_name: Name of parameter to modify
        new_value: New value to set
        site_name: Target site name
        cell_ids: List of cell IDs to modify (default: [1,2,3,4,5,6])
        reason: Reason for the change (for logging)

    Returns:
        String containing batch execution summary

    Example:
        modify_huawei_parameter_site("reference_signal_power_pdschcfg", -180,
                                    "MSH-0112-Bindura Hospital",
                                    reason="Improve coverage")
        Returns: "SUCCESS: Modified reference_signal_power_pdschcfg on 6/6 cells at MSH-0112-Bindura Hospital"
    """
    try:
        # Validate parameter name
        if parameter_name not in PARAMETERS:
            available = ", ".join(PARAMETERS.keys())
            return f"ERROR: Unknown parameter '{parameter_name}'. Available parameters: {available}"

        param_info = PARAMETERS[parameter_name]

        # Validate value is within range
        param_range = param_info.get('range', (None, None))
        if param_range[0] is not None and new_value < param_range[0]:
            return f"ERROR: Value {new_value} is below minimum {param_range[0]} for {parameter_name}"
        if param_range[1] is not None and new_value > param_range[1]:
            return f"ERROR: Value {new_value} is above maximum {param_range[1]} for {parameter_name}"

        # Default cell IDs for standard 6-cell site
        if cell_ids is None:
            cell_ids = [1, 2, 3, 4, 5, 6]

        logger.info(f"Modifying {parameter_name} for {site_name} across {len(cell_ids)} cells to {new_value}")
        logger.info(f"Reason: {reason}")

        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check if in dry-run mode
        if config.get('agents', {}).get('mml_executor', {}).get('dry_run', False):
            commands_preview = "\n".join([
                build_modify_command(parameter_name, new_value, cid)
                for cid in cell_ids[:3]  # Show first 3
            ])
            return f"[DRY RUN] Would modify {parameter_name} for {len(cell_ids)} cells at {site_name} to {new_value}\nSample commands:\n{commands_preview}\n... ({len(cell_ids)-3} more commands)"

        # Check if in offline/test mode
        if config.get('system', {}).get('offline_mode', False):
            return f"[OFFLINE MODE] Cannot modify parameters in offline mode. Would execute {len(cell_ids)} commands for {site_name}"

        # Initialize Huawei API client
        try:
            api_config = {
                'base_url': os.getenv('HUAWEI_API_URL'),
                'username': os.getenv('HUAWEI_USERNAME'),
                'password': os.getenv('HUAWEI_PASSWORD'),
                'timeout': 30,
                'retry_attempts': 2,
                'retry_delay': 3,
                'ssl_verify': False
            }
            client = HuaweiAPIClient(api_config)

            # Connect to API
            if not client.connect():
                return f"ERROR: Failed to authenticate with Huawei API"

            # Build command template
            command_template = build_modify_command_template(parameter_name, new_value)

            # Execute batch modification
            results = client.execute_mml_command_batch(
                command_template,
                site_name,
                cell_ids
            )

            # Analyze results
            successful = sum(1 for r in results if r.get('success', False))
            failed = len(results) - successful

            if successful == len(cell_ids):
                return f"SUCCESS: Modified {parameter_name} on {successful}/{len(cell_ids)} cells at {site_name} to {new_value}"
            elif successful > 0:
                failed_cells = [r['cell_id'] for r in results if not r.get('success', False)]
                return f"PARTIAL SUCCESS: Modified {parameter_name} on {successful}/{len(cell_ids)} cells at {site_name}. Failed cells: {failed_cells}"
            else:
                return f"FAILURE: Failed to modify {parameter_name} on all {len(cell_ids)} cells at {site_name}"

        except Exception as api_error:
            logger.error(f"Huawei API error: {api_error}")
            return f"ERROR: Huawei API unavailable ({str(api_error)}). Cannot modify parameters."

    except Exception as e:
        logger.error(f"Error in batch modification: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# TOOL 4: execute_mml_command (UPDATED - added site_name)
# ============================================================================

@tool
def execute_mml_command(
    mml_command: Annotated[str, "The MML command to execute (must end with semicolon)"],
    site_name: Annotated[str, "The site name (e.g., 'MSH-0112-Bindura Hospital')"]
) -> str:
    """
    Execute an arbitrary MML command on Huawei iMaster MAE API.

    This is a low-level tool for executing any MML command. Use the specialized
    tools (query_huawei_parameter, modify_huawei_parameter) when possible.

    IMPORTANT: This tool can execute any MML command. Use with caution.
    UPDATED: Now requires site_name parameter for API neNames field.

    Args:
        mml_command: Complete MML command string (e.g., "LST CELL: LOCALCELLID=1;")
        site_name: Target site name

    Returns:
        String containing raw MML response

    Example:
        execute_mml_command("LST CELL: LOCALCELLID=1;", "MSH-0112-Bindura Hospital")
        Returns: Raw MML response from Huawei API
    """
    try:
        # Validate command syntax
        if not validate_command_syntax(mml_command):
            return f"ERROR: Invalid MML command syntax. Command must start with MML keyword (LST, MOD, etc.) and end with semicolon."

        logger.info(f"Executing MML command on {site_name}: {mml_command}")

        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check if in offline/test mode
        if config.get('system', {}).get('offline_mode', False):
            return f"[OFFLINE MODE] Cannot execute MML commands in offline mode. Would execute on {site_name}: {mml_command}"

        # Initialize Huawei API client
        try:
            api_config = {
                'base_url': os.getenv('HUAWEI_API_URL'),
                'username': os.getenv('HUAWEI_USERNAME'),
                'password': os.getenv('HUAWEI_PASSWORD'),
                'timeout': 30,
                'retry_attempts': 2,
                'retry_delay': 3,
                'ssl_verify': False
            }
            client = HuaweiAPIClient(api_config)

            # Connect to API
            if not client.connect():
                return f"ERROR: Failed to authenticate with Huawei API"

            # Execute MML command with site_name
            response = client.execute_mml_command(mml_command, [site_name])
            return f"MML Response from {site_name}:\n{response}"

        except Exception as api_error:
            logger.error(f"Huawei API error: {api_error}")
            return f"ERROR: Huawei API unavailable ({str(api_error)})"

    except Exception as e:
        logger.error(f"Error executing MML command: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# TOOL 5: query_huawei_kpi (already has site_name - minor update)
# ============================================================================

@tool
def query_huawei_kpi(
    site_name: Annotated[str, "The site/eNodeB name to query"],
    cell_id: Annotated[int, "The cell ID to query (1-6)"] = 1
) -> str:
    """
    Query live KPI data from Huawei iMaster MAE API.

    This tool fetches current KPI measurements (throughput, IBLER, RACH success, etc.)
    from the Huawei API. If the API is unavailable, it falls back to historical data.

    KPIs returned:
    - Network Access Success (RACH Setup Success Rate)
    - Download Speed (DL PDCP Throughput)
    - Download Quality (100 - DL IBLER)
    - Upload Speed (UL PDCP Throughput)
    - Upload Quality (100 - UL IBLER)
    - Control Channel Load (PDCCH CCE Usage)
    - Feedback Channel Load (PUCCH Usage)

    Args:
        site_name: Site/eNodeB name (e.g., "MSH-0112-Bindura Hospital")
        cell_id: Cell ID (1-6, default: 1)

    Returns:
        String containing current KPI values or error message

    Example:
        query_huawei_kpi("MSH-0112-Bindura Hospital", 1)
        Returns: "KPI data for MSH-0112-Bindura Hospital (cell 1):..."
    """
    try:
        logger.info(f"Querying KPIs for site {site_name}, cell {cell_id}")

        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check if in offline/test mode - use database
        if config.get('system', {}).get('offline_mode', False):
            return f"[OFFLINE MODE] Use execute_lz_kpi_sql tool to query KPIs from historical database for site '{site_name}'"

        # Try to query from Huawei API
        try:
            api_config = {
                'base_url': os.getenv('HUAWEI_API_URL'),
                'username': os.getenv('HUAWEI_USERNAME'),
                'password': os.getenv('HUAWEI_PASSWORD'),
                'timeout': 10,
                'retry_attempts': 2,
                'retry_delay': 3,
                'ssl_verify': False
            }
            client = HuaweiAPIClient(api_config)

            # Connect to API
            if not client.connect():
                return f"[API UNAVAILABLE] Use execute_lz_kpi_sql tool to query KPIs from historical database for site '{site_name}'"

            # Query KPI counters via MML
            mml_command = f"LST PMDATA: OBJECTTYPE=CELL, LOCALCELLID={cell_id};"
            response = client.execute_mml_command(mml_command, [site_name])

            # Parse response (simplified - would need proper parsing)
            response_str = str(response)
            if "SUCCEED" in response_str.upper() or "SUCCESS" in response_str.upper() or "RETCODE = 0" in response_str:
                return f"KPI data for {site_name} (cell {cell_id}):\n{response_str[:1000]}"
            else:
                return f"ERROR: Failed to query KPIs. Response: {response_str[:500]}"

        except Exception as api_error:
            logger.warning(f"Huawei API error: {api_error}. Falling back to database.")
            return f"[API UNAVAILABLE] Use execute_lz_kpi_sql tool to query KPIs from historical database for site '{site_name}'"

    except Exception as e:
        logger.error(f"Error querying KPIs: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# TOOL 6: validate_parameter_range (unchanged)
# ============================================================================

@tool
def validate_parameter_range(
    parameter_name: Annotated[str, "The name of the parameter to validate"],
    proposed_value: Annotated[float, "The proposed new value"]
) -> str:
    """
    Validate if a proposed parameter value is within acceptable range.

    This tool checks if a proposed parameter change is safe by verifying:
    1. Parameter exists and is recognized
    2. Value is within defined min/max range
    3. Value follows parameter-specific constraints (e.g., aggregation levels)

    Use this tool BEFORE calling modify_huawei_parameter to ensure safety.

    Args:
        parameter_name: Name of parameter to validate
        proposed_value: Proposed new value

    Returns:
        String containing validation result (VALID or INVALID with reason)

    Example:
        validate_parameter_range("reference_signal_power_pdschcfg", -180)
        Returns: "VALID: Value -180 is within acceptable range [-600, 500]..."
    """
    try:
        # Check if parameter exists
        if parameter_name not in PARAMETERS:
            available = ", ".join(PARAMETERS.keys())
            return f"INVALID: Unknown parameter '{parameter_name}'. Available parameters: {available}"

        param_info = PARAMETERS[parameter_name]
        param_range = param_info.get('range', (None, None))

        # Check if range is defined
        if param_range[0] is None and param_range[1] is None:
            return f"WARNING: No range defined for {parameter_name}. Cannot validate value {proposed_value}"

        # Validate against range
        if param_range[0] is not None and proposed_value < param_range[0]:
            return f"INVALID: Value {proposed_value} is below minimum {param_range[0]} for {parameter_name}"

        if param_range[1] is not None and proposed_value > param_range[1]:
            return f"INVALID: Value {proposed_value} is above maximum {param_range[1]} for {parameter_name}"

        # Check for discrete values (e.g., aggregation levels)
        allowed_values = param_info.get('allowed_values')
        if allowed_values and proposed_value not in allowed_values:
            return f"INVALID: Value {proposed_value} not in allowed values {allowed_values} for {parameter_name}"

        # All checks passed
        units = param_info.get('units', '')
        default = param_info.get('default', 'N/A')

        result = f"VALID: Value {proposed_value} {units} is within acceptable range [{param_range[0]}, {param_range[1]}] for {parameter_name}\n"
        result += f"Current default: {default} {units}\n"

        # Add impact information
        impact = param_info.get('impact', [])
        if impact:
            result += f"Expected KPI impact: {', '.join(impact)}"

        return result

    except Exception as e:
        logger.error(f"Error validating parameter: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# Tool List for Agent Registration (UPDATED)
# ============================================================================

HUAWEI_TOOLS = [
    query_huawei_parameter,
    modify_huawei_parameter,
    modify_huawei_parameter_site,  # NEW
    execute_mml_command,
    query_huawei_kpi,
    validate_parameter_range
]


# ============================================================================
# Example Usage (for testing)
# ============================================================================

if __name__ == "__main__":
    # Example: Query parameter
    result = query_huawei_parameter.invoke({
        "parameter_name": "reference_signal_power_pdschcfg",
        "site_name": "MSH-0112-Bindura Hospital",
        "cell_id": 1
    })
    print("Query Result:", result)

    # Example: Validate value
    result = validate_parameter_range.invoke({
        "parameter_name": "reference_signal_power_pdschcfg",
        "proposed_value": -180
    })
    print("Validation Result:", result)

    # Example: Batch modification (dry-run mode recommended for testing)
    result = modify_huawei_parameter_site.invoke({
        "parameter_name": "reference_signal_power_pdschcfg",
        "new_value": -180,
        "site_name": "MSH-0112-Bindura Hospital",
        "reason": "Test batch modification"
    })
    print("Batch Modification Result:", result)
