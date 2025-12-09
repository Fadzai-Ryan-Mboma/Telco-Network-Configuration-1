# API Troubleshooting Guide

**Project:** Liquid Zimbabwe 4G Network Optimizer
**Date:** 2025-10-31
**Version:** 1.0

---

## Overview

This guide provides step-by-step troubleshooting procedures for API connectivity issues in the Liquid Zimbabwe 4G Network Optimizer. The system integrates with two external APIs:

1. **NVIDIA AI Endpoints** - LLM for agent reasoning
2. **Huawei iMaster MAE API** - Network equipment management

---

## Quick Diagnostics

### Run Pre-flight Check

```bash
cd lz-network-optimizer
python3 test_preflight.py
```

This checks:
- ✅ Streamlit UI running
- ✅ NVIDIA API key configured
- ✅ Database populated
- ✅ Python dependencies installed
- ✅ Docker available

---

### Run Comprehensive API Test

```bash
cd lz-network-optimizer
python3 test_api_comprehensive.py
```

This checks:
- ✅ NVIDIA API connectivity (4 tests)
- ✅ Huawei API connectivity (4 tests)
- ✅ System integration (2 tests)

---

## NVIDIA API Troubleshooting

### Issue 1: NVIDIA API Key Not Set

**Symptoms:**
```
⚠️ NVIDIA API KEY NOT SET
KeyError: 'NVIDIA_API_KEY'
```

**Diagnosis:**
```bash
echo $NVIDIA_API_KEY
# If empty, API key not configured
```

**Solution:**

**Step 1: Get API Key**
1. Visit: https://build.nvidia.com/
2. Sign up/login
3. Navigate to API Keys section
4. Generate new API key
5. Copy key (starts with "nvapi-...")

**Step 2: Set Environment Variable**

**Option A: Temporary (current terminal session)**
```bash
# macOS/Linux
export NVIDIA_API_KEY='nvapi-YOUR_KEY_HERE'

# Windows
set NVIDIA_API_KEY=nvapi-YOUR_KEY_HERE
```

**Option B: Persistent (.env file)**
```bash
cd lz-network-optimizer

# Create .env from template
cp .env.template .env

# Edit .env file
nano .env

# Add your key:
NVIDIA_API_KEY="nvapi-YOUR_KEY_HERE"
```

**Step 3: Verify**
```bash
python3 test_with_api.py
```

**Expected Output:**
```
✓ NVIDIA API key found (70 characters)
✅ API TEST SUCCESSFUL!
```

---

### Issue 2: NVIDIA API Connection Timeout

**Symptoms:**
```
TimeoutError: Request timed out after 30 seconds
ConnectionError: Failed to connect to NVIDIA API
```

**Diagnosis:**
```bash
# Test internet connectivity
ping integrate.api.nvidia.com

# Test HTTPS access
curl -I https://integrate.api.nvidia.com/v1
```

**Solutions:**

**Solution A: Check Internet Connection**
1. Verify internet access works
2. Try accessing https://build.nvidia.com/ in browser
3. Check firewall rules allow HTTPS (port 443)

**Solution B: Check Proxy Settings**
```bash
# If behind corporate proxy, set:
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1
```

**Solution C: Increase Timeout**
Edit agent configuration to increase timeout:
```python
# In agents/*.py files
llm = ChatNVIDIA(
    model="meta/llama-3.1-70b-instruct",
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=0.7,
    max_tokens=1024,
    timeout=60  # Increase from 30 to 60 seconds
)
```

---

### Issue 3: NVIDIA API Rate Limit Exceeded

**Symptoms:**
```
RateLimitError: Rate limit exceeded. Please try again later.
HTTP 429: Too Many Requests
```

**Diagnosis:**
- Check API usage dashboard: https://build.nvidia.com/
- Verify account tier and rate limits

**Solutions:**

**Solution A: Wait and Retry**
```python
# Implement exponential backoff
import time
for attempt in range(3):
    try:
        response = llm.invoke(prompt)
        break
    except RateLimitError:
        wait_time = 2 ** attempt  # 1s, 2s, 4s
        time.sleep(wait_time)
```

