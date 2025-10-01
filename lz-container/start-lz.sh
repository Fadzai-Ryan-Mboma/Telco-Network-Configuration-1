#!/bin/bash

# Liquid Zimbabwe 4G Network - Container Build and Run Script
# Phase 1 Implementation

set -e

echo "🚀 Liquid Zimbabwe 4G Network - Container Setup"
echo "================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Navigate to the container directory
cd "$(dirname "$0")"

echo "📦 Building Liquid Zimbabwe 4G container..."
docker compose -f docker-compose.lz.yaml build

echo "🔍 Validating container configuration..."
docker compose -f docker-compose.lz.yaml config

echo "🌐 Starting Liquid Zimbabwe 4G Network Optimizer..."
docker compose -f docker-compose.lz.yaml up -d

echo "⏳ Waiting for container to be ready..."
sleep 10

# Check container status
if docker compose -f docker-compose.lz.yaml ps | grep -q "Up"; then
    echo "✅ Liquid Zimbabwe 4G Network Optimizer is running!"
    echo ""
    echo "📊 Access the monitoring interface at: http://localhost:8501"
    echo "🔧 API endpoint available at: http://localhost:8502"
    echo ""
    echo "📋 Container Status:"
    docker compose -f docker-compose.lz.yaml ps
    echo ""
    echo "📝 To view logs: docker compose -f docker-compose.lz.yaml logs -f"
    echo "🛑 To stop: docker compose -f docker-compose.lz.yaml down"
else
    echo "❌ Failed to start container. Checking logs..."
    docker compose -f docker-compose.lz.yaml logs
    exit 1
fi