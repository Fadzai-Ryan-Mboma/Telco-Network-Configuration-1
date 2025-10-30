"""
Liquid Zimbabwe 4G Network Optimizer - MML Command Templates
Purpose: Huawei MML (Man-Machine Language) command templates for parameter queries and modifications
Created: 2025-10-30
"""

from typing import Dict, Any, Optional, List


# ============================================================================
# MML COMMAND TEMPLATES
# ============================================================================

MML_COMMANDS = {
    # ========================================================================
    # PDSCH Configuration (reference_signal_power_pdschcfg)
    # ========================================================================
    "reference_signal_power_pdschcfg": {
        "query": "LST PDSCHCFG: LOCALCELLID={cell_id};",
        "modify": "MOD PDSCHCFG: LOCALCELLID={cell_id}, REFERENCESIGNALPWR={value};",
        "parameter_field": "REFERENCESIGNALPWR",
        "description": "Query/Modify PDSCH Configuration - Reference Signal Power",
        "value_units": "0.1 dBm",
        "example_query": "LST PDSCHCFG: LOCALCELLID=1;",
        "example_modify": "MOD PDSCHCFG: LOCALCELLID=1, REFERENCESIGNALPWR=-200;"
    },

    # ========================================================================
    # A3 Event Configuration (a3_event_offset)
    # ========================================================================
    "a3_event_offset": {
        "query": "LST EUTRANMEASUREMENT: LOCALCELLID={cell_id}, EUTRANEVTID=3;",
        "modify": "MOD EUTRANMEASUREMENT: LOCALCELLID={cell_id}, EUTRANEVTID=3, A3OFFSET={value};",
        "parameter_field": "A3OFFSET",
        "description": "Query/Modify A3 Event Configuration - Handover Offset",
        "value_units": "dB",
        "example_query": "LST EUTRANMEASUREMENT: LOCALCELLID=1, EUTRANEVTID=3;",
        "example_modify": "MOD EUTRANMEASUREMENT: LOCALCELLID=1, EUTRANEVTID=3, A3OFFSET=3;"
    },

    # ========================================================================
    # T310 Timer Configuration (t310_timer)
    # ========================================================================
    "t310_timer": {
        "query": "LST CELLRADIORESALGO: LOCALCELLID={cell_id};",
        "modify": "MOD CELLRADIORESALGO: LOCALCELLID={cell_id}, T310={value};",
        "parameter_field": "T310",
        "description": "Query/Modify T310 Timer - Radio Link Failure Detection",
        "value_units": "ms",
        "example_query": "LST CELLRADIORESALGO: LOCALCELLID=1;",
        "example_modify": "MOD CELLRADIORESALGO: LOCALCELLID=1, T310=1000;"
    },

    # ========================================================================
    # P0 Nominal PUSCH Configuration (p0_nominal_pusch)
    # ========================================================================
    "p0_nominal_pusch": {
        "query": "LST CELLULPCPUSCH: LOCALCELLID={cell_id};",
        "modify": "MOD CELLULPCPUSCH: LOCALCELLID={cell_id}, P0NOMINALPUSCH={value};",
        "parameter_field": "P0NOMINALPUSCH",
        "description": "Query/Modify P0 Nominal PUSCH - Uplink Power Control",
        "value_units": "dBm",
        "example_query": "LST CELLULPCPUSCH: LOCALCELLID=1;",
        "example_modify": "MOD CELLULPCPUSCH: LOCALCELLID=1, P0NOMINALPUSCH=-90;"
    },

    # ========================================================================
    # PDCCH Aggregation Level Configuration (pdcch_aggregation_level)
    # ========================================================================
    "pdcch_aggregation_level": {
        "query": "LST CELLPDCCHALGO: LOCALCELLID={cell_id};",
        "modify": "MOD CELLPDCCHALGO: LOCALCELLID={cell_id}, PDCCHAGGLVL={value};",
        "parameter_field": "PDCCHAGGLVL",
        "description": "Query/Modify PDCCH Aggregation Level - Control Channel Resource Allocation",
        "value_units": "level (1, 2, 4, 8)",
        "example_query": "LST CELLPDCCHALGO: LOCALCELLID=1;",
        "example_modify": "MOD CELLPDCCHALGO: LOCALCELLID=1, PDCCHAGGLVL=4;"
    }
}


# ============================================================================
# GENERAL QUERY COMMANDS
# ============================================================================

GENERAL_COMMANDS = {
    # Cell information queries
    "query_cell_info": {
        "command": "LST CELL: LOCALCELLID={cell_id};",
        "description": "List cell basic information",
        "example": "LST CELL: LOCALCELLID=1;"
    },

    "query_all_cells": {
        "command": "LST CELL;",
        "description": "List all cells in eNodeB",
        "example": "LST CELL;"
    },

    # eNodeB information
    "query_enodeb_info": {
        "command": "DSP ENODEBFUNCTION;",
        "description": "Display eNodeB function information",
        "example": "DSP ENODEBFUNCTION;"
    },

    # Alarm queries
    "query_active_alarms": {
        "command": "DSP ALM;",
        "description": "Display active alarms",
        "example": "DSP ALM;"
    },

    # Performance counters
    "query_kpi_counters": {
        "command": "LST PMDATA: OBJECTTYPE=CELL, LOCALCELLID={cell_id};",
        "description": "List performance measurement data for cell",
        "example": "LST PMDATA: OBJECTTYPE=CELL, LOCALCELLID=1;"
    }
}


