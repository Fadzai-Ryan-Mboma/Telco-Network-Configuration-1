# Terminal Logging Guide - Liquid Zimbabwe 4G Network Optimizer

**Purpose:** See complete agentic workflow, prompts, and API interactions in your terminal
**Created:** 2025-11-03

---

## Quick Start

### Option 1: Run with Enhanced Logging Script (Recommended)

```bash
cd lz-network-optimizer

# Verbose mode (recommended) - Full workflow visibility
./run_with_logging.sh verbose

# Basic mode - Minimal output
./run_with_logging.sh basic

# Debug mode - Maximum verbosity
./run_with_logging.sh debug
```

### Option 2: Run Manually with Environment Variable

```bash
cd lz-network-optimizer

# Set logging mode
export LZ_LOG_MODE=verbose

# Run Streamlit
python3 -m streamlit run ui/app.py --server.headless=true
```

---

## Logging Modes

### 1. BASIC Mode (Quiet)

**Best for:** Production use, minimal terminal noise

**Shows:**
- Application startup/shutdown
- Error messages
- Critical events only

**Example Output:**
```
14:23:15 - INFO - Optimization workflow started
14:23:18 - INFO - Connected to Huawei API
14:23:22 - INFO - Optimization completed successfully
```

**Command:**
```bash
./run_with_logging.sh basic
```

---

### 2. VERBOSE Mode (Recommended)

**Best for:** Development, testing, understanding workflow

**Shows:**
- 🤖 **Agent execution** - Which agent is running
- 🔧 **Tool calls** - What tools are being invoked
- 🌐 **API requests** - Calls to Huawei iMaster MAE
- 📝 **LLM prompts** - Full prompts sent to NVIDIA AI
- 💬 **LLM responses** - Complete AI responses
- ⚖️ **Workflow decisions** - Routing and validation decisions
- 📊 **State transitions** - Workflow state changes
- ✅ **Results** - Optimization recommendations

**Example Output:**
```
================================================================================
🚀 OPTIMIZATION WORKFLOW STARTED
  📍 Site: MSH-0112-Bindura Hospital
  📡 Cell ID: 1
  💬 Query: Optimize network performance
================================================================================

────────────────────────────────────────────────────────────────────────────────
🤖 AGENT 1: NETWORK CONNECTOR AGENT
────────────────────────────────────────────────────────────────────────────────
14:23:18 - LZ-Agent              - INFO     - Connecting to Huawei iMaster MAE API

🔧 TOOL CALL: connect_to_huawei_api
   base_url: https://41.174.191.214:31127
   timeout: 30

🌐 API REQUEST: PUT /api/rest/securityManagement/v1/oauth/token
   username: cassava.ai

✓ API RESPONSE: 200 (0.225s)

✓ TOOL RESULT: connect_to_huawei_api
   Successfully authenticated. Token expires in 30 minutes.

✅ Network Connector Agent completed
   Summary: Successfully connected to Huawei API and authenticated

────────────────────────────────────────────────────────────────────────────────
🤖 AGENT 2: MONITORING AGENT
────────────────────────────────────────────────────────────────────────────────

🔧 TOOL CALL: query_huawei_parameter
   parameter_name: reference_signal_power_pdschcfg
   site_name: MSH-0112-Bindura Hospital
   cell_id: 1

🌐 API REQUEST: POST /api/rest/mmlManagement/v1/command
   neNames: ["MSH-0112-Bindura Hospital"]
   command: LST PDSCHCFG: LOCALCELLID=1;

✓ API RESPONSE: 200 (0.547s)

✓ TOOL RESULT: query_huawei_parameter
   Current value: 152 (15.2 dBm)

┌──────────────────────────────────────────────────────────────────────────────┐
│ 📝 LLM PROMPT (Monitoring Agent)                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│ You are a network monitoring expert for Liquid Zimbabwe's 4G LTE network.   │
│                                                                              │
│ Current KPI Values:                                                          │
│ - Network Access Success: 92.5%                                              │
│ - Download Speed: 45.2 Mbps                                                  │
│ - Upload Speed: 18.3 Mbps                                                    │
│                                                                              │
│ Thresholds:                                                                  │
│ - Network Access Success: 95% (minimum)                                      │
│ - Download Speed: 50 Mbps (minimum)                                          │
│                                                                              │
│ Analyze the KPIs and determine if optimization is needed.                    │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ 💬 LLM RESPONSE (Monitoring Agent)                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│ Based on the KPI analysis:                                                   │
│                                                                              │
│ 1. Network Access Success (92.5%) is BELOW threshold (95%)                  │
│    - Impact: Users experiencing connection failures                          │
│    - Priority: HIGH                                                          │
│                                                                              │
│ 2. Download Speed (45.2 Mbps) is BELOW threshold (50 Mbps)                  │
│    - Impact: Reduced data throughput                                         │
│    - Priority: MEDIUM                                                        │
│                                                                              │
│ RECOMMENDATION: Optimization needed                                          │
│ PRIMARY ISSUE: Poor network access success rate                              │
│ SUGGESTED ACTIONS:                                                           │
│ - Increase reference signal power to improve coverage                        │
│ - Adjust handover parameters to reduce call drops                            │
└──────────────────────────────────────────────────────────────────────────────┘

⚖️  DECISION: Needs Optimization?
   Decision: YES
   Reason: Network Access Success below threshold (92.5% < 95%)

📊 STATE TRANSITION: monitoring → kpi_analytics
   Reason: Optimization required

────────────────────────────────────────────────────────────────────────────────
🤖 AGENT 3: KPI ANALYTICS AGENT
────────────────────────────────────────────────────────────────────────────────
[... continues with remaining agents ...]

================================================================================
✅ WORKFLOW COMPLETED SUCCESSFULLY
  Summary: Generated 3 optimization recommendations for MSH-0112-Bindura Hospital
================================================================================
```

