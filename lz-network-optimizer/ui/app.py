#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network Optimizer - Streamlit UI (MVP)
Purpose: Natural language optimization interface with AI-powered recommendations
"""

import streamlit as st
import plotly.graph_objects as go
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import local modules
from database_helper import (
    get_all_sites,
    get_site_info,
    get_site_parameters,
    get_site_kpis,
    get_kpi_history,
    get_kpi_threshold,
    get_recent_activity,
    check_api_status,
    get_database_stats
)
from workflow_interface import run_optimization

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LZ-UI')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="LZ 4G Network Optimizer",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS (Cassava Branding)
# ============================================================================

st.markdown("""
<style>
    /* Cassava colors: Navy #001D58, Green #00F19C, Purple #964BEA */
    .stButton>button {
        background-color: #001D58;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        border: none;
    }
    .stButton>button:hover {
        background-color: #00F19C;
        color: #001D58;
    }
    h1, h2, h3 {
        color: #001D58;
    }
    .success-box {
        background-color: #E8FFF3;
        border-left: 4px solid #00F19C;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FFF4E8;
        border-left: 4px solid #964BEA;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #FFE8E8;
        border-left: 4px solid #FF4444;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_logo():
    """Load Cassava logo (theme-aware)."""
    # Check for logo files
    logo_dir = Path(__file__).parent / "assets" / "logos"

    # Try light logo first (default)
    logo_path = logo_dir / "cassava-logo-light.svg"
    if logo_path.exists():
        return str(logo_path)

    # Fallback to main logo
    logo_path = logo_dir / "cassava-logo.svg"
    if logo_path.exists():
        return str(logo_path)

    return None


def display_header():
    """Display page header with logo."""
    logo_path = load_logo()

    if logo_path:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo_path, width=300)
    else:
        st.title("📡 Liquid Zimbabwe 4G Network Optimizer")

    st.markdown("""
        <div style='text-align: center; color: #001D58; margin-bottom: 2rem;'>
            <h3>AI-Powered Network Performance Optimization</h3>
            <p>Natural language interface for intelligent network optimization</p>
        </div>
    """, unsafe_allow_html=True)


def format_parameter_value(param_name: str, value: any) -> str:
    """Format parameter value with units."""
    units = {
        "reference_signal_power_pdschcfg": "dBm",
        "a3_event_offset": "dB",
        "t310_timer": "ms",
        "p0_nominal_pusch": "dBm",
        "pdcch_aggregation_level": ""
    }
    unit = units.get(param_name, "")
    return f"{value} {unit}".strip()


