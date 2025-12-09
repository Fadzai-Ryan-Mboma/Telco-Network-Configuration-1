"""
UI Components Package.

Reusable Streamlit components for the Cassava Network Optimizer.
"""

from cassava_optimizer.ui.components.kpi_display import (
    render_kpi_card,
    render_kpi_grid,
    render_kpi_trend_chart,
    render_health_gauge,
)
from cassava_optimizer.ui.components.agent_progress import (
    render_agent_progress,
    render_workflow_timeline,
    render_agent_card,
)
from cassava_optimizer.ui.components.recommendations import (
    render_recommendation_card,
    render_recommendations_list,
    render_approval_panel,
    render_execution_results,
)
from cassava_optimizer.ui.components.error_display import (
    render_error_banner,
    render_error_summary,
    render_fail_fast_notice,
)
from cassava_optimizer.ui.components.site_selector import (
    render_site_selector,
)
from cassava_optimizer.ui.components.charts import (
    create_kpi_line_chart,
    create_health_radar_chart,
    create_comparison_bar_chart,
    create_gauge_chart,
)
from cassava_optimizer.ui.components.command_display import (
    render_command_list,
    render_command_card,
)

__all__ = [
    # KPI Display
    "render_kpi_card",
    "render_kpi_grid",
    "render_kpi_trend_chart",
    "render_health_gauge",
    # Agent Progress
    "render_agent_progress",
    "render_workflow_timeline",
    "render_agent_card",
    # Recommendations
    "render_recommendation_card",
    "render_recommendations_list",
    "render_approval_panel",
    "render_execution_results",
    # Error Display
    "render_error_banner",
    "render_error_summary",
    "render_fail_fast_notice",
    # Site Selector
    "render_site_selector",
    # Charts
    "create_kpi_line_chart",
    "create_health_radar_chart",
    "create_comparison_bar_chart",
    "create_gauge_chart",
    # Command Display
    "render_command_list",
    "render_command_card",
]
