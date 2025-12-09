"""
Helper utilities for the Cassava 4G Network Optimizer.

Common utility functions for formatting, parsing, and data manipulation.
"""

import re
import uuid
from datetime import timedelta
from typing import Any, Optional, TypeVar

T = TypeVar("T", int, float)


def format_kpi_value(
    value: float,
    kpi_name: str,
    include_unit: bool = True,
) -> str:
    """
    Format a KPI value for display with appropriate precision and units.
    
    Args:
        value: The KPI value to format
        kpi_name: Name of the KPI (to determine formatting)
        include_unit: Whether to include unit suffix
        
    Returns:
        Formatted string representation
    """
    # Percentage KPIs
    percentage_kpis = {
        "rrc_setup_success_rate",
        "erab_setup_success_rate",
        "handover_success_rate",
        "prb_utilization_dl",
        "prb_utilization_ul",
        "packet_loss_rate",
        "volte_drop_rate",
        "call_drop_rate",
    }
    
    # dB/dBm KPIs
    db_kpis = {
        "rsrp_average": "dBm",
        "rsrq_average": "dB",
        "sinr_average": "dB",
        "cqi_average": "",
    }
    
    # Throughput KPIs
    throughput_kpis = {
        "throughput_dl",
        "throughput_ul",
        "user_throughput_dl",
        "user_throughput_ul",
    }
    
    # Latency KPIs
    latency_kpis = {
        "latency_average",
        "rrc_setup_time",
        "erab_setup_time",
    }
    
    kpi_lower = kpi_name.lower()
    
    if kpi_lower in percentage_kpis:
        formatted = f"{value:.2f}"
        unit = "%" if include_unit else ""
    elif kpi_lower in db_kpis:
        formatted = f"{value:.1f}"
        unit = db_kpis.get(kpi_lower, "") if include_unit else ""
    elif kpi_lower in throughput_kpis:
        if value >= 1000:
            formatted = f"{value / 1000:.2f}"
            unit = "Gbps" if include_unit else ""
        else:
            formatted = f"{value:.2f}"
            unit = "Mbps" if include_unit else ""
    elif kpi_lower in latency_kpis:
        formatted = f"{value:.1f}"
        unit = "ms" if include_unit else ""
    else:
        # Default formatting
        if abs(value) >= 1000:
            formatted = f"{value:.0f}"
        elif abs(value) >= 1:
            formatted = f"{value:.2f}"
        else:
            formatted = f"{value:.4f}"
        unit = ""
    
    return f"{formatted}{unit}" if unit else formatted


def format_percentage(
    value: float,
    decimals: int = 2,
    include_sign: bool = False,
) -> str:
    """
    Format a value as a percentage.
    
    Args:
        value: The value to format (0-100 scale)
        decimals: Number of decimal places
        include_sign: Include + for positive values
        
    Returns:
        Formatted percentage string
    """
    sign = "+" if include_sign and value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_duration(
    seconds: float,
    compact: bool = False,
) -> str:
    """
    Format a duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        compact: Use compact format (1h30m vs 1 hour 30 minutes)
        
    Returns:
        Formatted duration string
    """
    if seconds < 0:
        return "N/A"
    
    td = timedelta(seconds=seconds)
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    
    parts = []
    
    if compact:
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")
        return "".join(parts)
    else:
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if secs > 0 or not parts:
            parts.append(f"{secs} second{'s' if secs != 1 else ''}")
        return " ".join(parts)


