# Phase 5 - Stage 5.2: Docker Deployment Validation Guide

**Date:** 2025-11-03
**Stage:** 5.2 - Docker Deployment Validation
**Purpose:** Manual validation steps for Docker deployment with Phase 5 updates

---

## Prerequisites Checklist

- ✅ Stage 5.1 Complete - Tools updated and tested
- ✅ Docker installed and accessible
- ✅ Docker Compose installed
- ✅ `.env` file configured with API credentials
- ✅ Database files present in `data/` directory

---

## Quick Start - Docker Deployment

### Step 1: Build Docker Image

```bash
cd lz-network-optimizer
docker build -f docker/Dockerfile -t lz-network-optimizer:phase5 .
```

**Expected Output:**
- Build completes successfully
- Image size: ~600-800MB
- No build errors

**Verification:**
```bash
docker images | grep lz-network-optimizer
```

### Step 2: Verify Image Contents

```bash
# Check updated tools are present
docker run --rm lz-network-optimizer:phase5 ls -la /app/tools/

# Should show:
# - huawei_tools.py (updated)
# - huawei_tools_original.py (backup)
# - rollback_manager.py (new)
```

### Step 3: Test Tool Imports in Container

```bash
# Test Huawei tools import (should show 6 tools)
docker run --rm lz-network-optimizer:phase5 \
  python3 -c "from tools.huawei_tools import HUAWEI_TOOLS; print(f'{len(HUAWEI_TOOLS)} tools loaded')"

# Test rollback manager import (should show 4 tools)
docker run --rm lz-network-optimizer:phase5 \
  python3 -c "from tools.rollback_manager import ROLLBACK_TOOLS; print(f'{len(ROLLBACK_TOOLS)} tools loaded')"
```

**Expected Output:**
```
6 tools loaded
4 tools loaded
```

### Step 4: Test API Connectivity from Container

```bash
# Run API connectivity test in container
docker run --rm --env-file .env \
  -v "$(pwd)/data:/app/data" \
  lz-network-optimizer:phase5 \
  python3 test_updated_tools.py
```

**Expected Results:**
- ✅ Tool Imports: PASS
- ✅ Rollback Manager Import: PASS
- ✅ API Connectivity: PASS
- ✅ Query with site_name: PASS (should retrieve value from Bindura Hospital)
- ✅ Batch Tool (Dry-Run): PASS

### Step 5: Test Database Access

```bash
# Check database connectivity
docker run --rm -v "$(pwd)/data:/app/data" \
  lz-network-optimizer:phase5 \
  python3 -c "import sqlite3; conn = sqlite3.connect('/app/data/lz_network.db'); cur = conn.cursor(); cur.execute('SELECT COUNT(*) FROM sites'); print(f'Sites: {cur.fetchone()[0]}'); conn.close()"
```

**Expected Output:** Shows number of sites in database

### Step 6: Test UI Startup

```bash
# Start UI in container (detached mode)
docker run -d --name lz-ui-test \
  --env-file .env \
  -v "$(pwd)/data:/app/data" \
  -p 8501:8501 \
  lz-network-optimizer:phase5 \
  streamlit run ui/app.py --server.headless=true
```

**Check UI Logs:**
```bash
docker logs -f lz-ui-test
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

**Test UI Access:**
- Open browser: `http://localhost:8501`
- Verify UI loads correctly
- Check all pages accessible

**Cleanup:**
```bash
docker stop lz-ui-test
docker rm lz-ui-test
```

---

## Docker Compose Deployment

### Step 1: Validate docker-compose.yml

```bash
docker-compose -f docker/docker-compose.yml config
```

**Expected:** Valid YAML with no errors

### Step 2: Build with Docker Compose

```bash
docker-compose -f docker/docker-compose.yml build
```

### Step 3: Start Services

```bash
# Start in detached mode
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

### Step 4: Health Check

```bash
# Check container status
docker-compose -f docker/docker-compose.yml ps

# Expected: Container status should be "healthy"
```

### Step 5: Run Tests Inside Running Container

```bash
# Execute test inside container
docker-compose -f docker/docker-compose.yml exec lz-optimizer \
  python3 test_updated_tools.py
