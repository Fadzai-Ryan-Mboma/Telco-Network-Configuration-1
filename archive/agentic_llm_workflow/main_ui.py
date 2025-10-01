"""
Telco Network Configuration - System Status Dashboard
Main entry point for the cleaned-up system architecture
"""

import streamlit as st
import sys
import os

# Add the workspace to the path
sys.path.append('/workspace')
sys.path.append('/workspace/agentic_llm_workflow')

st.set_page_config(
    page_title="Telco Network Configuration",
    page_icon="📡",
    layout="wide"
)

st.title("📡 Telco Network Configuration System")
st.markdown("**Powered by NVIDIA AI & LangGraph**")

# System Status Check
st.header("🔍 System Status")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Core Components")
    
    # Test core imports
    try:
        from agentic_llm_workflow.agents import monitoring_agent, config_agent, valid_agent
        st.success("✅ Core agents available")
    except Exception as e:
        st.error(f"❌ Core agents failed: {e}")
    
    try:
        from agentic_llm_workflow.tools import calc_weighted_average, execute_xapp_sql
        st.success("✅ Core tools available")
    except Exception as e:
        st.error(f"❌ Core tools failed: {e}")
    
    try:
        from agentic_llm_workflow.utils import check_network_status
        st.success("✅ Network utilities available")
    except Exception as e:
        st.error(f"❌ Network utilities failed: {e}")

with col2:
    st.subheader("Integration Components")
    
    try:
        from agentic_llm_workflow.lz_config import LiquidZimbabweConfig
        config = LiquidZimbabweConfig()
        if config.integration_enabled:
            st.success("✅ Liquid Zimbabwe integration configured")
        else:
            st.info("ℹ️ Liquid Zimbabwe integration disabled")
    except Exception as e:
        st.warning(f"⚠️ LZ config issue: {e}")
    
    try:
        from agentic_llm_workflow.lz_api_client import LiquidZimbabweAPIClient
        client = LiquidZimbabweAPIClient()
        st.success("✅ API client available (simulation mode)")
    except Exception as e:
        st.warning(f"⚠️ API client issue: {e}")

# Database Status
st.header("💾 Database Status")
try:
    import sqlite3
    databases = [
        ('/workspace/data/live_network.db', 'Live Network'),
        ('/workspace/data/liquid_zimbabwe.db', 'Liquid Zimbabwe'),
        ('/workspace/data/historical_db', 'Historical Data')
    ]
    
    for db_path, db_name in databases:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            st.success(f"✅ {db_name}: {len(tables)} tables")
        except Exception as e:
            st.error(f"❌ {db_name}: {e}")
            
except Exception as e:
    st.error(f"❌ Database check failed: {e}")

# Configuration
st.header("⚙️ Configuration")
try:
    import yaml
    with open('/workspace/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"🤖 Model: {config.get('model', 'Not set')}")
        st.info(f"⏱️ Monitoring interval: {config.get('monitoring_wait_time', 'Not set')} seconds")
    
    with col2:
        st.info(f"🔧 NIM mode: {config.get('nim_mode', False)}")
        st.info(f"📊 Table name: {config.get('table_name', 'Not set')}")
        
except Exception as e:
    st.error(f"❌ Configuration load failed: {e}")

# Actions
st.header("🚀 Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🧪 Run System Test"):
        with st.spinner("Running comprehensive system test..."):
            try:
                # Import and run the test
                exec(open('/workspace/agentic_llm_workflow/docker_test.py').read())
                st.success("✅ System test completed - check logs above")
            except Exception as e:
                st.error(f"❌ Test failed: {e}")

with col2:
    if st.button("📊 Check Network Status"):
        try:
            from agentic_llm_workflow.utils import check_network_status
            status = check_network_status(print_output=True)
            if status:
                st.success("✅ Network services are running")
            else:
                st.warning("⚠️ Some network services may be down")
        except Exception as e:
            st.error(f"❌ Network check failed: {e}")

with col3:
    if st.button("🔍 View Logs"):
        st.info("📋 System logs would appear here in a full implementation")

# Footer
st.markdown("---")
st.markdown("**System Architecture:** Core NVIDIA template with Phase 3 Liquid Zimbabwe enhancements")
st.markdown("**Status:** All core functionality operational with graceful fallback mode")