"""
MML (Man-Machine Language) command templates for Huawei eNodeB.

Contains command templates, validation rules, and rollback generation.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from cassava_optimizer.domain.enums import ParameterType
from cassava_optimizer.domain.exceptions import MMLCommandError


class MMLCommandType(str, Enum):
    """Types of MML commands."""
    
    MODIFY = "MOD"
    SET = "SET"
    ADD = "ADD"
    REMOVE = "RMV"
    LIST = "LST"
    DISPLAY = "DSP"


@dataclass(frozen=True)
class MMLTemplate:
    """
    Template for generating MML commands.
    
    Attributes:
        name: Template name
        command_type: Type of MML command
        template: Command template with {placeholders}
        description: What this command does
        parameters: Required parameter names
        rollback_template: Template for rollback command (if applicable)
        validation_pattern: Regex pattern for output validation
        requires_confirmation: Whether user confirmation is needed
        risk_level: Risk level (low/medium/high)
    """
    
    name: str
    command_type: MMLCommandType
    template: str
    description: str
    parameters: tuple[str, ...]
    rollback_template: str = ""
    validation_pattern: str = ""
    requires_confirmation: bool = True
    risk_level: str = "medium"
    
    def generate(self, **kwargs: Any) -> str:
        """
        Generate MML command from template.
        
        Args:
            **kwargs: Parameter values to substitute
            
        Returns:
            Generated MML command string
            
        Raises:
            MMLCommandError: If required parameters are missing
        """
        # Check required parameters
        missing = [p for p in self.parameters if p not in kwargs]
        if missing:
            raise MMLCommandError(
                f"Missing required parameters for {self.name}: {missing}",
                details={"template": self.name, "missing": missing},
            )
        
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise MMLCommandError(
                f"Invalid parameter in template: {e}",
                command=self.template,
            )
    
    def generate_rollback(self, **kwargs: Any) -> str | None:
        """
        Generate rollback command if template exists.
        
        Args:
            **kwargs: Parameter values (including original values)
            
        Returns:
            Rollback command string or None if not applicable
        """
        if not self.rollback_template:
            return None
        
        try:
            return self.rollback_template.format(**kwargs)
        except KeyError:
            return None


# =============================================================================
# MML Command Templates
# =============================================================================

# Cell Parameter Modification Templates
CELL_PARAM_TEMPLATES: dict[str, MMLTemplate] = {
    "modify_tx_power": MMLTemplate(
        name="modify_tx_power",
        command_type=MMLCommandType.MODIFY,
        template=(
            "MOD CELL:LocalCellId={local_cell_id}, ReferenceSignalPwr={new_power};"
        ),
        description="Modify cell reference signal power",
        parameters=("local_cell_id", "new_power"),
        rollback_template=(
            "MOD CELL:LocalCellId={local_cell_id}, ReferenceSignalPwr={old_power};"
        ),
        validation_pattern=r"RETCODE\s*=\s*0",
        risk_level="low",
    ),
    
    "modify_antenna_tilt": MMLTemplate(
        name="modify_antenna_tilt",
        command_type=MMLCommandType.MODIFY,
        template=(
            "MOD CELL:LocalCellId={local_cell_id}, "
            "AdditionalPenetrationLoss=0, "
            "ElectricalTilt={new_tilt};"
        ),
        description="Modify cell electrical antenna tilt",
        parameters=("local_cell_id", "new_tilt"),
        rollback_template=(
            "MOD CELL:LocalCellId={local_cell_id}, "
            "AdditionalPenetrationLoss=0, "
            "ElectricalTilt={old_tilt};"
        ),
        validation_pattern=r"RETCODE\s*=\s*0",
        risk_level="medium",
    ),
    
    "modify_pci": MMLTemplate(
        name="modify_pci",
        command_type=MMLCommandType.MODIFY,
        template=(
            "MOD CELL:LocalCellId={local_cell_id}, PhyCellId={new_pci};"
        ),
        description="Modify Physical Cell Identity",
        parameters=("local_cell_id", "new_pci"),
        rollback_template=(
            "MOD CELL:LocalCellId={local_cell_id}, PhyCellId={old_pci};"
        ),
        validation_pattern=r"RETCODE\s*=\s*0",
        risk_level="high",
        requires_confirmation=True,
    ),
}

# Handover Parameter Templates
HANDOVER_TEMPLATES: dict[str, MMLTemplate] = {
    "modify_a3_offset": MMLTemplate(
        name="modify_a3_offset",
        command_type=MMLCommandType.MODIFY,
        template=(
            "MOD CELLALGOSWITCH:LocalCellId={local_cell_id}, "
            "IntraFreqHoA3Offset={new_offset};"
        ),
        description="Modify intra-frequency handover A3 offset",
        parameters=("local_cell_id", "new_offset"),
        rollback_template=(
            "MOD CELLALGOSWITCH:LocalCellId={local_cell_id}, "
            "IntraFreqHoA3Offset={old_offset};"
        ),
        validation_pattern=r"RETCODE\s*=\s*0",
        risk_level="medium",
    ),
    
    "modify_ttt": MMLTemplate(
        name="modify_ttt",
        command_type=MMLCommandType.MODIFY,
        template=(
            "MOD CELLALGOSWITCH:LocalCellId={local_cell_id}, "
            "IntraFreqHoTimeToTrig={new_ttt};"
        ),
        description="Modify intra-frequency handover Time-to-Trigger",
        parameters=("local_cell_id", "new_ttt"),
        rollback_template=(
            "MOD CELLALGOSWITCH:LocalCellId={local_cell_id}, "
            "IntraFreqHoTimeToTrig={old_ttt};"
        ),
        validation_pattern=r"RETCODE\s*=\s*0",
        risk_level="medium",
    ),
    
    "modify_cio": MMLTemplate(
        name="modify_cio",
        command_type=MMLCommandType.MODIFY,
        template=(
            "MOD EUTRANINTRAFREQNCELL:LocalCellId={local_cell_id}, "
            "Mcc=\"{mcc}\", Mnc=\"{mnc}\", eNodeBId={neighbor_enb_id}, "
            "CellId={neighbor_cell_id}, CellIndividualOffset={new_cio};"
        ),
        description="Modify Cell Individual Offset for neighbor cell",
        parameters=("local_cell_id", "mcc", "mnc", "neighbor_enb_id", "neighbor_cell_id", "new_cio"),
        rollback_template=(
            "MOD EUTRANINTRAFREQNCELL:LocalCellId={local_cell_id}, "
            "Mcc=\"{mcc}\", Mnc=\"{mnc}\", eNodeBId={neighbor_enb_id}, "
            "CellId={neighbor_cell_id}, CellIndividualOffset={old_cio};"
        ),
        validation_pattern=r"RETCODE\s*=\s*0",
        risk_level="medium",
    ),
}

# Query Templates (read-only)
QUERY_TEMPLATES: dict[str, MMLTemplate] = {
    "list_cells": MMLTemplate(
        name="list_cells",
        command_type=MMLCommandType.LIST,
        template="LST CELL:;",
        description="List all cells on eNodeB",
        parameters=(),
        requires_confirmation=False,
        risk_level="low",
    ),
    
    "display_cell": MMLTemplate(
        name="display_cell",
        command_type=MMLCommandType.DISPLAY,
        template="DSP CELL:LocalCellId={local_cell_id};",
        description="Display cell parameters",
        parameters=("local_cell_id",),
        requires_confirmation=False,
        risk_level="low",
    ),
    
    "list_neighbors": MMLTemplate(
        name="list_neighbors",
        command_type=MMLCommandType.LIST,
        template="LST EUTRANINTRAFREQNCELL:LocalCellId={local_cell_id};",
        description="List intra-frequency neighbor cells",
        parameters=("local_cell_id",),
        requires_confirmation=False,
        risk_level="low",
    ),
    
    "display_alarms": MMLTemplate(
        name="display_alarms",
        command_type=MMLCommandType.DISPLAY,
        template="DSP ALMAF:;",
        description="Display active alarms",
        parameters=(),
        requires_confirmation=False,
        risk_level="low",
    ),
}

# Combine all templates
ALL_TEMPLATES: dict[str, MMLTemplate] = {
    **CELL_PARAM_TEMPLATES,
    **HANDOVER_TEMPLATES,
    **QUERY_TEMPLATES,
}


# =============================================================================
# Template Lookup and Generation
# =============================================================================

def get_template(name: str) -> MMLTemplate | None:
    """Get a template by name."""
    return ALL_TEMPLATES.get(name)


def get_template_for_parameter(param_type: ParameterType) -> MMLTemplate | None:
    """Get the appropriate template for modifying a parameter type."""
    mapping = {
        ParameterType.TX_POWER: "modify_tx_power",
        ParameterType.ANTENNA_TILT: "modify_antenna_tilt",
        ParameterType.PCI: "modify_pci",
        ParameterType.A3_OFFSET: "modify_a3_offset",
        ParameterType.TTT: "modify_ttt",
        ParameterType.CIO: "modify_cio",
    }
    
    template_name = mapping.get(param_type)
    if template_name:
        return get_template(template_name)
    return None


def generate_command(
    template_name: str,
    **kwargs: Any,
) -> tuple[str, str | None]:
    """
    Generate MML command and rollback from template.
    
    Args:
        template_name: Name of the template to use
        **kwargs: Parameter values
        
    Returns:
        Tuple of (command, rollback_command)
        
    Raises:
        MMLCommandError: If template not found or parameters invalid
    """
    template = get_template(template_name)
    if not template:
        raise MMLCommandError(
            f"Unknown MML template: {template_name}",
            details={"available_templates": list(ALL_TEMPLATES.keys())},
        )
    
    command = template.generate(**kwargs)
    rollback = template.generate_rollback(**kwargs)
    
    return command, rollback


# =============================================================================
# Command Validation
# =============================================================================

def validate_command_syntax(command: str) -> tuple[bool, str]:
    """
    Validate MML command syntax.
    
    Args:
        command: The MML command string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    command = command.strip()
    
    # Check for empty command
    if not command:
        return False, "Command cannot be empty"
    
    # Check for valid command prefix
    valid_prefixes = ("MOD ", "SET ", "ADD ", "RMV ", "LST ", "DSP ")
    if not any(command.upper().startswith(p) for p in valid_prefixes):
        return False, f"Invalid command prefix. Expected one of: {valid_prefixes}"
    
    # Check for semicolon terminator
    if not command.endswith(";"):
        return False, "Command must end with semicolon"
    
    # Check for balanced quotes
    if command.count('"') % 2 != 0:
        return False, "Unbalanced quotes in command"
    
    # Check for valid parameter format
    param_pattern = r'[A-Za-z_][A-Za-z0-9_]*\s*='
    if ":" in command and not re.search(param_pattern, command):
        return False, "Invalid parameter format"
    
    return True, ""


