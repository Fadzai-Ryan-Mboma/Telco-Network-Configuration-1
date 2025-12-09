#!/bin/bash
# ============================================================================
# Liquid Zimbabwe 4G Network Optimizer - Container Entrypoint
# ============================================================================
# Purpose: Initialize container environment and validate configuration
# Exit Codes:
#   0 = Success
#   1 = Critical error (container should not start)
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "Liquid Zimbabwe 4G Network Optimizer - Starting Container"
echo "============================================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "Container: $(hostname)"
echo "User: $(whoami)"
echo "Working Directory: $(pwd)"
echo "============================================================================"

# ============================================================================
# Function: Check Environment Variable
# ============================================================================
check_env_var() {
    local var_name="$1"
    local required="$2"

    if [ -z "${!var_name}" ]; then
        if [ "$required" = "true" ]; then
            echo "❌ ERROR: Required environment variable $var_name is not set"
            return 1
        else
            echo "⚠️  WARNING: Optional environment variable $var_name is not set"
            return 0
        fi
    else
        # Mask sensitive values
        if [[ "$var_name" == *"KEY"* ]] || [[ "$var_name" == *"PASSWORD"* ]] || [[ "$var_name" == *"SECRET"* ]]; then
            local value="${!var_name}"
            local masked="${value:0:10}...${value: -4}"
            echo "✓ $var_name is set ($masked)"
        else
            echo "✓ $var_name is set (${!var_name})"
        fi
        return 0
    fi
}

# ============================================================================
# Step 1: Validate Environment Variables
# ============================================================================
echo ""
echo "Step 1: Validating Environment Variables"
echo "----------------------------------------------------------------------------"

ENV_CHECK_PASSED=true

# Required variables
check_env_var "NVIDIA_API_KEY" "true" || ENV_CHECK_PASSED=false

# Optional variables (warnings only)
check_env_var "HUAWEI_API_URL" "false"
check_env_var "HUAWEI_USERNAME" "false"
check_env_var "HUAWEI_PASSWORD" "false"

if [ "$ENV_CHECK_PASSED" = "false" ]; then
    echo ""
    echo "❌ FATAL: Critical environment variables missing"
    echo "   Please ensure .env file is properly configured"
    echo "   See .env.template for reference"
    exit 1
fi

echo "✓ Environment validation passed"

# ============================================================================
# Step 2: Check Database Files
# ============================================================================
echo ""
echo "Step 2: Checking Database Files"
echo "----------------------------------------------------------------------------"

DB_DIR="/app/data"
if [ ! -d "$DB_DIR" ]; then
    echo "⚠️  WARNING: Database directory $DB_DIR does not exist"
    echo "   Creating directory..."
    mkdir -p "$DB_DIR"
fi

# Check for database files
DB_FILES=("lz_network.db" "liquid_zimbabwe.db" "live_network.db")
DB_FOUND=false

for db_file in "${DB_FILES[@]}"; do
    db_path="$DB_DIR/$db_file"
    if [ -f "$db_path" ]; then
        echo "✓ Found database: $db_file ($(du -h "$db_path" | cut -f1))"
        DB_FOUND=true
    else
        echo "  Missing database: $db_file (will use available databases)"
    fi
done

if [ "$DB_FOUND" = "false" ]; then
    echo "⚠️  WARNING: No database files found in $DB_DIR"
    echo "   System will operate with limited functionality"
fi

# ============================================================================
# Step 3: Check Application Structure
# ============================================================================
echo ""
echo "Step 3: Verifying Application Structure"
echo "----------------------------------------------------------------------------"

REQUIRED_DIRS=("agents" "tools" "prompts" "domain" "network" "config")
STRUCTURE_OK=true

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "/app/$dir" ]; then
        file_count=$(find "/app/$dir" -name "*.py" | wc -l)
        echo "✓ $dir/ directory exists ($file_count Python files)"
    else
        echo "❌ ERROR: Missing required directory: $dir/"
        STRUCTURE_OK=false
    fi
done

if [ "$STRUCTURE_OK" = "false" ]; then
    echo ""
    echo "❌ FATAL: Application structure is incomplete"
    exit 1
fi

# Check main entry point
if [ -f "/app/main.py" ]; then
    echo "✓ main.py entry point exists"
else
    echo "❌ ERROR: main.py not found"
    exit 1
fi

