"""
Cassava Technologies UI Theme Components
Provides branding and styling components matching cassavatechnologies.com
"""

import streamlit as st
from typing import Optional, Dict, Any
import base64

class CassavaTheme:
    """Cassava Technologies branding and theme components"""
    
    # Brand colors from cassavatechnologies.com
    COLORS = {
        "primary_blue": "#0066CC",      # Cassava primary blue
        "secondary_teal": "#00A0A0",    # Teal accent
        "dark_blue": "#003366",         # Dark blue for headers
        "light_gray": "#F8F9FA",        # Light background
        "white": "#FFFFFF",             # Pure white
        "success_green": "#28A745",     # Success states
        "warning_orange": "#FFC107",    # Warning states  
        "danger_red": "#DC3545",        # Critical states
        "text_dark": "#212529",         # Primary text
        "text_muted": "#6C757D"         # Secondary text
    }
    
    @staticmethod
    def inject_css():
        """Inject Cassava-branded CSS into Streamlit"""
        css = f"""
        <style>
        /* Main theme colors */
        :root {{
            --cassava-blue: {CassavaTheme.COLORS['primary_blue']};
            --cassava-teal: {CassavaTheme.COLORS['secondary_teal']};
            --cassava-dark: {CassavaTheme.COLORS['dark_blue']};
        }}
        
        /* Header styling */
        .main-header {{
            background: linear-gradient(90deg, var(--cassava-blue) 0%, var(--cassava-teal) 100%);
            color: white;
            padding: 1.5rem;
            margin: -1rem -1rem 2rem -1rem;
            border-radius: 0 0 10px 10px;
        }}
        
        .main-header h1 {{
            margin: 0;
            font-size: 2.2rem;
            font-weight: 600;
        }}
        
        .main-header .subtitle {{
            margin: 0;
            font-size: 1.1rem;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        /* KPI Cards */
        .kpi-card {{
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 4px solid var(--cassava-blue);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }}
        
        .kpi-card.status-good {{
            border-left-color: {CassavaTheme.COLORS['success_green']};
        }}
        
        .kpi-card.status-warning {{
            border-left-color: {CassavaTheme.COLORS['warning_orange']};
        }}
        
        .kpi-card.status-critical {{
            border-left-color: {CassavaTheme.COLORS['danger_red']};
        }}
        
        .kpi-value {{
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            color: var(--cassava-blue);
        }}
        
        .kpi-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
            color: var(--cassava-dark);
        }}
        
        .kpi-description {{
            font-size: 0.9rem;
            color: {CassavaTheme.COLORS['text_muted']};
            margin: 0.5rem 0 0 0;
        }}
        
        .kpi-technical {{
            font-size: 0.8rem;
            font-style: italic;
            color: {CassavaTheme.COLORS['text_muted']};
            border-top: 1px solid #eee;
            padding-top: 0.5rem;
            margin-top: 1rem;
        }}
        
        /* Connection Status */
        .connection-status {{
            display: flex;
            align-items: center;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-weight: 500;
        }}
        
        .connection-status.connected {{
            background: rgba(40, 167, 69, 0.1);
            border: 1px solid {CassavaTheme.COLORS['success_green']};
            color: {CassavaTheme.COLORS['success_green']};
        }}
        
        .connection-status.disconnected {{
            background: rgba(220, 53, 69, 0.1);
            border: 1px solid {CassavaTheme.COLORS['danger_red']};
            color: {CassavaTheme.COLORS['danger_red']};
        }}
        
        .connection-status.connecting {{
            background: rgba(255, 193, 7, 0.1);
            border: 1px solid {CassavaTheme.COLORS['warning_orange']};
            color: {CassavaTheme.COLORS['warning_orange']};
        }}
        
        /* Buttons */
        .stButton > button {{
            background: linear-gradient(90deg, var(--cassava-blue) 0%, var(--cassava-teal) 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(0, 102, 204, 0.3);
        }}
        
        /* Site/Cell Selection */
        .site-selector {{
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        /* Parameter Controls */
        .parameter-control {{
            background: {CassavaTheme.COLORS['light_gray']};
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            border: 1px solid #dee2e6;
        }}
        
        .parameter-title {{
            font-weight: 600;
            color: var(--cassava-dark);
            margin-bottom: 0.5rem;
        }}
        
        /* Toast notifications */
        .toast {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        }}
        
        .toast.success {{ background: {CassavaTheme.COLORS['success_green']}; }}
        .toast.warning {{ background: {CassavaTheme.COLORS['warning_orange']}; }}
        .toast.error {{ background: {CassavaTheme.COLORS['danger_red']}; }}
        
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        
        /* Sidebar styling */
        .css-1d391kg {{
            background: linear-gradient(180deg, var(--cassava-blue) 0%, var(--cassava-dark) 100%);
        }}
        
        .css-1d391kg .css-17ziqus {{
            color: white;
        }}
        
        /* Remove Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    
    @staticmethod
    def render_header(title: str, subtitle: Optional[str] = None):
        """Render Cassava-branded header"""
        header_html = f"""
        <div class="main-header">
            <h1>{title}</h1>
            {f'<p class="subtitle">{subtitle}</p>' if subtitle else ''}
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
    
    @staticmethod
    def render_connection_status(connected: bool, site_count: int = 0, message: str = ""):
        """Render network connection status"""
        if connected:
            status_class = "connected"
            icon = "✅"
            default_msg = f"Connected to Live Network ({site_count} sites accessible)"
        else:
            status_class = "disconnected" 
            icon = "❌"
            default_msg = "Disconnected from Live Network"
        
        status_html = f"""
        <div class="connection-status {status_class}">
            <span style="margin-right: 0.5rem;">{icon}</span>
            <span>{message or default_msg}</span>
        </div>
        """
        st.markdown(status_html, unsafe_allow_html=True)
    
    @staticmethod
    def render_kpi_card(kpi_name: str, technical_name: str, value: float, 
                       unit: str, description: str, status: str = "good"):
        """Render a KPI card with Cassava styling"""
        
        # Status indicators
        status_icons = {
            "good": "✅",
            "warning": "⚠️", 
            "critical": "🔴",
            "no_data": "⭕"
        }
        
        icon = status_icons.get(status, "➖")
        
        card_html = f"""
        <div class="kpi-card status-{status}">
            <div class="kpi-title">
                {icon} {kpi_name}
            </div>
            <div class="kpi-value">
                {value}{unit}
            </div>
            <div class="kpi-description">
                {description}
            </div>
            <div class="kpi-technical">
                Technical: {technical_name}
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
    
    @staticmethod
    def show_toast(message: str, toast_type: str = "success", duration: int = 3000):
        """Show toast notification"""
        toast_html = f"""
        <div class="toast {toast_type}" id="toast-{toast_type}">
            {message}
        </div>
        <script>
        setTimeout(function() {{
            document.getElementById('toast-{toast_type}').style.display = 'none';
        }}, {duration});
        </script>
        """
        st.markdown(toast_html, unsafe_allow_html=True)
    
    @staticmethod
    def render_site_selector(sites: list, current_site: Optional[str] = None):
        """Render site selection interface"""
        st.markdown('<div class="site-selector">', unsafe_allow_html=True)
        st.markdown("### 🏢 Network Site Selection")
        
        site_options = ["📊 All Sites"] + [f"🏗️ {site}" for site in sites]
        selected = st.selectbox(
            "Choose a site to monitor:",
            site_options,
            index=0 if not current_site else (site_options.index(f"🏗️ {current_site}") if f"🏗️ {current_site}" in site_options else 0)
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Return clean site name
        if selected == "📊 All Sites":
            return None
        else:
            return selected.replace("🏗️ ", "")
    
    @staticmethod
    def render_parameter_control(param_name: str, user_friendly_name: str, 
                               description: str, current_value: Any, 
                               param_range: tuple, unit: str):
        """Render parameter control interface"""
        st.markdown(f'<div class="parameter-control">', unsafe_allow_html=True)
        st.markdown(f'<div class="parameter-title">{user_friendly_name}</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"*{description}*")
            st.markdown(f"**Current Value:** {current_value} {unit}")
            st.markdown(f"**Range:** {param_range[0]} to {param_range[1]} {unit}")
        
        with col2:
            if st.button(f"Modify", key=f"modify_{param_name}"):
                st.session_state[f'show_{param_name}_modal'] = True
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """Get color for status"""
        colors = {
            "good": CassavaTheme.COLORS['success_green'],
            "warning": CassavaTheme.COLORS['warning_orange'],
            "critical": CassavaTheme.COLORS['danger_red'],
            "no_data": CassavaTheme.COLORS['text_muted']
        }
        return colors.get(status, CassavaTheme.COLORS['primary_blue'])