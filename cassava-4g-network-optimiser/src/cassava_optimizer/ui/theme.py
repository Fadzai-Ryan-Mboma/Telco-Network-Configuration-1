"""
Cassava brand theme and styling for the Streamlit UI.

Defines colors, typography, and CSS styling for a consistent
light mode interface with Cassava branding (dark mode available as option).
"""

import streamlit as st

# Cassava Brand Colors
CASSAVA_NAVY = "#001D58"      # Primary dark blue
CASSAVA_GREEN = "#00F19C"     # Accent green
CASSAVA_PURPLE = "#964BEA"    # Secondary purple

# Extended palette (Light theme - default)
COLORS = {
    "primary": CASSAVA_NAVY,
    "accent": CASSAVA_GREEN,
    "secondary": CASSAVA_PURPLE,
    "background": "#FFFFFF",
    "surface": "#F8F9FA",
    "card": "#FFFFFF",
    "card_bg": "#FFFFFF",  # Alias for card
    "border": "#E5E7EB",
    "text_primary": "#1A1D24",
    "text_secondary": "#4B5563",
    "text_muted": "#9CA3AF",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#3B82F6",
}

# Agent status colors
AGENT_COLORS = {
    "data_collector": "#3B82F6",    # Blue
    "analyzer": "#8B5CF6",          # Purple
    "strategy_planner": "#EC4899",  # Pink
    "validator": "#F59E0B",         # Orange
    "commander": "#10B981",         # Emerald
    "reviewer": "#6366F1",          # Indigo
}