# ============================================================================
# MML COMMAND BUILDER FUNCTIONS
# ============================================================================

def build_query_command(parameter_name: str, cell_id: int = 1) -> str:
    """
    Build MML query command for a specific parameter.

    Args:
        parameter_name: Name of parameter (e.g., 'reference_signal_power_pdschcfg')
        cell_id: Cell ID (default: 1)

    Returns:
        MML query command string

    Raises:
        ValueError: If parameter_name is not recognized
    """
    if parameter_name not in MML_COMMANDS:
        raise ValueError(f"Unknown parameter: {parameter_name}. Available: {list(MML_COMMANDS.keys())}")

    template = MML_COMMANDS[parameter_name]["query"]
    return template.format(cell_id=cell_id)


def build_modify_command(parameter_name: str, value: Any, cell_id: int = 1) -> str:
    """
    Build MML modify command for a specific parameter.

    Args:
        parameter_name: Name of parameter
        value: New value for parameter
        cell_id: Cell ID (default: 1)

    Returns:
        MML modify command string

    Raises:
        ValueError: If parameter_name is not recognized
    """
    if parameter_name not in MML_COMMANDS:
        raise ValueError(f"Unknown parameter: {parameter_name}. Available: {list(MML_COMMANDS.keys())}")

    template = MML_COMMANDS[parameter_name]["modify"]
    return template.format(cell_id=cell_id, value=value)


def get_parameter_field_name(parameter_name: str) -> str:
    """
    Get the MML field name for a parameter.

    Args:
        parameter_name: Name of parameter

    Returns:
        MML field name (e.g., 'REFERENCESIGNALPWR')
    """
    if parameter_name not in MML_COMMANDS:
        raise ValueError(f"Unknown parameter: {parameter_name}")

    return MML_COMMANDS[parameter_name]["parameter_field"]


def get_command_info(parameter_name: str) -> Dict[str, Any]:
    """
    Get complete information about MML commands for a parameter.

    Args:
        parameter_name: Name of parameter

    Returns:
        Dictionary with command templates and metadata
    """
    if parameter_name not in MML_COMMANDS:
        raise ValueError(f"Unknown parameter: {parameter_name}")

    return MML_COMMANDS[parameter_name]


def validate_command_syntax(command: str) -> bool:
    """
    Basic validation of MML command syntax.

    Args:
        command: MML command string

    Returns:
        True if command appears syntactically valid
    """
    # Basic checks
    command = command.strip()

    if not command:
        return False

    # Must start with MML keyword
    valid_keywords = ["LST", "MOD", "ADD", "DEL", "DSP", "ACT", "DEA"]
    if not any(command.startswith(kw) for kw in valid_keywords):
        return False

    # Must end with semicolon
    if not command.endswith(";"):
        return False

    # Must have colon after object type
    if ":" not in command:
        return False

    return True


def format_command_response(response: str, parameter_name: str) -> Dict[str, Any]:
    """
    Parse and format MML command response.

    Args:
        response: Raw MML response string
        parameter_name: Parameter being queried

    Returns:
        Dictionary with parsed response data
    """
    result = {
        "parameter_name": parameter_name,
        "raw_response": response,
        "success": False,
        "value": None,
        "error": None
    }

    # Check for error responses
    error_keywords = ["FAILURE", "ERROR", "DENIED", "NOT EXIST"]
    if any(keyword in response.upper() for keyword in error_keywords):
        result["error"] = "Command execution failed"
        return result

    # Check for success indicators
    success_keywords = ["SUCCEED", "SUCCESS", "COMPLETE"]
    if any(keyword in response.upper() for keyword in success_keywords):
        result["success"] = True

    # Try to extract parameter value (simplified - would need more robust parsing)
    if parameter_name in MML_COMMANDS:
        field_name = MML_COMMANDS[parameter_name]["parameter_field"]
        # Look for "FIELD_NAME=value" pattern
        import re
        match = re.search(rf"{field_name}=([^,;\s]+)", response)
        if match:
            result["value"] = match.group(1)

    return result


# ============================================================================
# MML COMMAND BATCHING
# ============================================================================

def build_batch_commands(commands: List[str]) -> str:
    """
    Combine multiple MML commands into a batch.

    Args:
        commands: List of individual MML commands

    Returns:
        Batch command string
    """
    # Huawei supports multiple commands separated by newlines
    return "\n".join(commands)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Build query command
    query = build_query_command("reference_signal_power_pdschcfg", cell_id=1)
    print("Query Command:", query)
    # Output: LST PDSCHCFG: LOCALCELLID=1;

    # Example: Build modify command
    modify = build_modify_command("reference_signal_power_pdschcfg", value=-200, cell_id=1)
    print("Modify Command:", modify)
    # Output: MOD PDSCHCFG: LOCALCELLID=1, REFERENCESIGNALPWR=-200;

    # Example: Validate command
    is_valid = validate_command_syntax(query)
    print("Valid?", is_valid)
    # Output: True

    # Example: Get parameter info
    info = get_command_info("a3_event_offset")
    print("Parameter Info:", info["description"])
    # Output: Query/Modify A3 Event Configuration - Handover Offset