**Command:**
```bash
./run_with_logging.sh verbose
```

---

### 3. DEBUG Mode (Maximum Verbosity)

**Best for:** Troubleshooting issues, deep debugging

**Shows:**
- Everything from VERBOSE mode
- Internal library logs (urllib3, httpx, LangChain)
- Detailed stack traces
- Raw API request/response bodies
- Database queries
- Cache hits/misses

**Example Output:**
```
[Same as verbose, plus:]

DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): 41.174.191.214:31127
DEBUG:urllib3.connectionpool:https://41.174.191.214:31127 "PUT /api/rest/securityManagement/v1/oauth/token HTTP/1.1" 200 256
DEBUG:httpx:load_ssl_context verify=False cert=None trust_env=True http2=False
DEBUG:LZ-Database:Executing query: SELECT * FROM kpi_data WHERE site_name = ? AND timestamp = ?
DEBUG:LZ-Database:Query returned 6 rows in 0.003s
```

**Command:**
```bash
./run_with_logging.sh debug
```

---

## What You'll See in the Terminal

### 1. Agent Workflow Execution

Each agent's execution is clearly marked:

```
────────────────────────────────────────────────────────────────────────────────
🤖 AGENT 1: NETWORK CONNECTOR AGENT
────────────────────────────────────────────────────────────────────────────────
```

### 2. Tool Invocations

Every tool call shows parameters and results:

```
🔧 TOOL CALL: query_huawei_parameter
   parameter_name: reference_signal_power_pdschcfg
   site_name: MSH-0112-Bindura Hospital

✓ TOOL RESULT: query_huawei_parameter
   Current value: 152 (15.2 dBm)
```

### 3. API Requests

All Huawei API interactions are logged:

```
🌐 API REQUEST: POST /api/rest/mmlManagement/v1/command
   neNames: ["MSH-0112-Bindura Hospital"]
   command: LST PDSCHCFG: LOCALCELLID=1;

✓ API RESPONSE: 200 (0.547s)
```

### 4. LLM Prompts and Responses

