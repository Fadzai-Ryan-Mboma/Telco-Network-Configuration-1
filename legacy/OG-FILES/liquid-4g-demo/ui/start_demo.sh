#!/bin/bash
# Liquid Zimbabwe 4G Network Optimizer - Agentic Demo Startup Script

echo "🚀 Starting Liquid Zimbabwe 4G Network Optimizer - Agentic Demo"
echo "=============================================================="

# Check if we're in the correct directory
if [ ! -f "agentic_demo_ui.py" ]; then
    echo "❌ Error: agentic_demo_ui.py not found. Please run from the ui directory."
    exit 1
fi

# Create data directory if it doesn't exist
if [ ! -d "../data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p ../data
fi

# Check Python version
python_version=$(python3 --version 2>&1)
echo "🐍 Python version: $python_version"

# Install/check dependencies
echo "📦 Checking dependencies..."
if [ -f "requirements-demo.txt" ]; then
    echo "Installing requirements..."
    pip3 install -r requirements-demo.txt
else
    echo "⚠️  requirements-demo.txt not found, installing basic dependencies..."
    pip3 install streamlit pandas plotly matplotlib pyyaml requests
fi

echo ""
echo "🌟 Liquid Zimbabwe Agentic Demo Features:"
echo "   🚨 Crisis Recovery Dashboard (Bindura Network)"
echo "   🤖 6-Stage Agentic Workflow Engine"
echo "   📊 Real-time Performance Analytics"
echo "   ⚙️  Automated Parameter Optimization"
echo "   🔍 Network Crisis Investigation"
echo ""
echo "📡 Demo showcases RACH success rate crisis: 0.536% → 92.5% recovery"
echo ""

# Start Streamlit
echo "🚀 Starting Streamlit demo on http://localhost:8501"
echo "   Press Ctrl+C to stop the demo"
echo ""

# Set environment for demo
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_THEME_PRIMARY_COLOR="#001d58"
export STREAMLIT_THEME_BACKGROUND_COLOR="#ffffff"
export STREAMLIT_THEME_SECONDARY_BACKGROUND_COLOR="#00f19c"

# Start the demo
streamlit run agentic_demo_ui.py --server.port 8502 --server.address 0.0.0.0