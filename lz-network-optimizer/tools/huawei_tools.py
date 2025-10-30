"""
Liquid Zimbabwe 4G Network Optimizer - Huawei API Tools
Purpose: LangChain tools for interacting with Huawei iMaster MAE API
Created: 2025-10-30

These tools allow agents to query and modify Huawei 4G parameters via MML commands.
"""

from langchain_core.tools import tool
from typing import Dict, Any, Optional, Annotated
import sys
import os
import logging
import yaml

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.mml_commands import (
    build_query_command,
    build_modify_command,
    validate_command_syntax,
    format_command_response
)
from domain.liquid_zimbabwe_parameters import PARAMETERS
from network.huawei_api_client import HuaweiAPIClient

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# TOOL 1: query_huawei_parameter
# ============================================================================

@tool
def query_huawei_parameter(
    parameter_name: Annotated[str, "The name of the parameter to query (e.g., 'reference_signal_power_pdschcfg')"],
    cell_id: Annotated[int, "The cell ID to query (default: 1)"] = 1
) -> str:
    """
    Query the current value of a Huawei 4G parameter via MML command.

    This tool queries the live Huawei iMaster MAE API to get the current value
    of a specific parameter for a cell. If the API is unavailable, it returns
    an error message.

    Available parameters:
    - reference_signal_power_pdschcfg: Reference signal power configuration
    - a3_event_offset: A3 handover event offset
    - t310_timer: Radio link failure detection timer
    - p0_nominal_pusch: Uplink power control parameter
    - pdcch_aggregation_level: Control channel aggregation level

    Args:
        parameter_name: Name of parameter to query
        cell_id: Cell ID (default: 1)

    Returns:
        String containing current parameter value or error message

    Example:
        query_huawei_parameter("reference_signal_power_pdschcfg", 1)
        Returns: "Current value of reference_signal_power_pdschcfg for cell 1: -200 (0.1 dBm units)"
    """
    try:
        # Validate parameter name
        if parameter_name not in PARAMETERS:
            available = ", ".join(PARAMETERS.keys())
            return f"ERROR: Unknown parameter '{parameter_name}'. Available parameters: {available}"

        # Build MML query command
        mml_command = build_query_command(parameter_name, cell_id)
        logger.info(f"Querying parameter {parameter_name} for cell {cell_id}: {mml_command}")

        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check if in offline/test mode
        if config.get('system', {}).get('offline_mode', False):
            # Return mock data for offline mode
            param_info = PARAMETERS[parameter_name]
            default_value = param_info.get('default', 'N/A')
            return f"[OFFLINE MODE] Current value of {parameter_name} for cell {cell_id}: {default_value} (using default value)"

        # Initialize Huawei API client
        try:
            client = HuaweiAPIClient(
                base_url=os.getenv('HUAWEI_API_URL'),
                username=os.getenv('HUAWEI_USERNAME'),
                password=os.getenv('HUAWEI_PASSWORD')
            )

            # Execute MML command
            response = client.execute_mml_command(mml_command)

            # Parse response
            parsed = format_command_response(response, parameter_name)

            if parsed['success'] and parsed['value']:
                param_info = PARAMETERS[parameter_name]
                units = param_info.get('units', '')
                return f"Current value of {parameter_name} for cell {cell_id}: {parsed['value']} {units}"
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
# TOOL 2: modify_huawei_parameter
# ============================================================================

