# ============================================================================
# Liquid Zimbabwe 4G Network Optimizer - Production Dockerfile
# ============================================================================
# Base Image: Python 3.11 Slim (Debian-based, optimized for size)
# Total Image Size: ~700MB (including all dependencies)
# Security: Non-root user execution, minimal attack surface
# Services: FastAPI (8503) + Streamlit UI (8501)
# ============================================================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="Liquid Zimbabwe Network Optimization Team"
LABEL description="AI-powered 4G network optimization using NVIDIA LLMs and LangGraph"
LABEL version="2.1.0"

# ============================================================================
# System Dependencies
# ============================================================================
# Install required system packages and clean up in same layer to reduce size
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    sqlite3 \
    libsqlite3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================================================
# Application Setup
# ============================================================================
# Set working directory
WORKDIR /app

# Copy requirements first (Docker layer caching optimization)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Copy Application Code
# ============================================================================
# Create necessary directories first
RUN mkdir -p /app/docker /app/data /app/logs /app/ui /app/api

# Copy all application files
COPY . /app/

# Ensure proper permissions on scripts
RUN chmod +x /app/docker/entrypoint.sh /app/docker/healthcheck.py

# ============================================================================
# Security: Non-Root User
# ============================================================================
# Create non-root user for security best practices
RUN useradd -m -s /bin/bash -u 1000 lzuser && \
    chown -R lzuser:lzuser /app

# Switch to non-root user
USER lzuser

# ============================================================================
# Container Configuration
# ============================================================================
# Environment variables (can be overridden at runtime)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Africa/Harare \
    PATH="/home/lzuser/.local/bin:${PATH}"

# Expose ports for API and UI
EXPOSE 8502
EXPOSE 8503

# ============================================================================
# Health Check
# ============================================================================
# Check container health every 30 seconds
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=15s \
            --retries=3 \
    CMD curl -f http://localhost:8503/api/health || exit 1

# ============================================================================
# Entrypoint & Command
# ============================================================================
# Use entrypoint script for initialization
ENTRYPOINT ["/bin/bash", "/app/docker/entrypoint.sh"]

# Default command: Run both API and UI
CMD ["both"]

# ============================================================================
# Build Instructions:
# ============================================================================
# From lz-network-optimizer/ directory:
#   docker build -f docker/Dockerfile -t lz-network-optimizer:latest .
#
# Run:
#   docker run --rm lz-network-optimizer:latest
#
# With docker-compose:
#   docker-compose -f docker/docker-compose.yml up
# ============================================================================
