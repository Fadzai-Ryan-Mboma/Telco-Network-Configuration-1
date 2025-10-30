#!/bin/bash
# Quick Deploy Script for Liquid Zimbabwe Optimizer
# For rapid deployment and testing

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Liquid Zimbabwe Quick Deploy${NC}"
echo "================================="

# Check if we're in the right directory
if [[ ! -f "requirements.txt" ]]; then
    echo -e "${YELLOW}Creating minimal requirements.txt...${NC}"
    cat > requirements.txt << 'EOF'
streamlit==1.45.0
requests==2.31.0
pandas==2.1.3
pyyaml==6.0.1
langchain==0.3.25
langchain-nvidia-ai-endpoints==0.3.10
langgraph==0.4.1
plotly==5.17.0
EOF
fi

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    echo -e "${BLUE}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create minimal config if it doesn't exist
if [[ ! -f "config.yaml" ]]; then
    echo -e "${BLUE}Creating minimal configuration...${NC}"
    cat > config.yaml << 'EOF'
# Minimal LZ Configuration for Testing
nvidia_api_key: "DEMO_MODE"
llm_model: "meta/llama-3.1-70b-instruct"
llm_base_url: "https://integrate.api.nvidia.com/v1"

huawei_api:
  base_url: "https://41.174.191.214:31127"
  username: "demo"
  password: "demo"
  verify_ssl: false

demo_mode: true
EOF
fi

# Create main UI if it doesn't exist
if [[ ! -f "main_ui.py" ]]; then
    echo -e "${BLUE}Creating demo main UI...${NC}"
    cp deploy/demo_ui.py main_ui.py 2>/dev/null || cat > main_ui.py << 'EOF'
import streamlit as st
import time
import random
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Liquid Zimbabwe Network Optimizer",
    page_icon="📡",
    layout="wide"
)

