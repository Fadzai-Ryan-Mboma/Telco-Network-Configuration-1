# Cassava 4G Network Optimizer - Multi-stage Docker Build
# Branding: Navy #001D58, Green #00F19C, Purple #964BEA

# ============================================================================
# Stage 1: Builder - Install dependencies and build the package
# ============================================================================
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements first for caching
WORKDIR /build
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install build && \
    pip install "langchain>=0.2.0" \
                "langchain-nvidia-ai-endpoints>=0.2.0" \
                "langgraph>=0.2.0" \
                "pydantic>=2.7.0" \
                "pydantic-settings>=2.2.0" \
                "sqlalchemy[asyncio]>=2.0.0" \
                "aiosqlite>=0.20.0" \
                "httpx>=0.27.0" \
                "structlog>=24.0.0" \
                "streamlit>=1.35.0" \
                "plotly>=5.22.0" \
                "pandas>=2.2.0" \
                "typer>=0.12.0" \
                "tenacity>=8.3.0" \
                "uvloop>=0.19.0" \
                "orjson>=3.10.0"

# Copy source code
COPY src/ ./src/
COPY README.md ./

# Install the package (not editable, for proper packaging)
RUN pip install .

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.11-slim as runtime

# Labels for Cassava branding
LABEL maintainer="Cassava Technologies" \
      version="1.0.0" \
      description="Cassava 4G Network Optimizer - AI-powered network optimization"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    # Application settings
    CASSAVA_ENV=production \
    CASSAVA_LOG_LEVEL=INFO \
    CASSAVA_DATABASE_URL=sqlite+aiosqlite:///data/cassava_network.db \
    # Streamlit settings
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_THEME_BASE=dark

# Create non-root user for security
RUN groupadd --gid 1000 cassava && \
    useradd --uid 1000 --gid cassava --shell /bin/bash --create-home cassava

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only necessary application files
COPY --chown=cassava:cassava pyproject.toml README.md ./
COPY --chown=cassava:cassava src/ ./src/
COPY --chown=cassava:cassava .streamlit/ ./.streamlit/
COPY --chown=cassava:cassava data/ ./data/

# Create necessary directories
RUN mkdir -p /app/logs /app/reports && \
    chown -R cassava:cassava /app

# Switch to non-root user
USER cassava

# Expose ports
# 8501 - Streamlit UI
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command - run the Streamlit UI
CMD ["python", "-m", "streamlit", "run", "src/cassava_optimizer/ui/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]

# ============================================================================
# Alternative entrypoints (use with docker run --entrypoint)
# ============================================================================
# Initialize database:
#   docker run --entrypoint python cassava-optimizer scripts/init_db.py
#
# Run optimization directly:
#   docker run --entrypoint python cassava-optimizer -m cassava_optimizer.scripts.run optimize --site-id SITE001
#
# Run with CLI:
#   docker run --entrypoint python cassava-optimizer scripts/run.py --help