See exactly what prompts are sent to NVIDIA AI and what it responds with:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 📝 LLM PROMPT (Monitoring Agent)                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│ You are a network monitoring expert...                                       │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ 💬 LLM RESPONSE (Monitoring Agent)                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│ Based on the analysis...                                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 5. Workflow Decisions

Critical routing decisions are highlighted:

```
⚖️  DECISION: Needs Optimization?
   Decision: YES
   Reason: Network Access Success below threshold (92.5% < 95%)
```

### 6. State Transitions

Track how the workflow moves between agents:

```
📊 STATE TRANSITION: monitoring → kpi_analytics
   Reason: Optimization required
```

---

## Configuration

### Enable/Disable Specific Logging Features

Edit [config/config.yaml](../config/config.yaml):

```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR

  # Agent-specific logging
  agent_logs:
    enabled: true
    log_state_transitions: true    # Show workflow routing
    log_tool_calls: true            # Show tool invocations
    log_llm_prompts: true           # Show prompts to AI
    log_llm_responses: true         # Show AI responses
```

**To disable LLM prompt/response logging:**
```yaml
    log_llm_prompts: false
    log_llm_responses: false
```

---

## Log Files

All terminal output is also saved to timestamped log files:

```bash
logs/
├── lz_optimizer_20251103_142315.log
├── lz_optimizer_20251103_151822.log
└── lz_optimizer_20251103_163544.log
```

**View a log file:**
```bash
cat logs/lz_optimizer_20251103_142315.log

# Or tail it in real-time
tail -f logs/lz_optimizer_20251103_142315.log
```

**Find recent logs:**
```bash
ls -lt logs/ | head -5
```

---

## Color-Coded Output

Terminal output uses colors to help distinguish different components:

| Component | Color | Example |
|-----------|-------|---------|
| Agents | Cyan | 🤖 AGENT 1: NETWORK CONNECTOR |
| Tools | Yellow | 🔧 TOOL CALL: query_parameter |
| API | Green | 🌐 API REQUEST: POST /mml/command |
| LLM | Blue | 📝 LLM PROMPT (Monitoring Agent) |
| State | Magenta | 📊 STATE TRANSITION: monitor → analytics |
| Success | Green | ✅ Workflow completed |
| Error | Red | ❌ Workflow failed |
| Warning | Yellow | ⚠️  Validation required |

---

## Practical Usage Examples

### Example 1: Monitor Optimization Workflow

```bash
# Terminal 1: Run the UI with verbose logging
cd lz-network-optimizer
./run_with_logging.sh verbose

# Terminal 2: Open the UI in browser
open http://localhost:8501

# In UI: Select site, enter query, run optimization
# Watch Terminal 1 for complete workflow execution
```

### Example 2: Debug API Connection Issues

```bash
# Run with debug mode to see all connection details
./run_with_logging.sh debug

# Look for API-related logs:
# - SSL handshake details
# - Authentication token generation
# - Request/response headers
# - Raw response bodies
```

### Example 3: Understand Agent Prompts

```bash
# Run with verbose mode
./run_with_logging.sh verbose

# Trigger an optimization in the UI
# Watch the terminal to see:
# 1. What prompt is sent to each agent
# 2. What tools the agent decides to call
# 3. What response the agent generates
# 4. Why the workflow routes to the next agent
```

### Example 4: Save Complete Workflow Log

```bash
# Run the application
./run_with_logging.sh verbose

# All output is automatically saved to:
logs/lz_optimizer_[timestamp].log

# After optimization, review the log file:
cat logs/lz_optimizer_20251103_142315.log

# Or search for specific events:
grep "TOOL CALL" logs/lz_optimizer_20251103_142315.log
grep "LLM PROMPT" logs/lz_optimizer_20251103_142315.log
grep "API REQUEST" logs/lz_optimizer_20251103_142315.log
```

---

## Troubleshooting

### Issue: No logs appearing in terminal

**Solution 1:** Check logging configuration
```bash
# Verify config.yaml settings
grep -A 5 "agent_logs:" config/config.yaml

# Should show:
#   agent_logs:
#     enabled: true
#     log_state_transitions: true
#     log_tool_calls: true
#     log_llm_prompts: true
#     log_llm_responses: true
```

