#!/bin/bash
"""
Startup Guide for Liquid 4G Network Optimizer

This guide shows you how to start both the UI and API services.
"""

# Liquid 4G Network Optimizer - Startup Guide
# ============================================

echo "🚀 Starting Liquid 4G Network Optimizer Services"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Not in liquid-4g-prod directory"
    echo "   Please run: cd liquid-4g-prod"
    exit 1
fi

echo ""
echo "📋 Quick Start Options:"
echo ""

echo "Option 1: Start UI only (recommended for testing)"
echo "  streamlit run src/liquid4g/interfaces/ui/app.py"
echo ""

echo "Option 2: Start API only"  
echo "  python -m liquid4g api --host localhost --port 8000"
echo ""

echo "Option 3: Start both services (requires 2 terminals)"
echo "  Terminal 1: python -m liquid4g api --host localhost --port 8000"
echo "  Terminal 2: streamlit run src/liquid4g/interfaces/ui/app.py"
echo ""

echo "Option 4: Start both with Docker (if Docker is set up)"
echo "  docker-compose up -d"
echo ""

echo "🔗 Access Points:"
echo "  • Web UI:    http://localhost:8501"
echo "  • API Docs:  http://localhost:8000/docs" 
echo "  • API Root:  http://localhost:8000"
echo ""

echo "🛠️ Troubleshooting:"
echo "  • UI not loading: Check if streamlit is installed (pip install streamlit)"
echo "  • API not working: Check if FastAPI is installed (pip install fastapi uvicorn)"
echo "  • Database errors: Run the database fix script first"
echo ""

echo "✅ The UI is currently working! You can access it at:"
echo "   http://localhost:8501"