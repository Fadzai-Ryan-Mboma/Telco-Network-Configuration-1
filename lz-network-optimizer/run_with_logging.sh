#!/bin/bash
#
# Liquid Zimbabwe 4G Network Optimizer - Startup Script with Logging
# Purpose: Run the application with enhanced terminal logging
# Created: 2025-11-03
#

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default logging mode
MODE="${1:-verbose}"

# Create logs directory
mkdir -p logs

# Set timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/lz_optimizer_${TIMESTAMP}.log"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Liquid Zimbabwe 4G Network Optimizer                         ║${NC}"
echo -e "${BLUE}║  Terminal Logging Mode: ${YELLOW}${MODE^^}${BLUE}                                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

case "$MODE" in
    basic)
        echo -e "${GREEN}📊 Starting in BASIC logging mode${NC}"
        echo -e "   - Minimal terminal output"
        echo -e "   - INFO level logs only"
        echo ""
        export LZ_LOG_MODE=basic
        ;;
    verbose)
        echo -e "${GREEN}📊 Starting in VERBOSE logging mode${NC}"
        echo -e "   - Full agent workflow visibility"
        echo -e "   - Tool calls and API requests"
        echo -e "   - LLM prompts and responses"
        echo -e "   - Colorized terminal output"
        echo ""
        export LZ_LOG_MODE=verbose
        ;;
    debug)
        echo -e "${GREEN}📊 Starting in DEBUG logging mode${NC}"
        echo -e "   - Complete internal debugging"
        echo -e "   - All third-party library logs"
        echo -e "   - Maximum verbosity"
        echo ""
        export LZ_LOG_MODE=debug
        ;;
    *)
        echo -e "${YELLOW}⚠️  Unknown mode: ${MODE}${NC}"
        echo -e "   Usage: $0 [basic|verbose|debug]"
        echo ""
        echo -e "   Modes:"
        echo -e "     ${GREEN}basic${NC}   - Minimal output (quiet)"
        echo -e "     ${GREEN}verbose${NC} - Full workflow visibility (recommended)"
        echo -e "     ${GREEN}debug${NC}   - Complete debugging info (very verbose)"
        echo ""
        exit 1
        ;;
esac

echo -e "${BLUE}📝 Log file:${NC} $LOG_FILE"
echo -e "${BLUE}🌐 UI will be available at:${NC} http://localhost:8501"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the application${NC}"
echo ""
echo -e "${BLUE}${'─' * 80}${NC}"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Activating virtual environment${NC}"
    source venv/bin/activate
fi

# Export log file path
export LZ_LOG_FILE="$LOG_FILE"

# Run Streamlit with Python logging enabled
python3 -m streamlit run ui/app.py \
    --server.headless=true \
    --server.port=8501 \
    --logger.level=info \
    2>&1 | tee "$LOG_FILE"
