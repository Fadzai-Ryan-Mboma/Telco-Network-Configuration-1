#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network Optimizer - Streamlit UI (MVP)
Purpose: Natural language optimization interface with AI-powered recommendations
"""

import streamlit as st
import plotly.graph_objects as go
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for utils import
sys.path.insert(0, str(Path(__file__).parent.parent))

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
    get_database_stats,
    get_live_parameters,
    get_site_parameters_with_live,
    log_optimization_query,
    update_optimization_query_status,
    init_optimization_queries_table
)
from workflow_interface import run_optimization

# Initialize optimization queries table
init_optimization_queries_table()

# Setup enhanced logging if configured
try:
    from utils.logging_config import setup_logging
    log_mode = os.getenv('LZ_LOG_MODE', 'basic')
    log_file = os.getenv('LZ_LOG_FILE', None)
    workflow_logger = setup_logging(mode=log_mode, log_file=log_file)
    logger = logging.getLogger('LZ-UI')
    logger.info(f"🚀 Enhanced logging enabled: {log_mode} mode")
except ImportError:
    # Fallback to basic logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('LZ-UI')
    workflow_logger = None

# ============================================================================
# CACHED DATA FETCHING (prevents UI dimming on reruns)
# ============================================================================

# FastAPI endpoint for live parameters (runs on port 8503)
FASTAPI_BASE_URL = os.getenv("FASTAPI_URL", "http://localhost:8503")

@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_params_cached(site_name: str):
    """Cached fetch of live parameters - prevents UI blocking on reruns.
    Cache expires after 5 minutes (ttl=300) or when manually cleared.
    """
    return get_live_parameters(site_name)


@st.cache_data(ttl=60, show_spinner=False)
def fetch_params_from_api(site_name: str) -> dict:
    """Fetch parameters from FastAPI endpoint with caching."""
    import requests
    try:
        response = requests.get(
            f"{FASTAPI_BASE_URL}/api/params/{site_name}",
            timeout=15
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"FastAPI fetch failed: {e}")
    return None


def display_current_parameters_live(site_name: str):
    """
    Display current parameters fetched from FastAPI.
    Uses caching to prevent repeated API calls on Streamlit reruns.
    """
    st.markdown("### Current Parameters")
    
    # Fetch from cached API call (no spinner needed due to caching)
    data = fetch_params_from_api(site_name)
    
    if data and data.get("parameters"):
        params = data["parameters"]
        status = data.get("status", "")
        
        # Determine caption based on status
        if status == "success":
            st.caption("📡 **Live from Huawei API**")
        elif status == "fallback":
            if data.get("site_offline"):
                st.caption("⚠️ **From database (Site is unavailable)**")
            else:
                st.caption("⚠️ **From database (API unavailable)**")
        else:
            st.caption("📊 **From database**")
        
        # Display each parameter
        for key, info in params.items():
            label = {
                "reference_signal_power_pdschcfg": "Signal Power",
                "a3_event_offset": "A3 Offset",
                "t310_timer": "T310 Timer",
                "p0_nominal_pusch": "P0 PUSCH",
                "pdcch_aggregation_level": "PDCCH Agg"
            }.get(key, key)
            
            value = info.get("value")
            unit = info.get("unit", "")
            display_val = value if value is not None else "N/A"
            st.write(f"• **{label}:** {display_val} {unit}")
    else:
        # Last resort: direct database query
        db_params = get_site_parameters(site_name)
        if db_params:
            st.caption("⚠️ **From database (API unavailable)**")
            param_display = {
                "Signal Power": format_parameter_value("reference_signal_power_pdschcfg", db_params.get("reference_signal_power_pdschcfg", "N/A")),
                "A3 Offset": format_parameter_value("a3_event_offset", db_params.get("a3_event_offset", "N/A")),
                "T310 Timer": format_parameter_value("t310_timer", db_params.get("t310_timer", "N/A")),
                "P0 PUSCH": format_parameter_value("p0_nominal_pusch", db_params.get("p0_nominal_pusch", "N/A")),
                "PDCCH Agg": format_parameter_value("pdcch_aggregation_level", db_params.get("pdcch_aggregation_level", "N/A"))
            }
            for param, value in param_display.items():
                st.write(f"• **{param}:** {value}")
        else:
            st.warning("No parameter data available")

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="LZ 4G Network Optimizer",
    page_icon="",
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
        st.markdown(
            f"""
            <div style='display: flex; flex-direction: column; align-items: center; margin-bottom: 1rem;'>
                <img src='data:image/svg+xml;base64,{__import__('base64').b64encode(open(logo_path, 'rb').read()).decode()}' width='300' style='margin-bottom: 0.5rem;'/>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown("<h1 style='text-align: center;'>Liquid Zimbabwe 4G Network Optimizer</h1>", unsafe_allow_html=True)

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


