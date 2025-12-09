"""
Cassava 4G Network Optimizer - UI Package.

Streamlit-based user interface with dark mode theme,
real-time agent progress tracking, and Cassava branding.
"""

from cassava_optimizer.ui.theme import (
    CASSAVA_NAVY,
    CASSAVA_GREEN,
    CASSAVA_PURPLE,
    COLORS,
    get_custom_css,
    get_plotly_template,
)

# Note: Import app.main lazily to avoid circular imports
# Use: from cassava_optimizer.ui.app import main as run_app

__all__ = [
    # Theme
    "CASSAVA_NAVY",
    "CASSAVA_GREEN",
    "CASSAVA_PURPLE",
    "COLORS",
    "get_custom_css",
    "get_plotly_template",
]
