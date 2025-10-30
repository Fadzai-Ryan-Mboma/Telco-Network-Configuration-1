#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Demo - Enhanced Streamlit UI
Interactive web interface for the 6-stage agentic workflow demonstration
Enhanced with liquid-4g-core styling, logos, and professional layout
"""

import streamlit as st
import asyncio
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
import time
from datetime import datetime, timedelta
import os
import sys
import yaml
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LZ-Demo-UI')

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'prompts'))

try:
    from bindura_data_loader import BinduraDataLoader
    from prompt_templates import PromptTemplates, ContextBuilder
    DATA_LOADER_AVAILABLE = True
except ImportError:
    st.error("Required modules not found. Please ensure all dependencies are installed.")
    DATA_LOADER_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="LZ 4G Network Optimizer - Agentic Demo",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_theme_colors():
    """Get Liquid Zimbabwe brand colors"""
    return {
        'primary_color': '#001d58',      # Dark blue
        'secondary_bg': '#00f19c',       # Bright green
        'background_color': '#ffffff',   # White
        'text_color': '#00082f',         # Very dark blue
        'accent_color': '#f63366',       # Red accent
        'success_color': '#00f19c',      # Green
        'warning_color': '#ff8c00',      # Orange
        'error_color': '#ff4444'         # Red
    }

def load_logo(logo_type="main", theme=None):
    """Load logo based on type and theme"""
    # Check for logo assets
    assets_path = Path(__file__).parent / "assets" / "logos"
    
    # Map logo types to filenames
    logo_files = {
        "main": "cassava-logo.svg",
        "icon": "cassava-logo-icon.svg",
        "dark": "cassava-logo-dark.svg", 
        "light": "cassava-logo-light.svg"
    }
    
    # Auto-detect theme if not specified
    if theme is None:
        try:
            theme = st.get_option("theme.base")
        except:
            theme = "light"
    
    # Use theme-appropriate logo for main type
    if logo_type == "main":
        if theme == "dark":
            logo_file = logo_files["dark"]
        else:
            logo_file = logo_files["light"]
    else:
        logo_file = logo_files.get(logo_type, logo_files["main"])
    
    logo_path = assets_path / logo_file
    
    # Check if logo exists, return path if found
    if logo_path.exists():
        return str(logo_path)
    else:
        logger.warning(f"Logo not found: {logo_path}")
        return None

def display_header_logo():
    """Display main logo in header with responsive design"""
    logo_path = load_logo("main")
    
    if logo_path:
        # Create columns for centered logo
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo_path, width=300)
    else:
        # Fallback to text header
        st.title("📡 Liquid Zimbabwe 4G Network Optimizer")

def display_sidebar_logo():
    """Display compact logo in sidebar"""
    logo_path = load_logo("icon")
    
    if logo_path:
        # Center the icon in sidebar
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo_path, width=64)
    else:
        # Fallback to emoji
        st.markdown("# 📡")

def apply_custom_styling():
    """Apply Liquid Zimbabwe custom CSS styling"""
    colors = get_theme_colors()
    
    st.markdown(f"""
    <style>
    /* Import brand fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styling */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    
    /* Header styling */
    h1, h2, h3 {{
        color: {colors['primary_color']};
        font-family: 'Inter', sans-serif;
        font-weight: 600;
    }}
    
    /* Metric cards */
    .metric-card {{
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 10px rgba(0, 29, 88, 0.1);
        border: 1px solid rgba(0, 29, 88, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    
    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0, 29, 88, 0.15);
    }}
    
    .critical-metric {{
        background: linear-gradient(135deg, #fff5f5 0%, #ffebee 100%);
        border-left: 4px solid {colors['error_color']};
        border-color: {colors['error_color']};
    }}
    
    .warning-metric {{
        background: linear-gradient(135deg, #fffaf5 0%, #fff3e0 100%);
        border-left: 4px solid {colors['warning_color']};
        border-color: {colors['warning_color']};
    }}
    
    .success-metric {{
        background: linear-gradient(135deg, #f5fff5 0%, #e8f5e8 100%);
        border-left: 4px solid {colors['success_color']};
        border-color: {colors['success_color']};
    }}
    
    /* Agentic workflow styling */
    .agent-card {{
        background: {colors['background_color']};
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 2px solid {colors['secondary_bg']};
        box-shadow: 0 4px 15px rgba(0, 241, 156, 0.1);
    }}
    
    .agent-title {{
        color: {colors['primary_color']};
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }}
    
    .agent-status {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }}
    
    .status-running {{
        background: {colors['warning_color']};
        color: white;
    }}
    
    .status-completed {{
        background: {colors['success_color']};
        color: {colors['primary_color']};
    }}
    
    .status-pending {{
        background: #e0e0e0;
        color: #666;
    }}
    
    /* Data visualization enhancements */
    .chart-container {{
        background: {colors['background_color']};
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 29, 88, 0.05);
    }}
    
    /* Sidebar enhancements */
    .sidebar .sidebar-content {{
        background: linear-gradient(180deg, {colors['background_color']} 0%, #f8f9ff 100%);
    }}
    
    /* Button styling */
    .stButton > button {{
        background: linear-gradient(135deg, {colors['primary_color']} 0%, #003d8a 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }}
    
    .stButton > button:hover {{
        background: linear-gradient(135deg, #003d8a 0%, {colors['primary_color']} 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 29, 88, 0.3);
    }}
    
    /* Progress bars */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, {colors['secondary_bg']} 0%, {colors['primary_color']} 100%);
    }}
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: {colors['background_color']};
        border-radius: 8px 8px 0 0;
        color: {colors['text_color']};
        font-weight: 500;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {colors['secondary_bg']};
        color: {colors['primary_color']};
    }}
    
    /* Notification styling */
    .notification-success {{
        background: {colors['success_color']};
        color: {colors['primary_color']};
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: 500;
    }}
    
    .notification-warning {{
        background: {colors['warning_color']};
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: 500;
    }}
    
    .notification-error {{
        background: {colors['error_color']};
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: 500;
    }}
    </style>
    """, unsafe_allow_html=True)

def main():
    """Main application function with enhanced liquid-4g-core styling"""
    # Apply custom styling
    apply_custom_styling()
    
    # Display header logo
    display_header_logo()
    
    # Enhanced title with subtitle
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <h1 style="margin-bottom: 0.5rem;">🇿🇼 Liquid Zimbabwe 4G Network Optimization</h1>
        <h3 style="color: #666; font-weight: 400;">Real Bindura Network Data - 6-Stage Agentic Workflow Demo</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced sidebar with logo
    with st.sidebar:
        display_sidebar_logo()
        st.markdown("---")
        
        st.header("🎯 Demo Configuration")
        demo_mode = st.selectbox(
            "Select Demo Mode",
            ["Real Data Analysis", "Agentic Workflow Simulation", "Prompt Architecture Demo", "Historical Comparison"],
            help="Choose the type of demonstration to run"
        )
        
        # Add connection status indicator
        st.markdown("---")
        st.subheader("🔗 System Status")
        
        # Mock system status (would be real in production)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Data Status", "✅ Active", help="Real Bindura data available")
        with col2:
            st.metric("Agents", "6 Ready", help="All workflow agents operational")
        
        # Add quick stats
        st.markdown("---")
        st.subheader("📊 Quick Stats")
        st.metric("Sites", "4 Bindura", delta="-Critical Issues", delta_color="inverse")
        st.metric("Records", "168", delta="+7 days", delta_color="normal")
        st.metric("RACH Rate", "0.536%", delta="-99.5%", delta_color="inverse")
    
    # Main content area with tabs
    if demo_mode == "Real Data Analysis":
        show_real_data_analysis_enhanced()
    elif demo_mode == "Agentic Workflow Simulation":
        show_agentic_workflow_simulation()
    elif demo_mode == "Prompt Architecture Demo":
        show_prompt_architecture_demo()
    else:
        show_historical_comparison_enhanced()

def show_real_data_analysis_enhanced():
    """Enhanced real data analysis with liquid-4g-core styling"""
    st.header("📊 Real Bindura Network Data Analysis")
    
    # Check if data file exists
    data_file = "../data/historical_data.csv"
    if not os.path.exists(data_file):
        st.error(f"Data file not found: {data_file}")
        st.info("Please ensure the historical_data.csv file is available in the data directory.")
        
        # Show demo data instead
        st.subheader("📊 Demo Network Analysis")
        show_demo_analysis()
        return
    
    if not DATA_LOADER_AVAILABLE:
        st.warning("⚠️ Data loader not available. Showing demo analysis instead.")
        show_demo_analysis()
        return
    
    try:
        # Load and analyze data with progress indication
        with st.spinner("Loading real Bindura network data..."):
            data_loader = BinduraDataLoader(data_file)
            analysis = data_loader.analyze_data()
        
        st.success("✅ Real network data loaded successfully!")
        
        # Enhanced data overview with styled metrics
        st.subheader("📈 Network Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Records", analysis.get("total_records", "168"), help="Historical measurements analyzed")
        with col2:
            st.metric("Sites Analyzed", analysis.get("sites", "4"), help="Bindura network sites")
        with col3:
            st.metric("Date Range", analysis.get("date_range", "7 days"), help="Data collection period")
        with col4:
            st.metric("Data Quality", analysis.get("status", "active").title(), help="Data validation status")
        
        # Display enhanced analysis with loaded data
        show_enhanced_metrics_analysis()
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Showing demo analysis instead...")
        show_demo_analysis()

def show_demo_analysis():
    """Show demo analysis when real data is not available"""
    st.subheader("📈 Network Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", "168", help="Historical measurements analyzed")
    with col2:
        st.metric("Sites Analyzed", "4", help="Bindura network sites")
    with col3:
        st.metric("Date Range", "7 days", help="Data collection period")
    with col4:
        st.metric("Data Quality", "Active", help="Data validation status")
    
    show_enhanced_metrics_analysis()

def show_enhanced_metrics_analysis():
    """Show enhanced metrics analysis with visualizations"""
    # Critical findings with enhanced styling
    st.subheader("🚨 Critical Performance Crisis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="metric-card critical-metric">
            <div class="agent-title">🚨 RACH Performance Crisis</div>
            <p style="font-size: 1.5rem; font-weight: 600; color: #d32f2f; margin: 0.5rem 0;">0.536%</p>
            <p><strong>Expected:</strong> >90% | <strong>Status:</strong> <span style="color: #d32f2f; font-weight: 600;">CRITICAL EMERGENCY</span></p>
            <p><strong>Impact:</strong> Severe accessibility issues - users cannot connect to network</p>
            <p><strong>Business Impact:</strong> Service availability crisis affecting all Bindura users</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card warning-metric">
            <div class="agent-title">⚠️ DL Quality Issues</div>
            <p style="font-size: 1.5rem; font-weight: 600; color: #f57c00; margin: 0.5rem 0;">15.94%</p>
            <p><strong>Expected:</strong> <8% | <strong>Status:</strong> <span style="color: #f57c00; font-weight: 600;">HIGH PRIORITY</span></p>
            <p><strong>Impact:</strong> Poor data quality severely degrading user experience</p>
            <p><strong>User Effect:</strong> Slow downloads, failed data transfers, poor video quality</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced data visualizations
    st.subheader("📊 Network Performance Trends")
    
    tabs = st.tabs(["📈 RACH Analysis", "📉 Quality Metrics", "🗺️ Site Distribution", "🔍 Root Cause"])
    
    with tabs[0]:
        # RACH performance visualization
        st.markdown("### 📈 RACH Performance Analysis")
        
        # Create mock RACH data for visualization
        dates = pd.date_range(start='2024-10-01', end='2024-10-07', freq='D')
        rach_data = pd.DataFrame({
            'date': dates,
            'rach_success_rate': [0.8, 0.6, 0.4, 0.3, 0.536, 0.52, 0.48],
            'rach_attempts': [1200, 1150, 1100, 1080, 1050, 1030, 1000]
        })
        metrics_data = {
            "KPI": ["RACH Success Rate", "DL IBLER", "Average Throughput", "Connection Success"],
            "Current Value": [0.536, 15.94, 8.5, 65.0],
            "Target Value": [5.0, 12.0, 15.0, 85.0],
            "Industry Benchmark": [95.0, 8.0, 25.0, 98.0]
        }
        
        df = pd.DataFrame(metrics_data)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Current Performance',
            x=df['KPI'],
            y=df['Current Value'],
            marker_color='#f44336'
        ))
        
        fig.add_trace(go.Bar(
            name='Target Performance',
            x=df['KPI'],
            y=df['Target Value'],
            marker_color='#ff9800'
        ))
        
        fig.add_trace(go.Bar(
            name='Industry Benchmark',
            x=df['KPI'],
            y=df['Industry Benchmark'],
            marker_color='#4caf50'
        ))
        
        fig.update_layout(
            title="Bindura Network Performance vs Targets",
            xaxis_title="Key Performance Indicators",
            yaxis_title="Performance Value",
            barmode='group',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Data insights
        st.subheader("💡 Key Insights")
        
        insights = [
            "🔴 **Critical Access Issues**: RACH success rate of 0.536% indicates severe network accessibility problems",
            "🟡 **Quality Degradation**: IBLER of 15.94% suggests significant signal quality issues affecting user experience", 
            "📱 **User Impact**: Low connection success rates directly impact customer satisfaction and revenue",
            "⚡ **Optimization Potential**: Significant improvement opportunities exist with targeted parameter optimization",
            "🎯 **Immediate Action Required**: Critical network parameters need immediate optimization to restore service quality"
        ]
        
        for insight in insights:
            st.markdown(insight)

def show_workflow_simulation():
    """Show the 6-stage workflow simulation"""
    st.header("🔄 6-Stage Agentic Workflow Simulation")
    
    # Workflow stages
    stages = [
        {"name": "Network Connector", "icon": "📡", "description": "Site discovery and connectivity validation"},
        {"name": "Monitoring Agent", "icon": "📊", "description": "KPI collection and real-time monitoring"},
        {"name": "KPI Analytics", "icon": "📈", "description": "Advanced analytics and correlation analysis"},
        {"name": "Configuration Agent", "icon": "⚙️", "description": "Optimization configuration generation"},
        {"name": "Validation Agent", "icon": "✅", "description": "Safety validation and risk assessment"},
        {"name": "Execution Agent", "icon": "🔧", "description": "Configuration deployment and monitoring"}
    ]
    
    # Workflow control
    if st.button("🚀 Start Agentic Workflow Simulation"):
        st.success("Workflow simulation started! This is a demo simulation.")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, stage in enumerate(stages):
            progress = (i + 1) / len(stages)
            progress_bar.progress(progress)
            status_text.text(f"Executing Stage {i+1}: {stage['name']}")
            
            # Show stage details
            with st.expander(f"{stage['icon']} Stage {i+1}: {stage['name']}", expanded=True):
                st.write(stage['description'])
                
                if i == 0:  # Network Connector
                    st.write("**Discovered Sites:**")
                    sites = ["MSH0013-Bindura-Zaoga", "MSH-0331-Chiwaridzo 2", "MSH-0112-Bindura Hospital", "MSH-0014-Chipadze"]
                    for site in sites:
                        st.write(f"✅ {site}")
                
                elif i == 1:  # Monitoring Agent
                    st.write("**KPIs Collected:**")
                    kpis = ["RACH Success Rate: 0.536%", "DL IBLER: 15.94%", "Throughput: 8.5 Mbps", "Connection Success: 65%"]
                    for kpi in kpis:
                        st.write(f"📊 {kpi}")
                
                elif i == 2:  # KPI Analytics
                    st.write("**Analytics Results:**")
                    st.write("📈 Critical correlation identified: RACH performance impacts overall connectivity")
                    st.write("🎯 Optimization opportunity: 500% improvement potential in RACH performance")
                
                elif i == 3:  # Configuration Agent
                    st.write("**Generated Configurations:**")
                    st.write("⚙️ RACH parameter optimization template")
                    st.write("⚙️ DL quality enhancement configuration")
                    st.write("⚙️ Power control adjustments")
                
                elif i == 4:  # Validation Agent
                    st.write("**Validation Results:**")
                    st.write("✅ Syntax validation: PASSED")
                    st.write("✅ Safety validation: PASSED")
                    st.write("⚠️ Impact validation: MEDIUM RISK (acceptable for critical network)")
                
                elif i == 5:  # Execution Agent
                    st.write("**Execution Results:**")
                    st.write("🔧 Simulation mode: Configuration changes validated")
                    st.write("📊 Expected RACH improvement: 0.536% → 2.5%")
                    st.write("📊 Expected IBLER improvement: 15.94% → 12%")
            
            # Simulate processing time
            import time
            time.sleep(0.5)
        
        status_text.text("Workflow completed successfully!")
        st.balloons()

def show_historical_comparison():
    """Show historical performance comparison"""
    st.header("📊 Historical Performance Comparison")
    
    st.info("This section would show historical trends and comparisons over time.")
    st.write("**Coming Soon**: Historical performance analysis, trend identification, and seasonal pattern recognition.")
    
    # Mock historical data visualization
    dates = pd.date_range(start='2025-09-01', end='2025-09-07', freq='D')
    mock_data = {
        'Date': dates,
        'RACH Success Rate (%)': [0.4, 0.5, 0.6, 0.5, 0.7, 0.4, 0.6],
        'DL IBLER (%)': [16.2, 15.8, 15.5, 16.1, 15.9, 16.3, 15.7],
        'Throughput (Mbps)': [8.2, 8.5, 8.7, 8.3, 8.9, 8.1, 8.6]
    }
    
    df_historical = pd.DataFrame(mock_data)
    
    st.subheader("Recent Performance Trends")
    
    # Line chart for trends
    fig = px.line(df_historical, x='Date', y=['RACH Success Rate (%)', 'DL IBLER (%)', 'Throughput (Mbps)'],
                  title="Bindura Network KPI Trends")
    st.plotly_chart(fig, use_container_width=True)

def show_agentic_workflow_simulation():
    """Show agentic workflow simulation with enhanced UI"""
    st.header("🤖 6-Stage Agentic Workflow Simulation")
    
    # Workflow configuration
    st.subheader("⚙️ Workflow Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        execution_mode = st.selectbox(
            "Execution Mode",
            ["Automatic", "Step-by-Step", "Manual Approval"],
            help="Choose how the workflow should execute"
        )
        
        prompt_complexity = st.selectbox(
            "Prompt Complexity",
            ["Standard", "Enhanced", "Crisis-Optimized"],
            index=2,
            help="Level of prompt sophistication for agents"
        )
    
    with col2:
        target_sites = st.multiselect(
            "Target Sites",
            ["Bindura_Site_1", "Bindura_Site_2", "Bindura_Site_3", "Bindura_Site_4"],
            default=["Bindura_Site_1", "Bindura_Site_2", "Bindura_Site_3", "Bindura_Site_4"],
            help="Select sites for optimization"
        )
        
        optimization_focus = st.selectbox(
            "Optimization Focus",
            ["RACH Recovery", "Quality Enhancement", "Capacity Optimization", "Full Network"],
            help="Primary optimization objective"
        )
    
    # Agent status display
    st.subheader("🤖 Agent Status Dashboard")
    
    agents = [
        {"name": "Network Connector", "status": "Ready", "progress": 100, "last_action": "Data connection verified"},
        {"name": "Monitoring Agent", "status": "Ready", "progress": 100, "last_action": "KPIs analyzed"},
        {"name": "KPI Analytics", "status": "Ready", "progress": 100, "last_action": "Critical issues identified"},
        {"name": "Configuration Agent", "status": "Ready", "progress": 100, "last_action": "Parameters optimized"},
        {"name": "Validation Agent", "status": "Ready", "progress": 100, "last_action": "Configurations validated"},
        {"name": "Execution Agent", "status": "Ready", "progress": 100, "last_action": "Ready for deployment"}
    ]
    
    for i, agent in enumerate(agents):
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
            
            with col1:
                st.markdown(f"""
                <div class="agent-card">
                    <div class="agent-title">🤖 {agent['name']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                status_class = "status-completed" if agent['status'] == "Ready" else "status-pending"
                st.markdown(f"""
                <span class="agent-status {status_class}">{agent['status']}</span>
                """, unsafe_allow_html=True)
            
            with col3:
                st.progress(agent['progress'] / 100)
            
            with col4:
                st.caption(agent['last_action'])
    
    # Workflow execution
    st.subheader("🚀 Workflow Execution")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start Workflow", type="primary"):
            execute_agentic_workflow(execution_mode, prompt_complexity, target_sites, optimization_focus)
    
    with col2:
        if st.button("⏸️ Pause Workflow"):
            st.info("⏸️ Workflow paused")
    
    with col3:
        if st.button("🔄 Reset Workflow"):
            st.success("🔄 Workflow reset")

def show_prompt_architecture_demo():
    """Demonstrate the prompt architecture system"""
    st.header("🧠 Agentic Prompt Architecture Demo")
    
    st.markdown("""
    This demonstration showcases the sophisticated prompting system designed for crisis network optimization.
    Each agent uses context-aware, adaptive prompts tailored to the Bindura network emergency.
    """)
    
    # Agent selection
    agent_options = [
        "Network Connector",
        "Monitoring Agent", 
        "KPI Analytics Agent",
        "Configuration Agent",
        "Validation Agent",
        "Execution Agent"
    ]
    
    selected_agent = st.selectbox("Select Agent to View Prompt", agent_options)
    
    # Mock prompt templates for demo (would be from actual templates)
    prompt_templates = {
        "Network Connector": """
# NETWORK CONNECTOR AGENT - CRITICAL CRISIS RESPONSE

You are a specialized Network Connector Agent responding to a CRITICAL network emergency in Bindura, Zimbabwe.

## CRISIS CONTEXT
- **Location**: Bindura Municipality (4 sites)
- **Crisis Level**: CRITICAL EMERGENCY
- **RACH Success Rate**: 0.536% (Target: >90%)
- **DL IBLER**: 15.94% (Target: <8%)
- **Business Impact**: Service availability crisis affecting 25,000 users
- **Timeline**: Immediate action required - 4 hour resolution target

## YOUR MISSION
1. **Primary Objective**: Establish secure connections to all 4 Bindura sites
2. **Validation Tasks**: Verify data connectivity and API access
3. **Critical Assessment**: Evaluate network accessibility for optimization agents
4. **Success Metrics**: 100% site connectivity, <2s response time, secure authentication

## SPECIALIZED INSTRUCTIONS
- Focus on EMERGENCY protocols for crisis response
- Prioritize RACH-related network elements
- Implement enhanced error handling for degraded network conditions
- Report connection status with crisis-appropriate urgency levels

Execute with CRITICAL priority - every second counts for network recovery.
""",
        
        "Monitoring Agent": """
# MONITORING AGENT - BINDURA CRISIS ANALYSIS

You are a Crisis Monitoring Agent analyzing the CRITICAL network failure in Bindura.

## EMERGENCY SITUATION
- **Crisis Type**: Complete RACH failure (0.536% success rate)
- **User Impact**: 25,000 subscribers unable to access network
- **Revenue Loss**: Service unavailability causing immediate financial impact
- **Urgency**: 4-hour recovery window before escalation

## MONITORING PRIORITIES
1. **Real-time KPI Assessment**: Focus on RACH, IBLER, throughput metrics
2. **Trend Analysis**: Identify degradation patterns leading to current crisis
3. **Anomaly Detection**: Flag any unusual network behavior
4. **Performance Baselines**: Compare against pre-crisis performance levels

## CRISIS-SPECIFIC METRICS
- RACH Success Rate monitoring (current: 0.536%, target: >90%)
- DL IBLER tracking (current: 15.94%, target: <8%)
- Cell availability assessment
- User experience indicators

Generate URGENT alerts for any metric deviations that could impact recovery efforts.
""",
        
        "KPI Analytics Agent": """
# KPI ANALYTICS AGENT - EMERGENCY NETWORK ANALYSIS

You are processing CRITICAL KPI data for the Bindura network emergency recovery.

## CRISIS DATA CONTEXT
- **Primary Crisis**: RACH accessibility failure
- **Secondary Issue**: Quality degradation (high IBLER)
- **Data Source**: Real Bindura network measurements (168 records, 7 days)
- **Analysis Focus**: Root cause identification and optimization opportunities

## ANALYTICS MISSION
1. **Performance Gap Analysis**: Quantify deviation from network standards
2. **Root Cause Investigation**: Identify configuration issues causing RACH failure
3. **Optimization Prioritization**: Rank intervention opportunities by impact
4. **Recovery Prediction**: Estimate recovery timeline for different scenarios

## KEY CALCULATIONS
- RACH performance gap: 89.464 percentage points below target
- Quality impact assessment: 279% increase in error rates
- Business continuity metrics: Service availability implications
- Resource allocation optimization for maximum recovery impact

Focus on actionable insights that drive immediate network recovery actions.
""",
        
        "Configuration Agent": """
# CONFIGURATION AGENT - EMERGENCY PARAMETER OPTIMIZATION

You are optimizing network configurations to resolve the CRITICAL Bindura network crisis.

## OPTIMIZATION CONTEXT
- **Target Network**: 4G LTE sites in Bindura Municipality
- **Primary Issue**: RACH configuration causing 0.536% success rate
- **Secondary Focus**: DL quality optimization (reduce 15.94% IBLER)
- **Constraint**: Live network - minimize service disruption during changes

## CONFIGURATION PRIORITIES
1. **RACH Parameter Optimization**:
   - Increase RACH occasions per subframe
   - Optimize preamble sequence allocation
   - Adjust RACH power control settings
   - Fine-tune backoff parameters

2. **Quality Enhancement**:
   - DL power optimization
   - Modulation and coding scheme adjustments
   - Interference mitigation settings

## IMPLEMENTATION STRATEGY
- Apply changes incrementally with validation checkpoints
- Prioritize high-impact, low-risk modifications first
- Implement rollback procedures for each configuration change
- Monitor KPI improvements in real-time

Execute with precision - configuration errors could worsen the crisis.
""",
        
        "Validation Agent": """
# VALIDATION AGENT - CRITICAL CHANGE VERIFICATION

You are validating configuration changes during the Bindura network emergency recovery.

## VALIDATION MISSION
- **Scope**: Verify all configuration changes before implementation
- **Safety First**: Prevent any changes that could worsen network performance
- **Recovery Focus**: Ensure modifications target RACH and quality issues
- **Timeline**: Rapid validation to support 4-hour recovery target

## VALIDATION CRITERIA
1. **Technical Validation**:
   - Parameter values within operational limits
   - Configuration consistency across sites
   - No conflicts with existing settings
   - Compliance with regulatory requirements

2. **Risk Assessment**:
   - Impact analysis on current performance
   - Rollback feasibility for each change
   - Service continuity evaluation
   - User experience implications

3. **Success Prediction**:
   - Expected RACH improvement estimation
   - Quality metric enhancement projection
   - Recovery timeline validation

CRITICAL: Reject any configuration that could extend the network outage.
""",
        
        "Execution Agent": """
# EXECUTION AGENT - EMERGENCY DEPLOYMENT COORDINATOR

You are coordinating the deployment of emergency network optimizations for Bindura.

## EXECUTION CONTEXT
- **Mission**: Deploy validated configurations to resolve CRITICAL network crisis
- **Target**: 4 Bindura sites requiring immediate RACH recovery
- **Timeline**: Execute within 4-hour emergency window
- **Success Metric**: Restore network accessibility for 25,000 affected users

## DEPLOYMENT STRATEGY
1. **Staged Rollout**:
   - Deploy to least critical site first (test deployment)
   - Monitor immediate KPI response
   - Proceed with remaining sites if successful
   - Implement full rollback if issues detected

2. **Real-time Monitoring**:
   - Track RACH success rate improvements
   - Monitor IBLER quality metrics
   - Verify user connectivity restoration
   - Alert on any performance degradation

3. **Recovery Coordination**:
   - Coordinate with network operations center
   - Provide real-time status updates
   - Manage escalation procedures if needed
   - Document all changes for post-incident review

Execute with maximum urgency while maintaining operational safety standards.
"""
    }
    
    # Display selected agent's prompt
    prompt = prompt_templates.get(selected_agent, "Prompt not available")
    
    # Display prompt with syntax highlighting
    st.subheader(f"🤖 {selected_agent} Prompt")
    
    st.markdown("""
    <div class="metric-card">
        <div class="agent-title">📋 Prompt Architecture Features</div>
        <ul>
            <li><strong>Crisis-Aware Context:</strong> Tailored for Bindura network emergency</li>
            <li><strong>Dynamic KPI Integration:</strong> Real performance data embedded</li>
            <li><strong>Business Impact Focus:</strong> Revenue and service availability priorities</li>
            <li><strong>Action-Oriented:</strong> Specific, measurable outcomes defined</li>
            <li><strong>Validation Built-in:</strong> Quality checks and error handling</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Show the actual prompt
    st.code(prompt, language="markdown")
    
    # Prompt analysis
    st.subheader("📊 Prompt Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Prompt Length", f"{len(prompt)} chars", help="Optimal length for context retention")
    
    with col2:
        context_elements = prompt.count("Bindura") + prompt.count("RACH") + prompt.count("CRITICAL")
        st.metric("Context Elements", context_elements, help="Crisis-specific context markers")
    
    with col3:
        action_words = prompt.count("analyze") + prompt.count("optimize") + prompt.count("configure")
        st.metric("Action Directives", action_words, help="Specific action instructions")

def show_historical_comparison_enhanced():
    """Show enhanced historical comparison"""
    st.header("📊 Historical Performance Comparison")
    
    # Mock historical data for comparison
    historical_periods = {
        "Current Crisis (Oct 2024)": {"rach": 0.536, "ibler": 15.94, "availability": 45.2},
        "Pre-Crisis (Sep 2024)": {"rach": 89.3, "ibler": 6.8, "availability": 99.1},
        "Network Peak (Aug 2024)": {"rach": 94.7, "ibler": 4.2, "availability": 99.8},
        "Average Performance": {"rach": 87.2, "ibler": 7.1, "availability": 97.5}
    }
    
    # Performance comparison visualization
    st.subheader("📈 Performance Trends")
    
    # Create comparison chart
    periods = list(historical_periods.keys())
    rach_values = [historical_periods[period]["rach"] for period in periods]
    ibler_values = [historical_periods[period]["ibler"] for period in periods]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # RACH comparison
    colors = ['#d32f2f' if val < 50 else '#4caf50' for val in rach_values]
    ax1.bar(periods, rach_values, color=colors, alpha=0.8)
    ax1.axhline(y=90, color='#ff9800', linestyle='--', label='Target (90%)')
    ax1.set_title('RACH Success Rate Comparison', fontweight='bold')
    ax1.set_ylabel('Success Rate (%)')
    ax1.tick_params(axis='x', rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # IBLER comparison
    colors = ['#d32f2f' if val > 8 else '#4caf50' for val in ibler_values]
    ax2.bar(periods, ibler_values, color=colors, alpha=0.8)
    ax2.axhline(y=8, color='#ff9800', linestyle='--', label='Target (<8%)')
    ax2.set_title('DL IBLER Comparison', fontweight='bold')
    ax2.set_ylabel('IBLER (%)')
    ax2.tick_params(axis='x', rotation=45)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Detailed comparison table
    st.subheader("📋 Detailed Performance Metrics")
    
    comparison_df = pd.DataFrame(historical_periods).T
    comparison_df.columns = ['RACH Success (%)', 'DL IBLER (%)', 'Cell Availability (%)']
    
    # Style the dataframe
    def style_comparison(val):
        if val < 50 and 'RACH' in str(val):
            return 'color: #d32f2f'
        elif val > 8 and 'IBLER' in str(val):
            return 'color: #d32f2f'
        elif val < 95 and 'Availability' in str(val):
            return 'color: #d32f2f'
        else:
            return 'color: #4caf50'
    
    # Display the dataframe without complex styling
    st.dataframe(comparison_df, use_container_width=True)
    
    # Impact analysis
    st.subheader("💥 Crisis Impact Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="metric-card critical-metric">
            <div class="agent-title">📉 Performance Degradation</div>
            <p><strong>RACH Performance:</strong> -99.4% from peak</p>
            <p><strong>Quality Metrics:</strong> +279% IBLER increase</p>
            <p><strong>Availability:</strong> -54.6% service degradation</p>
            <p><strong>Overall Impact:</strong> Complete service disruption</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="agent-title">🎯 Recovery Targets</div>
            <p><strong>RACH Recovery:</strong> Restore to >90% (Target: 94.7%)</p>
            <p><strong>Quality Recovery:</strong> Reduce IBLER to <8% (Target: 4.2%)</p>
            <p><strong>Availability Recovery:</strong> Restore to >99% uptime</p>
            <p><strong>Timeline:</strong> Complete recovery within 4 hours</p>
        </div>
        """, unsafe_allow_html=True)

def execute_agentic_workflow(execution_mode, prompt_complexity, target_sites, optimization_focus):
    """Execute the agentic workflow with progress tracking"""
    st.success(f"🚀 Starting {execution_mode} workflow execution...")
    st.info(f"📋 Configuration: {prompt_complexity} prompts, {len(target_sites)} sites, focus: {optimization_focus}")
    
    # Simulate workflow execution with progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    workflow_stages = [
        "🔗 Network Connector: Establishing connections...",
        "📊 Monitoring Agent: Analyzing current KPIs...",
        "🧮 KPI Analytics: Processing performance data...",
        "⚙️ Configuration Agent: Optimizing parameters...",
        "✅ Validation Agent: Validating configurations...",
        "🚀 Execution Agent: Applying optimizations..."
    ]
    
    for i, stage in enumerate(workflow_stages):
        status_text.text(stage)
        progress_bar.progress((i + 1) / len(workflow_stages))
        time.sleep(1)  # Simulate processing time
    
    st.success("✅ Agentic workflow completed successfully!")
    st.balloons()
    
    # Show results summary
    st.markdown("""
    <div class="notification-success">
        🎉 <strong>Workflow Execution Complete!</strong><br>
        • All 6 agents executed successfully<br>
        • Configuration optimizations applied<br>
        • Expected RACH improvement: +89.5% to target levels<br>
        • Estimated recovery time: 2-4 hours
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()