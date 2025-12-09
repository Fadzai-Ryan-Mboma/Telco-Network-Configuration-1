"""
Cassava 4G Network Optimizer - Tools Package.

LangChain-compatible tools for network operations,
database access, and KPI analysis.
"""

from cassava_optimizer.tools.huawei_tools import (
    get_site_kpis,
    get_cell_configuration,
    execute_mml_command,
    get_alarm_list,
    get_site_list,
)
from cassava_optimizer.tools.database_tools import (
    save_kpi_values,
    get_historical_kpis,
    save_recommendation,
    get_site_info,
    log_command_execution,
)
from cassava_optimizer.tools.analysis_tools import (
    analyze_kpi_trends,
    calculate_health_score,
    detect_anomalies,
    compare_with_baseline,
    generate_recommendations,
)

__all__ = [
    # Huawei Tools
    "get_site_kpis",
    "get_cell_configuration",
    "execute_mml_command",
    "get_alarm_list",
    "get_site_list",
    # Database Tools
    "save_kpi_values",
    "get_historical_kpis",
    "save_recommendation",
    "get_site_info",
    "log_command_execution",
    # Analysis Tools
    "analyze_kpi_trends",
    "calculate_health_score",
    "detect_anomalies",
    "compare_with_baseline",
    "generate_recommendations",
]