def get_custom_css() -> str:
    """
    Generate CSS styles for the Streamlit application.
    
    Returns:
        CSS string to inject into the page
    """
    return f"""
    <style>
        /* Global styles */
        .stApp {{
            background-color: {COLORS['background']};
        }}
        
        /* Header styling */
        .main-header {{
            background: linear-gradient(135deg, {CASSAVA_NAVY} 0%, #002B80 100%);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            border: 1px solid {COLORS['border']};
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        .main-header h1 {{
            color: #FFFFFF;
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .main-header .subtitle {{
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.95rem;
            margin-top: 0.5rem;
        }}
        
        /* Card styling */
        .card {{
            background: {COLORS['card']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}
        
        .card-header {{
            color: {COLORS['text_primary']};
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        /* KPI Cards */
        .kpi-card {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}
        
        .kpi-value {{
            font-size: 1.75rem;
            font-weight: 700;
            color: {CASSAVA_NAVY};
        }}
        
        .kpi-value.success {{
            color: {COLORS['success']};
        }}
        
        .kpi-value.warning {{
            color: {COLORS['warning']};
        }}
        
        .kpi-value.error {{
            color: {COLORS['error']};
        }}
        
        .kpi-label {{
            color: {COLORS['text_secondary']};
            font-size: 0.85rem;
            margin-top: 0.25rem;
        }}
        
        .kpi-trend {{
            font-size: 0.8rem;
            margin-top: 0.5rem;
        }}
        
        .kpi-trend.up {{
            color: {CASSAVA_GREEN};
        }}
        
        .kpi-trend.down {{
            color: {COLORS['error']};
        }}
        
        /* Agent Progress */
        .agent-progress {{
            background: {COLORS['card']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }}
        
        .agent-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.75rem;
        }}
        
        .agent-name {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        }}
        
        .agent-status {{
            font-size: 0.8rem;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 500;
        }}
        
        .agent-status.pending {{
            background: {COLORS['border']};
            color: {COLORS['text_muted']};
        }}
        
        .agent-status.running {{
            background: rgba(59, 130, 246, 0.2);
            color: #60A5FA;
            animation: pulse 2s infinite;
        }}
        
        .agent-status.complete {{
            background: rgba(0, 241, 156, 0.2);
            color: {CASSAVA_GREEN};
        }}
        
        .agent-status.error {{
            background: rgba(239, 68, 68, 0.2);
            color: #F87171;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}
        
        .agent-progress-bar {{
            height: 4px;
            background: {COLORS['border']};
            border-radius: 2px;
            overflow: hidden;
        }}
        
        .agent-progress-fill {{
            height: 100%;
            border-radius: 2px;
            transition: width 0.3s ease;
        }}
        
        .agent-message {{
            font-size: 0.85rem;
            color: {COLORS['text_secondary']};
            margin-top: 0.5rem;
        }}
        
        /* Recommendation cards */
        .recommendation-card {{
            background: {COLORS['surface']};
            border-left: 4px solid {CASSAVA_GREEN};
            border-radius: 0 8px 8px 0;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }}
        
        .recommendation-card.warning {{
            border-left-color: {COLORS['warning']};
        }}
        
        .recommendation-card.high-risk {{
            border-left-color: {COLORS['error']};
        }}
        
        .recommendation-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.75rem;
        }}
        
        .recommendation-title {{
            font-weight: 600;
            color: {COLORS['text_primary']};
        }}
        
        .recommendation-confidence {{
            font-size: 0.8rem;
            padding: 2px 8px;
            border-radius: 4px;
            background: rgba(0, 241, 156, 0.2);
            color: {CASSAVA_GREEN};
        }}
        
        .recommendation-details {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
            margin-bottom: 0.75rem;
        }}
        
        .recommendation-detail {{
            font-size: 0.85rem;
        }}
        
        .recommendation-detail .label {{
            color: {COLORS['text_muted']};
        }}
        
        .recommendation-detail .value {{
            color: {COLORS['text_primary']};
            font-weight: 500;
        }}
        
        .recommendation-reasoning {{
            font-size: 0.85rem;
            color: {COLORS['text_secondary']};
            padding-top: 0.75rem;
            border-top: 1px solid {COLORS['border']};
        }}
        
        /* Error display */
        .error-card {{
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid {COLORS['error']};
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        
        .error-header {{
            color: {COLORS['error']};
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 0.5rem;
        }}
        
        .error-message {{
            color: {COLORS['text_secondary']};
            font-family: monospace;
            font-size: 0.85rem;
        }}
        
        /* Button styling */
        .stButton > button {{
            background: linear-gradient(135deg, {CASSAVA_GREEN} 0%, #00D989 100%);
            color: {CASSAVA_NAVY};
            font-weight: 600;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            transition: all 0.2s ease;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 241, 156, 0.3);
        }}
        
        .stButton > button:disabled {{
            background: {COLORS['border']};
            color: {COLORS['text_muted']};
        }}
        
        /* Secondary button */
        .secondary-button > button {{
            background: transparent;
            border: 2px solid {COLORS['border']};
            color: {COLORS['text_primary']};
        }}
        
        .secondary-button > button:hover {{
            border-color: {CASSAVA_GREEN};
            color: {CASSAVA_GREEN};
        }}
        
        /* Input styling */
        .stSelectbox > div > div {{
            background: {COLORS['surface']};
            border-color: {COLORS['border']};
        }}
        
        .stTextInput > div > div > input {{
            background: {COLORS['surface']};
            border-color: {COLORS['border']};
            color: {COLORS['text_primary']};
        }}
        
        /* Sidebar styling */
        .css-1d391kg {{
            background: {COLORS['surface']};
        }}
        
        [data-testid="stSidebar"] {{
            background: {COLORS['surface']};
            border-right: 1px solid {COLORS['border']};
        }}
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {{
            background: transparent;
            gap: 0.5rem;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            color: {COLORS['text_secondary']};
            padding: 0.75rem 1.25rem;
        }}
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background: {CASSAVA_GREEN};
            border-color: {CASSAVA_GREEN};
            color: white;
        }}
        
        /* Metric styling */
        [data-testid="metric-container"] {{
            background: {COLORS['card']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 1rem;
        }}
        
        [data-testid="metric-container"] label {{
            color: {COLORS['text_secondary']};
        }}
        
        [data-testid="metric-container"] [data-testid="stMetricValue"] {{
            color: {CASSAVA_GREEN};
        }}
        
        /* Expander styling */
        .streamlit-expanderHeader {{
            background: {COLORS['surface']};
            border-radius: 8px;
        }}
        
        /* DataFrames */
        .stDataFrame {{
            background: {COLORS['card']};
            border-radius: 8px;
        }}
        
        /* Tooltips */
        [data-baseweb="tooltip"] {{
            background: {COLORS['card']};
            border: 1px solid {COLORS['border']};
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 1.5rem;
            color: {COLORS['text_muted']};
            font-size: 0.85rem;
            border-top: 1px solid {COLORS['border']};
            margin-top: 2rem;
        }}
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {COLORS['background']};
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {COLORS['border']};
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {COLORS['text_muted']};
        }}
    </style>
    """