def create_kpi_chart(site_name: str, kpi_name: str, days: int = 7):
    """Create Plotly chart for KPI history."""
    history = get_kpi_history(site_name, kpi_name, days)
    threshold = get_kpi_threshold(kpi_name)

    if not history:
        return None

    dates = [h[0] for h in history]
    values = [h[1] for h in history]

    fig = go.Figure()

    # Add KPI line
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name=kpi_name.replace('_', ' ').title(),
        line=dict(color='#001D58', width=3),
        marker=dict(size=8, color='#001D58')
    ))

    # Add threshold line
    fig.add_hline(
        y=threshold,
        line_dash="dash",
        line_color="#00F19C",
        line_width=2,
        annotation_text=f"Threshold: {threshold}",
        annotation_position="right"
    )

    # Layout
    fig.update_layout(
        title=f"{kpi_name.replace('_', ' ').title()} - {days} Day Trend",
        xaxis_title="Date",
        yaxis_title="Value",
        hovermode='x unified',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#001D58')
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')

    return fig


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'selected_site' not in st.session_state:
    st.session_state.selected_site = None

if 'optimization_result' not in st.session_state:
    st.session_state.optimization_result = None

if 'optimization_running' not in st.session_state:
    st.session_state.optimization_running = False

# ============================================================================
# HEADER
# ============================================================================

display_header()

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### 🏢 Site Selection")

    # Get all sites
    sites = get_all_sites()

    if sites:
        site_names = [site["site_name"] for site in sites]
        selected_site_name = st.selectbox(
            "Select Site",
            site_names,
            index=0 if st.session_state.selected_site is None else site_names.index(st.session_state.selected_site) if st.session_state.selected_site in site_names else 0
        )
        st.session_state.selected_site = selected_site_name

        # Get site info
        site_info = get_site_info(selected_site_name)

        if site_info:
            st.markdown("---")
            st.markdown("### 📍 Site Information")
            st.write(f"**Name:** {site_info['site_name']}")
            st.write(f"**Location:** {site_info['location']}")
            st.write(f"**Cells:** {site_info['cell_count']} (aggregated)")
            st.write(f"**Status:** {site_info['status']}")

        # Get current parameters
        params = get_site_parameters(selected_site_name)

        if params:
            st.markdown("---")
            st.markdown("### 🎛️ Current Parameters")
            st.caption("Read-only display of current configuration")

            param_display = {
                "Signal Power": format_parameter_value("reference_signal_power_pdschcfg", params["reference_signal_power_pdschcfg"]),
                "A3 Offset": format_parameter_value("a3_event_offset", params["a3_event_offset"]),
                "T310 Timer": format_parameter_value("t310_timer", params["t310_timer"]),
                "P0 PUSCH": format_parameter_value("p0_nominal_pusch", params["p0_nominal_pusch"]),
                "PDCCH Agg": format_parameter_value("pdcch_aggregation_level", params["pdcch_aggregation_level"])
            }

            for param, value in param_display.items():
                st.write(f"• **{param}:** {value}")

    else:
        st.error("No sites found in database")

    # System status
    st.markdown("---")
    st.markdown("### 🔧 System Status")

    status = check_api_status()
    for component, status_text in status.items():
        st.write(f"• {status_text}")

    # Database stats
    stats = get_database_stats()
    if stats['latest_update']:
        update_time = datetime.fromisoformat(stats['latest_update'])
        formatted_time = update_time.strftime("%Y-%m-%d %H:%M:%S")
        st.write(f"• **Updated:** {formatted_time}")

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Query Input Section
st.markdown("## 💬 Natural Language Optimization")

query = st.text_area(
    "What would you like to optimize?",
    height=100,
    placeholder="Examples:\n• Optimize download speed for this site\n• Improve network access success\n• Fix upload quality issues",
    disabled=st.session_state.optimization_running
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_button = st.button(
        "🚀 Run Optimization",
        use_container_width=True,
        disabled=st.session_state.optimization_running or not query.strip()
    )

# Handle optimization execution
if run_button and query.strip() and st.session_state.selected_site:
    st.session_state.optimization_running = True
    st.session_state.optimization_result = None

    with st.spinner("🤖 AI agents analyzing network... This may take 30-60 seconds"):
        try:
            # Get site info for cell_id
            site_info = get_site_info(st.session_state.selected_site)
            cell_id = site_info['cell_id'] if site_info else 1

            # Run optimization
            result = run_optimization(
                st.session_state.selected_site,
                cell_id,
                query.strip()
            )

            st.session_state.optimization_result = result
            st.session_state.optimization_running = False
            st.rerun()

        except Exception as e:
            st.error(f"Optimization failed: {str(e)}")
            st.session_state.optimization_running = False

# Display Results
if st.session_state.optimization_result:
    st.markdown("---")
    st.markdown("## 📋 Optimization Results")

    result = st.session_state.optimization_result

    if result['status'] == 'success':
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("### ✅ Optimization Completed")
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🎯 Issue Identified")
            st.write(result['issue'])

            st.markdown("#### 💡 Recommended Changes")
            if result['recommendations']:
                for rec in result['recommendations']:
                    st.write(f"• **{rec['parameter']}:** {rec['description']}")
            else:
                st.write("No specific changes recommended")

        with col2:
            st.markdown("#### ⚠️ Risk Assessment")
            risk_color = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(result['risk_level'], "⚪")
            st.write(f"{risk_color} **{result['risk_level']}** (Score: {result['risk_score']}/10)")

            st.markdown("#### 📈 Expected Impact")
            st.write(result['expected_impact'])

        if result['mml_commands']:
            st.markdown("#### 📝 MML Commands")
            st.code('\n'.join(result['mml_commands']), language='text')

        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✓ Approve & Execute", use_container_width=True):
                st.info("Execution feature will be implemented in Phase 3.1")
        with col2:
            if st.button("✗ Reject", use_container_width=True):
                st.session_state.optimization_result = None
                st.rerun()

    elif result['status'] == 'rejected':
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("### ⚠️ Optimization Rejected")
        st.write(result['message'])
        st.markdown('</div>', unsafe_allow_html=True)

    elif result['status'] == 'error':
        st.markdown('<div class="error-box">', unsafe_allow_html=True)
        st.markdown("### ❌ Error")
        st.write(result.get('error_message', 'Unknown error occurred'))
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# TABS
# ============================================================================

st.markdown("---")
tab1, tab2 = st.tabs(["📊 Historical Trends", "📝 Activity Log"])

# Historical Trends Tab
with tab1:
    st.markdown("### 📊 KPI Historical Trends")

    if st.session_state.selected_site:
        col1, col2 = st.columns([2, 1])

        with col1:
            kpi_options = {
                "network_access_success": "Network Access Success (%)",
                "download_speed": "Download Speed (Mbps)",
                "upload_speed": "Upload Speed (Mbps)",
                "download_quality": "Download Quality (%)",
                "upload_quality": "Upload Quality (%)",
                "control_channel_load": "Control Channel Load (%)",
                "feedback_channel_load": "Feedback Channel Load (%)"
            }

            selected_kpi = st.selectbox(
                "Select KPI to visualize",
                list(kpi_options.keys()),
                format_func=lambda x: kpi_options[x]
            )

        with col2:
            days = st.selectbox("Time Range", [7, 14, 30, 60, 90], index=0, format_func=lambda x: f"Last {x} Days")

        # Create and display chart
        fig = create_kpi_chart(st.session_state.selected_site, selected_kpi, days)

        if fig:
            st.plotly_chart(fig, use_container_width=True)

            # Display current value vs threshold
            kpis = get_site_kpis(st.session_state.selected_site)
            if kpis:
                current_value = kpis[selected_kpi]
                threshold = get_kpi_threshold(selected_kpi)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Value", f"{current_value:.2f}")
                with col2:
                    st.metric("Threshold", f"{threshold:.2f}")
                with col3:
                    status = "🟢 Above" if current_value >= threshold else "🔴 Below"
                    st.metric("Status", status)
        else:
            st.info("No historical data available for this KPI")
    else:
        st.info("Please select a site to view trends")

# Activity Log Tab
with tab2:
    st.markdown("### 📝 Recent Activity")

    activities = get_recent_activity(limit=10)

    if activities:
        for activity in activities:
            timestamp = datetime.fromisoformat(activity['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
            status_icon = {"success": "✅", "rejected": "❌", "detected": "🔍"}.get(activity.get('status', 'info'), "ℹ️")

            st.markdown(f"**{timestamp}** | {activity['site_name']}")
            st.write(f"{status_icon} {activity['description']}")
            if activity.get('changes'):
                st.caption(f"Changes: {activity['changes']}")
            if activity.get('result'):
                st.caption(f"Result: {activity['result']}")
            st.markdown("---")
    else:
        st.info("No recent activity. Start by running an optimization!")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8rem;'>
    <p>Liquid Zimbabwe 4G Network Optimizer | Powered by NVIDIA AI & LangGraph</p>
    <p>Phase 3 MVP | Cassava AI © 2025</p>
</div>
""", unsafe_allow_html=True)
