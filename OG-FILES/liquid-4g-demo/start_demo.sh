#!/bin/bash
# Demo Startup Script
# ===================
# Quick start script for the 6-Stage Agentic Network Optimization Demo

echo "=================================="
echo "6-STAGE AGENTIC DEMO STARTUP"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "main_demo_orchestrator.py" ]; then
    echo "Error: Please run this script from the liquid-4g-demo directory"
    exit 1
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p demo_results
mkdir -p test_results
mkdir -p logs

# Check Python version
echo "Checking Python..."
python3 --version || {
    echo "Error: Python 3 is required"
    exit 1
}

# Install basic requirements if available
if [ -f "../requirements-lz.txt" ]; then
    echo "Installing requirements..."
    pip3 install -r ../requirements-lz.txt || echo "Warning: Some packages may not be available"
fi

echo ""
echo "=================================="
echo "DEMO STARTUP OPTIONS"
echo "=================================="
echo "1. Run Interactive Console Demo"
echo "2. Run Specific Scenario (Automated)"
echo "3. Run Test Suite"
echo "4. Start Streamlit UI (if available)"
echo "5. Show Available Scenarios"
echo ""

read -p "Select option (1-5): " choice

case $choice in
    1)
        echo "Starting interactive console demo..."
        python3 main_demo_orchestrator.py
        ;;
    2)
        echo "Available scenarios:"
        echo "- bindura_optimization"
        echo "- emergency_response"
        echo "- preventive_maintenance"
        echo "- full_showcase"
        echo ""
        read -p "Enter scenario name: " scenario
        echo "Running scenario: $scenario"
        python3 main_demo_orchestrator.py "$scenario" automated
        ;;
    3)
        echo "Running comprehensive test suite..."
        python3 demo_test_suite.py
        ;;
    4)
        echo "Starting Streamlit UI..."
        if command -v streamlit &> /dev/null; then
            streamlit run enhanced_streamlit_demo.py
        else
            echo "Streamlit not available. Install with: pip install streamlit"
            echo "Falling back to console interface..."
            python3 main_demo_orchestrator.py
        fi
        ;;
    5)
        echo "Available Demo Scenarios:"
        echo ""
        echo "1. Bindura Network Optimization (25 min, Medium Risk)"
        echo "   - Real Bindura network data"
        echo "   - RACH and IBLER optimization"
        echo "   - Interactive approval workflow"
        echo ""
        echo "2. Emergency Network Response (15 min, High Risk)"
        echo "   - Rapid response simulation"
        echo "   - Emergency capacity optimization"
        echo "   - Accelerated approval process"
        echo ""
        echo "3. Preventive Network Maintenance (35 min, Low Risk)"
        echo "   - Proactive optimization"
        echo "   - Multi-site analysis"
        echo "   - Comprehensive monitoring"
        echo ""
        echo "4. Complete Capability Showcase (45 min, Medium Risk)"
        echo "   - Full 6-stage demonstration"
        echo "   - All features and capabilities"
        echo "   - Step-by-step execution"
        ;;
    *)
        echo "Invalid option. Exiting..."
        exit 1
        ;;
esac

echo ""
echo "Demo execution completed."
echo "Results available in: demo_results/"
echo "Logs available in: logs/"