# Cassava branding
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #0066CC 0%, #00A0A0 100%);
    color: white;
    padding: 1.5rem;
    margin: -1rem -1rem 2rem -1rem;
    border-radius: 0 0 10px 10px;
    text-align: center;
}
.kpi-card {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-left: 4px solid #0066CC;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('''
<div class="main-header">
    <h1>🔷 Cassava Technologies</h1>
    <h2>Liquid Zimbabwe Network Optimizer</h2>
    <p>AI-Powered 4G Network Optimization Platform</p>
</div>
''', unsafe_allow_html=True)

# Status row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🌐 Network Status", "🟢 Connected", "Live Demo")

with col2:
    st.metric("⏱️ Last Update", datetime.now().strftime("%H:%M:%S"), "Real-time")

with col3:
    st.metric("🎯 System Health", "✅ Optimal", "Demo Mode")

with col4:
    st.metric("🔗 API Status", "🟡 Demo", "Simulation")

st.markdown("---")

# Main dashboard
st.header("📊 Network Performance Dashboard")

# KPI metrics
st.subheader("🎯 Core KPIs (Live Simulation)")
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

# Simulate live KPI data
network_access = 95 + random.uniform(-2, 3)
download_quality = 8 + random.uniform(-2, 2)
upload_quality = 4 + random.uniform(-1, 2)
download_speed = 18000 + random.uniform(-3000, 5000)

with kpi_col1:
    st.metric(
        "🎯 Network Access Success",
        f"{network_access:.1f}%",
        f"{random.uniform(-0.5, 1.5):.1f}%"
    )

with kpi_col2:
    st.metric(
        "📥 Download Quality (IBLER)",
        f"{download_quality:.1f}%",
        f"{random.uniform(-0.3, 0.8):.1f}%"
    )

with kpi_col3:
    st.metric(
        "📤 Upload Quality (IBLER)",
        f"{upload_quality:.1f}%",
        f"{random.uniform(-0.2, 0.5):.1f}%"
    )

with kpi_col4:
    st.metric(
        "🚀 Download Speed",
        f"{download_speed/1000:.1f} Mbps",
        f"{random.uniform(-0.5, 2.0):.1f} Mbps"
    )

# Performance charts
st.subheader("📈 Performance Trends")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # Generate sample time series data
    times = pd.date_range(start="2025-10-01 00:00", periods=24, freq="H")
    kpi_data = pd.DataFrame({
        "Time": times,
        "Network Access": [95 + random.uniform(-3, 5) for _ in range(24)],
        "Download Quality": [8 + random.uniform(-2, 3) for _ in range(24)],
        "Upload Quality": [4 + random.uniform(-1, 2) for _ in range(24)]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=kpi_data["Time"], y=kpi_data["Network Access"], 
                           name="Network Access %", line=dict(color="#0066CC")))
    fig.update_layout(title="Network Access Success (24h)", yaxis_title="Percentage")
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=kpi_data["Time"], y=kpi_data["Download Quality"], 
                            name="Download Quality %", line=dict(color="#00A0A0")))
    fig2.add_trace(go.Scatter(x=kpi_data["Time"], y=kpi_data["Upload Quality"], 
                            name="Upload Quality %", line=dict(color="#FFC107")))
    fig2.update_layout(title="Quality Metrics (24h)", yaxis_title="Error Rate %")
    st.plotly_chart(fig2, use_container_width=True)

# Parameter control section
st.header("⚙️ Parameter Control Panel")
param_col1, param_col2 = st.columns(2)

with param_col1:
    st.subheader("📶 Signal Power Control")
    current_power = st.slider("Reference Signal Power (dBm)", -200, 50, -120)
    st.info(f"Current setting: {current_power} dBm")
    
    if st.button("🎯 AI Optimize Signal Power"):
        with st.spinner("AI analyzing optimal power level..."):
            time.sleep(2)
            optimal_power = current_power + random.uniform(-10, 15)
            st.success(f"✅ AI Recommendation: {optimal_power:.1f} dBm")
            st.info("Expected improvement: +5% coverage, +2% throughput")

with param_col2:
    st.subheader("🔄 Handover Control")
    handover_threshold = st.slider("A3 Event Offset (dB)", 0, 15, 6)
    st.info(f"Current setting: {handover_threshold} dB")
    
    if st.button("🎯 AI Optimize Handover"):
        with st.spinner("AI analyzing optimal handover settings..."):
            time.sleep(2)
            optimal_handover = handover_threshold + random.uniform(-2, 3)
            st.success(f"✅ AI Recommendation: {optimal_handover:.1f} dB")
            st.info("Expected improvement: -15% call drops")

# AI Assistant section
st.header("🤖 AI Optimization Assistant")
assistant_col1, assistant_col2 = st.columns([2, 1])

with assistant_col1:
    st.markdown("""
    <div class="kpi-card">
        <h4>💬 Current Analysis</h4>
        <p><strong>Network Status:</strong> Operating within normal parameters</p>
        <p><strong>Optimization Opportunity:</strong> Download quality can be improved by 12% with signal power adjustment</p>
        <p><strong>Risk Assessment:</strong> Low risk - changes within safe operational limits</p>
        <p><strong>Recommendation:</strong> Implement suggested optimizations during low-traffic hours</p>
    </div>
    """, unsafe_allow_html=True)

with assistant_col2:
    if st.button("🔄 Run Full Analysis"):
        with st.spinner("AI analyzing network performance..."):
            time.sleep(3)
            st.success("✅ Analysis complete!")
            
    if st.button("📊 Generate Report"):
        with st.spinner("Generating performance report..."):
            time.sleep(2)
            st.success("✅ Report ready for download!")
    
    if st.button("⚠️ Check Alerts"):
        st.info("No active alerts - system operating normally")

# System information
st.markdown("---")
st.subheader("ℹ️ System Information")
info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:
    st.metric("🔧 Version", "1.0.0-demo", "Latest")

with info_col2:
    st.metric("⚡ Performance", "98%", "Optimal")

with info_col3:
    st.metric("💾 Memory Usage", "1.2 GB", "Normal")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🔷 <strong>Cassava Technologies</strong> | Liquid Zimbabwe Network Optimizer</p>
    <p>AI-Powered Network Optimization for 4G/LTE Networks</p>
    <p><em>Demo Mode - Connect to live API for full functionality</em></p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh (optional)
if st.checkbox("🔄 Auto-refresh (30s)"):
    time.sleep(30)
    st.experimental_rerun()
EOF
fi

# Make sure we can run Streamlit
echo -e "${BLUE}Testing Streamlit installation...${NC}"
python -c "import streamlit; print('✅ Streamlit installed successfully')"

# Start the application
echo -e "${GREEN}🎉 Ready to launch!${NC}"
echo ""
echo "To start the Liquid Zimbabwe Optimizer:"
echo -e "${YELLOW}streamlit run main_ui.py${NC}"
echo ""
echo "Or run in background:"
echo -e "${YELLOW}nohup streamlit run main_ui.py --server.port=8501 --server.address=0.0.0.0 &${NC}"
echo ""
echo "Access at: http://localhost:8501"

# Offer to start immediately
read -p "Start the application now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}🚀 Starting Liquid Zimbabwe Optimizer...${NC}"
    streamlit run main_ui.py
fi