**Solution 2:** Check environment variable
```bash
# Ensure LZ_LOG_MODE is set
echo $LZ_LOG_MODE

# Should output: verbose (or basic/debug)

# If empty, set it:
export LZ_LOG_MODE=verbose
```

### Issue: Too much noise in terminal

**Solution:** Use basic mode or disable specific features
```bash
# Option 1: Use basic mode
./run_with_logging.sh basic

# Option 2: Edit config.yaml to disable LLM logs
# Set log_llm_prompts: false and log_llm_responses: false
```

### Issue: Colors not showing in terminal

**Solution:** Check terminal support
```bash
# Some terminals don't support ANSI colors
# Try a different terminal (iTerm2, Terminal.app, etc.)

# Or disable colors in config.yaml:
# logging:
#   console_logging:
#     colorize: false
```

### Issue: Log file not created

**Solution:** Check logs directory permissions
```bash
# Create logs directory if missing
mkdir -p logs

# Check permissions
ls -ld logs/

# Should show: drwxr-xr-x (readable and writable)
```

---

## Advanced Usage

### Programmatic Logging in Custom Code

If you're writing custom agents or tools, use the WorkflowLogger:

```python
from utils.logging_config import WorkflowLogger

# Create logger
logger = WorkflowLogger("My-Custom-Agent")

# Log workflow start
logger.log_workflow_start("MSH-0112-Bindura Hospital", 1, "Custom optimization")

# Log agent execution
logger.log_agent_start("Custom Agent", 1)

# Log tool calls
logger.log_tool_call("my_custom_tool", {"param1": "value1"})
logger.log_tool_result("my_custom_tool", "Tool result", success=True)

# Log LLM interactions
logger.log_llm_prompt("Custom Agent", "Your prompt here...")
logger.log_llm_response("Custom Agent", "AI response here...")

# Log decisions
logger.log_decision("Custom Decision", "YES", "Reason for decision")

# Log workflow end
logger.log_workflow_end(True, "Custom workflow completed")
```

### Filter Logs by Component

```bash
# View only agent logs
grep "AGENT" logs/lz_optimizer_20251103_142315.log

# View only tool calls
grep "TOOL CALL" logs/lz_optimizer_20251103_142315.log

# View only API requests
grep "API REQUEST" logs/lz_optimizer_20251103_142315.log

# View only decisions
grep "DECISION" logs/lz_optimizer_20251103_142315.log

# View only LLM prompts
grep "LLM PROMPT" logs/lz_optimizer_20251103_142315.log
```

### Real-Time Log Monitoring

```bash
# Terminal 1: Run the application
./run_with_logging.sh verbose

# Terminal 2: Watch the log file in real-time
tail -f logs/lz_optimizer_20251103_142315.log

# Terminal 3: Filter for specific events
tail -f logs/lz_optimizer_20251103_142315.log | grep "AGENT"
```

---

## Summary

### To See Agentic Workflow in Terminal:

1. **Run with the startup script:**
   ```bash
   ./run_with_logging.sh verbose
   ```

2. **Or set environment variable:**
   ```bash
   export LZ_LOG_MODE=verbose
   python3 -m streamlit run ui/app.py --server.headless=true
   ```

3. **Ensure config.yaml has logging enabled:**
   ```yaml
   agent_logs:
     enabled: true
     log_llm_prompts: true
     log_llm_responses: true
   ```

4. **Trigger an optimization in the UI**

5. **Watch your terminal** for complete workflow execution

### You'll See:
- ✅ Agent execution (which agent is running)
- ✅ Tool calls (parameters and results)
- ✅ API requests (to Huawei network)
- ✅ LLM prompts (sent to NVIDIA AI)
- ✅ LLM responses (AI decisions)
- ✅ Workflow routing decisions
- ✅ State transitions
- ✅ Final recommendations

---

**Created:** 2025-11-03
**Updated:** 2025-11-03
**Version:** 1.0
