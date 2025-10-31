# Testing Guide - Liquid Zimbabwe 4G Network Optimizer

## Prerequisites

### 1. Get NVIDIA API Key

1. Go to https://build.nvidia.com/
2. Sign in or create an account
3. Navigate to "API Catalog"
4. Generate an API key for "Llama 3.1 70B Instruct"
5. Copy your API key

### 2. Set Environment Variable

**On macOS/Linux:**
```bash
export NVIDIA_API_KEY='nvapi-your-key-here'
```

**On Windows (Command Prompt):**
```cmd
set NVIDIA_API_KEY=nvapi-your-key-here
```

**On Windows (PowerShell):**
```powershell
$env:NVIDIA_API_KEY='nvapi-your-key-here'
```

### 3. Verify API Key

```bash
echo $NVIDIA_API_KEY
```

You should see your API key printed.

---

## Running Tests

### Quick API Test (Recommended First)

This test verifies your NVIDIA API key works and tests a single agent:

```bash
cd lz-network-optimizer
python3 test_with_api.py
```

**Expected Output:**
- ✓ NVIDIA API key found
- ✓ All agents imported successfully
- ✓ NVIDIA LLM initialized
- ✓ LLM Response: "Hello from NVIDIA API"
- ✓ Agent executed with tools

---

### Full Integration Test

Once the quick test passes, run the complete integration test:

```bash
python3 test_workflow.py
```

**Expected Results:**
- ✓ PASS: DATABASE (4 sites, 168 records)
- ✓ PASS: TOOLS (10 tools working)
- ✓ PASS: PROMPTS (system + few-shot + context)
- ✓ PASS: WORKFLOW (6-agent orchestration)

**Note:** The workflow test will execute all 6 agents in sequence:
1. Network Connector (queries data)
2. Monitoring (checks KPIs)
3. KPI Analytics (analyzes issues)
4. Configuration (recommends changes)
5. Validation (assesses safety)
6. MML Executor (executes changes in dry-run mode)

---

### Run Live Optimization

After tests pass, you can run a real optimization:

```bash
# List available sites
python3 main.py --list-sites

# Run optimization for a specific site
python3 main.py --site "MSH0013-Bindura-Zaoga" --query "Optimize download speed"

# Run in offline mode (historical data only)
python3 main.py --site "MSH0013-Bindura-Zaoga" --offline

# Enable verbose logging
python3 main.py --site "MSH0013-Bindura-Zaoga" --verbose
```

---

## Troubleshooting

### Issue: "NVIDIA_API_KEY not set"
**Solution:**
- Set the environment variable as shown above
- Verify with `echo $NVIDIA_API_KEY`

### Issue: "Module not found" errors
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "Database not found"
**Solution:**
```bash
cd lz-network-optimizer
python3 scripts/import_historical_data.py
```

### Issue: "API connection failed"
**Solution:**
- Check internet connection
- Verify API key is valid at https://build.nvidia.com/
- Try the offline mode: `--offline`

### Issue: Agent execution is slow
**Expected Behavior:**
- Each agent may take 10-30 seconds with the LLM
- Full workflow: 2-5 minutes total
- This is normal for LLM-based reasoning

---

## Test Coverage

### What Gets Tested

1. **Database Layer**
   - SQLite connectivity
   - 168 historical KPI records
   - 4 test sites available

2. **Tool Layer (10 tools)**
   - Huawei API tools (5)
   - SQL database tools (2)
   - Calculation tools (2)
   - Validation tools (2)

3. **Prompt Layer**
   - System prompts for 6 agents
   - 5 few-shot examples
   - Context builders

4. **Agent Layer (6 agents)**
   - Network Connector
   - Monitoring
   - KPI Analytics
   - Configuration
   - Validation
   - MML Executor

5. **Workflow Orchestration**
   - LangGraph state management
   - Conditional routing
   - Memory persistence

---

## Expected Test Duration

- **Quick API Test**: 30-60 seconds
- **Full Integration Test**: 3-5 minutes
- **Live Optimization**: 5-10 minutes

---

## Success Criteria

All tests should show:
- ✓ PASS: DATABASE
- ✓ PASS: TOOLS
- ✓ PASS: PROMPTS
- ✓ PASS: WORKFLOW

If any test fails, check the error message and refer to Troubleshooting section.

---

## Next Steps After Testing

Once all tests pass:

1. **Phase 2.5**: Docker containerization (1 day)
2. **Checkpoint #2**: Demo to stakeholders
3. **Phase 3**: UI development with Streamlit
4. **Production**: Deploy to Liquid Zimbabwe network

---

## Support

For issues or questions:
1. Check error messages in test output
2. Review troubleshooting section above
3. Check logs in `logs/` directory (if enabled)
4. Refer to main README.md for architecture details
