#!/bin/bash

# ============================================================================
# Liquid Zimbabwe Network Optimizer - Deployment Script
# ============================================================================
# Created: 2025-10-31
# Description: Automates the deployment of the LZ Network Optimizer container
# ============================================================================

# Set error handling
set -e

# Color definitions for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check if Docker is running
check_docker() {
    log "Checking Docker status..."
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
    fi
    log "Docker is running ✓"
}

# Verify environment file
check_env() {
    log "Checking environment configuration..."
    # Get the script's directory and project root
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"
    ENV_FILE="$PROJECT_ROOT/.env"
    
    log "Looking for .env file at: $ENV_FILE"
    
    if [ ! -f "$ENV_FILE" ]; then
        error ".env file not found at $ENV_FILE. Please ensure you have configured your environment variables."
    fi
    
    # Check required variables
    source "$ENV_FILE"
    if [ -z "$NVIDIA_API_KEY" ] || [ -z "$HUAWEI_API_URL" ] || [ -z "$HUAWEI_USERNAME" ] || [ -z "$HUAWEI_PASSWORD" ]; then
        error "Required environment variables are missing. Please check your .env file."
    fi
    log "Environment configuration verified ✓"
}

# Stop existing containers
stop_existing() {
    log "Stopping any existing containers..."
    docker compose -f "$PROJECT_ROOT/docker/docker-compose.yml" down --remove-orphans 2>/dev/null || true
    log "Cleaned up existing containers ✓"
}

# Build and deploy
deploy() {
    log "Building container..."
    # Change to project root directory
    cd "$PROJECT_ROOT" || error "Failed to change to project root directory"
    
    log "Building from directory: $(pwd)"
    docker compose -f docker/docker-compose.yml build || error "Build failed"
    log "Build completed successfully ✓"

    log "Starting container..."
    docker compose -f docker/docker-compose.yml up -d || error "Container startup failed"
    log "Container started successfully ✓"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Wait for container to be ready
    sleep 5
    
    if ! docker ps | grep -q "lz-network-optimizer"; then
        error "Container is not running. Please check the logs."
    fi
    
    # Check container health
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' lz-network-optimizer 2>/dev/null || echo "none")
    if [ "$HEALTH" != "healthy" ] && [ "$HEALTH" != "none" ]; then
        warning "Container health check failed. Please check the logs for details."
    fi
    
    log "Deployment verified ✓"
    log "Container logs will follow. Press Ctrl+C to exit logs (container will continue running)"
    docker logs -f lz-network-optimizer
}

# Main execution
main() {
    log "Starting LZ Network Optimizer deployment..."
    check_docker
    check_env
    stop_existing
    deploy
    verify_deployment
}

# Run main function
main