**Solution B: Upgrade Account**
- Free tier: Limited requests/minute
- Paid tier: Higher rate limits
- Visit: https://build.nvidia.com/pricing

**Solution C: Enable Offline Mode**
For testing without API:
```bash
# Set in .env
OFFLINE_MODE=true
```

This uses mock responses for development.

---

### Issue 4: NVIDIA Model Not Available

**Symptoms:**
```
ModelNotFoundError: Model 'meta/llama-3.1-70b-instruct' not available
```

**Diagnosis:**
```bash
# Check available models
curl -H "Authorization: Bearer $NVIDIA_API_KEY" \
  https://integrate.api.nvidia.com/v1/models
```

**Solution:**
Update to available model in agent configurations:
```python
# Alternative models:
llm = ChatNVIDIA(
    model="meta/llama3-70b-instruct",  # Try different version
    # or
    model="mistralai/mixtral-8x7b-instruct-v0.1",
    # or
    model="google/gemma-7b",
    ...
)
```

Check NVIDIA catalog: https://build.nvidia.com/explore/discover

---

## Huawei API Troubleshooting

### Issue 1: Huawei API Credentials Not Set

**Symptoms:**
```
ERROR: HUAWEI_API_URL not configured
KeyError: 'HUAWEI_USERNAME'
```

**Diagnosis:**
```bash
echo $HUAWEI_API_URL
echo $HUAWEI_USERNAME
echo $HUAWEI_PASSWORD
# If empty, credentials not configured
```

**Solution:**

