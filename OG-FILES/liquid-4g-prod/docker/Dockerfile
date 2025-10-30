# Production Dockerfile for Liquid 4G Network Optimizer

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create data directory
RUN mkdir -p /app/data

# Expose ports
EXPOSE 8000 8501

# Default command (can be overridden)
CMD ["python", "-m", "liquid4g", "api"]
