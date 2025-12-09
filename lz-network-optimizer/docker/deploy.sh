#!/bin/bash
# ============================================================================
# Liquid Zimbabwe 4G Network Optimizer - Docker Deployment Script
# ============================================================================
# Usage: ./deploy.sh [build|start|stop|restart|logs|status]
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Liquid Zimbabwe 4G Network Optimizer - Docker Deployment${NC}"
echo -e "${BLUE}============================================================================${NC}"

# Change to project directory
cd "$PROJECT_DIR"

case "${1:-help}" in
    build)
        echo -e "${YELLOW}Building Docker image...${NC}"
        docker-compose -f docker/docker-compose.yml build
        echo -e "${GREEN}✓ Build complete${NC}"
        ;;
        
    start)
        echo -e "${YELLOW}Starting services...${NC}"
        docker-compose -f docker/docker-compose.yml up -d
        echo ""
        echo -e "${GREEN}✅ Services started!${NC}"
        echo ""
        echo -e "   ${BLUE}Streamlit UI:${NC}    http://localhost:8502"
        echo -e "   ${BLUE}FastAPI Backend:${NC} http://localhost:8503"
        echo -e "   ${BLUE}API Docs:${NC}        http://localhost:8503/docs"
        echo ""
        echo -e "   ${YELLOW}View logs:${NC} ./docker/deploy.sh logs"
        ;;
        
    stop)
        echo -e "${YELLOW}Stopping services...${NC}"
        docker-compose -f docker/docker-compose.yml down
        echo -e "${GREEN}✓ Services stopped${NC}"
        ;;
        
    restart)
        echo -e "${YELLOW}Restarting services...${NC}"
        docker-compose -f docker/docker-compose.yml down
        docker-compose -f docker/docker-compose.yml up -d
        echo -e "${GREEN}✓ Services restarted${NC}"
        ;;
        
    logs)
        echo -e "${YELLOW}Showing logs (Ctrl+C to exit)...${NC}"
        docker-compose -f docker/docker-compose.yml logs -f
        ;;
        
    status)
        echo -e "${YELLOW}Service status:${NC}"
        docker-compose -f docker/docker-compose.yml ps
        echo ""
        echo -e "${YELLOW}Health check:${NC}"
        curl -s http://localhost:8503/api/health 2>/dev/null | python3 -m json.tool || echo -e "${RED}API not responding${NC}"
        ;;
        
    shell)
        echo -e "${YELLOW}Opening shell in container...${NC}"
        docker-compose -f docker/docker-compose.yml exec lz-optimizer bash
        ;;
        
    rebuild)
        echo -e "${YELLOW}Rebuilding and restarting...${NC}"
        docker-compose -f docker/docker-compose.yml down
        docker-compose -f docker/docker-compose.yml build --no-cache
        docker-compose -f docker/docker-compose.yml up -d
        echo -e "${GREEN}✓ Rebuild complete${NC}"
        ;;
        
    help|--help|-h|*)
        echo ""
        echo "Usage: ./deploy.sh [command]"
        echo ""
        echo "Commands:"
        echo -e "  ${GREEN}build${NC}    - Build Docker image"
        echo -e "  ${GREEN}start${NC}    - Start services (API + UI)"
        echo -e "  ${GREEN}stop${NC}     - Stop all services"
        echo -e "  ${GREEN}restart${NC}  - Restart all services"
        echo -e "  ${GREEN}logs${NC}     - View live logs"
        echo -e "  ${GREEN}status${NC}   - Show service status and health"
        echo -e "  ${GREEN}shell${NC}    - Open shell in container"
        echo -e "  ${GREEN}rebuild${NC}  - Rebuild image and restart"
        echo ""
        echo "Examples:"
        echo "  ./docker/deploy.sh build   # Build the image"
        echo "  ./docker/deploy.sh start   # Start services"
        echo "  ./docker/deploy.sh logs    # View logs"
        echo ""
        ;;
esac