**Step 1: Get Credentials**
Contact Huawei iMaster MAE administrator for:
- API endpoint URL (e.g., https://41.174.191.214:31127)
- Username (e.g., cassava.ai)
- Password

**Step 2: Configure .env**
```bash
cd lz-network-optimizer
nano .env

# Add credentials:
HUAWEI_API_URL="https://41.174.191.214:31127"
HUAWEI_USERNAME="cassava.ai"
HUAWEI_PASSWORD="#Pass123#"
```

**Step 3: Verify**
```bash
python3 test_api_comprehensive.py
```

Look for:
```
Test 2.1: Huawei API Configuration
✅ PASSED: All Huawei API credentials configured
```

---

### Issue 2: Huawei API Connection Refused

**Symptoms:**
```
ConnectionRefusedError: [Errno 61] Connection refused
TCP Connection: FAILED (port 31127)
```

**Diagnosis:**
```bash
# Test TCP connectivity
nc -zv 41.174.191.214 31127

# Test HTTPS access
curl -k https://41.174.191.214:31127
```

**Solutions:**

**Solution A: Check Network Connectivity**
```bash
# Ping server
ping 41.174.191.214

# Check DNS resolution
nslookup 41.174.191.214

# Traceroute
traceroute 41.174.191.214
```

**Solution B: Check VPN Connection**
Huawei iMaster MAE may require VPN access:
1. Connect to corporate VPN
2. Verify VPN connection active
3. Retry connection test

**Solution C: Check Firewall Rules**
```bash
# Verify port 31127 not blocked
telnet 41.174.191.214 31127

# If "Connection refused", check:
# - Server firewall allows your IP
# - Corporate firewall allows port 31127
# - API server is running
```

**Solution D: Contact Network Admin**
- Verify API server is running
- Check your IP is whitelisted
- Confirm port 31127 is open

---

### Issue 3: Huawei API SSL Certificate Error

**Symptoms:**
```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
SSL verification failed (self-signed certificate)
```

**Diagnosis:**
```bash
# Check SSL certificate
openssl s_client -connect 41.174.191.214:31127 -showcerts

# Look for "self signed certificate"
```

**Solution:**

This is **expected behavior**. Huawei iMaster MAE uses self-signed certificates.

**Current Configuration (Correct):**
```python
config = {
    'base_url': os.getenv('HUAWEI_API_URL'),
    'username': os.getenv('HUAWEI_USERNAME'),
    'password': os.getenv('HUAWEI_PASSWORD'),
    'timeout': 30,
    'retry_attempts': 2,
    'retry_delay': 3,
    'ssl_verify': False  # ✅ Disable SSL verification for self-signed cert
}
client = HuaweiAPIClient(config)
```

**Do NOT change** `ssl_verify` to `True` unless valid CA-signed certificate installed.

---

### Issue 4: Huawei API Authentication Failed (404)

**Symptoms:**
```
HTTP 404: Not Found
Auth endpoint: /rest-oss/rest/plat/smapp/v1/login returns 404
⚠️ Fallback to DB
```

**Diagnosis:**
```bash
# Test auth endpoint
curl -k -X POST https://41.174.191.214:31127/rest-oss/rest/plat/smapp/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"cassava.ai","password":"#Pass123#"}'

# If 404, endpoint may have changed
```

**Current Status:**
This is a **known issue**. TCP connection succeeds but auth endpoint returns 404.

**Possible Causes:**
1. Internal/development API with different endpoint structure
2. API version mismatch (v1 vs v2)
3. Demo environment with limited endpoints
4. Endpoint path changed in newer version

**Workaround:**
System **correctly falls back to database**. No action required for testing/demo.

**Long-term Solution:**

**Step 1: Contact Huawei Support**
- Request correct auth endpoint for your API version
- Verify API documentation matches implementation
- Confirm credentials format

**Step 2: Try Alternative Endpoints**
```bash
# Try different auth paths:
curl -k -X POST https://41.174.191.214:31127/api/v1/login ...
curl -k -X POST https://41.174.191.214:31127/rest/login ...
curl -k -X POST https://41.174.191.214:31127/auth/login ...
```

**Step 3: Update HuaweiAPIClient**
Once correct endpoint found, update:
```python
# network/huawei_api_client.py
def authenticate(self):
    url = f"{self.base_url}/CORRECT_ENDPOINT_HERE"
    ...
```

**Step 4: Test**
```bash
python3 test_api_comprehensive.py
```

---

### Issue 5: HuaweiAPIClient Initialization Error

**Symptoms:**
```
TypeError: HuaweiAPIClient.__init__() got an unexpected keyword argument 'base_url'
```

**Diagnosis:**
Check how HuaweiAPIClient is being called:
```bash
grep -n "HuaweiAPIClient(" tools/*.py network/*.py
```

**Solution:**

**WRONG (causes error):**
```python
client = HuaweiAPIClient(
    base_url=os.getenv('HUAWEI_API_URL'),
    username=os.getenv('HUAWEI_USERNAME'),
    password=os.getenv('HUAWEI_PASSWORD')
)
```

**CORRECT (config dict pattern):**
```python
config = {
    'base_url': os.getenv('HUAWEI_API_URL'),
    'username': os.getenv('HUAWEI_USERNAME'),
    'password': os.getenv('HUAWEI_PASSWORD'),
    'timeout': 30,
    'retry_attempts': 2,
    'retry_delay': 3,
    'ssl_verify': False
}
client = HuaweiAPIClient(config)
```

**Files to Check:**
1. tools/huawei_tools.py (4 functions)
2. network/kpi_collector.py (1 function)

**Status:** ✅ Fixed in Phase 4

---

## Database Troubleshooting

### Issue 1: Database Not Found

**Symptoms:**
```
ERROR: Database not found at data/lz_network.db
sqlite3.OperationalError: unable to open database file
```

**Diagnosis:**
```bash
cd lz-network-optimizer
ls -la data/lz_network.db
```

**Solution:**

**If file missing:**
```bash
# Check if database exists elsewhere
find . -name "lz_network.db" -type f

# If found in different location, update .env:
nano .env
DATABASE_PATH=path/to/lz_network.db
```

**If file doesn't exist:**
```bash
# Database needs to be created and populated
# Contact project admin for database backup
# Or run data import script (if available):
python3 data/csv_to_db_importer.py
```

---

### Issue 2: Database Schema Mismatch

**Symptoms:**
```
ERROR: no such table: parameter_history
ERROR: no such column: action_type
```

**Diagnosis:**
```bash
# Check database schema
sqlite3 data/lz_network.db ".schema"

# List tables
sqlite3 data/lz_network.db ".tables"
```

**Solution:**

**Expected Tables:**
- `kpi_data` - Historical KPI records
- `parameter_changes` - Parameter modification history
- `optimization_history` - Optimization activity log
- `thresholds` - KPI threshold values

**If tables missing:**
```bash
# Database may need migration/update
# Check for migration scripts:
ls -la migrations/

# Or restore from backup
cp backups/lz_network.db.backup data/lz_network.db
```

**Status:** ✅ Fixed in Phase 4 (database_helper.py updated to match actual schema)

---

### Issue 3: No Data in Database

**Symptoms:**
```
WARNING: Database has 0 records
No historical data available for this KPI
```

**Diagnosis:**
```bash
sqlite3 data/lz_network.db "SELECT COUNT(*) FROM kpi_data;"
```

**Solution:**

**If 0 records:**
```bash
# Import historical data
python3 data/csv_to_db_importer.py

# Or run KPI collector
python3 network/kpi_collector.py
```

**Expected Data:**
- 168 records (4 sites × 6 cells × 7 days)
- Date range: 2025-09-01 to 2025-09-07 (test data)

---

## System Integration Issues

### Issue 1: Python Dependencies Missing

**Symptoms:**
```
ModuleNotFoundError: No module named 'streamlit'
ImportError: cannot import name 'ChatNVIDIA'
```

**Diagnosis:**
```bash
pip list | grep streamlit
pip list | grep langchain
```

**Solution:**
```bash
cd lz-network-optimizer
pip install -r requirements.txt

# Verify installation
python3 -c "import streamlit; print(streamlit.__version__)"
python3 -c "from langchain_nvidia_ai_endpoints import ChatNVIDIA; print('OK')"
```

---

### Issue 2: Streamlit UI Not Running

**Symptoms:**
```
ERROR: Port 8501 is already in use
streamlit: command not found
```

**Diagnosis:**
```bash
# Check if Streamlit running
lsof -ti:8501

# Check if streamlit installed
which streamlit
```

**Solution:**

**If port in use:**
```bash
# Kill existing process
kill $(lsof -ti:8501)

# Or use different port
streamlit run ui/app.py --server.port 8502
```

**If streamlit not found:**
```bash
pip install streamlit
# Or
pip install -r requirements.txt
```

---

### Issue 3: Docker Not Accessible

**Symptoms:**
```
docker: command not found
Cannot connect to Docker daemon
```

**Diagnosis:**
```bash
# Check Docker installed
which docker

# Check Docker running
docker info
```

**Solution:**

**If not installed:**
1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
2. Install and start Docker Desktop
3. Verify: `docker --version`

**If installed but not in PATH:**
```bash
# Add to PATH (macOS)
export PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin"

# Or use full path
/Applications/Docker.app/Contents/Resources/bin/docker --version
```

**If Docker Desktop not running:**
1. Open Docker Desktop application
2. Wait for "Docker Desktop is running" message
3. Verify: `docker info`

---

## UI Status Indicators

### Understanding Status Messages

**NVIDIA API Status:**
- `✅ Connected` - API key valid, LLM responding
- `⚠️ Offline Mode` - OFFLINE_MODE=true in .env
- `❌ Not Configured` - NVIDIA_API_KEY not set
- `❌ Connection Failed` - Network or timeout error

**Huawei API Status:**
- `✅ Connected` - TCP connection successful
- `⚠️ Fallback to DB` - TCP works but auth fails (expected)
- `❌ Not Configured` - Credentials not set
- `❌ Connection Failed` - Network unreachable

**Database Status:**
- `✅ Active (168 records)` - Database accessible with data
- `⚠️ Empty (0 records)` - Database exists but no data
- `❌ Not Found` - Database file missing

---

## Common Error Messages

### Error: "KeyError: 'cell_count'"

**Solution:** Restart Streamlit UI to reload cached code:
```bash
kill $(lsof -ti:8501)
streamlit run ui/app.py
```

---

### Error: "No historical data available"

**Solution:** Select longer time range (60 or 90 days) to see Sept 1-7 test data:
```
Historical Trends tab → Time Range → "Last 60 Days"
```

---

### Error: "Activity log is empty"

**Solution:** This is expected. Run optimization workflow to populate:
```
1. Select site
2. Enter query (e.g., "Optimize download speed")
3. Click "🚀 Run Optimization"
4. Check Activity Log tab after completion
```

---

## Testing Commands Reference

### Quick Test Commands

```bash
# Pre-flight checks (5 tests)
python3 test_preflight.py

# Comprehensive API tests (10 tests)
python3 test_api_comprehensive.py

# Simple API test
python3 test_with_api.py

# Database query test
sqlite3 data/lz_network.db "SELECT COUNT(*) FROM kpi_data;"

# Check Streamlit running
lsof -ti:8501

# Check Docker
docker --version && docker info
```

---

### Manual API Tests

**NVIDIA API:**
```bash
# Test API key
curl -H "Authorization: Bearer $NVIDIA_API_KEY" \
  https://integrate.api.nvidia.com/v1/models

# Expected: List of available models (JSON response)
```

**Huawei API:**
```bash
# Test TCP connection
nc -zv 41.174.191.214 31127

# Test SSL handshake
openssl s_client -connect 41.174.191.214:31127

# Test auth endpoint
curl -k -X POST https://41.174.191.214:31127/rest-oss/rest/plat/smapp/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"cassava.ai","password":"#Pass123#"}'
```

---

## Escalation Paths

### NVIDIA API Issues
- **Documentation:** https://docs.nvidia.com/ai-endpoints/
- **Support:** https://build.nvidia.com/support
- **Community:** https://forums.developer.nvidia.com/

### Huawei API Issues
- **Contact:** Huawei iMaster MAE administrator
- **Documentation:** Request API docs from Huawei support
- **Support:** Contact Liquid Zimbabwe network operations team

### System Issues
- **Project Lead:** Fadzai (user)
- **Documentation:** See `documentation/` folder
- **Logs:** Check `lz-network-optimizer/logs/` (if configured)

---

## Appendix: Environment Variables Reference

### Required Variables

```bash
# NVIDIA AI API
NVIDIA_API_KEY="nvapi-..."               # Get from https://build.nvidia.com/

# Huawei iMaster MAE API
HUAWEI_API_URL="https://..."             # Get from network admin
HUAWEI_USERNAME="username"               # Get from network admin
HUAWEI_PASSWORD="password"               # Get from network admin
```

### Optional Variables

```bash
# Database
DATABASE_PATH="data/lz_network.db"       # Override default path

# Logging
LOG_LEVEL="INFO"                         # DEBUG|INFO|WARNING|ERROR|CRITICAL

# System Modes
OFFLINE_MODE="false"                     # true = no API calls, use mock data
DEBUG_MODE="false"                       # true = verbose logging
TEST_MODE="false"                        # true = use test data

# UI
UI_PORT="8501"                           # Streamlit port
```

---

## Appendix: API Configuration Examples

### Correct HuaweiAPIClient Usage

```python
import os
from network.huawei_api_client import HuaweiAPIClient

# ✅ CORRECT: Config dict pattern
config = {
    'base_url': os.getenv('HUAWEI_API_URL'),
    'username': os.getenv('HUAWEI_USERNAME'),
    'password': os.getenv('HUAWEI_PASSWORD'),
    'timeout': 30,
    'retry_attempts': 2,
    'retry_delay': 3,
    'ssl_verify': False
}
client = HuaweiAPIClient(config)

# ❌ WRONG: Keyword arguments
client = HuaweiAPIClient(
    base_url=os.getenv('HUAWEI_API_URL'),
    username=os.getenv('HUAWEI_USERNAME'),
    password=os.getenv('HUAWEI_PASSWORD')
)  # TypeError!
```

### Correct ChatNVIDIA Usage

```python
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import os

# ✅ CORRECT
llm = ChatNVIDIA(
    model="meta/llama-3.1-70b-instruct",
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=0.7,
    max_tokens=1024,
    timeout=30
)

response = llm.invoke("Your prompt here")
print(response.content)
```

---

**Guide Version:** 1.0
**Last Updated:** 2025-10-31
**Maintained By:** Liquid Zimbabwe 4G Network Optimizer Team