```

### Step 6: Cleanup

```bash
docker-compose -f docker/docker-compose.yml down
```

---

## Validation Checklist

### Build Validation
- [ ] Docker image builds successfully
- [ ] Image size is reasonable (~600-800MB)
- [ ] No build warnings or errors
- [ ] All dependencies installed correctly

### Tool Validation
- [ ] `huawei_tools.py` present and updated
- [ ] `rollback_manager.py` present
- [ ] Original tools backed up as `huawei_tools_original.py`
- [ ] 6 Huawei tools import successfully
- [ ] 4 Rollback tools import successfully
- [ ] `modify_huawei_parameter_site` tool available

### API Connectivity
- [ ] Container can authenticate with Huawei API
- [ ] Query operations work with site_name parameter
- [ ] Retrieved live data from Bindura Hospital
- [ ] Batch modification tool generates correct commands
- [ ] Dry-run mode prevents actual modifications

### Database Validation
- [ ] Database file accessible from container
- [ ] SQLite connection works
- [ ] Sites table readable
- [ ] KPI data accessible

### UI Validation
- [ ] Streamlit starts successfully
- [ ] UI accessible on port 8501
- [ ] All pages load without errors
- [ ] Database integration working
- [ ] API status shows connected (if API available)

### Docker Compose Validation
- [ ] docker-compose.yml syntax valid
- [ ] Service builds successfully
- [ ] Container starts and becomes healthy
- [ ] Volumes mount correctly
- [ ] Environment variables loaded from .env
- [ ] Logs show no errors

---

## Troubleshooting

### Issue: Build fails with dependency errors

**Solution:**
```bash
# Clean Docker cache and rebuild
docker system prune -f
docker build --no-cache -f docker/Dockerfile -t lz-network-optimizer:phase5 .
```

### Issue: API connectivity fails in container

**Check:**
1. `.env` file has correct credentials
2. Container has network access to Huawei API
3. SSL verification disabled in config

**Test:**
```bash
docker run --rm --env-file .env lz-network-optimizer:phase5 \
  python3 -c "import os; print(f'API URL: {os.getenv(\"HUAWEI_API_URL\")}')"
```

### Issue: Database not accessible

**Check volume mounts:**
```bash
docker run --rm -v "$(pwd)/data:/app/data" lz-network-optimizer:phase5 \
  ls -la /app/data/
```

### Issue: UI doesn't start

**Check logs:**
```bash
docker logs lz-ui-test
```

**Common causes:**
- Port 8501 already in use
- Database not mounted
- Missing environment variables

### Issue: Permission errors

**Fix permissions:**
```bash
# Ensure data directory is accessible
chmod -R 755 data/
```

---

## Performance Benchmarks

### Expected Build Times
- First build: 5-10 minutes (downloading dependencies)
- Subsequent builds: 1-2 minutes (using cache)

### Expected Container Startup
- Container start: < 5 seconds
- UI ready: < 15 seconds
- Database connection: < 1 second

### Resource Usage
- Memory: 1-2GB (normal operation)
- CPU: 1-2 cores (during optimization)
- Disk: ~1GB (image + data)

---

## Next Steps After Successful Deployment

1. **Stage 5.3: End-to-End Workflow - Generation Mode**
   - Test optimization recommendation generation
   - Validate agent communication
   - Verify workflow state management

2. **Stage 5.4: End-to-End Workflow - Execution Mode**
   - Test parameter modification (dry-run first!)
   - Validate rollback functionality
   - Confirm KPI improvement tracking

3. **Stage 5.5: UAT Preparation**
   - Document all features
   - Create user guide
   - Prepare demo scenarios

---

## Quick Reference Commands

```bash
# Build
docker build -f docker/Dockerfile -t lz-network-optimizer:phase5 .

# Run with UI
docker run -d --name lz-ui --env-file .env \
  -v "$(pwd)/data:/app/data" -p 8501:8501 \
  lz-network-optimizer:phase5 streamlit run ui/app.py --server.headless=true

# Run tests
docker run --rm --env-file .env -v "$(pwd)/data:/app/data" \
  lz-network-optimizer:phase5 python3 test_updated_tools.py

# View logs
docker logs -f lz-ui

# Stop and remove
docker stop lz-ui && docker rm lz-ui

# Docker Compose
docker-compose -f docker/docker-compose.yml up -d
docker-compose -f docker/docker-compose.yml logs -f
docker-compose -f docker/docker-compose.yml down
```

---

## Manual Testing Results Template

Copy this to record your test results:

```
## Stage 5.2 - Docker Deployment Test Results

**Date:** [Date]
**Tester:** [Name]

### Build Validation
- [ ] Image built successfully
- Image size: [Size]
- Build time: [Time]

### Tool Imports
- [ ] 6 Huawei tools loaded
- [ ] 4 Rollback tools loaded
- [ ] modify_huawei_parameter_site present

### API Connectivity
- [ ] Authentication successful
- [ ] Query test passed
- Retrieved value from Bindura: [Value]

### Database
- [ ] Database accessible
- Sites count: [Count]

### UI
- [ ] UI started successfully
- [ ] All pages accessible
- [ ] No errors in logs

### Issues Encountered
[Describe any issues and resolutions]

### Overall Status
[ ] PASS - All tests successful
[ ] PARTIAL - Some tests failed (specify above)
[ ] FAIL - Critical issues blocking deployment
```

---

**Document Prepared By:** Claude (Sonnet 4.5)
**Status:** Ready for Manual Execution
**Next:** Execute commands in your terminal and report results
