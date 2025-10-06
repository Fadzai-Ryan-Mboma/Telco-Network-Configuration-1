#!/bin/bash
# Quick Start Script for Liquid Zimbabwe Network Optimizer
# Powered by Cassava Technologies

echo "🚀 Starting Liquid Zimbabwe Network Optimizer..."
echo "📡 Powered by Cassava Technologies"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start the container
echo "🔨 Building Docker container..."
docker-compose build

echo "📊 Starting network optimizer..."
docker-compose up -d

# Wait for container to be ready
echo "⏳ Waiting for application to start..."
sleep 10

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Success! Liquid Zimbabwe Network Optimizer is running"
    echo ""
    echo "🌐 Open your browser and go to: http://localhost:8507"
    echo ""
    echo "📋 Default Huawei API Credentials:"
    echo "   - URL: https://41.174.191.214:31127"
    echo "   - Username: cassava.ai"
    echo "   - Password: #Pass123#"
    echo ""
    echo "🔄 To import historical data:"
    echo "   docker exec telco-network-configuration-telco_ui-1 python import_historical_data.py"
    echo ""
    echo "🛑 To stop: docker-compose down"
else
    echo "❌ Failed to start. Check logs with: docker-compose logs"
fi