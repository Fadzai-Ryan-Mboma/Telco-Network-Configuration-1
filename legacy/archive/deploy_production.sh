#!/bin/bash
# Liquid Zimbabwe 4G - Production Deployment Script

echo "🚀 LIQUID ZIMBABWE 4G - PRODUCTION DEPLOYMENT"
echo "============================================="

# Set production environment
export LZ_API_URL=https://41.174.191.214:31127
export LZ_API_USERNAME=cassava.ai
export LZ_API_PASSWORD='#Pass123#'
export LZ_ENV=production
export PYTHONUNBUFFERED=1
export TZ=Africa/Harare

echo "✅ Production environment configured"
echo "   URL: $LZ_API_URL"
echo "   User: $LZ_API_USERNAME"
echo "   Timezone: $TZ"

# Validate system before deployment
echo ""
echo "🔍 Validating production readiness..."
python production_validator.py

validation_exit_code=$?

if [ $validation_exit_code -eq 0 ]; then
    echo ""
    echo "🎊 ✅ VALIDATION PASSED - READY FOR PRODUCTION!"
    echo ""
    echo "🚀 Starting Liquid Zimbabwe 4G Production System..."
    echo "   Dashboard: http://localhost:8501"
    echo "   Press Ctrl+C to stop"
    echo ""
    
    # Start the production system
    streamlit run ui/ui.py --server.port 8501 --server.address 0.0.0.0
    
elif [ $validation_exit_code -eq 1 ]; then
    echo ""
    echo "⚠️  VALIDATION PASSED WITH WARNINGS"
    echo "   System is functional but has minor issues"
    echo ""
    read -p "   Continue with deployment? (y/n): " continue_deploy
    
    if [ "$continue_deploy" = "y" ] || [ "$continue_deploy" = "Y" ]; then
        echo ""
        echo "🚀 Starting Liquid Zimbabwe 4G Production System..."
        echo "   Dashboard: http://localhost:8501"
        echo "   Press Ctrl+C to stop"
        echo ""
        streamlit run ui/ui.py --server.port 8501 --server.address 0.0.0.0
    else
        echo "❌ Deployment cancelled"
        exit 1
    fi
else
    echo ""
    echo "❌ VALIDATION FAILED - PRODUCTION DEPLOYMENT BLOCKED"
    echo "   Please resolve critical issues before deployment"
    exit 1
fi