def get_plotly_template() -> dict:
    """
    Get Plotly template configuration for Cassava branding.
    
    Returns:
        Plotly template dictionary
    """
    return {
        "layout": {
            "paper_bgcolor": COLORS["background"],
            "plot_bgcolor": COLORS["surface"],
            "font": {"color": COLORS["text_primary"]},
            "xaxis": {
                "gridcolor": COLORS["border"],
                "zerolinecolor": COLORS["border"],
            },
            "yaxis": {
                "gridcolor": COLORS["border"],
                "zerolinecolor": COLORS["border"],
            },
            "colorway": [
                CASSAVA_GREEN,
                CASSAVA_PURPLE,
                COLORS["info"],
                COLORS["warning"],
                COLORS["error"],
            ],
        }
    }


def apply_theme() -> None:
    """Apply the Cassava theme to the Streamlit app."""
    st.set_page_config(
        page_title="Cassava 4G Network Optimizer",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Inject CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)


def render_header() -> None:
    """Render the application header with Cassava branding."""
    st.markdown(
        """
        <div class="main-header" style="display: flex; align-items: center; gap: 16px;">
            <div>
                <svg width="48" height="48" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                    <path fill="#00f19c" d="M0,0h31.01C31.55,0,32,.45,32,.99v31.01H.99c-.55,0-.99-.45-.99-.99V0h0Z"/>
                    <path fill="#001c5c" d="M9.32,27.09c-1.19,0-2.2-.2-3.05-.61-.85-.4-1.5-.95-1.95-1.65-.45-.7-.68-1.48-.68-2.34s.22-1.69.66-2.37c.44-.68,1.14-1.21,2.1-1.59.96-.39,2.21-.58,3.75-.58h4.03v2.57h-3.56c-1.03,0-1.74.17-2.13.51-.39.34-.58.76-.58,1.27,0,.56.22,1.01.66,1.34.44.33,1.05.49,1.82.49s1.39-.17,1.98-.52c.58-.35,1.01-.86,1.27-1.54l.68,2.03c-.32.98-.9,1.72-1.75,2.23-.85.51-1.94.76-3.27.76ZM13.95,26.86v-2.96l-.28-.65v-5.3c0-.94-.29-1.67-.86-2.2-.57-.53-1.45-.79-2.64-.79-.81,0-1.6.13-2.38.38-.78.25-1.44.6-1.99,1.03l-1.58-3.08c.83-.58,1.82-1.03,2.99-1.35,1.17-.32,2.35-.48,3.56-.48,2.31,0,4.11.55,5.39,1.64,1.28,1.09,1.92,2.79,1.92,5.11v8.66h-4.12Z"/>
                    <path fill="#001c5c" d="M24.24,9.56c-.81,0-1.47-.23-1.98-.71-.51-.47-.76-1.05-.76-1.75s.25-1.28.76-1.75c.51-.47,1.17-.71,1.98-.71s1.47.22,1.98.66c.51.44.76,1.01.76,1.71,0,.73-.25,1.34-.75,1.82-.5.48-1.16.72-1.99.72ZM22.04,26.86v-15.18h4.4v15.18h-4.4Z"/>
                </svg>
            </div>
            <div>
                <h1 style="margin: 0; font-size: 1.8rem;">Cassava 4G Network Optimizer</h1>
                <p class="subtitle" style="margin: 4px 0 0 0;">AI-Powered Network Analysis and Optimization for LTE Infrastructure</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render the application footer."""
    st.markdown(
        """
        <div class="footer">
            <p>Cassava 4G Network Optimizer v1.0.0 | Powered by NVIDIA NIM & LangGraph</p>
            <p>© 2024 Cassava Network Technologies</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
