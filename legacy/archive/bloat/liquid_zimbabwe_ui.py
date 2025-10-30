"""
Liquid Zimbabwe Network Optimizer - Main UI
Powered by Cassava Technologies

This is the main Streamlit interface for the Live Network Optimization System.
Integrates with Huawei iMaster MAE API for real-time network management.

Features:
- Live Huawei network connectivity
- Real-time KPI monitoring with user-friendly names
- Parameter optimization with MML command execution
- Historical trend analysis
- Cassava Technologies branding

Author: Cassava AI Team
Version: 2.0 - Live Network Integration
"""

import time
import yaml
import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Import our custom components
from ui_components.cassava_theme import CassavaTheme

try:
    from huawei_api_client import HuaweiAPIClient
    from live_network_manager import LiveNetworkManager
    from liquid_zimbabwe_kpi import LiquidZimbabweKPIManager as LiquidZimbabweKPI
    from liquid_zimbabwe_parameters import LiquidZimbabweParameterManager as LiquidZimbabweParameters
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some imports failed: {e}")
    print("Running in fallback mode...")
    IMPORTS_AVAILABLE = False
    
    # Fallback classes for when imports fail
    class HuaweiAPIClient:
        def __init__(self): 
            self.connected = False
        def connect(self): 
            return True
        def get_network_elements(self): 
            return [{"name": "Demo-Site-001", "type": "gNodeB"}]
    
    class LiveNetworkManager:
        def __init__(self): 
            pass
        def check_network_status(self): 
            return True
    
    class LiquidZimbabweKPI:
        def __init__(self, db_path="demo.db"): 
            pass
        def get_kpi_dashboard_data(self): 
            return {"demo": True}
    
    class LiquidZimbabweParameters:
        def __init__(self, db_path="demo.db"): 
            pass
        def get_parameter_dashboard_data(self): 
            return {"demo": True}

# ========================================
# INITIALIZATION & CONFIGURATION
# ========================================