@tool
def modify_huawei_parameter(
    parameter_name: Annotated[str, "The name of the parameter to modify"],
    new_value: Annotated[float, "The new value to set"],
    cell_id: Annotated[int, "The cell ID to modify (default: 1)"] = 1,
    reason: Annotated[str, "Reason for the change"] = "Agent optimization"
) -> str:
    """
    Modify a Huawei 4G parameter via MML command.

    This tool sends an MML modify command to the Huawei iMaster MAE API to change
    a parameter value. It validates the new value is within acceptable range before
    sending the command.

    IMPORTANT: This tool makes real changes to the live network. Only use after
    validation and risk assessment.

    Args:
        parameter_name: Name of parameter to modify
        new_value: New value to set
        cell_id: Cell ID (default: 1)
        reason: Reason for the change (for logging)

    Returns:
        String containing success/failure message

    Example:
        modify_huawei_parameter("reference_signal_power_pdschcfg", -180, 1, "Improve coverage")
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
        logger.info(f"Modifying parameter {parameter_name} for cell {cell_id} to {new_value}: {mml_command}")
        logger.info(f"Reason: {reason}")

        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check if in dry-run mode
        if config.get('agents', {}).get('mml_executor', {}).get('dry_run', False):
            return f"[DRY RUN] Would modify {parameter_name} for cell {cell_id} to {new_value}. Command: {mml_command}"

        # Check if in offline/test mode
        if config.get('system', {}).get('offline_mode', False):
            return f"[OFFLINE MODE] Cannot modify parameters in offline mode. Would execute: {mml_command}"

        # Initialize Huawei API client
        try:
            client = HuaweiAPIClient(
                base_url=os.getenv('HUAWEI_API_URL'),
                username=os.getenv('HUAWEI_USERNAME'),
                password=os.getenv('HUAWEI_PASSWORD')
            )

            # Execute MML command
            response = client.execute_mml_command(mml_command)

            # Check for success
            if "SUCCEED" in response.upper() or "SUCCESS" in response.upper():
                # Log to database (would integrate with database tools)
                return f"SUCCESS: Modified {parameter_name} for cell {cell_id} to {new_value}. Response: {response}"
            else:
                return f"FAILURE: Failed to modify {parameter_name}. Response: {response}"

        except Exception as api_error:
            logger.error(f"Huawei API error: {api_error}")
            return f"ERROR: Huawei API unavailable ({str(api_error)}). Cannot modify parameter."

    except Exception as e:
        logger.error(f"Error modifying parameter: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# TOOL 3: execute_mml_command
# ============================================================================

@tool
def execute_mml_command(
    mml_command: Annotated[str, "The MML command to execute (must end with semicolon)"]
) -> str:
    """
    Execute an arbitrary MML command on Huawei iMaster MAE API.

    This is a low-level tool for executing any MML command. Use the specialized
    tools (query_huawei_parameter, modify_huawei_parameter) when possible.

    IMPORTANT: This tool can execute any MML command. Use with caution.

    Args:
        mml_command: Complete MML command string (e.g., "LST CELL;")

    Returns:
        String containing raw MML response

    Example:
        execute_mml_command("LST CELL: LOCALCELLID=1;")
        Returns: Raw MML response from Huawei API
    """
    try:
        # Validate command syntax
        if not validate_command_syntax(mml_command):
            return f"ERROR: Invalid MML command syntax. Command must start with MML keyword (LST, MOD, etc.) and end with semicolon."

        logger.info(f"Executing MML command: {mml_command}")

        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check if in offline/test mode
        if config.get('system', {}).get('offline_mode', False):
            return f"[OFFLINE MODE] Cannot execute MML commands in offline mode. Would execute: {mml_command}"

        # Initialize Huawei API client
        try:
            client = HuaweiAPIClient(
                base_url=os.getenv('HUAWEI_API_URL'),
                username=os.getenv('HUAWEI_USERNAME'),
                password=os.getenv('HUAWEI_PASSWORD')
            )

            # Execute MML command
            response = client.execute_mml_command(mml_command)
            return f"MML Response:\n{response}"

        except Exception as api_error:
            logger.error(f"Huawei API error: {api_error}")
            return f"ERROR: Huawei API unavailable ({str(api_error)})"

    except Exception as e:
        logger.error(f"Error executing MML command: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# TOOL 4: query_huawei_kpi
# ============================================================================

@tool
def query_huawei_kpi(
    site_name: Annotated[str, "The site/eNodeB name to query"],
    cell_id: Annotated[int, "The cell ID to query"] = 1
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
        site_name: Site/eNodeB name (e.g., "MSH0013-Bindura-Zaoga")
        cell_id: Cell ID (default: 1)

    Returns:
        String containing current KPI values or error message

    Example:
        query_huawei_kpi("MSH0013-Bindura-Zaoga", 1)
        Returns: "KPI data for MSH0013-Bindura-Zaoga (cell 1):..."
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
            client = HuaweiAPIClient(
                base_url=os.getenv('HUAWEI_API_URL'),
                username=os.getenv('HUAWEI_USERNAME'),
                password=os.getenv('HUAWEI_PASSWORD')
            )

            # Query KPI counters via MML
            mml_command = f"LST PMDATA: OBJECTTYPE=CELL, LOCALCELLID={cell_id};"
            response = client.execute_mml_command(mml_command)

            # Parse response (simplified - would need proper parsing)
            if "SUCCEED" in response.upper() or "SUCCESS" in response.upper():
                return f"KPI data for {site_name} (cell {cell_id}):\n{response}"
            else:
                return f"ERROR: Failed to query KPIs. Response: {response}"

        except Exception as api_error:
            logger.warning(f"Huawei API error: {api_error}. Falling back to database.")
            return f"[API UNAVAILABLE] Use execute_lz_kpi_sql tool to query KPIs from historical database for site '{site_name}'"

    except Exception as e:
        logger.error(f"Error querying KPIs: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# TOOL 5: validate_parameter_range
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
        Returns: "VALID: Value -180 is within acceptable range [-600, 500] for reference_signal_power_pdschcfg"
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
# Tool List for Agent Registration
# ============================================================================

HUAWEI_TOOLS = [
    query_huawei_parameter,
    modify_huawei_parameter,
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
        "cell_id": 1
    })
    print("Query Result:", result)

    # Example: Validate value
    result = validate_parameter_range.invoke({
        "parameter_name": "reference_signal_power_pdschcfg",
        "proposed_value": -180
    })
    print("Validation Result:", result)
