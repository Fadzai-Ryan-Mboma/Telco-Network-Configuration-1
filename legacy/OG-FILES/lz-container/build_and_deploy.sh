#!/bin/bash

# Liquid Zimbabwe 4G Platform - Production Container Deployment Script
# This script builds and deploys the LZ 4G optimization platform in a container

set -e  # Exit on any error

echo "=========================================="
echo "LZ 4G PLATFORM - CONTAINER DEPLOYMENT"
echo "=========================================="

# Configuration
LZ_IMAGE_NAME="liquid-zimbabwe-4g"
LZ_CONTAINER_NAME="lz-4g-platform"
LZ_VERSION="production-1.0"

echo "Building LZ 4G Platform container..."
echo "Image: ${LZ_IMAGE_NAME}:${LZ_VERSION}"

# Build the container
docker build -f Dockerfile.lz -t ${LZ_IMAGE_NAME}:${LZ_VERSION} ../

if [ $? -eq 0 ]; then
    echo "✅ Container build successful!"
else
    echo "❌ Container build failed!"
    exit 1
fi

echo ""
echo "=========================================="
echo "DEPLOYMENT OPTIONS"
echo "=========================================="
echo ""
echo "1. Quick Start (using docker-compose):"
echo "   docker-compose -f docker-compose.lz.yaml up -d"
echo ""
echo "2. Manual Docker Run:"
echo "   docker run -d --name ${LZ_CONTAINER_NAME} \\"
echo "              -p 8501:8501 \\"
echo "              -v \$(pwd)/data:/app/data \\"
echo "              -v \$(pwd)/logs:/app/logs \\"
echo "              --env-file production.env \\"
echo "              ${LZ_IMAGE_NAME}:${LZ_VERSION}"
echo ""
echo "3. Production Deployment:"
echo "   docker-compose -f docker-compose.lz.yaml up -d"
echo ""

read -p "Would you like to start the container now? (y/n): " start_now

if [ "$start_now" = "y" ] || [ "$start_now" = "Y" ]; then
    echo ""
    echo "Starting LZ 4G Platform with docker compose..."
    docker compose -f docker-compose.lz.yaml up -d
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ LZ 4G Platform is now running!"
        echo "🌐 Access the dashboard at: http://localhost:8501"
        echo "📊 Monitor with: docker logs ${LZ_CONTAINER_NAME}"
        echo "🛑 Stop with: docker compose -f docker-compose.lz.yaml down"
        echo ""
        echo "Production API Configuration:"
        echo "• URL: https://41.174.191.214:31127"
        echo "• User: cassava.ai"
        echo "• Status: ✅ Authenticated and validated"
    else
        echo "❌ Failed to start container!"
        exit 1
    fi
else
    echo ""
    echo "Container built successfully. Use the deployment commands above when ready."
fi

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo "=========================================="