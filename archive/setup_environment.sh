#!/bin/bash
# Liquid Zimbabwe 4G - Quick Environment Setup Script

echo "🚀 LIQUID ZIMBABWE 4G - ENVIRONMENT SETUP"
echo "=========================================="

# Create .env template if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env template..."
    cat > .env << EOF
# Huawei iMaster MAE API Configuration
# Replace with your actual values:
LZ_API_URL=https://your-huawei-imaster-server.com
LZ_API_USERNAME=your_api_username
LZ_API_PASSWORD=your_api_password

# Optional Configuration
LZ_API_TIMEOUT=30
LZ_API_RETRY_ATTEMPTS=3
LZ_API_SSL_VERIFY=true

# Database Configuration
LZ_DB_PATH=./data/historical_db

# Logging Configuration
LZ_LOG_LEVEL=INFO
LZ_LOG_PATH=./logs/lz_system.log
EOF
    echo "✅ .env template created - please update with your actual values"
    echo "⚠️  IMPORTANT: Update the API credentials in .env before proceeding"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p data logs
chmod 750 logs

# Secure the .env file
chmod 600 .env
echo "🔒 .env file secured"

# Check if .gitignore needs updating
if [ -f ../.gitignore ]; then
    if ! grep -q "\.env" ../.gitignore; then
        echo ".env" >> ../.gitignore
        echo "*.log" >> ../.gitignore
        echo "🔒 Added .env and logs to .gitignore"
    fi
fi

echo ""
echo "🎯 NEXT STEPS:"
echo "1. Edit .env file with your Huawei API credentials:"
echo "   nano .env"
echo ""
echo "2. Test your configuration:"
echo "   python production_validator.py"
echo ""
echo "3. If validation passes, start the system:"
echo "   streamlit run ui/ui.py --server.port 8501"
echo ""
echo "✅ Environment setup complete!"