# Page config - Cassava branding
st.set_page_config(
    page_title="Liquid Zimbabwe Network Optimizer",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Cassava theme
CassavaTheme.inject_css()

# Initialize managers
@st.cache_resource
def initialize_managers():
    """Initialize network managers with caching"""
    try:
        # API client
        api_client = HuaweiAPIClient(
            base_url="https://41.174.191.214:31127",
            username="cassava.ai",
            password="#Pass123#"
        )
        
        # Network manager
        network_manager = LiveNetworkManager(api_client)
        
        # Set up database path for managers
        db_path = os.path.join("data", "liquid_zimbabwe.db")
        os.makedirs("data", exist_ok=True)
        
        # KPI manager
        kpi_manager = LiquidZimbabweKPI(db_path)
        
        # Parameter manager  
        param_manager = LiquidZimbabweParameters(db_path)
        
        return api_client, network_manager, kpi_manager, param_manager
    except Exception as e:
        st.error(f"Failed to initialize managers: {str(e)}")
        return None, None, None, None

# Get managers
api_client, network_manager, kpi_manager, param_manager = initialize_managers()

# ========================================
# SESSION STATE MANAGEMENT
# ========================================

def initialize_session_state():
    """Initialize session state variables"""
    
    # Connection state
    if "network_connected" not in st.session_state:
        st.session_state.network_connected = False
    
    if "last_connection_check" not in st.session_state:
        st.session_state.last_connection_check = datetime.now()
    
    # Selected site/cluster
    if "selected_site" not in st.session_state:
        st.session_state.selected_site = None
    
    # Available sites
    if "available_sites" not in st.session_state:
        st.session_state.available_sites = []
    
    # KPI data
    if "current_kpis" not in st.session_state:
        st.session_state.current_kpis = {}
    
    # Parameter data
    if "current_parameters" not in st.session_state:
        st.session_state.current_parameters = {}
    
    # Auto-refresh settings
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = True
    
    if "refresh_interval" not in st.session_state:
        st.session_state.refresh_interval = 300  # 5 minutes
    
    # Last data update
    if "last_data_update" not in st.session_state:
        st.session_state.last_data_update = None

# Initialize session state
initialize_session_state()

# ========================================
# NETWORK CONNECTION FUNCTIONS
# ========================================

def check_network_connection() -> bool:
    """Check if we can connect to the live network"""
    try:
        if api_client is None:
            return False
        
        # Test connectivity
        success = api_client.test_connectivity()
        
        # Update session state
        st.session_state.network_connected = success
        st.session_state.last_connection_check = datetime.now()
        
        return success
    except Exception as e:
        st.error(f"Connection check failed: {str(e)}")
        st.session_state.network_connected = False
        return False

def connect_to_network():
    """Attempt to connect to the live network"""
    with st.spinner("🔄 Connecting to Live Huawei Network..."):
        if check_network_connection():
            # Get available sites
            try:
                sites = network_manager.get_available_sites()
                st.session_state.available_sites = sites
                CassavaTheme.show_toast(
                    f"✅ Connected! Found {len(sites)} sites", 
                    "success"
                )
                return True
            except Exception as e:
                st.error(f"Failed to retrieve sites: {str(e)}")
                return False
        else:
            CassavaTheme.show_toast(
                "❌ Connection failed. Check credentials and network.", 
                "error"
            )
            return False

def disconnect_from_network():
    """Disconnect from the network"""
    st.session_state.network_connected = False
    st.session_state.available_sites = []
    st.session_state.current_kpis = {}
    st.session_state.current_parameters = {}
    CassavaTheme.show_toast("🔌 Disconnected from network", "warning")

# ========================================
# DATA REFRESH FUNCTIONS
# ========================================

def refresh_kpi_data():
    """Refresh KPI data from the network"""
    if not st.session_state.network_connected or not kpi_manager:
        return
    
    try:
        with st.spinner("📊 Refreshing KPI data..."):
            # Get KPIs for selected site or all sites
            if st.session_state.selected_site:
                kpi_data = kpi_manager.get_site_kpis(st.session_state.selected_site)
                # If site-specific data doesn't have proper KPI structure, use all KPIs
                if not any(key in kpi_data for key in ['network_access_success', 'download_quality', 'upload_quality']):
                    kpi_data = kpi_manager.get_all_kpis()
            else:
                kpi_data = kpi_manager.get_all_kpis()
            
            st.session_state.current_kpis = kpi_data
            st.session_state.last_data_update = datetime.now()
            
            # Store in database (only if kpi_data has proper structure)
            if isinstance(kpi_data, dict) and any(key in kpi_data for key in ['network_access_success', 'download_quality']):
                kpi_manager.store_kpi_snapshot(kpi_data)
            
    except Exception as e:
        st.error(f"Failed to refresh KPI data: {str(e)}")

def refresh_parameter_data():
    """Refresh parameter data from the network"""
    if not st.session_state.network_connected or not param_manager:
        return
    
    try:
        with st.spinner("⚙️ Refreshing parameter data..."):
            if st.session_state.selected_site:
                param_data = param_manager.get_site_parameters(st.session_state.selected_site)
            else:
                param_data = param_manager.get_all_parameters()
            
            st.session_state.current_parameters = param_data
            
    except Exception as e:
        st.error(f"Failed to refresh parameter data: {str(e)}")

# ========================================
# MAIN UI RENDERING
# ========================================

def render_header():
    """Render the main header with Cassava branding"""
    CassavaTheme.render_header(
        "Liquid Zimbabwe Network Optimizer",
        "Real-time RAN Performance Management | Powered by Cassava Technologies"
    )

def render_connection_panel():
    """Render network connection controls"""
    st.markdown("## 🌐 Live Network Connection")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Connection status
        CassavaTheme.render_connection_status(
            connected=st.session_state.network_connected,
            site_count=len(st.session_state.available_sites)
        )
    
    with col2:
        if st.session_state.network_connected:
            if st.button("🔌 Disconnect", key="disconnect_btn"):
                disconnect_from_network()
                st.rerun()
        else:
            if st.button("🔗 Connect to Live Network", key="connect_btn"):
                if connect_to_network():
                    st.rerun()
    
    with col3:
        if st.session_state.network_connected:
            if st.button("🔄 Refresh Data", key="refresh_btn"):
                refresh_kpi_data()
                refresh_parameter_data()
                st.rerun()

def render_site_selector():
    """Render site selection interface"""
    if not st.session_state.network_connected:
        return None
    
    st.markdown("---")
    selected_site = CassavaTheme.render_site_selector(
        sites=st.session_state.available_sites,
        current_site=st.session_state.selected_site
    )
    
    # Update session state if selection changed
    if selected_site != st.session_state.selected_site:
        st.session_state.selected_site = selected_site
        # Refresh data for new site
        refresh_kpi_data()
        refresh_parameter_data()
        st.rerun()
    
    return selected_site

def render_kpi_dashboard():
    """Render the main KPI dashboard"""
    if not st.session_state.network_connected:
        st.info("👆 Connect to the live network to view KPI data")
        return
    
    st.markdown("---")
    st.markdown("## 📊 Real-time KPI Dashboard")
    
    if not st.session_state.current_kpis:
        st.info("📡 No KPI data available. Click 'Refresh Data' to load latest metrics.")
        return
    
    # Get KPI definitions
    kpi_config = kpi_manager.KPI_CONFIG if kpi_manager else {}
    
    # Render KPI cards in grid layout
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]
    
    for i, (kpi_id, kpi_data) in enumerate(st.session_state.current_kpis.items()):
        # Skip meta information and non-KPI entries
        if kpi_id in ['meta', 'site_name', 'cells']:
            continue
            
        config = kpi_config.get(kpi_id, {})
        
        # Handle both dictionary and string data formats
        if isinstance(kpi_data, dict):
            value = kpi_data.get('value', 0)
            status = kpi_data.get('status', 'no_data')
        else:
            # Fallback for unexpected data types
            value = 0
            status = 'no_data'
        
        with cols[i % 3]:
            CassavaTheme.render_kpi_card(
                kpi_name=config.get('user_friendly_name', kpi_id),
                technical_name=config.get('technical_name', kpi_id),
                value=value,
                unit=config.get('unit', ''),
                description=config.get('description', 'No description available'),
                status=status
            )

