"""
UI Pages Package for the Cassava 4G Network Optimizer.

Contains individual page modules for the Streamlit multipage application.
"""

from cassava_optimizer.ui.pages.dashboard import render_dashboard_page
from cassava_optimizer.ui.pages.optimization import render_optimization_page
from cassava_optimizer.ui.pages.history import render_history_page
from cassava_optimizer.ui.pages.settings import render_settings_page

__all__ = [
    "render_dashboard_page",
    "render_optimization_page",
    "render_history_page",
    "render_settings_page",
]