# ============================================================================
# Step 4: Verify Python Dependencies
# ============================================================================
echo ""
echo "Step 4: Verifying Python Dependencies"
echo "----------------------------------------------------------------------------"

# Test critical imports
python3 -c "import langchain; print('✓ langchain installed')" || exit 1
python3 -c "import langgraph; print('✓ langgraph installed')" || exit 1
python3 -c "import langchain_nvidia_ai_endpoints; print('✓ langchain-nvidia-ai-endpoints installed')" || exit 1
python3 -c "from dotenv import load_dotenv; print('✓ python-dotenv installed')" || exit 1

echo "✓ All critical dependencies available"

# ============================================================================
# Step 5: Set Permissions (if needed)
# ============================================================================
echo ""
echo "Step 5: Checking Permissions"
echo "----------------------------------------------------------------------------"

# Ensure logs directory is writable
LOGS_DIR="/app/logs"
if [ ! -d "$LOGS_DIR" ]; then
    mkdir -p "$LOGS_DIR"
fi

if [ -w "$LOGS_DIR" ]; then
    echo "✓ Logs directory is writable"
else
    echo "⚠️  WARNING: Logs directory is not writable"
fi

# ============================================================================
# Step 6: Display Configuration Summary
# ============================================================================
echo ""
echo "============================================================================"
echo "Container Configuration Summary"
echo "============================================================================"
echo "Python Version: $(python3 --version)"
echo "Working Directory: $(pwd)"
echo "Data Directory: $DB_DIR"
echo "Logs Directory: $LOGS_DIR"
echo "Timezone: ${TZ:-UTC}"
echo "App Environment: ${APP_ENV:-production}"
echo "============================================================================"

# ============================================================================
# Step 7: Execute Command
# ============================================================================
echo ""
echo "Starting Application..."
echo "============================================================================"
echo ""

# Setup logging directory
LOG_DIR="/app/logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# Handle different run modes
case "${1:-help}" in
    "both"|"all")
        echo "🚀 Starting both FastAPI Backend and Streamlit UI..."
        echo ""
        
        # Start FastAPI backend with logging
        echo "Starting FastAPI on port 8503..."
        uvicorn api.main:app --host 0.0.0.0 --port 8503 \
            2>&1 | tee -a "$LOG_DIR/api.log" &
        API_PID=$!
        echo "✓ FastAPI started (PID: $API_PID)"
        
        # Wait for API to be ready
        sleep 3
        
        # Start Streamlit UI with logging
        echo "Starting Streamlit UI on port 8502..."
        streamlit run ui/app.py \
            --server.port 8502 \
            --server.address 0.0.0.0 \
            --server.headless true \
            --browser.gatherUsageStats false \
            2>&1 | tee -a "$LOG_DIR/ui.log" &
        UI_PID=$!
        echo "✓ Streamlit UI started (PID: $UI_PID)"
        
        echo ""
        echo "============================================================================"
        echo "✅ Services Running:"
        echo "   • Streamlit UI:    http://localhost:8502"
        echo "   • FastAPI Backend: http://localhost:8503"
        echo "   • API Docs:        http://localhost:8503/docs"
        echo ""
        echo "📁 Logs available at:"
        echo "   • API logs: $LOG_DIR/api.log"
        echo "   • UI logs:  $LOG_DIR/ui.log"
        echo "============================================================================"
        
        # Wait for both processes
        wait $API_PID $UI_PID
        ;;
        
    "api")
        echo "🚀 Starting FastAPI Backend only..."
        exec uvicorn api.main:app --host 0.0.0.0 --port 8503 \
            2>&1 | tee -a "$LOG_DIR/api.log"
        ;;
        
    "ui")
        echo "🚀 Starting Streamlit UI only..."
        exec streamlit run ui/app.py \
            --server.port 8502 \
            --server.address 0.0.0.0 \
            --server.headless true \
            --browser.gatherUsageStats false \
            2>&1 | tee -a "$LOG_DIR/ui.log"
        ;;
        
    "help"|"--help"|"-h")
        echo "Usage: entrypoint.sh [command]"
        echo ""
        echo "Commands:"
        echo "  both    - Start both FastAPI and Streamlit (default)"
        echo "  api     - Start FastAPI backend only"
        echo "  ui      - Start Streamlit UI only"
        echo "  help    - Show this help message"
        echo ""
        exec "$@"
        ;;
        
    *)
        # Execute any other command passed
        exec "$@"
        ;;
esac
