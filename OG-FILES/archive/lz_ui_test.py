#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network Optimizer - Streamlit UI Test
Simple monitoring interface for container testing
"""

import streamlit as st
import os
import time
import json
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LZ-UI')

# Page configuration
st.set_page_config(
    page_title="LZ 4G Network Optimizer",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_system_info():
    """Get system configuration and status"""
    return {
        "api_url": os.getenv('LZ_API_URL', 'Not configured'),
        "username": os.getenv('LZ_API_USERNAME', 'Not configured'),
        "environment": os.getenv('LZ_ENV', 'development'),
        "timezone": os.getenv('TZ', 'UTC'),
        "container_port": os.getenv('CONTAINER_PORT', '8501'),
        "api_port": os.getenv('API_PORT', '8502')
    }

def get_mock_kpi_data():
    """Generate mock KPI data for testing"""
    import random
    
    return {
        "network_access_success_rate": round(random.uniform(95.0, 99.9), 2),
        "download_quality": round(random.uniform(80.0, 95.0), 1),
        "upload_quality": round(random.uniform(75.0, 90.0), 1),
        "prb_uplink_usage": round(random.uniform(20.0, 70.0), 1),
        "prb_downlink_usage": round(random.uniform(30.0, 80.0), 1),
        "avg_dl_throughput": round(random.uniform(50.0, 120.0), 1),
        "avg_ul_throughput": round(random.uniform(15.0, 40.0), 1)
    }

def get_mock_parameters():
    """Generate mock parameter data for testing"""
    return {
        "earfcn": 2300,
        "pci": 150,
        "tac": 12345,
        "txpower": 43,
        "bandwidth": 20
    }

def main():
    """Main Streamlit UI"""
    
    # Header
    st.title("📡 Liquid Zimbabwe 4G Network Optimizer")
    st.markdown("---")
    
    # Sidebar - System Status
    with st.sidebar:
        st.header("🔧 System Status")
        
        # System info
        sys_info = get_system_info()
        
        # Status indicator
        status_color = "🟢" if sys_info["environment"] == "development" else "🟡"
        st.markdown(f"{status_color} **Status:** Running")
        st.markdown(f"🌍 **Environment:** {sys_info['environment']}")
        st.markdown(f"🕐 **Timezone:** {sys_info['timezone']}")
        
        st.markdown("---")
        
        # API Configuration
        st.subheader("📡 API Configuration")
        st.text(f"URL: {sys_info['api_url'][:30]}...")
        st.text(f"User: {sys_info['username']}")
        
        st.markdown("---")
        
        # Container Info
        st.subheader("🐳 Container Info")
        st.text(f"UI Port: {sys_info['container_port']}")
        st.text(f"API Port: {sys_info['api_port']}")
        
        # Auto-refresh
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # KPI Dashboard
        st.header("📊 Key Performance Indicators")
        
        kpi_data = get_mock_kpi_data()
        
        # KPI Metrics in columns
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        
        with kpi_col1:
            st.metric(
                "Network Access Success",
                f"{kpi_data['network_access_success_rate']}%",
                delta="0.2%"
            )
            st.metric(
                "Download Quality",
                f"{kpi_data['download_quality']}/100",
                delta="2.1"
            )
            
        with kpi_col2:
            st.metric(
                "Upload Quality", 
                f"{kpi_data['upload_quality']}/100",
                delta="1.5"
            )
            st.metric(
                "PRB UL Usage",
                f"{kpi_data['prb_uplink_usage']}%",
                delta="-3.2%"
            )
            
        with kpi_col3:
            st.metric(
                "PRB DL Usage",
                f"{kpi_data['prb_downlink_usage']}%", 
                delta="1.8%"
            )
            st.metric(
                "Avg DL Throughput",
                f"{kpi_data['avg_dl_throughput']} Mbps",
                delta="5.2 Mbps"
            )
    
    with col2:
        # Network Parameters
        st.header("⚙️ Network Parameters")
        
        params = get_mock_parameters()
        
        st.markdown("**Current Configuration:**")
        st.json(params)
        
        # Quick actions
        st.markdown("---")
        st.markdown("**Quick Actions:**")
        
        if st.button("🔄 Optimize Parameters"):
            st.success("Parameter optimization initiated!")
            
        if st.button("📈 Run Analytics"):
            st.info("Analytics running in background...")
            
        if st.button("🔍 Health Check"):
            st.success("System health: All green! ✅")
    
    # Network Performance Chart Area
    st.markdown("---")
    st.header("📈 Performance Trends")
    
    # Generate sample data for chart
    import random
    
    chart_data = []
    base_time = datetime.now() - timedelta(hours=1)
    
    for i in range(60):  # Last 60 minutes
        timestamp = base_time + timedelta(minutes=i)
        chart_data.append({
            "Time": timestamp.strftime("%H:%M"),
            "Throughput (Mbps)": random.uniform(80, 120),
            "Network Access (%)": random.uniform(95, 99.5),
            "Quality Score": random.uniform(80, 95)
        })
    
    # Display chart
    st.line_chart(chart_data, x="Time", y=["Throughput (Mbps)", "Quality Score"])
    
    # Agent Status
    st.markdown("---")
    st.header("🤖 Agent Status")
    
    agent_col1, agent_col2, agent_col3 = st.columns(3)
    
    with agent_col1:
        st.markdown("**🔍 Monitoring Agent**")
        st.success("Active - Last update: 30s ago")
        
    with agent_col2:
        st.markdown("**⚙️ Optimization Agent**")
        st.success("Active - Next run: 5 min")
        
    with agent_col3:
        st.markdown("**📊 Analytics Agent**")
        st.success("Active - Processing data...")
    
    # Footer
    st.markdown("---")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"🕐 Last updated: {current_time} | 🌍 Liquid Zimbabwe 4G Network")

if __name__ == "__main__":
    main()