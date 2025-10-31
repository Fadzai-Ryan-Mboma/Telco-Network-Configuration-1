# ============================================================================
# Liquid Zimbabwe 4G Network Optimizer - Production Dockerfile
# ============================================================================
# Base Image: Python 3.11 Slim (Debian-based, optimized for size)
# Total Image Size: ~600MB (including all dependencies)
# Security: Non-root user execution, minimal attack surface
# ============================================================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="Liquid Zimbabwe Network Optimization Team"
LABEL description="AI-powered 4G network optimization using NVIDIA LLMs and LangGraph"
LABEL version="1.0.0"

# ============================================================================
# System Dependencies
# ============================================================================
# Install required system packages and clean up in same layer to reduce size
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    sqlite3 \
    libsqlite3-dev \
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
# Copy application structure (order matters for caching)
COPY agents/ ./agents/
COPY tools/ ./tools/
COPY prompts/ ./prompts/
COPY domain/ ./domain/
COPY network/ ./network/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY main.py .

# Copy Docker utilities
COPY docker/healthcheck.py ./docker/
COPY docker/entrypoint.sh ./docker/

# Create directories for runtime data
RUN mkdir -p /app/data /app/logs

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

# Expose ports (if needed in future for API/UI)
# EXPOSE 8501  # Streamlit UI (Phase 3)
# EXPOSE 8000  # FastAPI (Phase 3)

# ============================================================================
# Health Check
# ============================================================================
# Check container health every 30 seconds
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=5s \
            --retries=3 \
    CMD python3 /app/docker/healthcheck.py || exit 1

# ============================================================================
# Entrypoint & Command
# ============================================================================
# Use entrypoint script for initialization
ENTRYPOINT ["/bin/bash", "/app/docker/entrypoint.sh"]

# Default command: show help
CMD ["python3", "main.py", "--help"]

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