def render_kpi_trends():
    """Render KPI trend charts"""
    if not st.session_state.network_connected or not kpi_manager:
        return
    
    st.markdown("---")
    st.markdown("## 📈 KPI Trends & Historical Analysis")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=7),
            key="trend_start"
        )
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=datetime.now(),
            key="trend_end"
        )
    
    try:
        # Get historical data
        historical_data = kpi_manager.get_historical_kpis(
            site_name=st.session_state.selected_site,
            start_time=datetime.combine(start_date, datetime.min.time()),
            end_time=datetime.combine(end_date, datetime.max.time())
        )
        
        # Check if historical data is available
        if isinstance(historical_data, dict):
            if not historical_data or len(historical_data) == 0:
                st.info("📊 No historical data found for selected period")
                return
        elif hasattr(historical_data, 'empty'):
            if historical_data.empty:
                st.info("📊 No historical data found for selected period")
                return
        else:
            st.info("📊 No historical data available")
            return
        
        # Create trend charts
        for kpi_id in kpi_manager.KPI_CONFIG.keys():
            # Handle both DataFrame and dict formats
            kpi_available = False
            if isinstance(historical_data, dict):
                # For dictionary format (site drill-down), skip trend visualization
                continue
            elif hasattr(historical_data, 'columns'):
                kpi_available = kpi_id in historical_data.columns
            
            if not kpi_available:
                continue
                
            config = kpi_manager.KPI_CONFIG[kpi_id]
            
            # Create the trend chart from DataFrame
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=historical_data.index,
                y=historical_data[kpi_id],
                mode='lines+markers',
                name=config['user_friendly_name'],
                line=dict(color=CassavaTheme.COLORS['primary_blue'], width=2),
                marker=dict(size=6)
            ))
            
            # Add normal range as background
            if 'normal_range' in config:
                normal_min, normal_max = config['normal_range']
                fig.add_hrect(
                    y0=normal_min, y1=normal_max,
                    fillcolor="rgba(0, 255, 0, 0.1)",
                    layer="below",
                    annotation_text="Normal Range",
                    annotation_position="top left"
                )
            
            # Add critical threshold line
            if 'critical_threshold' in config:
                threshold = config['critical_threshold']
                fig.add_hline(
                    y=threshold,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Critical: {threshold}{config['unit']}"
                )
            
            fig.update_layout(
                title=f"📈 {config['user_friendly_name']} Trend",
                xaxis_title="Date",
                yaxis_title=f"{config['user_friendly_name']} ({config['unit']})",
                height=300,
                showlegend=True,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="Arial", size=12),
                title_font=dict(size=16, color=CassavaTheme.COLORS['primary_blue'])
            )
            
            fig.update_xaxes(showgrid=True, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridcolor='lightgray')
            
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading trend data: {str(e)}")

