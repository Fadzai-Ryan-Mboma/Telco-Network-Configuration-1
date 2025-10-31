# NVIDIA Blueprint to Liquid Zimbabwe 4G Network Mapping

**Document Version**: 1.0
**Date**: 2025-10-30
**Phase**: Phase 1 - Architecture Design
**Purpose**: Complete mapping from Nvidia Telco Network Configuration Blueprint to Liquid Zimbabwe 4G Network Optimizer

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Network Stack Mapping](#network-stack-mapping)
3. [Agent Architecture Mapping](#agent-architecture-mapping)
4. [Tool Mapping](#tool-mapping)
5. [Parameter Mapping](#parameter-mapping)
6. [KPI Mapping](#kpi-mapping)
7. [Database Mapping](#database-mapping)
8. [State Management Mapping](#state-management-mapping)
9. [UI Mapping](#ui-mapping)
10. [Configuration Mapping](#configuration-mapping)

---

## Executive Summary

### Nvidia Blueprint Overview
- **Technology**: BubbleRAN 5G O-RAN
- **Agents**: 3 (Configuration, Validation, Monitoring)
- **Parameters**: 5 (5G-specific: p0_nominal, dl/ul_carrierBandwidth, att_tx/rx)
- **Tools**: 4 (@tool decorated functions)
- **Database**: SQLite (persistent + historical)
- **UI**: Streamlit (~300 lines)
- **Deployment**: Docker Compose with BubbleRAN containers

### Liquid Zimbabwe Target
- **Technology**: Huawei 4G iMaster MAE API
- **Agents**: 6 (3 core + 3 extensions)
- **Parameters**: 5 (4G Huawei-specific with MML commands)
- **Tools**: 8 (Huawei API, SQL, calculation, validation)
- **Database**: SQLite (single unified database)
- **UI**: Streamlit (~400 lines with Cassava branding)
- **Deployment**: Docker (single container, deploy-anywhere)

### Key Differences
| Aspect | Nvidia Blueprint | LZ Implementation |
|--------|------------------|-------------------|
| Network | BubbleRAN 5G simulation | Live Huawei 4G production |
| API | Docker network endpoints | HTTPS REST API with auth |
| Parameters | 5G O-RAN config files | 4G MML commands |
| KPI Weighting | Equal weights | 3-tier weighted (25/50/25) |
| Agents | 3 agents | 6 agents (expanded workflow) |
| Complexity | Baseline | +40% (controlled expansion) |

---

## Network Stack Mapping

### Nvidia Blueprint Stack
```
┌─────────────────────────────────────┐
│  Streamlit UI (telco_planner_ui.py) │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   LangGraph Agents (agents.py)      │
│   - Configuration Agent              │
│   - Validation Agent                 │
│   - Monitoring Agent                 │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   Tools (tools.py)                   │
│   - execute_xapp_sql                 │
│   - execute_historical_sql           │
│   - find_value_in_gnb                │
│   - calc_weighted_average            │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   Utils (utils.py)                   │
│   - start_network()                  │
│   - stop_network()                   │
│   - update_value_in_gnb()            │
│   - check_network_status()           │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   BubbleRAN 5G Network               │
│   - gNodeB (5G base station)         │
│   - Core Network (Docker containers) │
│   - xApp Database (KPI collection)   │
└──────────────────────────────────────┘
```

### Liquid Zimbabwe Stack
```
┌─────────────────────────────────────┐
│  Streamlit UI (ui/app.py)            │
│  + Cassava Branding                  │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   LangGraph Workflow (agents/       │
│   workflow.py)                       │
│   - 6 Agents with few-shot prompting │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   Domain Knowledge (domain/)         │
│   - Parameters (5 Huawei 4G params)  │
│   - KPIs (7 weighted metrics)        │
│   - Optimization Rules (10 scenarios)│
│   - MML Command Templates            │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   Tools (tools/)                     │
│   - Huawei API tools                 │
│   - SQL tools (KPI + historical)     │
│   - Calculation tools (weighted)     │
│   - Validation tools (safety)        │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   Huawei API Client (network/       │
│   huawei_client.py)                  │
│   - OAuth2 authentication            │
│   - MML command execution            │
│   - KPI data collection              │
│   - Retry logic & rate limiting      │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   Huawei iMaster MAE API             │
│   - Live 4G Network Elements         │
│   - Site: MSH-0112-Bindura Hospital  │
│   - URL: https://41.174.191.214:31127│
└──────────────────────────────────────┘
```

### Stack Component Mapping

| Nvidia Component | LZ Component | Notes |
|------------------|--------------|-------|
| `telco_planner_ui.py` | `ui/app.py` | Add Cassava branding, simplify to ~400 lines |
| `agents.py` (1,710 lines) | `agents/*.py` (6 files) | Split agents, add 3 extensions |
| `tools.py` (305 lines) | `tools/*.py` (4 files) | Split by category (Huawei, SQL, calc, validation) |
| `utils.py` (617 lines) | `network/huawei_client.py` | Replace with API client |
| BubbleRAN Docker | Huawei API | Direct HTTPS integration |
| xApp SQLite DB | `data/lz_network.db` | Single unified database |
| config.yaml | `config/config.yaml` | Adapt for Huawei + LZ KPIs |

---

## Agent Architecture Mapping

### Nvidia Blueprint: 3 Agents

**1. Configuration Agent** (lines 531-810 in agents.py)
- **Purpose**: Analyze KPIs and recommend parameter changes
- **Input**: User query, historical KPI data
- **Tools**: `execute_historical_sql`, `find_value_in_gnb`
- **Output**: Recommended parameter values with reasoning
- **Prompt**: Generic ("You are an agent in a LangGraph...")
- **Key Pattern**:
  ```python
  system_prompt = 'You are an agent in a LangGraph. Your task is to help a user configure...'
  llm_agent = create_react_agent(llm, tools=[execute_historical_sql, find_value_in_gnb], prompt=system_prompt)
  ```

**2. Validation Agent** (lines 812-1078 in agents.py)
- **Purpose**: Test recommended changes on live network
- **Input**: Proposed parameter changes
- **Tools**: `update_value_in_gnb`, `execute_xapp_sql`, `calc_weighted_average`
- **Output**: Validation results, rollback decision
- **Workflow**:
  1. Record baseline KPIs
  2. Apply changes
  3. Monitor for validation_wait_time
  4. Calculate weighted gain
  5. Rollback if degraded
- **Key Pattern**:
  ```python
  # Collect baseline KPIs
  time.sleep(validation_wait_time)
  # Compare before/after
  if weighted_gain < 0: rollback()
  ```

**3. Monitoring Agent** (lines 106-529 in agents.py)
- **Purpose**: Continuous KPI monitoring, detect degradation
- **Input**: Current parameter values
- **Tools**: `execute_xapp_sql`, `calc_weighted_average`
- **Output**: Alerts, escalation to Configuration Agent
- **Workflow**: For each parameter:
  1. Collect KPIs for monitoring_wait_time
  2. Calculate weighted average
  3. Compare to thresholds
  4. Escalate if degraded
- **Key Pattern**:
  ```python
  for param in parameters:
      time.sleep(monitoring_wait_time)
      weighted_avg = calc_weighted_average(kpi_data)
      if weighted_avg < threshold: escalate_to_config_agent()
  ```

### Liquid Zimbabwe: 6 Agents

**Core Agents (Enhanced from Nvidia)**

**1. Configuration Agent** → `agents/config_agent.py`
- **Enhanced With**:
  - Few-shot prompting (3-5 optimization examples)
  - Domain knowledge injection (5 params, 7 KPIs, 10 rules)
  - Weighted KPI scoring (3-tier: 25/50/25)
  - MML command generation
- **Input**: User query + KPI issues + site information
- **Tools**:
  - `execute_historical_sql` (historical optimization data)
  - `execute_lz_kpi_sql` (live KPI data)
  - `calc_weighted_kpi_score` (weighted scoring)
  - `query_huawei_parameter` (current values)
- **Output**:
  - Parameter recommendations with MML commands
  - Expected KPI improvements
  - Risk assessment
- **New Prompt Structure**:
  ```python
  system_prompt = build_configuration_prompt(domain_knowledge, few_shot_examples)
  # Includes: role definition, parameter specs, optimization rules, examples
  ```

**2. Validation Agent** → `agents/validation_agent.py`
- **Enhanced With**:
  - Huawei MML command execution
  - Enhanced safety validation (range checks, impact scoring)
  - Automatic rollback with audit trail
  - Before/after weighted KPI comparison
- **Input**: Recommended parameter changes + MML commands
- **Tools**:
  - `execute_mml_command` (apply changes)
  - `collect_live_kpis` (monitor performance)
  - `calc_weighted_kpi_score` (compare before/after)
  - `validate_parameter_range` (safety check)
- **Output**:
  - Validation results (success/failure)
  - KPI improvement metrics
  - Rollback decision with reasoning
- **Enhanced Workflow**:
  ```python
  1. Validate parameter ranges (safety pre-check)
  2. Calculate risk score
  3. Record baseline weighted KPI score
  4. Execute MML command
  5. Monitor KPIs for validation_duration (5 minutes)
  6. Calculate new weighted KPI score
  7. If improvement: commit, else: rollback
  8. Log to optimization_history table
  ```

**3. Monitoring Agent** → `agents/monitoring_agent.py`
- **Enhanced With**:
  - 7 weighted KPIs (vs 5 unweighted in Nvidia)
  - Threshold-based alerts (normal vs critical)
  - Trend analysis (performance degradation over time)
  - Huawei-specific KPI collection
- **Input**: Site name, cell ID
- **Tools**:
  - `execute_lz_kpi_sql` (query KPI database)
  - `collect_live_kpis` (from Huawei API)
  - `calc_weighted_kpi_score` (overall health score)
  - `detect_degradation` (trend analysis)
- **Output**:
  - KPI status report
  - Degradation alerts
  - Escalation to Configuration Agent if needed
- **Enhanced Workflow**:
  ```python
  # Continuous monitoring loop
  while monitoring_active:
      kpis = collect_live_kpis(site, cell_id)
      weighted_score = calc_weighted_kpi_score(kpis)

      for kpi, value in kpis.items():
          if value < threshold_critical: alert(CRITICAL, kpi)
          elif value < threshold_normal: alert(WARNING, kpi)

      if weighted_score_degraded: escalate_to_config_agent()
      time.sleep(monitoring_interval)
  ```

**Extension Agents (New for LZ)**

**4. KPI Analytics Agent** → `agents/kpi_analytics_agent.py`
- **Purpose**: Deep KPI analysis, root cause identification
- **Input**: Historical + live KPI data, site information
- **Tools**:
  - `execute_historical_sql` (historical patterns)
  - `execute_lz_kpi_sql` (recent data)
  - `calc_kpi_correlation` (parameter-KPI relationships)
  - `identify_root_cause` (pattern matching)
- **Output**:
  - Root cause analysis
  - KPI correlations
  - Optimization opportunity identification
- **Use Case**:
  - User asks "Why is download speed low at Bindura Hospital?"
  - Agent analyzes historical data, identifies patterns
  - Correlates with parameter changes and network events
  - Provides detailed explanation with evidence

**5. Network Connector Agent** → `agents/network_connector_agent.py`
- **Purpose**: Manage Huawei API connection lifecycle
- **Input**: Connection request (connect/disconnect/status)
- **Tools**:
  - `connect_huawei_api` (authenticate)
  - `disconnect_huawei_api` (cleanup)
  - `check_api_status` (health check)
  - `discover_network_elements` (site/cell inventory)
- **Output**:
  - Connection status
  - API health information
  - Available network elements (sites, cells)
- **Use Case**:
  - User starts session: "Connect to Bindura Hospital site"
  - Agent authenticates to Huawei API
  - Discovers available cells for the site
  - Returns connection status and site inventory

**6. MML Executor Agent** → `agents/mml_executor_agent.py`
- **Purpose**: Safe MML command execution with validation
- **Input**: Validated MML commands, site/cell information
- **Tools**:
  - `execute_mml_command` (command execution)
  - `parse_mml_response` (result validation)
  - `validate_mml_syntax` (pre-execution check)
  - `rollback_mml_command` (undo if needed)
- **Output**:
  - Execution results
  - Parameter confirmation (before/after values)
  - Error handling with suggestions
- **Safety Features**:
  - Syntax validation before execution
  - Response parsing for error detection
  - Automatic retry on transient failures
  - Rollback capability

---

## Tool Mapping

### Nvidia Tools (4 tools in tools.py)

**1. `execute_xapp_sql(sql_query: str) -> str`**
- **Purpose**: Query persistent database (live KPI data from xApp)
- **Database**: `config['persistent_db_path']`
- **Returns**: Pandas DataFrame as formatted string
- **Use Case**: Get current network performance metrics
- **Example**:
  ```python
  sql = "SELECT AVG(dl_bitrate) FROM kpi_data WHERE timestamp > datetime('now', '-5 minutes')"
  result = execute_xapp_sql(sql)
  ```

**2. `execute_historical_sql(sql_query: str) -> str`**
- **Purpose**: Query historical database (past optimization data)
- **Database**: `config['historical_db_path']`
- **Returns**: Pandas DataFrame as formatted string
- **Use Case**: Analyze historical patterns for recommendations
- **Example**:
  ```python
  sql = "SELECT p0_nominal, AVG(dl_bitrate) FROM historical GROUP BY p0_nominal"
  result = execute_historical_sql(sql)
  ```

**3. `find_value_in_gnb(var: str) -> int`**
- **Purpose**: Read current parameter value from gNodeB config file
- **Method**: Parses gnb.conf file using subprocess
- **Returns**: Integer parameter value
- **Use Case**: Get current parameter settings before changes
- **Example**:
  ```python
  current_p0 = find_value_in_gnb("p0_nominal")  # Returns: -90
  ```

**4. `calc_weighted_average(weight1: float, weight2: float, ...) -> float`**
- **Purpose**: Calculate weighted average of KPI metrics
- **Method**: (weight1 * kpi1 + weight2 * kpi2) / (weight1 + weight2)
- **Returns**: Float weighted average
- **Use Case**: Combine multiple KPIs into single performance score
- **Example**:
  ```python
  # Weights from config.yaml: [0.6, 0.4] for DL bitrate and SNR
  score = calc_weighted_average(0.6, dl_bitrate_avg, 0.4, snr_avg)
  ```

### Liquid Zimbabwe Tools (8 tools across 4 files)

**A) Huawei API Tools** → `tools/huawei_tools.py`

**1. `@tool connect_huawei_api(config: dict) -> dict`**
- **Purpose**: Authenticate to Huawei iMaster MAE API
- **Replaces**: `start_network()` from Nvidia utils.py
- **Method**: OAuth2 token-based authentication
- **Returns**: Connection status + auth token + session info
- **Example**:
  ```python
  config = {"base_url": "https://41.174.191.214:31127", "username": "cassava.ai", ...}
  status = connect_huawei_api(config)
  # Returns: {"status": "connected", "token": "...", "expires_at": "..."}
  ```

**2. `@tool query_huawei_parameter(param_name: str, site_name: str, cell_id: int) -> dict`**
- **Purpose**: Query current parameter value via MML
- **Replaces**: `find_value_in_gnb(var)` from Nvidia
- **Method**: Execute LST MML command via API
- **Returns**: Parameter value + metadata
- **Example**:
  ```python
  result = query_huawei_parameter(
      "reference_signal_power_pdschcfg",
      "MSH-0112-Bindura Hospital",
      1
  )
  # Returns: {"parameter": "reference_signal_power_pdschcfg", "value": -200, "unit": "0.1 dBm"}
  ```

**3. `@tool execute_mml_command(mml_command: str, site_name: str) -> dict`**
- **Purpose**: Execute MML command (LST or MOD)
- **Replaces**: `update_value_in_gnb(var, val)` from Nvidia
- **Method**: POST to Huawei MML API endpoint
- **Returns**: Execution result + confirmation
- **Example**:
  ```python
  mml = "MOD PDSCHCFG:LOCALCELLID=1,REFERENCESIGNALPWR=-150;"
  result = execute_mml_command(mml, "MSH-0112-Bindura Hospital")
  # Returns: {"status": "success", "message": "Parameter updated", "old_value": -200, "new_value": -150}
  ```

**4. `@tool collect_live_kpis(site_name: str, cell_id: int, duration: int) -> dict`**
- **Purpose**: Collect KPI data from Huawei API
- **Replaces**: Implicit in `execute_xapp_sql()` from Nvidia
- **Method**: Query Huawei KPI endpoint, aggregate data
- **Returns**: 7 KPIs + timestamp
- **Example**:
  ```python
  kpis = collect_live_kpis("MSH-0112-Bindura Hospital", 1, duration=60)
  # Returns: {
  #   "network_access_success": 96.5,
  #   "download_speed": 8500,
  #   "download_quality": 12.3,
  #   ...
  # }
  ```

**5. `@tool check_api_status() -> dict`**
- **Purpose**: Health check for Huawei API connection
- **Replaces**: `check_network_status()` from Nvidia
- **Method**: Ping API health endpoint, check token validity
- **Returns**: API health status
- **Example**:
  ```python
  status = check_api_status()
  # Returns: {"status": "healthy", "response_time": "0.234s", "token_valid": true}
  ```

**B) SQL Tools** → `tools/sql_tools.py`

**6. `@tool execute_lz_kpi_sql(sql_query: str) -> str`**
- **Purpose**: Query LZ KPI database (live + historical data)
- **Maps to**: `execute_xapp_sql()` from Nvidia
- **Database**: `data/lz_network.db` (table: kpi_data)
- **Returns**: Pandas DataFrame as formatted string
- **Example**:
  ```python
  sql = "SELECT AVG(network_access_success) FROM kpi_data WHERE site_name = 'MSH-0112-Bindura Hospital' AND timestamp > datetime('now', '-1 hour')"
  result = execute_lz_kpi_sql(sql)
  ```

**7. `@tool execute_historical_sql(sql_query: str) -> str`**
- **Purpose**: Query historical optimization data
- **Maps to**: Same function from Nvidia (keep as-is)
- **Database**: `data/lz_network.db` (table: optimization_history)
- **Returns**: Pandas DataFrame as formatted string
- **Use Case**: Analyze past optimizations to inform new recommendations
- **Example**:
  ```python
  sql = "SELECT parameters_changed, weighted_improvement FROM optimization_history WHERE success = 1 AND kpi_issue LIKE '%low_download_speed%' ORDER BY timestamp DESC LIMIT 10"
  result = execute_historical_sql(sql)
  ```

**C) Calculation Tools** → `tools/calculation_tools.py`

**8. `@tool calc_weighted_kpi_score(kpis: dict, weights: dict) -> float`**
- **Purpose**: Calculate weighted KPI score (0-100 scale)
- **Enhanced from**: `calc_weighted_average()` from Nvidia
- **Method**: Normalize KPIs, apply 3-tier weights, compute weighted sum
- **Returns**: Weighted score (0-100, higher is better)
- **Weighting**: 3-tier system from kpi_weights.yaml
- **Example**:
  ```python
  kpis = {
      "network_access_success": 96.5,  # Higher is better
      "download_speed": 8500,           # Higher is better
      "download_quality": 12.3,         # IBLER - Lower is better
      ...
  }
  weights = {
      "network_access_success": 0.25,  # Tier 1: Foundation
      "download_speed": 0.20,           # Tier 2: Revenue
      ...
  }
  score = calc_weighted_kpi_score(kpis, weights)
  # Returns: 89.2 (normalized weighted score)
  ```

**D) Validation Tools** → `tools/validation_tools.py`

**9. `@tool validate_parameter_range(param_name: str, new_value: int) -> dict`**
- **Purpose**: Validate parameter value is within safe range
- **New Tool**: Safety validation not in Nvidia blueprint
- **Method**: Check against parameter definitions from domain/parameters.py
- **Returns**: Validation result + warnings
- **Example**:
  ```python
  result = validate_parameter_range("reference_signal_power_pdschcfg", -50)
  # Returns: {
  #   "valid": false,
  #   "reason": "Value -50 exceeds maximum -600",
  #   "allowed_range": "(-600, 500)",
  #   "suggested_value": -150
  # }
  ```

**10. `@tool calculate_risk_score(param_changes: dict) -> dict`**
- **Purpose**: Calculate risk score for proposed parameter changes
- **New Tool**: Risk assessment not in Nvidia blueprint
- **Method**: Assess impact level, validate ranges, check correlations
- **Returns**: Risk score (1-5) + risk factors
- **Example**:
  ```python
  changes = {"reference_signal_power_pdschcfg": {"old": -200, "new": -150}}
  risk = calculate_risk_score(changes)
  # Returns: {
  #   "risk_score": 2,  # Low-Medium risk
  #   "risk_level": "LOW",
  #   "factors": ["Single parameter change", "Within safe range", "Historical success rate: 85%"]
  # }
  ```

### Tool Comparison Summary

| Nvidia Tool | LZ Tool(s) | Change Type |
|-------------|------------|-------------|
| `execute_xapp_sql` | `execute_lz_kpi_sql` | Renamed, same function |
| `execute_historical_sql` | `execute_historical_sql` | Keep as-is |
| `find_value_in_gnb` | `query_huawei_parameter` | API-based, not file parsing |
| `calc_weighted_average` | `calc_weighted_kpi_score` | Enhanced with 3-tier weighting |
| `start_network` | `connect_huawei_api` | OAuth2 auth vs Docker start |
| `stop_network` | `disconnect_huawei_api` | API cleanup vs Docker stop |
| `update_value_in_gnb` | `execute_mml_command` | MML command vs file edit |
| `check_network_status` | `check_api_status` | API health check vs Docker ps |
| *(none)* | `collect_live_kpis` | **NEW** - Huawei KPI collection |
| *(none)* | `validate_parameter_range` | **NEW** - Safety validation |
| *(none)* | `calculate_risk_score` | **NEW** - Risk assessment |

---

## Parameter Mapping

### Nvidia Blueprint: 5G O-RAN Parameters

**1. p0_nominal**
- **Type**: Power control parameter (uplink)
- **Range**: [-98, -94, -90, -86] (discrete values from config.yaml)
- **Default**: -90 dBm
- **File**: gnb.conf
- **Impact**: Uplink bitrate, SNR
- **MML**: *(N/A - file-based config)*

**2. dl_carrierBandwidth**
- **Type**: Downlink bandwidth allocation
- **Range**: [24, 51, 106] RBs (Resource Blocks)
- **Default**: 51 RBs
- **File**: gnb.conf
- **Impact**: Downlink bitrate, SNR
- **MML**: *(N/A)*

**3. ul_carrierBandwidth**
- **Type**: Uplink bandwidth allocation
- **Range**: [24, 51, 106] RBs
- **Default**: 51 RBs
- **File**: gnb.conf
- **Impact**: Uplink bitrate, SNR
- **MML**: *(N/A)*

**4. att_tx**
- **Type**: TX attenuation
- **Range**: [0, 10, 20, 30, 40] dB
- **Default**: 10 dB
- **File**: gnb.conf
- **Impact**: Downlink bitrate, SNR
- **MML**: *(N/A)*

**5. att_rx**
- **Type**: RX attenuation
- **Range**: [0, 10, 20, 30, 40] dB
- **Default**: 10 dB
- **File**: gnb.conf
- **Impact**: Uplink bitrate, retransmissions
- **MML**: *(N/A)*

### Liquid Zimbabwe: 4G Huawei Parameters

**1. reference_signal_power_pdschcfg**
- **Type**: PDSCH reference signal power (downlink coverage)
- **Range**: -600 to 500 (0.1 dBm units) → -60.0 to 50.0 dBm
- **Default**: -200 (-20.0 dBm)
- **Impact**: Network access success, download speed, download quality
- **MML Query**: `LST PDSCHCFG: LOCALCELLID=1;`
- **MML Modify**: `MOD PDSCHCFG:LOCALCELLID=1,REFERENCESIGNALPWR=-150;`
- **Optimization Scenarios**:
  - Low network access + low download speed → Increase (stronger signal)
  - High control channel load → Decrease (reduce interference)

**2. a3_event_offset**
- **Type**: Handover trigger offset (mobility)
- **Range**: 0 to 15 dB
- **Default**: 3 dB
- **Format**: `dB3` (dB prefix required)
- **Impact**: Network access success, control channel load
- **MML Query**: `LST UECOOPERATIONPARA: LOCALCELLID=1;`
- **MML Modify**: `MOD UECOOPERATIONPARA:LOCALCELLID=1,A3OFFSET=dB5;`
- **Optimization Scenarios**:
  - High control channel load → Increase (reduce handover frequency)
  - Low network access success + mobility issues → Adjust (optimize handover)

**3. t310_timer**
- **Type**: Radio link failure timer (connection stability)
- **Range**: 100 to 6000 ms
- **Default**: 1000 ms
- **Format**: `MS1000_T310` (MS prefix + _T310 suffix)
- **Impact**: Network access success, upload quality
- **MML Query**: `LST UETIMERCONST: LOCALCELLID=1;`
- **MML Modify**: `MOD UETIMERCONST:LOCALCELLID=1,T310=MS1500_T310;`
- **Optimization Scenarios**:
  - Low network access success + frequent disconnections → Increase (more tolerance)
  - High upload quality issues → Adjust (balance stability vs responsiveness)

**4. p0_nominal_pusch**
- **Type**: Uplink power control (PUSCH target power)
- **Range**: -126 to 24 dBm
- **Default**: -70 dBm
- **Impact**: Upload speed, upload quality, feedback channel load
- **MML Query**: `LST CELLULPCCOMM: LOCALCELLID=1;`
- **MML Modify**: `MOD CELLULPCCOMM:LOCALCELLID=1,P0NOMINALPUSCH=-67;`
- **Optimization Scenarios**:
  - Low upload speed → Increase (boost uplink power)
  - High upload quality (IBLER) → Adjust (balance power vs quality)
  - High feedback channel load → Decrease (reduce interference)

**5. pdcch_aggregation_level**
- **Type**: Control channel aggregation (robustness vs capacity)
- **Range**: 0 to 30
- **Default**: 12
- **Impact**: Control channel load, network access success
- **MML Query**: `LST CELLUSPARACFG: LOCALCELLID=1;`
- **MML Modify**: `MOD CELLUSPARACFG:LOCALCELLID=1,USDATAPDCCHSINROFFSET=15;`
- **Optimization Scenarios**:
  - High control channel load → Decrease (improve efficiency)
  - Low network access success + poor coverage → Increase (improve robustness)

### Parameter Mapping Notes

**Why Parameters Don't Map 1:1**:
- Nvidia: 5G O-RAN parameters (file-based configuration)
- LZ: 4G Huawei parameters (MML command-based)
- Different radio technologies (5G NR vs 4G LTE)
- Different vendors (open RAN vs Huawei proprietary)

**Common Concepts**:
- Power control: `p0_nominal` (Nvidia) ↔ `reference_signal_power_pdschcfg` + `p0_nominal_pusch` (LZ)
- Bandwidth: `dl/ul_carrierBandwidth` (Nvidia) ↔ Fixed in Huawei 4G deployment
- Attenuation: `att_tx/rx` (Nvidia) ↔ Implicit in Huawei power settings

---

## KPI Mapping

### Nvidia Blueprint: Variable KPIs

**From xApp Database** (persistent_db):
- `dl_bitrate` - Downlink bitrate (Mbps)
- `ul_bitrate` - Uplink bitrate (Mbps)
- `snr` - Signal-to-Noise Ratio (dB)
- `mcs` - Modulation and Coding Scheme
- `ldpc_iterations` - LDPC decoder iterations
- `retx` - Retransmissions requested by UE

**Weighting**: Equal weights or simple 2-factor weights from config.yaml
- Example: `p0_nominal_WA_weights: [0.6, 0.4]` (60% DL bitrate, 40% SNR)

**Aggregation**: Simple average over time period
- No normalization
- No tier-based weighting
- Each parameter has its own weights

### Liquid Zimbabwe: 7 Weighted KPIs

**From Huawei API + Database** (lz_network.db):

**Tier 1: Foundation (25% total weight)**
1. **Network Access Success** - 25%
   - Metric: RACH Setup Success Rate (%)
   - Threshold: Normal ≥95%, Critical <90%
   - CSV Column: `RACH Setup Success Rate(%)`
   - Direction: Higher is better
   - Business Impact: Critical - affects all users, direct churn driver

**Tier 2: Revenue & Experience (50% total weight)**
2. **Download Speed** - 20%
   - Metric: DL Throughput (kbit/s)
   - Threshold: Normal ≥5000, Critical <2000
   - CSV Column: `Downlink Throughput(kbit/s)`
   - Direction: Higher is better
   - Business Impact: High - primary revenue driver (data consumption)

3. **Download Quality** - 15%
   - Metric: DL IBLER (%) - Initial Block Error Rate
   - Threshold: Normal ≤15%, Critical >20%
   - CSV Column: `Downlink IBLER(%)`
   - Direction: Lower is better
   - Business Impact: High - user experience (video, streaming)

4. **Upload Speed** - 15%
   - Metric: UL Throughput (kbit/s)
   - Threshold: Normal ≥1000, Critical <500
   - CSV Column: `Uplink Throughput(kbit/s)`
   - Direction: Higher is better
   - Business Impact: Medium-High - important for video calls, uploads

5. **Upload Quality** - 10%
   - Metric: UL IBLER (%)
   - Threshold: Normal ≤10%, Critical >15%
   - CSV Column: `Uplink IBLER(%)`
   - Direction: Lower is better
   - Business Impact: Medium - background services, IoT

**Tier 3: Efficiency (25% total weight)**
6. **Control Channel Load** - 10%
   - Metric: PDCCH CCE Usage (%)
   - Threshold: Normal ≤70%, Critical >85%
   - CSV Column: `PDCCH CCE Usage(%)`
   - Direction: Lower is better
   - Business Impact: Medium - network capacity optimization

7. **Feedback Channel Load** - 5%
   - Metric: PUCCH Usage (%)
   - Threshold: Normal ≤10%, Critical >15%
   - CSV Column: `PUCCH Usage(%)`
   - Direction: Lower is better
   - Business Impact: Low - fine-tuning only

### KPI Weighting Rationale

**3-Tier System** (from kpi_weights.yaml):
```yaml
static_weights:
  network_access_success: 0.25   # Tier 1: Foundation
  download_speed: 0.20            # Tier 2: Revenue
  download_quality: 0.15          # Tier 2: Experience
  upload_speed: 0.15              # Tier 2: Important
  upload_quality: 0.10            # Tier 2: Background
  control_channel_load: 0.10      # Tier 3: Efficiency
  feedback_channel_load: 0.05     # Tier 3: Fine-tuning
```

**Why Weighted**:
- Reflects business priorities (revenue, churn, capacity)
- Aligns with telecom industry standards (3GPP, NGMN)
- Zimbabwean market: Data-heavy usage patterns
- Enables ROI calculation for optimizations

**Nvidia vs LZ KPI Approach**:

| Aspect | Nvidia | LZ |
|--------|--------|-----|
| **Number of KPIs** | Variable (6) | Fixed (7) |
| **Weighting** | Equal or 2-factor | 3-tier weighted (25/50/25) |
| **Normalization** | None | Normalized to 0-100 scale |
| **Thresholds** | Implicit | Explicit (normal/critical) |
| **Business Alignment** | Technical focus | Business + technical |
| **Aggregation** | Simple average | Weighted sum with normalization |
| **Calculation** | `(w1*kpi1 + w2*kpi2) / (w1+w2)` | `Σ(weight * normalized_kpi)` |

---

## Database Mapping

### Nvidia Blueprint: 2 Databases

**1. Persistent Database** (`persistent_db_path`)
- **Purpose**: Live KPI data from running network (xApp)
- **Tables**: `kpi_data`
- **Schema**:
  ```sql
  CREATE TABLE kpi_data (
      timestamp TEXT,
      p0_nominal INTEGER,
      dl_carrierBandwidth INTEGER,
      ul_carrierBandwidth INTEGER,
      att_tx INTEGER,
      att_rx INTEGER,
      dl_bitrate REAL,
      ul_bitrate REAL,
      snr REAL,
      mcs INTEGER,
      ldpc_iterations INTEGER,
      retx INTEGER
  );
  ```
- **Populated By**: xApp (Docker container) → collects KPIs from gNodeB
- **Accessed By**: `execute_xapp_sql()` tool

**2. Historical Database** (`historical_db_path`)
- **Purpose**: Past optimization data for analysis
- **Tables**: `historical_data`
- **Schema**: Similar to kpi_data (aggregated)
- **Populated By**: CSV import at startup (`read_historical_data()`)
- **Accessed By**: `execute_historical_sql()` tool

### Liquid Zimbabwe: Single Unified Database

**Database**: `data/lz_network.db` (SQLite)

**Table 1: kpi_data** (Live + Historical KPIs)
```sql
CREATE TABLE kpi_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    site_name TEXT NOT NULL,
    cell_id INTEGER NOT NULL,

    -- 7 KPIs (Tier 1: Foundation)
    network_access_success REAL,      -- RACH Setup Success Rate (%)

    -- Tier 2: Revenue & Experience
    download_speed REAL,               -- DL Throughput (kbit/s)
    download_quality REAL,             -- DL IBLER (%)
    upload_speed REAL,                 -- UL Throughput (kbit/s)
    upload_quality REAL,               -- UL IBLER (%)

    -- Tier 3: Efficiency
    control_channel_load REAL,         -- PDCCH CCE Usage (%)
    feedback_channel_load REAL,        -- PUCCH Usage (%)

    -- Metadata
    data_source TEXT DEFAULT 'live',   -- 'live' or 'historical'

    INDEX idx_site_timestamp (site_name, timestamp),
    INDEX idx_data_source (data_source)
);
```

**Table 2: parameter_changes** (Audit Trail)
```sql
CREATE TABLE parameter_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    site_name TEXT NOT NULL,
    cell_id INTEGER NOT NULL,
    parameter_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    reason TEXT,
    mml_command TEXT,
    success BOOLEAN DEFAULT 0,
    error_message TEXT,
    changed_by TEXT DEFAULT 'system',

    INDEX idx_site_param (site_name, parameter_name)
);
```

**Table 3: optimization_history** (Before/After Analysis)
```sql
CREATE TABLE optimization_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    site_name TEXT NOT NULL,
    cell_id INTEGER NOT NULL,

    -- Issue identification
    kpi_issue TEXT NOT NULL,           -- JSON array: ["low_download_speed", "poor_access"]
    trigger_reason TEXT,

    -- Changes made
    parameters_changed TEXT NOT NULL,  -- JSON: [{"param": "...", "old": "...", "new": "..."}]
    mml_commands TEXT,                 -- JSON array of MML commands executed

    -- Before/after KPIs
    kpi_before TEXT NOT NULL,          -- JSON: {"network_access_success": 88.5, ...}
    kpi_after TEXT,                    -- JSON: {"network_access_success": 96.2, ...}

    -- Results
    weighted_score_before REAL,
    weighted_score_after REAL,
    weighted_improvement REAL,
    success BOOLEAN,
    rolled_back BOOLEAN DEFAULT 0,

    -- Business impact
    revenue_risk_before REAL,
    revenue_risk_after REAL,

    INDEX idx_site_timestamp (site_name, timestamp),
    INDEX idx_success (success)
);
```

### Database Mapping Summary

| Aspect | Nvidia | LZ |
|--------|--------|-----|
| **Number of DBs** | 2 (persistent + historical) | 1 (unified) |
| **KPI Table** | `kpi_data` (xApp) | `kpi_data` (live + historical) |
| **Historical Data** | Separate DB | Same DB (data_source field) |
| **Audit Trail** | None | `parameter_changes` table |
| **Optimization History** | None | `optimization_history` table |
| **Schema** | 5 params + 6 KPIs | 5 params + 7 KPIs + metadata |
| **Site Tracking** | No | Yes (site_name, cell_id) |
| **Before/After** | Not stored | Stored in optimization_history |

---

## State Management Mapping

### Nvidia State (TypedDict in agents.py)

```python
class State(TypedDict):
    next: str                              # Next agent to route to
    agent_id: str                          # Current agent identifier
    messages: Annotated[list, add_messages]  # LangGraph message history
    average_kpis_df: Optional[pd.DataFrame]  # Aggregated KPI data
    weighted_average_gain: Optional[pd.DataFrame]  # Weighted gain calculation
    vars_current: Dict[str, int]           # Current parameter values
    vars_new: Dict[str, int]               # New proposed parameter values
```

**Usage Pattern**:
```python
# Initialized in UI (telco_planner_ui.py)
st.session_state.global_state = [State()]
st.session_state.global_state[0]["vars_current"] = {
    "p0_nominal": -90,
    "dl_carrierBandwidth": 51,
    "ul_carrierBandwidth": 51,
    "att_tx": 10,
    "att_rx": 10,
}

# Passed through agents
def monitoring_agent(state: State) -> State:
    # Access current values
    p0_current = state["vars_current"]["p0_nominal"]
    # Update state
    state["messages"].append(HumanMessage("Monitoring complete"))
    return state
```

### Liquid Zimbabwe State (Enhanced TypedDict)

```python
class State(TypedDict):
    # Routing
    next: str                              # Next agent in workflow
    agent_id: str                          # Current agent identifier

    # LangGraph message history
    messages: Annotated[list, add_messages]

    # Site/Cell identification
    site_name: str                         # e.g., "MSH-0112-Bindura Hospital"
    cell_id: int                           # e.g., 1

    # KPI data
    kpi_current: Dict[str, float]          # Current 7 KPI values
    kpi_baseline: Dict[str, float]         # Baseline (before optimization)
    weighted_score_current: float          # Current weighted KPI score (0-100)
    weighted_score_baseline: float         # Baseline weighted score
    kpi_issues: List[str]                  # Identified KPI issues

    # Parameter data
    params_current: Dict[str, Any]         # Current parameter values
    params_proposed: Dict[str, Any]        # Proposed parameter changes
    mml_commands: List[str]                # MML commands to execute

    # Validation data
    validation_duration: int               # Monitoring duration (seconds)
    validation_status: str                 # "pending"/"success"/"failed"
    rollback_needed: bool                  # Rollback flag

    # Analysis
    root_cause: Optional[str]              # Root cause analysis
    risk_score: Optional[int]              # Risk score (1-5)
    expected_improvement: Optional[float]  # Expected weighted score improvement

    # API connection
    api_connected: bool                    # Huawei API connection status
    api_token: Optional[str]               # Authentication token
```

**Usage Pattern**:
```python
# Initialized in UI (ui/app.py)
initial_state = State(
    next="network_connector",
    agent_id="",
    messages=[],
    site_name="MSH-0112-Bindura Hospital",
    cell_id=1,
    kpi_current={},
    params_current={},
    api_connected=False,
    ...
)

# Workflow execution
app = workflow.compile()
result = app.invoke(initial_state)

# Agents access and update state
def config_agent(state: State) -> Command[Literal["validation", "monitoring"]]:
    # Access current KPIs
    current_kpis = state["kpi_current"]
    weighted_score = state["weighted_score_current"]

    # Identify issues
    issues = identify_kpi_issues(current_kpis)

    # Generate recommendations
    recommendations = generate_recommendations(issues, state["params_current"])

    # Update state
    return Command(
        update={
            "params_proposed": recommendations,
            "kpi_issues": issues,
            "mml_commands": generate_mml_commands(recommendations),
            "risk_score": calculate_risk(recommendations),
        },
        goto="validation"  # Route to validation agent
    )
```

### State Mapping Summary

| Field | Nvidia | LZ | Change |
|-------|--------|-----|--------|
| **Routing** | `next`, `agent_id` | Same | Keep |
| **Messages** | `messages` (list) | Same | Keep |
| **Site ID** | *(none)* | `site_name`, `cell_id` | **NEW** |
| **KPI Data** | `average_kpis_df` | `kpi_current`, `kpi_baseline` | Enhanced |
| **Weighted Score** | `weighted_average_gain` | `weighted_score_current/baseline` | Enhanced |
| **Parameters** | `vars_current`, `vars_new` | `params_current`, `params_proposed` | Renamed |
| **MML Commands** | *(implicit)* | `mml_commands` | **NEW** |
| **Validation** | *(implicit)* | `validation_duration`, `validation_status`, `rollback_needed` | **NEW** |
| **Analysis** | *(none)* | `root_cause`, `risk_score`, `expected_improvement` | **NEW** |
| **API Connection** | *(network status)* | `api_connected`, `api_token` | **NEW** |

**Key Enhancements**:
1. **Site Tracking**: Added `site_name` and `cell_id` for multi-site support
2. **KPI Structure**: Separate current vs baseline for before/after comparison
3. **Weighted Scoring**: Explicit weighted score fields (0-100 scale)
4. **MML Commands**: Explicit list of commands for execution
5. **Validation State**: Detailed validation tracking for rollback
6. **Analysis Fields**: Root cause, risk score, expected improvement
7. **API State**: Connection status and token management

---

## UI Mapping

### Nvidia UI Structure (telco_planner_ui.py ~300 lines)

**Key Components**:

1. **Initialization** (lines 41-95)
   - Session state variables
   - Parameter initialization from network or config
   - Network status check

2. **Main Layout**
   ```python
   st.title("Network Performance Planner")
   st.write("Telco agent-based LLM workflow...")
   ```

3. **Sidebar** (Network Control)
   - Start Network button
   - Stop Network button
   - Parameter sliders (p0_nominal, dl/ul_carrierBandwidth, att_tx/rx)
   - Monitoring/Validation time settings

4. **Main Content Area**
   - User query text area
   - "Run Configuration Agent" button
   - Configuration output display
   - "Apply Configuration" button (conditional)
   - "Run Validation Agent" button (conditional)
   - Monitoring agent toggle

5. **Agent Execution Patterns**
   ```python
   # Configuration Agent
   if st.button("Run Configuration Agent"):
       with st.spinner("Running configuration agent..."):
           # Build workflow
           graph = StateGraph(State)
           graph.add_node("config", config_agent)
           # ...
           app = graph.compile()
           result = app.invoke(state)
           st.session_state.config_output = result

   # Validation Agent
   if st.button("Apply Configuration"):
       with st.spinner("Applying configuration and validating..."):
           # Execute validation workflow
           # ...
   ```

6. **Session State Management**
   - `st.session_state.user_query`
   - `st.session_state.config_output`
   - `st.session_state.show_validation_keys`
   - `st.session_state.global_state`
   - `st.session_state.monitoring`

### Liquid Zimbabwe UI Structure (ui/app.py ~400 lines target)

**Enhanced Components**:

1. **Page Configuration & Branding**
   ```python
   st.set_page_config(
       page_title="Liquid Zimbabwe 4G Network Optimizer",
       page_icon="ui/assets/logos/cassava-logo-icon.svg",
       layout="wide"
   )

   # Custom CSS for Cassava colors
   st.markdown("""
       <style>
       .main-header { color: #FF6B35; }  /* Cassava orange */
       /* ... */
       </style>
   """, unsafe_allow_html=True)
   ```

2. **Header with Logo**
   ```python
   col1, col2 = st.columns([1, 4])
   with col1:
       st.image("ui/assets/logos/cassava-logo.svg", width=150)
   with col2:
       st.title("Liquid Zimbabwe 4G Network Optimizer")
       st.caption("Intelligent network optimization powered by AI")
   ```

3. **Sidebar** (Enhanced)
   ```python
   with st.sidebar:
       st.header("🔌 Network Connection")

       # Connection controls
       if st.button("Connect to Huawei API"):
           status = connect_huawei_api()
           st.success("Connected to Huawei iMaster MAE")

       # Site selection
       st.header("📍 Site Selection")
       site = st.selectbox("Select Site", get_available_sites())
       cell = st.number_input("Cell ID", min_value=1, value=1)

       # Current KPIs (collapsible)
       with st.expander("📊 Current KPIs"):
           kpis = get_current_kpis(site, cell)
           display_kpi_metrics(kpis)

       # Settings
       with st.expander("⚙️ Settings"):
           monitoring_interval = st.slider("Monitoring Interval (s)", 30, 300, 60)
           validation_duration = st.slider("Validation Duration (s)", 60, 600, 300)
   ```

4. **Main Content Area** (Tabbed Interface)
   ```python
   tab1, tab2, tab3 = st.tabs(["🔍 Analyze", "📈 History", "📖 Help"])

   with tab1:  # Analyze
       st.subheader("Natural Language Query")
       user_query = st.text_area(
           "What would you like to optimize?",
           placeholder="Example: Download speed is low at Bindura Hospital",
           height=100
       )

       col1, col2 = st.columns(2)
       with col1:
           if st.button("🔍 Analyze Network", type="primary"):
               analyze_and_recommend(user_query, site, cell)
       with col2:
           if st.button("🔄 Refresh KPIs"):
               refresh_kpis(site, cell)

       # Results display
       if st.session_state.get("analysis_complete"):
           display_analysis_results()
           display_recommendations()

           if st.button("✅ Apply Recommendations"):
               apply_and_validate()

   with tab2:  # History
       st.subheader("Optimization History")
       history = get_optimization_history(site)
       st.dataframe(history)

       # Visualizations
       st.line_chart(history[["timestamp", "weighted_score_before", "weighted_score_after"]])

   with tab3:  # Help
       st.subheader("How to Use")
       st.markdown("""
       1. **Connect**: Click "Connect to Huawei API" in sidebar
       2. **Select Site**: Choose site and cell ID
       3. **Query**: Describe network issue in natural language
       4. **Analyze**: Click "Analyze Network" for recommendations
       5. **Apply**: Review and apply recommended changes
       6. **Monitor**: Track KPI improvements
       """)
   ```

5. **Result Display Components**
   ```python
   def display_analysis_results():
       st.subheader("📊 Analysis Results")

       # KPI Issues
       issues = st.session_state.kpi_issues
       for issue in issues:
           st.warning(f"⚠️ {format_issue(issue)}")

       # Root Cause
       if st.session_state.root_cause:
           with st.expander("🔍 Root Cause Analysis"):
               st.markdown(st.session_state.root_cause)

       # Current Weighted Score
       st.metric(
           "Current Network Health",
           f"{st.session_state.weighted_score_current:.1f}",
           delta=f"{st.session_state.expected_improvement:+.1f}" if st.session_state.expected_improvement else None
       )

   def display_recommendations():
       st.subheader("💡 Recommendations")

       recommendations = st.session_state.params_proposed
       mml_commands = st.session_state.mml_commands

       for param, change in recommendations.items():
           col1, col2, col3 = st.columns(3)
           with col1:
               st.write(f"**{param}**")
           with col2:
               st.write(f"{change['old']} → {change['new']}")
           with col3:
               st.code(change['mml_command'], language="sql")

       # Risk Assessment
       risk_score = st.session_state.risk_score
       if risk_score <= 2:
           st.success(f"✅ Low Risk (Score: {risk_score}/5)")
       elif risk_score <= 3:
           st.warning(f"⚠️ Medium Risk (Score: {risk_score}/5)")
       else:
           st.error(f"❌ High Risk (Score: {risk_score}/5)")
   ```

6. **Footer with Branding**
   ```python
   st.markdown("---")
   col1, col2, col3 = st.columns([1, 2, 1])
   with col2:
       st.markdown(
           """
           <div style="text-align: center; color: #FF6B35;">
           Powered by Cassava AI | Liquid Zimbabwe 4G Network Optimizer
           </div>
           """,
           unsafe_allow_html=True
       )
   ```

### UI Mapping Summary

| Component | Nvidia | LZ | Change |
|-----------|--------|-----|--------|
| **Title** | "Network Performance Planner" | "Liquid Zimbabwe 4G Network Optimizer" | Branded |
| **Logo** | None | Cassava logo (4 variants) | **NEW** |
| **Colors** | Default Streamlit | Cassava orange (#FF6B35) + custom theme | **NEW** |
| **Network Control** | Start/Stop buttons | Connect/Disconnect API | API-based |
| **Site Selection** | None (single gNodeB) | Site dropdown + cell ID | **NEW** |
| **Query Interface** | Text area + button | Same (enhanced placeholder) | Enhanced |
| **Results Display** | Simple text output | Structured (issues, recommendations, risk) | **NEW** |
| **KPI Display** | None | Sidebar collapsible metrics | **NEW** |
| **History** | None | Tab with history + charts | **NEW** |
| **Help** | None | Tab with usage instructions | **NEW** |
| **Validation Flow** | Buttons appear conditionally | Integrated "Apply" flow | Simplified |
| **Session State** | 5 variables | 10+ variables (enhanced state) | Expanded |
| **Layout** | Single column | Tabs + columns (structured) | Enhanced |
| **Line Count** | ~300 lines | ~400 lines target | +33% |

**Design Principles**:
1. **Simplicity**: Clean, focused interface (~400 lines vs 1,505 in old implementation)
2. **Branding**: Professional Cassava identity
3. **Clarity**: Structured results display (issues, recommendations, risk)
4. **Transparency**: Show MML commands, explain decisions
5. **Safety**: Risk assessment visible, confirm before apply
6. **History**: Track optimizations over time

---

## Configuration Mapping

### Nvidia Configuration (config.yaml)

```yaml
# LLM Configuration
nvidia_api_key: "nvapi-..."
llm_model: "meta/llama-3.1-70b-instruct"
llm_base_url: "https://integrate.api.nvidia.com/v1"
llm_temp: 0
llm_top_p: 0.7
llm_max_tokens: 1024

# NIM Mode (local hosting)
NIM_mode: False
nim_image: "nvcr.io/nim/meta/llama-3.1-70b-instruct:latest"
nim_llm_port: 8000

# BubbleRAN Network Setup
bubbleran_network_setup: "5g-sa-nr-sim"  # or "5g-sa-usrp"

# Parameter Defaults & Ranges
default_p0_nominal_value: -90
p0_nominal_values: [-86, -90, -94, -98]
p0_nominal_WA_weights: [0.6, 0.4]  # DL bitrate, SNR

default_dl_carrierBandwidth_value: 51
dl_carrierBandwidth_values: [24, 51, 106]
dl_carrierBandwidth_WA_weights: [0.6, 0.4]

# (Similar for ul_carrierBandwidth, att_tx, att_rx)

# Time Periods
monitoring_wait_time: 1  # seconds
validation_wait_time: 10  # seconds

# Database Paths
persistent_db_path: "./data/persistent_db"
historical_db_path: "./data/historical_db"
table_name: "kpi_data"
debugging: True
```

### Liquid Zimbabwe Configuration

**1. Main Configuration** (`config/config.yaml`)
```yaml
# NVIDIA API Configuration
nvidia_api_key: "${NVIDIA_API_KEY}"
llm_model: "meta/llama-3.1-70b-instruct"
llm_base_url: "https://integrate.api.nvidia.com/v1"
llm_temp: 0
llm_top_p: 0.7
llm_max_tokens: 1024

# Huawei API Configuration
huawei:
  api_url: "${HUAWEI_API_URL}"
  username: "${HUAWEI_USERNAME}"
  password: "${HUAWEI_PASSWORD}"
  ssl_verify: false  # Self-signed certificate
  timeout: 30
  retry_attempts: 3
  retry_delay: 5

# Database Configuration
database:
  path: "./data/lz_network.db"
  historical_csv: "./data/historical_data.csv"

# Agent Configuration
agents:
  monitoring_interval: 60          # seconds
  validation_duration: 300         # 5 minutes
  max_concurrent_optimizations: 1

# Logging
logging:
  level: "INFO"
  file: "./logs/lz_optimizer.log"
```

**2. KPI Weights Configuration** (`config/kpi_weights.yaml`)
```yaml
# KPI Weighting Configuration
# Tier 1: Foundation (25%)
# Tier 2: Revenue & Experience (50%)
# Tier 3: Efficiency (25%)

static_weights:
  network_access_success: 0.25   # TIER 1 - Critical foundation
  download_speed: 0.20           # TIER 2 - Revenue driver
  download_quality: 0.15         # TIER 2 - User experience
  upload_speed: 0.15             # TIER 2 - Important
  upload_quality: 0.10           # TIER 2 - Background services
  control_channel_load: 0.10     # TIER 3 - Network efficiency
  feedback_channel_load: 0.05    # TIER 3 - Fine-tuning

# KPI Thresholds
thresholds:
  network_access_success:
    normal_min: 95.0
    critical: 90.0
    higher_is_better: true

  download_speed:
    normal_min: 5000.0  # kbit/s
    critical: 2000.0
    higher_is_better: true

  download_quality:  # DL IBLER
    normal_max: 15.0
    critical: 20.0
    higher_is_better: false  # Lower IBLER is better

  upload_speed:
    normal_min: 1000.0
    critical: 500.0
    higher_is_better: true

  upload_quality:  # UL IBLER
    normal_max: 10.0
    critical: 15.0
    higher_is_better: false

  control_channel_load:
    normal_max: 70.0
    critical: 85.0
    higher_is_better: false

  feedback_channel_load:
    normal_max: 10.0
    critical: 15.0
    higher_is_better: false
```

**3. Environment Template** (`.env.template`)
```bash
# Liquid Zimbabwe 4G Network Optimizer - Environment Configuration
# Copy this to .env and fill in your credentials

# NVIDIA API (for LLM)
NVIDIA_API_KEY=nvapi-YOUR_KEY_HERE

# Huawei iMaster MAE API
HUAWEI_API_URL=https://41.174.191.214:31127
HUAWEI_USERNAME=your_username
HUAWEI_PASSWORD=your_password
```

### Configuration Mapping Summary

| Aspect | Nvidia | LZ | Change |
|--------|--------|-----|--------|
| **Structure** | Single file (config.yaml) | 3 files (config.yaml, kpi_weights.yaml, .env) | Split concerns |
| **Credentials** | Inline in config.yaml | Environment variables (.env) | **Security improvement** |
| **Network Setup** | BubbleRAN mode selection | Huawei API connection params | API-based |
| **Parameters** | Default values + ranges + weights (per param) | Defined in domain/parameters.py | Separated domain knowledge |
| **KPI Weights** | Per-parameter 2-factor weights | Global 7-KPI 3-tier weights | **NEW weighting system** |
| **KPI Thresholds** | None (implicit) | Explicit normal/critical thresholds | **NEW** |
| **Timings** | monitoring_wait_time, validation_wait_time | monitoring_interval, validation_duration | Renamed, longer durations |
| **Database** | 2 paths (persistent + historical) | 1 path (unified DB) | Simplified |
| **Logging** | debugging boolean | Structured logging config | **NEW** |

---

## Implementation Checklist

### Phase 2: Core Agent Implementation (Using This Mapping)

**Day 1-2: Foundation**
- [ ] Copy domain knowledge from rebuild-assets/ to domain/
- [ ] Create config/config.yaml (adapt from Nvidia)
- [ ] Create config/kpi_weights.yaml (3-tier weights)
- [ ] Create .env.template
- [ ] Create database schema (lz_network.db with 3 tables)
- [ ] Import historical_data.csv

**Day 3-4: Huawei Integration**
- [ ] Create tools/huawei_tools.py (5 tools)
  - [ ] connect_huawei_api
  - [ ] query_huawei_parameter
  - [ ] execute_mml_command
  - [ ] collect_live_kpis
  - [ ] check_api_status
- [ ] Copy huawei_api_client.py from rebuild-assets/api/
- [ ] Test API connectivity (authentication, MML query)

**Day 5: SQL & Calculation Tools**
- [ ] Create tools/sql_tools.py (2 tools)
  - [ ] execute_lz_kpi_sql
  - [ ] execute_historical_sql (adapt from Nvidia)
- [ ] Create tools/calculation_tools.py (1 tool)
  - [ ] calc_weighted_kpi_score (3-tier weighted)

**Day 6: Validation Tools**
- [ ] Create tools/validation_tools.py (2 tools)
  - [ ] validate_parameter_range
  - [ ] calculate_risk_score

**Day 7-8: Agents**
- [ ] Create agents/config_agent.py (enhanced from Nvidia)
- [ ] Create agents/validation_agent.py (enhanced from Nvidia)
- [ ] Create agents/monitoring_agent.py (enhanced from Nvidia)
- [ ] Create agents/kpi_analytics_agent.py (NEW)
- [ ] Create agents/network_connector_agent.py (NEW)
- [ ] Create agents/mml_executor_agent.py (NEW)
- [ ] Create agents/workflow.py (LangGraph orchestration)

**Day 9: State Management**
- [ ] Define State TypedDict (enhanced structure)
- [ ] Test state flow through agents
- [ ] Implement Command pattern for routing

**Checkpoint #2**: Demo agent functionality with historical data

---

## Appendix: Key Differences Summary

### Technology Stack
| Component | Nvidia | LZ |
|-----------|--------|-----|
| Network | BubbleRAN 5G O-RAN (Docker) | Huawei 4G iMaster MAE (API) |
| Parameters | File-based (gnb.conf) | MML commands (HTTPS API) |
| KPIs | xApp database (Docker) | Huawei API + SQLite |
| Deployment | Docker Compose (multi-container) | Docker (single container) |

### Architecture
| Component | Nvidia | LZ |
|-----------|--------|-----|
| Agents | 3 (Config, Valid, Monitor) | 6 (3 core + 3 extensions) |
| Tools | 4 (@tool functions) | 10 (@tool functions) |
| State Fields | 7 fields | 15+ fields (enhanced) |
| Prompts | Generic | Few-shot + domain knowledge |
| Database | 2 SQLite DBs | 1 SQLite DB (3 tables) |

### KPI System
| Aspect | Nvidia | LZ |
|--------|--------|-----|
| Number | Variable (6) | Fixed (7) |
| Weighting | Equal or 2-factor | 3-tier (25/50/25) |
| Thresholds | None | Explicit (normal/critical) |
| Scoring | Simple average | Weighted + normalized |
| Business Alignment | Technical | Technical + business |

### Complexity
| Metric | Nvidia | LZ Target |
|--------|--------|-----------|
| Total Files | ~20 | ~30 (+50%) |
| Agent Files | 1 (1,710 lines) | 6 files (~200 lines each) |
| Tool Files | 1 (305 lines) | 4 files (~100 lines each) |
| UI Lines | ~300 | ~400 (+33%) |
| Database Tables | 2 | 3 |
| **Complexity** | Baseline | **+40%** (controlled) |

---

**Document Status**: Complete
**Next Step**: Begin Phase 2 implementation using this mapping
**Reference**: Use alongside docs/PROMPT_INTEGRATION_PLAN.md for prompt design
