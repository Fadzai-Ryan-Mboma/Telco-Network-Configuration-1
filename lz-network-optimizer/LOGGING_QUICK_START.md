# Quick Start: See Agentic Workflow in Terminal

## TL;DR - Three Simple Steps

```bash
# 1. Navigate to project
cd lz-network-optimizer

# 2. Run with verbose logging
./run_with_logging.sh verbose

# 3. Open UI and run an optimization
# Watch your terminal for complete workflow output!
```

---

## What You'll See

### 🤖 Agent Execution
Every agent's start and completion:
```
────────────────────────────────────────────────────────────────
🤖 AGENT 1: NETWORK CONNECTOR AGENT
────────────────────────────────────────────────────────────────
✅ Network Connector Agent completed
```

### 🔧 Tool Calls
Every tool invocation with parameters:
```
🔧 TOOL CALL: query_huawei_parameter
   parameter_name: reference_signal_power_pdschcfg
   site_name: MSH-0112-Bindura Hospital

✓ TOOL RESULT: query_huawei_parameter
   Current value: 152 (15.2 dBm)
```

### 🌐 API Requests
All Huawei API interactions:
```
🌐 API REQUEST: POST /api/rest/mmlManagement/v1/command
   command: LST PDSCHCFG: LOCALCELLID=1;

✓ API RESPONSE: 200 (0.547s)
```

### 📝 LLM Prompts & Responses
Complete AI interactions:
```
┌──────────────────────────────────────────────────────────────┐
│ 📝 LLM PROMPT (Monitoring Agent)                            │
├──────────────────────────────────────────────────────────────┤
│ You are a network monitoring expert...                       │
│ Current KPI Values:                                          │
│ - Network Access Success: 92.5%                              │
│ Analyze and determine if optimization is needed.             │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ 💬 LLM RESPONSE (Monitoring Agent)                          │
├──────────────────────────────────────────────────────────────┤
│ Based on analysis:                                           │
│ 1. Network Access Success BELOW threshold                    │
│ RECOMMENDATION: Optimization needed                          │
└──────────────────────────────────────────────────────────────┘
```

### ⚖️ Workflow Decisions
Critical routing points:
```
⚖️  DECISION: Needs Optimization?
   Decision: YES
   Reason: Network Access Success below threshold
```

### 📊 State Transitions
Workflow routing between agents:
```
📊 STATE TRANSITION: monitoring → kpi_analytics
   Reason: Optimization required
```

---

## Logging Modes

### Verbose (Recommended)
```bash
./run_with_logging.sh verbose
```
Shows: Agents, tools, API, LLM prompts/responses, decisions

### Basic (Quiet)
```bash
./run_with_logging.sh basic
```
Shows: Essential messages only

### Debug (Maximum)
```bash
./run_with_logging.sh debug
```
Shows: Everything + internal library logs

---

## Enable/Disable Features

Edit `config/config.yaml`:

```yaml
logging:
  agent_logs:
    log_state_transitions: true   # Workflow routing
    log_tool_calls: true           # Tool invocations
    log_llm_prompts: true          # AI prompts
    log_llm_responses: true        # AI responses
```

Set to `false` to disable any feature.

---

## Log Files

All output is saved to:
```
logs/lz_optimizer_[timestamp].log
```

View a log file:
```bash
cat logs/lz_optimizer_20251103_142315.log
```

Watch in real-time:
```bash
tail -f logs/lz_optimizer_20251103_142315.log
```

---

## Test It Now

```bash
# See the logging demo (simulated workflow)
python3 test_terminal_logging.py

# Run the actual optimizer with logging
./run_with_logging.sh verbose
```

---

## Troubleshooting

**No logs appearing?**
```bash
# Check config
grep "log_llm_prompts:" config/config.yaml

# Should show: log_llm_prompts: true
# If false, change to true
```

**Too much output?**
```bash
# Use basic mode
./run_with_logging.sh basic
```

---

**Full Documentation:** [documentation/TERMINAL_LOGGING_GUIDE.md](documentation/TERMINAL_LOGGING_GUIDE.md)
