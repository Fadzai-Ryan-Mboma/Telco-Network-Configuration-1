#!/bin/bash
# Docker PATH Configuration Script
# Purpose: Add Docker to PATH for testing environment
# Created: 2025-10-31

echo "=================================================="
echo "Docker PATH Configuration"
echo "=================================================="
echo ""

# Add Docker to PATH
export PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin"

echo "✓ Docker PATH added: /Applications/Docker.app/Contents/Resources/bin"
echo ""

# Test Docker availability
if command -v docker &> /dev/null; then
    echo "✅ Docker is now accessible"
    docker --version
    echo ""

    # Check if Docker Desktop is running
    if docker info &> /dev/null; then
        echo "✅ Docker Desktop is running"
        echo ""
        echo "You can now use Docker commands:"
        echo "  - docker --version"
        echo "  - docker compose version"
        echo "  - docker ps"
    else
        echo "⚠️  Docker command available but Docker Desktop may not be running"
        echo ""
        echo "To start Docker Desktop:"
        echo "  open -a Docker"
    fi
else
    echo "❌ Docker command not found"
    echo ""
    echo "Please verify Docker Desktop is installed:"
    echo "  ls /Applications/Docker.app/Contents/Resources/bin/docker"
fi

echo ""
echo "=================================================="
echo "To make this permanent, add to your shell config:"
echo "  echo 'export PATH=\"\$PATH:/Applications/Docker.app/Contents/Resources/bin\"' >> ~/.zshrc"
echo "  source ~/.zshrc"
echo "=================================================="
