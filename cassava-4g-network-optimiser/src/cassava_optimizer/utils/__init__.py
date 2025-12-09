"""
Cassava 4G Network Optimizer - Utilities Package.

Common utilities for logging, formatting, and helper functions.
"""

from cassava_optimizer.utils.logging import (
    setup_logging,
    get_logger,
    log_agent_action,
    log_api_call,
    log_optimization_event,
)
from cassava_optimizer.utils.helpers import (
    format_kpi_value,
    format_percentage,
    format_duration,
    truncate_string,
    generate_correlation_id,
    parse_mml_response,
    safe_divide,
    clamp,
    deep_merge,
    flatten_dict,
)
from cassava_optimizer.utils.env_manager import (
    get_env_manager,
    get_env,
    set_env_pending,
    save_env,
    restore_env,
    update_env,
)

__all__ = [
    # Logging
    "setup_logging",
    "get_logger",
    "log_agent_action",
    "log_api_call",
    "log_optimization_event",
    # Helpers
    "format_kpi_value",
    "format_percentage",
    "format_duration",
    "truncate_string",
    "generate_correlation_id",
    "parse_mml_response",
    "safe_divide",
    "clamp",
    "deep_merge",
    "flatten_dict",
    # Env Manager
    "get_env_manager",
    "get_env",
    "set_env_pending",
    "save_env",
    "restore_env",
    "update_env",
]