def format_detailed_section(content: str, section_type: str) -> str:
    """
    Format detailed technical content for better visual presentation.
    
    Args:
        content: Raw text content from config_output
        section_type: Type of section (issue, recommendations, risk, impact)
        
    Returns:
        HTML-formatted string for better display
    """
    if not content:
        return ""
    
    lines = content.strip().split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Primary/Secondary headers
        if line.startswith('Primary:'):
            formatted_lines.append(f"<p style='margin-bottom: 0.5em;'><strong style='color: #001D58;'>{line}</strong></p>")
        elif line.startswith('Secondary'):
            formatted_lines.append(f"<p style='margin-top: 1em; margin-bottom: 0.5em;'><strong style='color: #555;'>{line}</strong></p>")
        
        # Parameter sections
        elif 'Parameter:' in line:
            formatted_lines.append(f"<p style='margin-top: 0.8em; margin-bottom: 0.3em;'><strong style='color: #001D58;'>{line}</strong></p>")
        
        # Current/Recommended/Change lines with code styling
        elif any(line.startswith(prefix) for prefix in ['Current:', 'Recommended:', 'Change:', 'Reasoning:']):
            parts = line.split(':', 1)
            if len(parts) == 2:
                label, value = parts
                formatted_lines.append(f"<p style='margin: 0.2em 0; margin-left: 1em;'><span style='color: #666;'>{label}:</span> <code style='background-color: #f5f5f5; padding: 2px 6px; border-radius: 3px; color: #333;'>{value.strip()}</code></p>")
            else:
                formatted_lines.append(f"<p style='margin: 0.2em 0; margin-left: 1em; color: #666;'>{line}</p>")
        
        # Risk factors and bullet points
        elif line.startswith('•') or line.startswith('-'):
            # Color code based on content
            color = '#333'
            if any(word in line.lower() for word in ['improve', 'increase', 'success', 'better', 'optimization']):
                color = '#28a745'  # Green for positive
            elif any(word in line.lower() for word in ['risk', 'warning', 'monitor', 'caution', 'degradation']):
                color = '#fd7e14'  # Orange for warnings
            
            formatted_lines.append(f"<p style='margin: 0.3em 0; margin-left: 1.5em; color: {color};'>{line}</p>")
        
        # Performance metrics
        elif '→' in line or any(op in line for op in ['+%', 'Mbps', 'dBm', 'ms', '%)']):
            formatted_lines.append(f"<p style='margin: 0.3em 0; margin-left: 1em; font-family: monospace; background-color: #f8f9fa; padding: 4px 8px; border-radius: 3px; color: #333;'>{line}</p>")
        
        # Technical layers (PHY/MAC/RRC)
        elif any(layer in line for layer in ['PHY Layer:', 'MAC Layer:', 'RRC Layer:']):
            formatted_lines.append(f"<p style='margin: 0.5em 0; margin-left: 1em; color: #6610f2; font-weight: 500;'>{line}</p>")
        
        # Risk scores with colored indicators
        elif 'Score:' in line and '/10' in line:
            if '🟢' in line or 'LOW' in line:
                formatted_lines.append(f"<p style='margin: 0.5em 0; color: #28a745; font-weight: 600;'>{line}</p>")
            elif '🟡' in line or 'MEDIUM' in line:
                formatted_lines.append(f"<p style='margin: 0.5em 0; color: #ffc107; font-weight: 600;'>{line}</p>")
            elif '🔴' in line or 'HIGH' in line:
                formatted_lines.append(f"<p style='margin: 0.5em 0; color: #dc3545; font-weight: 600;'>{line}</p>")
            else:
                formatted_lines.append(f"<p style='margin: 0.5em 0; font-weight: 600;'>{line}</p>")
        
        # Trade-off warnings
        elif 'Trade-off:' in line or 'Trade-' in line:
            formatted_lines.append(f"<p style='margin: 0.8em 0; padding: 8px; background-color: #fff3cd; border-left: 4px solid #ffc107; color: #856404;'><strong>⚖️ {line}</strong></p>")
        
        # Enhanced monitoring warnings
        elif '⚠️' in line or 'Enhanced monitoring' in line:
            formatted_lines.append(f"<p style='margin: 0.8em 0; padding: 8px; background-color: #fff3cd; border-left: 4px solid #fd7e14; color: #856404;'>{line}</p>")
        
        # Default text
        else:
            formatted_lines.append(f"<p style='margin: 0.3em 0; color: #333;'>{line}</p>")
    
    return '<div style="line-height: 1.6;">' + ''.join(formatted_lines) + '</div>'


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

    # Add operating average line
    fig.add_hline(
        y=threshold,
        line_dash="dash",
        line_color="#00F19C",
        line_width=2,
        annotation_text=f"Operating Average: {threshold}",
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

if 'current_query_id' not in st.session_state:
    st.session_state.current_query_id = -1

# ============================================================================
# HEADER
# ============================================================================

display_header()

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### Site Selection")

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
            st.markdown("### Site Information")
            st.write(f"**Name:** {site_info['site_name']}")
            st.write(f"**Location:** {site_info['location']}")
            st.write(f"**Cells:** {site_info['cell_count']} (aggregated)")
            st.write(f"**Status:** {site_info['status']}")

        # Current Parameters - Fetched from FastAPI with caching
        st.markdown("---")
        display_current_parameters_live(selected_site_name)

    else:
        st.error("No sites found in database")

    # System status
    st.markdown("---")
    st.markdown("### System Status")

    # Pass selected site to check NE connectivity
    selected_site = st.session_state.get("selected_site")
    status = check_api_status(selected_site)
    
    # Display in order: API, NEs, DB
    st.write(f"• {status.get('api', '❌ API Unreachable')}")
    st.write(f"• {status.get('ne', '⚠️ NEs Unknown')}")
    st.write(f"• {status.get('db', '❌ DB Unreachable')}")

    # Database stats
    stats = get_database_stats()
    if stats['latest_update']:
        update_time = datetime.fromisoformat(stats['latest_update'])
        formatted_date = update_time.strftime("%Y-%m-%d")
        st.write(f"• **DB Updated:** {formatted_date}")

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Query Input Section
st.markdown("## Optimization Query")

query = st.text_area(
    "What would you like to optimize?",
    height=100,
    placeholder="Examples:\n• Optimize download speed for this site\n• Improve network access success\n• Fix upload quality issues",
    disabled=st.session_state.optimization_running
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_button = st.button(
        "Run Optimization",
        use_container_width=True,
        disabled=st.session_state.optimization_running or not query.strip()
    )

# Handle optimization execution
if run_button and query.strip() and st.session_state.selected_site:
    st.session_state.optimization_running = True
    st.session_state.optimization_result = None

    # Log the query as incomplete initially
    query_id = log_optimization_query(
        site_name=st.session_state.selected_site,
        user_query=query.strip(),
        status="incomplete"
    )
    st.session_state.current_query_id = query_id

    with st.spinner("🔄 AI agents analyzing network... This may take 30-60 seconds"):
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
            
            # Update query log with recommendation summary
            if query_id > 0 and result:
                rec_summary = result.get('issue', 'No issue identified')
                kpi_issue = result.get('kpi_issue', result.get('issue', ''))
                update_optimization_query_status(
                    query_id=query_id,
                    status="incomplete",  # Still incomplete until approved/rejected
                    recommendation_summary=rec_summary,
                    kpi_issue=kpi_issue
                )
            
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
        st.markdown("### 🔍 Details")
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🎯 Issue Identified")
            if 'detailed_issue' in result and result['detailed_issue']:
                formatted_issue = format_detailed_section(result['detailed_issue'], 'issue')
                st.markdown(formatted_issue, unsafe_allow_html=True)
            else:
                st.write(result['issue'])

            st.markdown("#### 💡 Recommended Changes")
            if 'detailed_recommendations' in result and result['detailed_recommendations']:
                formatted_recs = format_detailed_section(result['detailed_recommendations'], 'recommendations')
                st.markdown(formatted_recs, unsafe_allow_html=True)
            elif result['recommendations']:
                for rec in result['recommendations']:
                    st.write(f"• **{rec['parameter']}:** {rec['description']}")
            else:
                st.write("No specific changes recommended")

        with col2:
            st.markdown("#### ⚠️ Risk Assessment")
            if 'detailed_risk' in result and result['detailed_risk']:
                formatted_risk = format_detailed_section(result['detailed_risk'], 'risk')
                st.markdown(formatted_risk, unsafe_allow_html=True)
            else:
                risk_color = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(result['risk_level'], "⚪")
                st.write(f"{risk_color} **{result['risk_level']}** (Score: {result['risk_score']}/10)")

            st.markdown("#### 📈 Expected Impact")
            if 'detailed_impact' in result and result['detailed_impact']:
                formatted_impact = format_detailed_section(result['detailed_impact'], 'impact')
                st.markdown(formatted_impact, unsafe_allow_html=True)
            else:
                st.write(result['expected_impact'])

        if result['mml_commands']:
            st.markdown("#### 📝 MML Commands")
            st.code('\n'.join(result['mml_commands']), language='text')

        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✓ Approve & Execute", use_container_width=True):
                # Execute the optimization
                if st.session_state.selected_site:
                    with st.spinner("🔄 Executing optimization..."):
                        try:
                            from ui.workflow_interface import execute_optimization
                            exec_result = execute_optimization(
                                st.session_state.selected_site,
                                result['recommendations'],
                                result['mml_commands']
                            )

                            # Store execution result
                            st.session_state.execution_result = exec_result
                            
                            # Update query status to approved
                            if hasattr(st.session_state, 'current_query_id') and st.session_state.current_query_id > 0:
                                update_optimization_query_status(
                                    query_id=st.session_state.current_query_id,
                                    status="approved",
                                    execution_result=exec_result.get('message', 'Executed')
                                )
                            
                            # Invalidate cached params to force re-fetch after mod
                            fetch_live_params_cached.clear()
                            
                            st.rerun()

                        except Exception as e:
                            st.error(f"Execution failed: {str(e)}")
                else:
                    st.error("No site selected")
        with col2:
            if st.button("✗ Reject", use_container_width=True):
                # Update query status to rejected
                if hasattr(st.session_state, 'current_query_id') and st.session_state.current_query_id > 0:
                    update_optimization_query_status(
                        query_id=st.session_state.current_query_id,
                        status="rejected"
                    )
                st.session_state.optimization_result = None
                st.rerun()

        # Display execution result if available
        if 'execution_result' in st.session_state and st.session_state.execution_result:
            exec_res = st.session_state.execution_result

            st.markdown("---")
            st.markdown("### 🎯 Execution Results")

            if exec_res['status'] == 'success':
                st.success(exec_res['message'])
                if exec_res.get('dry_run'):
                    st.info("ℹ️ System is in DRY-RUN mode. No actual changes were made to the network.")
            elif exec_res['status'] == 'partial':
                st.warning(exec_res['message'])
            else:
                st.error(exec_res['message'])

            # Show details
            if exec_res.get('details'):
                with st.expander("📝 Execution Details"):
                    for detail in exec_res['details']:
                        status_icon = "✓" if detail['status'] == 'success' else "✗"
                        st.write(f"{status_icon} {detail['command']}")

            # Clear button
            if st.button("🗑️ Clear Results"):
                st.session_state.execution_result = None
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
            days = st.selectbox("Time Range", [7, 14, 30, 60, 90, 120, 180], index=0, format_func=lambda x: f"Last {x} Days")

        # Create and display chart
        fig = create_kpi_chart(st.session_state.selected_site, selected_kpi, days)

        if fig:
            st.plotly_chart(fig, use_container_width=True)

            # Display current value vs operating average
            kpis = get_site_kpis(st.session_state.selected_site)
            if kpis:
                current_value = kpis[selected_kpi]
                threshold = get_kpi_threshold(selected_kpi)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Value", f"{current_value:.2f}")
                with col2:
                    st.metric("Operating Average", f"{threshold:.2f}")
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
    <p>Cassava 4G Network Optimizer | Powered by NVIDIA</p>
    <p>Cassava AI © 2025</p>
</div>
""", unsafe_allow_html=True)
