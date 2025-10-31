# Docker Deployment Guide - Liquid Zimbabwe 4G Network Optimizer

**Version:** 1.0.0
**Date:** 2025-10-31
**Phase:** 2.5 - Docker Containerization

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Build & Deploy](#build--deploy)
6. [Running the Container](#running-the-container)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)
9. [Production Considerations](#production-considerations)
10. [Maintenance](#maintenance)

---

## Overview

This guide covers deploying the Liquid Zimbabwe 4G Network Optimizer using Docker containers. The application uses:

- **Base Image:** python:3.11-slim
- **Architecture:** Single container (Phase 2.5)
- **Orchestration:** Docker Compose
- **Size:** ~600MB (with dependencies)
- **Security:** Non-root user execution

### What's Included

- 6 LangGraph AI agents
- 10 LangChain tools
- 4-layer prompt system
- SQLite database (168 records)
- NVIDIA API integration
- Huawei API client (with fallback)

---

## Prerequisites

### Required Software

1. **Docker Engine** (20.10+)
   ```bash
   # Check installation
   docker --version

   # Install on Ubuntu/Debian
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Install on MacOS
   brew install --cask docker
   ```

2. **Docker Compose** (2.0+)
   ```bash
   # Check installation
   docker compose version

   # Usually included with Docker Desktop
   # For Linux, install separately:
   sudo apt-get install docker-compose-plugin
   ```

### Required Credentials

You must have:
- **NVIDIA API Key** - Get from [https://build.nvidia.com/](https://build.nvidia.com/)
- **Huawei API Credentials** (optional, system falls back to database)

### System Requirements

- **RAM:** 2GB minimum, 4GB recommended
- **CPU:** 2 cores minimum
- **Disk:** 5GB free space
- **OS:** Linux, MacOS, Windows (with WSL2)

---

## Quick Start

### 1. Clone & Navigate

```bash
cd lz-network-optimizer/
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.template .env

# Edit with your credentials
nano .env  # or vim, code, etc.
```

Add your credentials:
```env
NVIDIA_API_KEY="your-nvidia-api-key-here"
HUAWEI_API_URL="https://your-huawei-endpoint"
HUAWEI_USERNAME="your-username"
HUAWEI_PASSWORD="your-password"
```

### 3. Build Container

```bash
docker compose -f docker/docker-compose.yml build
```

### 4. Run Container

```bash
# See help menu
docker compose -f docker/docker-compose.yml run --rm lz-optimizer

# Run optimization for specific site
docker compose -f docker/docker-compose.yml run --rm lz-optimizer \
  python3 main.py optimize --site MSH0013-Bindura-Zaoga
```

---

## Configuration

### Environment Variables

The container requires these environment variables (configured in `.env`):

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NVIDIA_API_KEY` | ✅ Yes | NVIDIA AI API key | `nvapi-xxxxx...` |
| `HUAWEI_API_URL` | ⚠️ Optional | Huawei iMaster API endpoint | `https://41.174.191.214:31127` |
| `HUAWEI_USERNAME` | ⚠️ Optional | Huawei API username | `cassava.ai` |
| `HUAWEI_PASSWORD` | ⚠️ Optional | Huawei API password | `#Pass123#` |
| `TZ` | ⚠️ Optional | Timezone | `Africa/Harare` |
| `APP_ENV` | ⚠️ Optional | Environment mode | `production` |

### Volume Mounts

The container uses these volume mounts:

| Host Path | Container Path | Mode | Purpose |
|-----------|----------------|------|---------|
| `./data/` | `/app/data/` | RW | Database persistence |
| `./config/` | `/app/config/` | RO | Configuration files |
| `lz-logs` (volume) | `/app/logs/` | RW | Application logs |

### Resource Limits

Configured in `docker-compose.yml`:

- **Memory Limit:** 2GB max
- **Memory Reservation:** 1GB guaranteed
- **CPU Limit:** 2.0 cores max
- **CPU Reservation:** 1.0 core guaranteed

---

## Build & Deploy

### Build from Scratch

```bash
# Build using docker-compose
docker compose -f docker/docker-compose.yml build

# Or build directly with docker
docker build -f docker/Dockerfile -t lz-network-optimizer:latest .
```

### Build Options

```bash
# Build with no cache (force fresh build)
docker compose -f docker/docker-compose.yml build --no-cache

# Build with progress output
docker compose -f docker/docker-compose.yml build --progress=plain

# Multi-platform build (for deployment to different architectures)
docker buildx build --platform linux/amd64,linux/arm64 \
  -f docker/Dockerfile -t lz-network-optimizer:latest .
```

### Verify Build

```bash
# Check image size
docker images lz-network-optimizer

# Expected output:
# REPOSITORY              TAG       SIZE
# lz-network-optimizer    latest    ~600MB
```

---

## Running the Container

### Interactive Mode

```bash
# Start container with shell access
docker compose -f docker/docker-compose.yml run --rm lz-optimizer bash

# Inside container, run commands:
python3 main.py --help
python3 test_workflow.py
```

### One-Off Commands

```bash
# Show help
docker compose -f docker/docker-compose.yml run --rm lz-optimizer \
  python3 main.py --help

# Optimize specific site
docker compose -f docker/docker-compose.yml run --rm lz-optimizer \
  python3 main.py optimize --site MSH0013-Bindura-Zaoga --dry-run

# Run integration tests
docker compose -f docker/docker-compose.yml run --rm lz-optimizer \
  python3 test_workflow.py
```

### Background Service

```bash
# Start as background service
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f

# Stop service
docker compose -f docker/docker-compose.yml down
```

### Port Forwarding (Future UI)

When Streamlit UI is added in Phase 3:

```bash
# Uncomment ports in docker-compose.yml
# ports:
#   - "8501:8501"  # Streamlit UI

# Then access at: http://localhost:8501
```

---

## Testing

### Run All Integration Tests

```bash
docker compose -f docker/docker-compose.yml run --rm lz-optimizer \
  python3 test_workflow.py
```

Expected output:
```
✅ PASS: DATABASE (4 sites, 168 records)
✅ PASS: TOOLS (10 LangChain tools)
✅ PASS: PROMPTS (system prompts, few-shot examples)
✅ PASS: WORKFLOW (6-agent orchestration)

🎉 ALL TESTS PASSED!
```

### Run API Test

```bash
docker compose -f docker/docker-compose.yml run --rm lz-optimizer \
  python3 test_with_api.py
```

### Health Check Test

```bash
# Run health check manually
docker compose -f docker/docker-compose.yml run --rm lz-optimizer \
  python3 /app/docker/healthcheck.py
```

Expected output:
```
HEALTHY: All checks passed
  ✓ Python Imports: Python imports OK
  ✓ Environment Variables: Environment variables OK
  ✓ Database Connectivity: Database OK: lz_network.db, liquid_zimbabwe.db
  ✓ Application Structure: Application structure OK
  ✓ Entry Point: Entry point OK
```

### Container Health Check (Docker)

```bash
# Check container health status
docker compose -f docker/docker-compose.yml ps

# Expected: STATE shows "healthy" after 5 seconds
```

---

## Troubleshooting

### Issue 1: Build Fails - Missing Dependencies

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement langchain==0.3.25
```

**Solution:**
```bash
# Update pip in Dockerfile or use --no-cache
docker compose -f docker/docker-compose.yml build --no-cache
```

### Issue 2: Environment Variables Not Loading

**Symptoms:**
```
UNHEALTHY: Some checks failed
  ✗ Environment Variables: Missing environment variables: NVIDIA_API_KEY
```

**Solution:**
```bash
# Verify .env file exists in parent directory
ls -la ../env

# Check docker-compose.yml env_file path
grep "env_file" docker/docker-compose.yml

# Should show: ../.env (relative to docker/ directory)
```

### Issue 3: Database Not Found

**Symptoms:**
```
⚠️  WARNING: No database files found in /app/data
```

**Solution:**
```bash
# Check database files exist
ls -lh data/*.db

# Verify volume mount in docker-compose.yml
docker compose -f docker/docker-compose.yml config | grep -A5 volumes
```

### Issue 4: Permission Denied

**Symptoms:**
```
ERROR: Cannot write to /app/logs
```

**Solution:**
```bash
# Container runs as lzuser (UID 1000)
# Ensure host directories are accessible

# Fix permissions on host
sudo chown -R 1000:1000 data/ logs/

# Or run with user override (not recommended for production)
docker compose -f docker/docker-compose.yml run --user root --rm lz-optimizer
```

### Issue 5: Out of Memory

**Symptoms:**
```
Container killed (exit code 137)
```

**Solution:**
```bash
# Increase memory limits in docker-compose.yml
# Edit resources.limits.memory from 2G to 4G

# Or run without limits (testing only)
docker run --rm lz-network-optimizer:latest
```

### Issue 6: Network Connection Issues

**Symptoms:**
```
ERROR: Failed to connect to Huawei API
```

**Solution:**
```bash
# This is expected behavior - system falls back to database
# To enable live API access, ensure:

# 1. Huawei API URL is accessible from container
docker compose -f docker/docker-compose.yml run --rm lz-optimizer \
  curl -k https://41.174.191.214:31127

# 2. If behind firewall, add network mode
# In docker-compose.yml, add:
# network_mode: "host"
```

---

## Production Considerations

### Security Best Practices

1. **Never commit .env file**
   ```bash
   # Already in .gitignore
   git check-ignore .env
   # Should return: .env
   ```

2. **Use Docker Secrets (Production)**
   ```yaml
   # In docker-compose.yml (production version)
   secrets:
     nvidia_api_key:
       external: true

   services:
     lz-optimizer:
       secrets:
         - nvidia_api_key
   ```

3. **Enable TLS for Huawei API**
   - Use valid SSL certificates (not self-signed)
   - Verify certificates in production

4. **Network Isolation**
   ```yaml
   # Restrict network access
   networks:
     lz-network:
       internal: true  # No external access
   ```

### Monitoring & Logging

1. **Centralized Logging**
   ```yaml
   # Use logging driver for ELK, CloudWatch, etc.
   logging:
     driver: "fluentd"
     options:
       fluentd-address: localhost:24224
       tag: lz-optimizer
   ```

2. **Metrics Collection**
   - Add Prometheus exporter (Phase 3)
   - Monitor container resource usage
   - Track optimization success rates

3. **Health Monitoring**
   ```bash
   # Set up periodic health checks
   docker compose -f docker/docker-compose.yml ps

   # Integrate with monitoring tools:
   # - Kubernetes liveness/readiness probes
   # - AWS ECS health checks
   # - Docker Swarm health checks
   ```

### Backup & Recovery

1. **Database Backups**
   ```bash
   # Backup databases before optimizations
   docker compose -f docker/docker-compose.yml run --rm lz-optimizer \
     sqlite3 /app/data/lz_network.db ".backup '/app/data/lz_network_backup.db'"

   # Or backup from host
   cp data/lz_network.db data/backups/lz_network_$(date +%Y%m%d).db
   ```

2. **Configuration Backups**
   ```bash
   # Backup config directory
   tar -czf config_backup_$(date +%Y%m%d).tar.gz config/
   ```

### Scaling Considerations

**Current (Phase 2.5):** Single container
**Future (Phase 3+):** Multi-container architecture

```yaml
# Future: Multiple services
services:
  lz-api:
    build: ./api
    replicas: 3  # Horizontal scaling

  lz-ui:
    build: ./ui

  lz-worker:
    build: .
    replicas: 5  # Multiple optimization workers

  redis:
    image: redis:7-alpine
```

---

## Maintenance

### Update Container

```bash
# Pull latest code
git pull origin main

# Rebuild container
docker compose -f docker/docker-compose.yml build --no-cache

# Restart service
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up -d
```

### Clean Up

```bash
# Remove stopped containers
docker compose -f docker/docker-compose.yml down

# Remove volumes (WARNING: deletes data)
docker compose -f docker/docker-compose.yml down -v

# Remove images
docker rmi lz-network-optimizer:latest

# Prune all unused Docker resources
docker system prune -a
```

### View Logs

```bash
# Follow logs in real-time
docker compose -f docker/docker-compose.yml logs -f

# View last 100 lines
docker compose -f docker/docker-compose.yml logs --tail=100

# View logs for specific time range
docker compose -f docker/docker-compose.yml logs --since 2025-10-31T00:00:00
```

### Shell Access

```bash
# Access running container
docker compose -f docker/docker-compose.yml exec lz-optimizer bash

# Or start new container with shell
docker compose -f docker/docker-compose.yml run --rm lz-optimizer bash
```

---

## Advanced Usage

### Custom Commands

Edit `docker-compose.yml` command section:

```yaml
# Run specific optimization
command: ["python3", "main.py", "optimize", "--site", "MSH0013-Bindura-Zaoga"]

# Run in interactive mode
command: ["python3", "main.py", "interactive"]

# Start API server (Phase 3)
command: ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment-Specific Configs

```bash
# Development
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up

# Production
docker compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d

# Staging
docker compose -f docker/docker-compose.yml -f docker/docker-compose.staging.yml up -d
```

### Multi-Stage Builds (Future Optimization)

```dockerfile
# In Dockerfile
FROM python:3.11-slim as builder
# Build dependencies

FROM python:3.11-slim as runtime
# Copy only runtime requirements
# Results in smaller final image (~400MB vs 600MB)
```

---

## Support

### Getting Help

1. **Check logs first:**
   ```bash
   docker compose -f docker/docker-compose.yml logs
   ```

2. **Run health check:**
   ```bash
   docker compose -f docker/docker-compose.yml run --rm lz-optimizer \
     python3 /app/docker/healthcheck.py
   ```

3. **Review documentation:**
   - [README.md](../README.md) - Project overview
   - [TESTING_GUIDE.md](../TESTING_GUIDE.md) - Testing procedures
   - [NVIDIA_API_INTEGRATION_FIX.md](../documentation/NVIDIA_API_INTEGRATION_FIX.md) - API integration guide

### Common Commands Reference

```bash
# Build
docker compose -f docker/docker-compose.yml build

# Run
docker compose -f docker/docker-compose.yml run --rm lz-optimizer python3 main.py

# Start service
docker compose -f docker/docker-compose.yml up -d

# Stop service
docker compose -f docker/docker-compose.yml down

# Logs
docker compose -f docker/docker-compose.yml logs -f

# Shell
docker compose -f docker/docker-compose.yml run --rm lz-optimizer bash

# Health check
docker compose -f docker/docker-compose.yml ps

# Clean up
docker compose -f docker/docker-compose.yml down -v
```

---

## Changelog

### Version 1.0.0 (2025-10-31)

**Phase 2.5 Complete:**
- ✅ Created Dockerfile (python:3.11-slim)
- ✅ Created docker-compose.yml
- ✅ Added health check script
- ✅ Added entrypoint script
- ✅ Configured volume mounts
- ✅ Implemented security best practices
- ✅ Documentation complete

**Ready For:**
- Live deployment with Docker
- Integration with CI/CD pipelines
- Kubernetes orchestration (future)

---

**Last Updated:** 2025-10-31
**Document Version:** 1.0.0
**Project Phase:** 2.5 - Docker Containerization Complete