def validate_command_safety(command: str) -> tuple[bool, str, str]:
    """
    Check if command is safe to execute.
    
    Args:
        command: The MML command string
        
    Returns:
        Tuple of (is_safe, risk_level, warning_message)
    """
    command_upper = command.upper()
    
    # High-risk commands
    high_risk_patterns = [
        ("RMV ", "Remove commands can cause service impact"),
        ("PHYCELLIDCFG", "PCI changes affect handover and interference"),
        ("ACTCELLOP", "Cell activation/deactivation affects service"),
        ("RSTCELL", "Cell reset causes temporary service outage"),
    ]
    
    for pattern, warning in high_risk_patterns:
        if pattern in command_upper:
            return False, "high", warning
    
    # Medium-risk commands
    medium_risk_patterns = [
        ("CELLALGOSWITCH", "Algorithm switch may affect performance"),
        ("INTRAFREQHO", "Handover parameter changes affect mobility"),
    ]
    
    for pattern, warning in medium_risk_patterns:
        if pattern in command_upper:
            return True, "medium", warning
    
    # Query commands are always safe
    if any(command_upper.startswith(p) for p in ("LST ", "DSP ")):
        return True, "low", ""
    
    return True, "low", ""


def parse_command_output(
    output: str,
    expected_pattern: str = r"RETCODE\s*=\s*0",
) -> tuple[bool, str]:
    """
    Parse MML command output for success/failure.
    
    Args:
        output: Command output from eNodeB
        expected_pattern: Regex pattern for success
        
    Returns:
        Tuple of (success, message)
    """
    if not output:
        return False, "No output received from command"
    
    # Check for explicit error patterns
    error_patterns = [
        (r"RETCODE\s*=\s*(\d+)", "Command returned error code: {}"),
        (r"ERROR", "Command execution error"),
        (r"FAILED", "Command failed"),
        (r"PERMISSION DENIED", "Permission denied for this command"),
    ]
    
    for pattern, msg_template in error_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            if pattern == error_patterns[0][0]:
                error_code = match.group(1)
                if error_code != "0":
                    return False, msg_template.format(error_code)
            else:
                return False, msg_template
    
    # Check for success pattern
    if re.search(expected_pattern, output):
        return True, "Command executed successfully"
    
    # Default to assuming success if no error found
    return True, "Command completed (output received)"