def truncate_string(
    text: str,
    max_length: int = 100,
    suffix: str = "...",
) -> str:
    """
    Truncate a string to maximum length with suffix.
    
    Args:
        text: String to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[: max_length - len(suffix)] + suffix


def generate_correlation_id() -> str:
    """
    Generate a unique correlation ID for request tracking.
    
    Returns:
        UUID string for correlation
    """
    return str(uuid.uuid4())


def parse_mml_response(response: str) -> dict[str, Any]:
    """
    Parse an MML command response into structured data.
    
    Handles common Huawei MML response formats including:
    - RETCODE success/failure
    - Parameter listings
    - Error messages
    
    Args:
        response: Raw MML response string
        
    Returns:
        Parsed response dictionary
    """
    result: dict[str, Any] = {
        "success": False,
        "retcode": None,
        "message": "",
        "data": {},
    }
    
    if not response:
        result["message"] = "Empty response"
        return result
    
    lines = response.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        
        # Check for RETCODE
        retcode_match = re.search(r"RETCODE\s*=\s*(\d+)", line, re.IGNORECASE)
        if retcode_match:
            result["retcode"] = int(retcode_match.group(1))
            result["success"] = result["retcode"] == 0
            continue
        
        # Check for error messages
        if "ERROR" in line.upper() or "FAIL" in line.upper():
            result["message"] = line
            result["success"] = False
            continue
        
        # Check for success messages
        if "SUCCESS" in line.upper() or "COMPLETE" in line.upper():
            result["message"] = line
            result["success"] = True
            continue
        
        # Parse parameter lines (KEY=VALUE or KEY:VALUE format)
        param_match = re.match(r"(\w+)\s*[=:]\s*(.+)", line)
        if param_match:
            key = param_match.group(1).strip()
            value = param_match.group(2).strip()
            
            # Try to convert to numeric
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass
            
            result["data"][key] = value
    
    return result


def safe_divide(
    numerator: float,
    denominator: float,
    default: float = 0.0,
) -> float:
    """
    Safely divide two numbers, returning default on division by zero.
    
    Args:
        numerator: Dividend
        denominator: Divisor
        default: Value to return if denominator is zero
        
    Returns:
        Division result or default
    """
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(
    value: T,
    min_value: T,
    max_value: T,
) -> T:
    """
    Clamp a value between minimum and maximum bounds.
    
    Args:
        value: Value to clamp
        min_value: Minimum bound
        max_value: Maximum bound
        
    Returns:
        Clamped value
    """
    return max(min_value, min(value, max_value))


def deep_merge(
    base: dict[str, Any],
    override: dict[str, Any],
) -> dict[str, Any]:
    """
    Deep merge two dictionaries, with override taking precedence.
    
    Args:
        base: Base dictionary
        override: Override dictionary
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(
    d: dict[str, Any],
    parent_key: str = "",
    separator: str = ".",
) -> dict[str, Any]:
    """
    Flatten a nested dictionary into a single level.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        separator: Key separator
        
    Returns:
        Flattened dictionary
    
    Example:
        {"a": {"b": 1}} -> {"a.b": 1}
    """
    items: list[tuple[str, Any]] = []
    
    for key, value in d.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, separator).items())
        else:
            items.append((new_key, value))
    
    return dict(items)


def unflatten_dict(
    d: dict[str, Any],
    separator: str = ".",
) -> dict[str, Any]:
    """
    Unflatten a flattened dictionary back to nested structure.
    
    Args:
        d: Flattened dictionary
        separator: Key separator used when flattening
        
    Returns:
        Nested dictionary
    
    Example:
        {"a.b": 1} -> {"a": {"b": 1}}
    """
    result: dict[str, Any] = {}
    
    for key, value in d.items():
        parts = key.split(separator)
        target = result
        
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        
        target[parts[-1]] = value
    
    return result


def validate_site_name(site_name: str) -> bool:
    """
    Validate a site name format.
    
    Site names should:
    - Be 1-50 characters
    - Start with a letter
    - Contain only alphanumeric, underscores, hyphens
    
    Args:
        site_name: Site name to validate
        
    Returns:
        True if valid
    """
    if not site_name or len(site_name) > 50:
        return False
    
    pattern = r"^[A-Za-z][A-Za-z0-9_-]*$"
    return bool(re.match(pattern, site_name))


def validate_mml_command(command: str) -> tuple[bool, Optional[str]]:
    """
    Validate an MML command for basic syntax.
    
    Args:
        command: MML command to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not command or not command.strip():
        return False, "Command is empty"
    
    command = command.strip()
    
    # Check for dangerous commands
    dangerous_patterns = [
        r"\bDEL\s+ENB\b",
        r"\bRMV\s+ENB\b",
        r"\bRST\s+ENB\b",
        r"\bDEL\s+ALL\b",
        r"\bRMV\s+ALL\b",
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Dangerous command pattern detected: {pattern}"
    
    # Check for valid command prefix
    valid_prefixes = [
        "DSP",  # Display
        "LST",  # List
        "MOD",  # Modify
        "ADD",  # Add
        "SET",  # Set
        "ACT",  # Activate
        "DEA",  # Deactivate
        "BLK",  # Block
        "UBL",  # Unblock
    ]
    
    first_word = command.split()[0].upper()
    if first_word not in valid_prefixes:
        return False, f"Unknown command prefix: {first_word}"
    
    # Check for balanced parentheses/brackets
    open_count = command.count("(") + command.count("[") + command.count("{")
    close_count = command.count(")") + command.count("]") + command.count("}")
    if open_count != close_count:
        return False, "Unbalanced brackets in command"
    
    return True, None


def calculate_improvement_score(
    before: float,
    after: float,
    higher_is_better: bool = True,
) -> float:
    """
    Calculate improvement score as percentage change.
    
    Args:
        before: Value before optimization
        after: Value after optimization
        higher_is_better: Whether higher values are better
        
    Returns:
        Improvement score (positive = improvement)
    """
    if before == 0:
        return 100.0 if after > 0 and higher_is_better else -100.0
    
    change_pct = (after - before) / abs(before) * 100
    
    return change_pct if higher_is_better else -change_pct


def batch_list(
    items: list[Any],
    batch_size: int,
) -> list[list[Any]]:
    """
    Split a list into batches of specified size.
    
    Args:
        items: List to split
        batch_size: Size of each batch
        
    Returns:
        List of batches
    """
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]