def render_parameter_controls():
    """Render parameter modification controls"""
    if not st.session_state.network_connected or not param_manager:
        return
    
    st.markdown("---")
    st.markdown("## ⚙️ Network Parameter Management")
    
    if not st.session_state.current_parameters:
        st.info("⚙️ No parameter data available. Click 'Refresh Data' to load current values.")
        return
    
    # Parameter controls
    for param_id, param_data in st.session_state.current_parameters.items():
        config = param_manager.PARAMETER_CONFIG.get(param_id, {})
        
        CassavaTheme.render_parameter_control(
            param_name=param_id,
            user_friendly_name=config.get('user_friendly_name', param_id),
            description=config.get('description', 'No description available'),
            current_value=param_data.get('value', 'Unknown'),
            param_range=(config.get('min_value', 0), config.get('max_value', 100)),
            unit=config.get('unit', '')
        )

def render_sidebar_controls():
    """Render sidebar controls"""
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # Auto-refresh controls
        st.session_state.auto_refresh = st.checkbox(
            "🔄 Auto-refresh data", 
            value=st.session_state.auto_refresh
        )
        
        if st.session_state.auto_refresh:
            st.session_state.refresh_interval = st.selectbox(
                "Refresh interval",
                options=[60, 300, 600, 1800],  # 1min, 5min, 10min, 30min
                index=1,  # Default 5min
                format_func=lambda x: f"{x//60} minute{'s' if x//60 != 1 else ''}"
            )
        
        # Data status
        st.markdown("---")
        st.markdown("### 📊 Data Status")
        
        if st.session_state.last_data_update:
            time_diff = datetime.now() - st.session_state.last_data_update
            minutes_ago = int(time_diff.total_seconds() // 60)
            st.info(f"Last update: {minutes_ago} minute{'s' if minutes_ago != 1 else ''} ago")
        else:
            st.warning("No data loaded yet")
        
        # System info
        st.markdown("---")
        st.markdown("### ℹ️ System Info")
        st.markdown("**Version:** 2.0")
        st.markdown("**API:** Huawei iMaster MAE") 
        st.markdown("**Provider:** Liquid Zimbabwe")
        st.markdown("**Powered by:** Cassava Technologies")

# ========================================
# MAIN APPLICATION FLOW
# ========================================

def main():
    """Main application function"""
    
    # Render header
    render_header()
    
    # Connection panel
    render_connection_panel()
    
    # Site selector
    render_site_selector()
    
    # Main dashboard
    if st.session_state.network_connected:
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs([
            "📊 Live Dashboard", 
            "📈 Historical Trends", 
            "⚙️ Parameter Controls"
        ])
        
        with tab1:
            render_kpi_dashboard()
        
        with tab2:
            render_kpi_trends()
        
        with tab3:
            render_parameter_controls()
    
    # Sidebar controls
    render_sidebar_controls()
    
    # Auto-refresh logic
    if (st.session_state.auto_refresh and 
        st.session_state.network_connected and 
        st.session_state.last_data_update):
        
        time_since_update = datetime.now() - st.session_state.last_data_update
        if time_since_update.total_seconds() >= st.session_state.refresh_interval:
            refresh_kpi_data()
            refresh_parameter_data()
            st.rerun()

# ========================================
# ENTRY POINT
# ========================================

if __name__ == "__main__":
    main()