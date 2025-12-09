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
        "query_global": False,
        "modify": "MOD PDSCHCFG: LOCALCELLID={cell_id}, REFERENCESIGNALPWR={value};",
        "parameter_field": "Reference signal power",
        "parameter_field_alt": "REFERENCESIGNALPWR",
        "description": "Query/Modify PDSCH Configuration - Reference Signal Power",
        "value_units": "0.1 dBm",
        "example_query": "LST PDSCHCFG: LOCALCELLID=1;",
        "example_modify": "MOD PDSCHCFG: LOCALCELLID=1, REFERENCESIGNALPWR=-200;"
    },

    # ========================================================================
    # Reference Signal Power RS (reference_signal_power_rs) - Same as PDSCHCFG
    # ========================================================================
    "reference_signal_power_rs": {
        "query": "LST PDSCHCFG: LOCALCELLID={cell_id};",
        "query_global": False,
        "modify": "MOD PDSCHCFG: LOCALCELLID={cell_id}, REFERENCESIGNALPWR={value};",
        "parameter_field": "Reference signal power",
        "parameter_field_alt": "REFERENCESIGNALPWR",
        "description": "Query/Modify RS Power - Primary Reference Signal Power",
        "value_units": "0.1 dBm",
        "example_query": "LST PDSCHCFG: LOCALCELLID=1;",
        "example_modify": "MOD PDSCHCFG: LOCALCELLID=1, REFERENCESIGNALPWR=-180;"
    },

    # ========================================================================
    # A3 Event Configuration (a3_event_offset)
    # UPDATED: Uses LST UECOOPERATIONPARA (global query - returns all cells)
    # ========================================================================
    "a3_event_offset": {
        "query": "LST UECOOPERATIONPARA:;",
        "query_global": True,
        "modify": "MOD UECOOPERATIONPARA: LOCALCELLID={cell_id}, A3OFFSET=dB{value};",
        "parameter_field": "A3 Handover Threshold Offset",
        "parameter_field_alt": "A3OFFSET",
        "description": "Query/Modify A3 Event Configuration - Handover Offset",
        "value_units": "dB",
        "example_query": "LST UECOOPERATIONPARA:;",
        "example_modify": "MOD UECOOPERATIONPARA: LOCALCELLID=1, A3OFFSET=dB3;"
    },

    # ========================================================================
    # T310 Timer Configuration (t310_timer)
    # UPDATED: Uses LST UETIMERCONST (global query - returns all cells)
    # ========================================================================
    "t310_timer": {
        "query": "LST UETIMERCONST:;",
        "query_global": True,
        "modify": "MOD UETIMERCONST: LOCALCELLID={cell_id}, T310={value};",
        "parameter_field": "Timer 310",
        "parameter_field_alt": "T310",
        "description": "Query/Modify T310 Timer - Radio Link Failure Detection",
        "value_units": "ms",
        "valid_values": ["MS100_T310", "MS200_T310", "MS500_T310", "MS1000_T310", 
                        "MS1500_T310", "MS2000_T310", "MS2500_T310", "MS6000_T310"],
        "example_query": "LST UETIMERCONST:;",
        "example_modify": "MOD UETIMERCONST: LOCALCELLID=1, T310=MS1000_T310;"
    },

    # ========================================================================
    # P0 Nominal PUSCH Configuration (p0_nominal_pusch)
    # FIXED: Uses cell-specific query LST CELLULPCCOMM:LOCALCELLID={cell_id};
    # NOTE: Global query (LST CELLULPCCOMM:;) returns INVALID on this Huawei version
    # ========================================================================
    "p0_nominal_pusch": {
        "query": "LST CELLULPCCOMM: LOCALCELLID={cell_id};",
        "query_global": False,
        "modify": "MOD CELLULPCCOMM: LOCALCELLID={cell_id}, P0NOMINALPUSCH={value};",
        "parameter_field": "P0 nominal PUSCH",
        "parameter_field_alt": "P0NOMINALPUSCH",
        "description": "Query/Modify P0 Nominal PUSCH - Uplink Power Control",
        "value_units": "dBm",
        "example_query": "LST CELLULPCCOMM: LOCALCELLID=1;",
        "example_modify": "MOD CELLULPCCOMM: LOCALCELLID=1, P0NOMINALPUSCH=-70;"
    },

    # ========================================================================
    # PDCCH Aggregation Level Configuration (pdcch_aggregation_level)
    # ========================================================================
    "pdcch_aggregation_level": {
        "query": "LST CELLPDCCHALGO: LOCALCELLID={cell_id};",
        "query_global": False,
        "modify": "MOD CELLPDCCHALGO: LOCALCELLID={cell_id}, PDCCHAGGLVL={value};",
        "parameter_field": "PDCCH Aggregation Strategy Level",
        "parameter_field_alt": "PDCCHAGGLVL",
        "description": "Query/Modify PDCCH Aggregation Level - Control Channel Resource Allocation",
        "value_units": "level (1, 2, 4, 8)",
        "example_query": "LST CELLPDCCHALGO: LOCALCELLID=1;",
        "example_modify": "MOD CELLPDCCHALGO: LOCALCELLID=1, PDCCHAGGLVL=4;"
    },

    # ========================================================================
    # Cell Status (cell_status) - Query cell configuration
    # ========================================================================
    "cell_status": {
        "query": "LST CELL:;",
        "query_global": True,
        "modify": None,
        "parameter_field": "Cell Name",
        "parameter_field_alt": "CELLNAME",
        "description": "Query cell status and configuration (read-only)",
        "value_units": "",
        "example_query": "LST CELL:;",
        "example_modify": None
    },

    # ========================================================================
    # eNodeB Function (enodeb_function) - Query eNodeB status
    # ========================================================================
    "enodeb_function": {
        "query": "DSP ENODEBFUNCTION:;",
        "query_global": True,
        "modify": None,
        "parameter_field": "eNodeB Function Name",
        "parameter_field_alt": "ENODEBFUNCTIONNAME",
        "description": "Display eNodeB function status (read-only)",
        "value_units": "",
        "example_query": "DSP ENODEBFUNCTION:;",
        "example_modify": None
    },

    # ========================================================================
    # Active Alarms (active_alarms) - Query current alarms
    # ========================================================================
    "active_alarms": {
        "query": "DSP ALM:;",
        "query_global": True,
        "modify": None,
        "parameter_field": "Alarm ID",
        "parameter_field_alt": "ALARMID",
        "description": "Display active alarms on site (read-only)",
        "value_units": "",
        "example_query": "DSP ALM:;",
        "example_modify": None
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
        cell_id: Cell ID (default: 1) - ignored for global queries

    Returns:
        MML query command string

    Raises:
        ValueError: If parameter_name is not recognized
    
    Note:
        Some parameters use global queries (query_global=True) that return all cells.
        For these, the cell_id parameter is ignored and the command returns data
        for all 6 cells. Cell-specific filtering should be done when parsing response.
        
        For cell-specific queries, use build_query_all_cells() to get commands for all 6 cells.
    """
    if parameter_name not in MML_COMMANDS:
        raise ValueError(f"Unknown parameter: {parameter_name}. Available: {list(MML_COMMANDS.keys())}")

    template = MML_COMMANDS[parameter_name]["query"]
    
    # Check if this is a global query (returns all cells)
    if MML_COMMANDS[parameter_name].get("query_global", False):
        # Global queries don't need cell_id formatting
        return template
    
    # Cell-specific queries need cell_id
    return template.format(cell_id=cell_id)


def build_query_all_cells(parameter_name: str, cell_ids: List[int] = None) -> List[str]:
    """
    Build MML query commands for all cells at a site.
    
    For global queries (query_global=True), returns a single command that retrieves all cells.
    For cell-specific queries, returns 6 commands (one per cell).
    
    Args:
        parameter_name: Name of parameter (e.g., 'reference_signal_power_pdschcfg')
        cell_ids: List of cell IDs to query (default: [1, 2, 3, 4, 5, 6])
    
    Returns:
        List of MML query command strings
    
    Raises:
        ValueError: If parameter_name is not recognized
    
    Example:
        >>> build_query_all_cells("reference_signal_power_pdschcfg")
        ['LST PDSCHCFG: LOCALCELLID=1;', 'LST PDSCHCFG: LOCALCELLID=2;', ...]
        
        >>> build_query_all_cells("a3_event_offset")  # Global query
        ['LST UECOOPERATIONPARA:;']  # Single command returns all cells
    """
    if parameter_name not in MML_COMMANDS:
        raise ValueError(f"Unknown parameter: {parameter_name}. Available: {list(MML_COMMANDS.keys())}")
    
    if cell_ids is None:
        cell_ids = [1, 2, 3, 4, 5, 6]  # Default 6-cell site configuration
    
    # Check if this is a global query (returns all cells in one command)
    if MML_COMMANDS[parameter_name].get("query_global", False):
        # Global queries return all cells with a single command
        return [build_query_command(parameter_name)]
    
    # Cell-specific queries need one command per cell
    return [build_query_command(parameter_name, cell_id) for cell_id in cell_ids]


def is_global_query(parameter_name: str) -> bool:
    """
    Check if a parameter uses a global query (returns all cells in one API call).
    
    Args:
        parameter_name: Name of parameter
    
    Returns:
        True if parameter uses global query, False if cell-specific
    
    Example:
        >>> is_global_query("a3_event_offset")
        True
        >>> is_global_query("reference_signal_power_pdschcfg")
        False
    """
    if parameter_name not in MML_COMMANDS:
        raise ValueError(f"Unknown parameter: {parameter_name}. Available: {list(MML_COMMANDS.keys())}")
    
    return MML_COMMANDS[parameter_name].get("query_global", False)


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


def build_modify_command_template(parameter_name: str, value: Any) -> str:
    """
    Build MML modify command TEMPLATE with {cell_id} placeholder for batch execution.

    This function is used when modifying parameters across multiple cells at a site.
    The returned template contains a {cell_id} placeholder that can be formatted
    for each cell (1-6) during batch execution.

    CRITICAL: Huawei API requires cell-by-cell modifications. Site-wide parameter
    changes require executing 6 separate MML commands (one per cell).

    Args:
        parameter_name: Name of parameter (e.g., 'reference_signal_power_pdschcfg')
        value: New value for parameter

    Returns:
        MML modify command template with {cell_id} placeholder

    Raises:
        ValueError: If parameter_name is not recognized

    Example:
        >>> build_modify_command_template("reference_signal_power_pdschcfg", -180)
        "MOD PDSCHCFG: LOCALCELLID={cell_id}, REFERENCESIGNALPWR=-180;"

        >>> # Usage in batch execution:
        >>> template = build_modify_command_template("a3_event_offset", 3)
        >>> for cell_id in [1, 2, 3, 4, 5, 6]:
        ...     command = template.format(cell_id=cell_id)
        ...     # command: "MOD EUTRANMEASUREMENT: LOCALCELLID=1, EUTRANEVTID=3, A3OFFSET=3;"
    """
    if parameter_name not in MML_COMMANDS:
        raise ValueError(f"Unknown parameter: {parameter_name}. Available: {list(MML_COMMANDS.keys())}")

    # Get the modify template
    template = MML_COMMANDS[parameter_name]["modify"]

    # Format with value but keep {cell_id} as placeholder
    # The template has placeholders: {cell_id} and {value}
    # We format {value} but preserve {cell_id} for later formatting
    return template.replace("{cell_id}", "{{cell_id}}").format(cell_id="{cell_id}", value=value)


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


def format_command_response(response: Any, parameter_name: str) -> Dict[str, Any]:
    """
    Parse and format MML command response.

    Args:
        response: Raw MML response (can be string or dict from API)
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

    # Convert response to string for parsing
    if isinstance(response, dict):
        # Convert dict to JSON string for parsing
        import json
        response_str = json.dumps(response)
    else:
        response_str = str(response)

    # Check for error responses
    error_keywords = ["FAILURE", "ERROR", "DENIED", "NOT EXIST"]
    if any(keyword in response_str.upper() for keyword in error_keywords):
        result["error"] = "Command execution failed"
        return result

    # Check for success indicators
    success_keywords = ["SUCCEED", "SUCCESS", "COMPLETE", "RETCODE"]
    if any(keyword in response_str.upper() for keyword in success_keywords):
        result["success"] = True

    # Try to extract parameter value from actual Huawei MML response format
    if parameter_name in MML_COMMANDS:
        field_name = MML_COMMANDS[parameter_name]["parameter_field"]
        field_name_alt = MML_COMMANDS[parameter_name].get("parameter_field_alt", field_name)
        import re

        # Parameter-specific patterns based on actual Huawei API responses
        # These patterns are tested against live iMaster MAE API output
        # Last updated: 2025-12-03 - Verified against MSH-0014-Chipadze
        # Format types:
        #   - Key=Value format: "Reference signal power(0.1dBm)  =  49"
        #   - Table format: Headers on one line, values on following lines (global queries)
        parameter_patterns = {
            "reference_signal_power_pdschcfg": [
                r"Reference signal power\([^\)]+\)\s*=\s*(\d+)",  # Reference signal power(0.1dBm)  =  49
                r"REFERENCESIGNALPWR\s*=?\s*([^,;\s\r\n]+)",
            ],
            "reference_signal_power_rs": [
                r"Reference signal power\([^\)]+\)\s*=\s*(\d+)",
                r"REFERENCESIGNALPWR\s*=?\s*([^,;\s\r\n]+)",
            ],
            "a3_event_offset": [
                # Table format: Column 4 is "A3 Handover Threshold Offset" - look for values like "3dB"
                r"(?:^|\s)(\d+dB)(?:\s|$)",  # Matches standalone values like "3dB"
                r"A3[^=]*=\s*(\d+)",  # Fallback if ever in key=value format
            ],
            "t310_timer": [
                # Table format: Column 4 is "Timer 310" - look for values like "1000ms"
                r"(?:^|\s)(\d+ms)(?:\s|$)",  # Matches standalone values like "1000ms"
                r"Timer 310\s*=\s*(\d+)",  # Fallback if ever in key=value format
            ],
            "p0_nominal_pusch": [
                r"P0 nominal PUSCH\([^\)]*\)\s*=\s*(-?\d+)",  # P0 nominal PUSCH(dBm)  =  -67
                r"P0NOMINALPUSCH\s*=?\s*(-?\d+)",
            ],
            "pdcch_aggregation_level": [
                r"SignalCongregateLevel\s*=\s*(\S+)",  # SignalCongregateLevel  =  CONGREG_LV4
                r"PDCCH Aggregation Level\s*=\s*(\S+)",  # Alternative
                r"PDCCHAGGLVL\s*=?\s*(\d+)",  # Old format
            ],
        }

        # Get patterns for this parameter, or use generic patterns
        patterns = parameter_patterns.get(parameter_name, [
            rf"{field_name}\s+([^\s\r\n]+)",  # Field Name  value (space-separated)
            rf"{field_name_alt}\s*=?\s*([^,;\s\r\n]+)",  # FIELD_NAME = value
        ])

        # First, try to extract from 'report' field if it exists in dict
        if isinstance(response, dict) and 'results' in response:
            for res in response['results']:
                if 'report' in res:
                    report = res['report']
                    
                    for pattern in patterns:
                        match = re.search(pattern, report, re.IGNORECASE)
                        if match:
                            result["value"] = match.group(1)
                            break

                    if result["value"]:
                        break

        # Fallback: Try patterns on string representation
        if not result["value"]:
            for pattern in patterns:
                match = re.search(pattern, response_str, re.IGNORECASE)
                if match:
                    result["value"] = match.group(1)
                    break

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
