# Liquid Zimbabwe 4G Network Optimizer - Project Structure Design

**Document Version**: 1.0
**Date**: 2025-10-30
**Phase**: Phase 2 - Implementation
**Purpose**: Complete directory structure and file organization for /lz-network-optimizer/ rebuild
**Target**: ~30 files (+50% vs Nvidia's ~20), +40% complexity
**Base**: Nvidia Telco Network Configuration Blueprint → Liquid Zimbabwe 4G iMaster MAE

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Directory Tree](#directory-tree)
3. [File Organization & Purpose](#file-organization--purpose)
4. [Module Organization](#module-organization)
5. [Dependencies & Import Structure](#dependencies--import-structure)
6. [File Size Estimates](#file-size-estimates)
7. [Phase 2 Implementation Order](#phase-2-implementation-order)
8. [File Templates & Skeleton Code](#file-templates--skeleton-code)
9. [Configuration Management](#configuration-management)
10. [Testing Strategy](#testing-strategy)

---

## Executive Summary

### Project Context

**Nvidia Blueprint**:
- 3 agents (Configuration, Validation, Monitoring)
- 4 tools in single `tools.py` file
- 5 BubbleRAN 5G parameters
- Single Streamlit UI
- ~1,700 lines agents + 300 lines tools + 600 lines utils

**Liquid Zimbabwe Target**:
- 6 agents (3 core + 3 extensions)
- 8 tools across 4 specialized files
- 5 Huawei 4G parameters
- Cassava-branded Streamlit UI
- ~2,400 lines agents + 600 lines tools
- Enhanced domain knowledge system
- Unified database with optimization history

### Key Design Principles

1. **Modularity**: Split monolithic files by responsibility (agents, tools, domain)
2. **Scalability**: Support future addition of more agents/tools
3. **Maintainability**: Clear naming, consistent patterns, comprehensive documentation
4. **Testability**: Each module independently testable with fixtures
5. **Configuration-Driven**: Domain knowledge externalized to config files
6. **Safety-First**: Validation, rollback, and audit trails built-in

### File Organization Summary

```
lz-network-optimizer/
├── agents/              (7 files)   - 6 agents + orchestration
├── tools/               (4 files)   - Specialized tool groups
├── prompts/             (3 files)   - System, few-shot, context
├── domain/              (4 files)   - Parameters, KPIs, rules, MML
├── network/             (2 files)   - Huawei client + KPI collection
├── ui/                  (3+ files)  - Streamlit app + assets
├── config/              (3 files)   - YAML config + environment
├── data/, tests/, scripts/, docs/
```

**Total: ~30 files (excluding test fixtures and assets)**

---

## Directory Tree

```
lz-network-optimizer/
│
├── agents/                                 # Agent implementations (7 files)
│   ├── __init__.py
│   ├── config_agent.py                    # Configuration recommendation agent
│   ├── validation_agent.py                # Parameter change validation
│   ├── monitoring_agent.py                # KPI monitoring & alerting
│   ├── kpi_analytics_agent.py             # Root cause & correlation analysis
│   ├── network_connector_agent.py         # Huawei API lifecycle management
│   ├── mml_executor_agent.py              # Safe MML command execution
│   └── workflow.py                        # LangGraph workflow orchestration
│
├── tools/                                  # Specialized tools (4 files, 10 tools)
│   ├── __init__.py
│   ├── huawei_tools.py                    # API connection & MML execution (5 tools)
│   ├── sql_tools.py                       # Database query operations (2 tools)
│   ├── calculation_tools.py               # KPI scoring & analytics (2 tools)
│   └── validation_tools.py                # Parameter validation & risk (2 tools)
│
├── prompts/                                # Prompt templates & builders (3 files)
│   ├── __init__.py
│   ├── system_prompts.py                  # Core system prompts for agents
│   ├── few_shot_examples.py               # Optimization examples & context
│   └── context_builders.py                # Dynamic prompt construction
│
├── domain/                                 # Domain knowledge (4 files)
│   ├── __init__.py
│   ├── parameters.py                      # 5 Huawei parameters + ranges
│   ├── kpis.py                            # 7 KPIs + weighting tiers
│   ├── optimization_rules.py              # 10 optimization scenarios
│   └── mml_commands.py                    # MML command templates
│
├── network/                                # Network integration (2 files)
│   ├── __init__.py
│   ├── huawei_client.py                   # Huawei API client (auth, retry, rate limit)
│   └── kpi_collector.py                   # Live KPI aggregation
│
├── ui/                                     # Streamlit UI (~400 lines)
│   ├── __init__.py
│   ├── app.py                             # Main Streamlit application
│   ├── pages/                             # Multi-page app structure
│   │   ├── __init__.py
│   │   ├── 1_dashboard.py                 # KPI monitoring dashboard
│   │   ├── 2_optimization.py              # Recommendation engine UI
│   │   ├── 3_validation.py                # Validation test UI
│   │   ├── 4_analytics.py                 # Analytics & insights
│   │   └── 5_settings.py                  # Connection & parameter settings
│   ├── components/                        # Reusable UI components
│   │   ├── __init__.py
│   │   ├── metrics_display.py             # KPI metric cards
│   │   ├── parameter_form.py              # Parameter input forms
│   │   └── alert_handler.py               # Alert & notification display
│   └── assets/                            # UI assets
│       ├── logos/                         # Cassava branding
│       ├── images/                        # Diagrams and charts
│       └── styles/                        # Custom CSS
│
├── config/                                 # Configuration (3 files)
│   ├── config.yaml                        # Main application config
│   ├── kpi_weights.yaml                   # 3-tier KPI weights
│   └── .env.template                      # Environment variables template
│
├── data/                                   # Data persistence (3 items)
│   ├── lz_network.db                      # SQLite unified database
│   ├── historical_data.csv                # Historical KPI archive
│   └── migrations/                        # Database schema migrations
│
├── tests/                                  # Test suite (6+ files)
│   ├── __init__.py
│   ├── conftest.py                        # Pytest fixtures & config
│   ├── test_agents/                       # Agent tests
│   ├── test_tools/                        # Tool tests
│   ├── test_domain/                       # Domain tests
│   ├── test_network/                      # Network tests
│   ├── fixtures/                          # Mock data and test DB
│   └── integration/                       # End-to-end tests
│
├── scripts/                                # Automation scripts (3+ files)
│   ├── setup.py                           # Project setup & dependencies
│   ├── init_database.py                   # Database initialization
│   └── deploy.sh                          # Docker deployment script
│
├── docs/                                   # Documentation (existing)
│   └── PROJECT_STRUCTURE.md               # This file
│
├── main.py                                 # Application entry point
├── requirements.txt                        # Python dependencies
├── Dockerfile                              # Container definition
├── docker-compose.yaml                     # Multi-container orchestration
└── .env.example                            # Environment template

```

---

## File Organization & Purpose

### AGENTS/ (7 files, ~2,400 lines total)

#### agents/config_agent.py (~350 lines)
**Configuration Agent** - Analyzes KPIs and recommends parameter changes

- **Purpose**: Main recommendation engine
- **Replaces/Enhances**: Nvidia agents.py ConfigurationAgent (lines 531-810)
- **Key Features**:
  - Few-shot prompting (3-5 examples from domain knowledge)
  - Domain knowledge injection (parameters, KPIs, optimization rules)
  - Weighted KPI analysis
  - MML command generation recommendations
- **Main Methods**:
  - `analyze_kpi_issue(issue_description, current_kpis)`
  - `generate_recommendations(analysis_results)`
  - `format_mml_commands(recommendations)`
- **Tools Used**: execute_historical_sql, execute_lz_kpi_sql, calc_weighted_kpi_score, query_huawei_parameter
- **Dependencies**: tools/ (all), domain/ (all), prompts/

#### agents/validation_agent.py (~450 lines)
**Validation Agent** - Tests recommended changes on live network

- **Purpose**: Safe change testing and validation
- **Replaces/Enhances**: Nvidia agents.py ValidationAgent (lines 812-1078)
- **Key Features**:
  - Pre-validation safety checks (parameter ranges)
  - MML command execution on live network
  - Before/after weighted KPI comparison
  - Automatic rollback on degradation
  - Audit trail logging
- **Main Methods**:
  - `validate_changes(parameter_changes, mml_commands)`
  - `perform_baseline_collection(duration=60)`
  - `execute_and_monitor(mml_command, monitoring_duration)`
  - `calculate_improvement(baseline_kpis, post_change_kpis)`
  - `rollback_changes(previous_mml_command)`
- **Tools Used**: validate_parameter_range, calculate_risk_score, execute_mml_command, collect_live_kpis, calc_weighted_kpi_score
- **Dependencies**: tools/ (all), domain/parameters, optimization_rules

#### agents/monitoring_agent.py (~400 lines)
**Monitoring Agent** - Continuous KPI monitoring and alerting

- **Purpose**: Real-time KPI monitoring and degradation detection
- **Replaces/Enhances**: Nvidia agents.py MonitoringAgent (lines 106-529)
- **Key Features**:
  - 7 weighted KPIs (vs 5 unweighted in Nvidia)
  - Threshold-based alerts (normal, warning, critical)
  - Trend analysis and degradation detection
  - Automatic escalation to Config Agent
  - Multi-site/cell support
- **Main Methods**:
  - `start_monitoring(site_name, cell_id, interval=60)`
  - `collect_and_analyze_kpis(site_name, cell_id)`
  - `check_thresholds(kpis, thresholds)`
  - `detect_degradation(kpi_history)`
  - `escalate_to_config_agent(issue)`
- **Tools Used**: execute_lz_kpi_sql, collect_live_kpis, calc_weighted_kpi_score, detect_degradation
- **Dependencies**: tools/, domain/kpis, prompts/

#### agents/kpi_analytics_agent.py (~350 lines)
**KPI Analytics Agent** - Deep analysis and root cause identification (NEW)

- **Purpose**: Historical pattern analysis and anomaly detection
- **Key Features**:
  - Historical pattern analysis
  - Parameter-KPI correlation analysis
  - Root cause identification
  - Anomaly detection
  - Trend forecasting
- **Main Methods**:
  - `analyze_degradation(kpi_name, site_name, duration_hours)`
  - `identify_root_cause(kpi_issue, context)`
  - `correlate_parameters_to_kpis(parameter_changes)`
  - `detect_anomalies(kpi_data)`
  - `forecast_trends(kpi_history, forecast_hours)`
- **Tools Used**: execute_historical_sql, execute_lz_kpi_sql, calc_weighted_kpi_score, identify_root_cause
- **Dependencies**: tools/, domain/, scipy/numpy for statistical analysis

#### agents/network_connector_agent.py (~250 lines)
**Network Connector Agent** - Manage Huawei API lifecycle (NEW)

- **Purpose**: Connection/disconnection and network element discovery
- **Key Features**:
  - OAuth2 authentication
  - Connection state management
  - Network element discovery (sites, cells)
  - Connection health monitoring
  - Automatic reconnection on failure
- **Main Methods**:
  - `connect(credentials)`
  - `disconnect()`
  - `check_status()`
  - `discover_network_elements()`
  - `discover_sites()`
  - `discover_cells(site_name)`
- **Tools Used**: connect_huawei_api, disconnect_huawei_api, check_api_status
- **Dependencies**: network/huawei_client, tools/huawei_tools

#### agents/mml_executor_agent.py (~300 lines)
**MML Executor Agent** - Safe command execution with validation (NEW)

- **Purpose**: Enhanced MML command execution safety
- **Key Features**:
  - MML syntax validation
  - Pre/post execution checks
  - Automatic retry on transient failures
  - Response parsing and validation
  - Rollback capability
  - Execution audit trail
- **Main Methods**:
  - `validate_mml_syntax(mml_command)`
  - `execute_mml_command(mml_command, site_name)`
  - `parse_mml_response(response)`
  - `retry_on_failure(mml_command, max_retries=3)`
  - `verify_parameter_change(param_name, expected_value)`
- **Tools Used**: execute_mml_command, parse_mml_response, validate_parameter_range
- **Dependencies**: tools/, domain/mml_commands, network/huawei_client

#### agents/workflow.py (~300 lines)
**Orchestration Workflow** - Coordinate agent interactions (NEW)

- **Purpose**: LangGraph workflow orchestration
- **Key Features**:
  - Multi-agent workflow graph
  - State management between agents
  - Conditional routing (based on results)
  - Error handling and recovery
  - Execution history tracking
- **Main Structure**:
  - Input: User query + context (site, cell)
  - Network Connector: Check/establish connection
  - Monitoring: Collect current KPIs
  - Config Agent: Generate recommendations
  - Validation: Test recommendations
  - MML Executor: Execute approved changes
  - Output: Results summary + audit trail
- **Dependencies**: langgraph, all agents, all tools

---

### TOOLS/ (4 files, 10 tools, ~780 lines total)

#### tools/huawei_tools.py (~280 lines)
**Huawei API Tools** - Direct API integration

Tools:
1. `connect_huawei_api(config)` - OAuth2 authentication
2. `query_huawei_parameter(param_name, site_name, cell_id)` - Query current values via LST
3. `execute_mml_command(mml_command, site_name)` - Execute MOD commands
4. `collect_live_kpis(site_name, cell_id, duration)` - Aggregate KPI data
5. `check_api_status()` - Health check for API connection

**Dependencies**: network/huawei_client, requests, logging

#### tools/sql_tools.py (~150 lines)
**SQL Database Tools** - Database query operations

Tools:
1. `execute_lz_kpi_sql(sql_query)` - Query KPI data (live + historical)
2. `execute_historical_sql(sql_query)` - Query optimization history

**Dependencies**: sqlite3, pandas, logging

#### tools/calculation_tools.py (~200 lines)
**Calculation Tools** - KPI scoring and analytics

Tools:
1. `calc_weighted_kpi_score(kpis, weights)` - Normalized weighted score (0-100)
2. `detect_degradation(kpi_history, threshold_percent)` - Trend-based degradation detection

**Dependencies**: numpy, scipy, domain/kpis, logging

#### tools/validation_tools.py (~150 lines)
**Validation Tools** - Parameter safety validation (NEW)

Tools:
1. `validate_parameter_range(param_name, new_value)` - Range and dependency validation
2. `calculate_risk_score(param_changes, current_state)` - Risk assessment (1-5 scale)

**Dependencies**: domain/parameters, tools/sql_tools, logging

---

### PROMPTS/ (3 files, ~400 lines total)

#### prompts/system_prompts.py (~180 lines)
**System Prompts** - Agent-specific system prompts

Functions:
- `get_config_agent_system_prompt(domain_knowledge)` - Configuration agent prompt
- `get_validation_agent_system_prompt()` - Validation agent prompt
- `get_monitoring_agent_system_prompt()` - Monitoring agent prompt
- `get_kpi_analytics_system_prompt()` - KPI analytics prompt
- `get_network_connector_system_prompt()` - Network connector prompt
- `get_mml_executor_system_prompt()` - MML executor prompt

**Key Content**:
- Agent role definition
- Parameter specifications (5 Huawei parameters)
- KPI definitions (7 metrics)
- Optimization rules (10 scenarios)
- Output format specifications

#### prompts/few_shot_examples.py (~150 lines)
**Few-Shot Examples** - Optimization examples for agent learning

Examples Included (3-5 per agent):
- "Low Download Speed" optimization (Bindura Hospital case)
- "High Access Failure Rate" correction
- "Poor Call Quality" remediation
- "Network Congestion" handling
- "MML Command Execution" safety patterns

Example Format:
```python
{
  "scenario": "Low download speed at peak hours",
  "site": "MSH-0112-Bindura Hospital",
  "initial_kpis": {...},
  "root_cause": "Reference signal power too low",
  "recommended_change": {"reference_signal_power_pdschcfg": -150},
  "expected_improvement": {"download_speed": "+35%", "quality": "+12%"},
  "validation_result": "success",
  "lessons_learned": "..."
}
```

#### prompts/context_builders.py (~70 lines)
**Dynamic Context Builders** - Runtime prompt assembly

Functions:
- `build_config_agent_prompt(domain_knowledge, few_shot, current_state)` - Build full prompt
- `build_validation_agent_prompt(parameter_changes, baseline_kpis)` - Validation context
- `build_monitoring_agent_prompt(alert_info, historical_context)` - Monitoring context
- `inject_site_context(base_prompt, site_name, cell_id)` - Add site-specific info
- `inject_kpi_context(base_prompt, current_kpis)` - Add KPI context
- `select_relevant_examples(scenario_type, count=3)` - Dynamic example selection

---

### DOMAIN/ (4 files, ~710 lines total)

#### domain/parameters.py (~200 lines)
**Huawei 4G Parameters** - Parameter definitions and safe ranges

5 Parameters:
1. `reference_signal_power_pdschcfg` - PDSCH reference signal (-600 to 500, 0.1 dBm)
2. `tx_power_control` - Transmit power control
3. `dl_carrier_bandwidth` - Downlink bandwidth
4. `ul_carrier_bandwidth` - Uplink bandwidth
5. `antenna_tilt_electrical` - Antenna electrical tilt

Per Parameter:
- Name, MML name, type, min/max range, default value
- Impact level (LOW/MEDIUM/HIGH)
- Affected KPIs
- Parameter correlations
- MML command template
- Description and optimization tips

Functions:
- `get_parameter(param_name)` - Retrieve parameter definition
- `get_all_parameters()` - Get all 5 parameters
- `validate_parameter_value(param_name, value)` - Validate against range
- `get_parameter_correlation(param1, param2)` - Check dependencies

#### domain/kpis.py (~180 lines)
**KPI Definitions & Weighting** - 7 KPIs with 3-tier system

7 KPIs:
- **Tier 1 - Foundation (25% total)**:
  1. `network_access_success` (%) - Higher is better (weight: 0.125)
  2. `call_completion_rate` (%) - Higher is better (weight: 0.125)
- **Tier 2 - Revenue (50% total)**:
  3. `download_speed` (Mbps) - Higher is better (weight: 0.15)
  4. `upload_speed` (Mbps) - Higher is better (weight: 0.10)
  5. `active_users` (count) - Higher is better (weight: 0.15)
  6. `network_throughput` (Mbps) - Higher is better (weight: 0.10)
- **Tier 3 - Experience (25% total)**:
  7. `download_quality` (IBLER %) - Lower is better (weight: 0.15)
  8. `call_quality` (MOS) - Higher is better (weight: 0.10)

Per KPI:
- Name, display name, unit, tier, weight
- Min/max/target values
- Alert thresholds (normal, warning, critical)
- Higher/lower is better flag
- Calculation method

Functions:
- `get_kpi(kpi_name)` - Retrieve KPI definition
- `get_all_kpis()` - Get all 7 KPIs
- `get_kpi_weight(kpi_name)` - Get weight in 3-tier system
- `get_kpi_tier(kpi_name)` - Return tier (1/2/3)
- `normalize_kpi_value(kpi_name, value)` - Normalize to 0-100 scale
- `get_alert_level(kpi_name, value)` - Return alert level (normal/warning/critical)

#### domain/optimization_rules.py (~180 lines)
**Optimization Rules** - 10 problem-solution mappings

10 Rules:
1. Low Download Speed
2. Low Upload Speed
3. High Access Failure Rate
4. Poor Call Quality
5. High Network Congestion
6. Low Cell Edge Coverage
7. Interference Mitigation
8. Antenna Optimization
9. Load Balancing
10. Power Efficiency Optimization

Per Rule:
- ID, name, problem description
- Trigger KPI and threshold
- Root causes
- Recommended parameter changes (with direction, magnitude, step size)
- Expected KPI improvement percentages
- Risk level (LOW/MEDIUM/HIGH)
- Validation duration
- Historical success rate
- Applicable sites (all or specific)
- Implementation notes

Functions:
- `get_rule(rule_id)` - Retrieve rule by ID
- `get_all_rules()` - Get all 10 rules
- `get_applicable_rules(kpi_issue)` - Get rules for KPI issue
- `assess_rule_applicability(rule, current_state)` - Check if applicable
- `estimate_success_probability(rule, current_state)` - Success prediction

#### domain/mml_commands.py (~150 lines)
**MML Command Templates** - Command builders and parsers

Features:
- MML command templates for all parameters
- Command validation and formatting
- Response parsing patterns
- Error handling for MML

Per Template:
- Parameter name
- Operation (MOD, LST, QRY)
- MML name (Huawei-specific)
- Template with placeholders
- Query template
- Response regex pattern
- Error patterns (syntax, range, etc.)

Functions:
- `build_mml_command(param_name, value, cell_id, site_name)` - Build MOD command
- `build_query_command(param_name, cell_id, site_name)` - Build LST command
- `validate_mml_syntax(mml_command)` - Check syntax
- `parse_mml_response(response, param_name)` - Extract value from response
- `get_error_message(response)` - Parse error from response
- `format_mml_batch(param_changes, cell_id)` - Build batch commands

---

### NETWORK/ (2 files, ~400 lines total)

#### network/huawei_client.py (~250 lines)
**Huawei API Client** - HTTPS API integration with OAuth2

Class: `HuaweiAPIClient`

Methods:
- `__init__(base_url, username, password, verify_ssl=False)`
- `authenticate()` - OAuth2 token acquisition
- `refresh_token()` - Token refresh
- `is_authenticated()` - Check auth status
- `execute_mml_command(command, site_name)` - Execute MML
- `query_parameter(param_mml_name, cell_info)` - Query parameter value
- `get_kpi_data(site_name, cell_id, duration=60)` - Fetch KPI data
- `discover_sites()` - List available sites
- `discover_cells(site_name)` - List cells for site
- `health_check()` - API health status
- `close()` - Cleanup connection

Features:
- SSL handling (self-signed certs)
- Request/response logging
- Retry logic with exponential backoff
- Rate limiting
- Connection pooling
- Error handling and recovery

#### network/kpi_collector.py (~150 lines)
**KPI Collector** - Live KPI data aggregation

Class: `KPICollector`

Methods:
- `__init__(huawei_client)`
- `collect_kpis(site_name, cell_id, duration=60)` - Collect single cell
- `collect_multi_site_kpis(site_names, duration=60)` - Multiple sites
- `collect_multi_cell_kpis(site_name, cell_ids, duration=60)` - Multiple cells
- `aggregate_kpis(kpi_data_list)` - Average multiple collections
- `normalize_to_lz_kpis(raw_huawei_kpis)` - Map to LZ KPI definitions
- `validate_kpi_data(kpi_dict)` - Check completeness

Features:
- Time-series aggregation
- Handle missing/incomplete data
- Normalization to LZ KPI definitions
- Data validation

---

### UI/ (750+ lines across 9 files)

#### ui/app.py (~150 lines)
**Main Streamlit Application**

- Multi-page navigation (Streamlit 1.28+ st.navigation)
- Session state management
- Cassava branding and custom styling
- Error handling and user feedback
- Real-time KPI updates
- Integration with workflow

Structure:
- Header with Cassava logo
- Sidebar: Connection status, site selector, settings
- Main area: Route to selected page
- Footer: Version, status, help

#### ui/pages/1_dashboard.py (~120 lines)
**KPI Monitoring Dashboard**

Features:
- Real-time KPI display with metric cards
- Threshold indicators (normal/warning/critical)
- Historical trend charts (sparklines)
- Alert list with escalation controls
- Site/cell selection dropdown
- Auto-refresh button

Layout:
- Top: Site/cell selector, refresh interval
- Middle: 7 KPI metric cards in 3 rows
- Bottom: Detailed charts, trend analysis, alerts

#### ui/pages/2_optimization.py (~100 lines)
**Optimization Recommendation Interface**

Features:
- Text input for KPI issue description
- Root cause analysis display
- Recommendations with explanations
- MML command preview
- Manual/automatic validation toggle
- Accept/Reject buttons

#### ui/pages/3_validation.py (~80 lines)
**Change Validation Testing**

Features:
- Approve/reject recommendation
- Real-time monitoring during validation (60-300 seconds)
- Before/after metrics comparison
- Commit/Rollback decision UI
- Execution progress bar

#### ui/pages/4_analytics.py (~80 lines)
**Deep Analytics & Insights**

Features:
- Root cause analysis visualization
- Parameter-KPI correlation heatmap
- Historical optimization patterns
- Anomaly detection results
- Trend forecasting charts

#### ui/pages/5_settings.py (~70 lines)
**Settings & Configuration**

Features:
- Huawei API connection settings
- Test connection button
- Site/cell discovery from API
- Alert threshold configuration
- Database status and backup
- Log viewer

#### ui/components/metrics_display.py (~50 lines)
**KPI Metric Cards** - Reusable metric display component

#### ui/components/parameter_form.py (~60 lines)
**Parameter Input Form** - Reusable parameter form with validation

#### ui/components/alert_handler.py (~40 lines)
**Alert Display** - Reusable alert and notification component

---

### CONFIG/ (3 files, ~155 lines total)

#### config/config.yaml (~80 lines)
**Main Application Configuration**

Sections:
- `huawei_api`: Base URL, username, password, SSL settings, timeouts
- `database`: Database path, backups, retention
- `monitoring`: Collection intervals, alert thresholds
- `validation`: Baseline duration, post-change duration, thresholds
- `ui`: Theme, page title, default site, refresh interval
- `logging`: Level, format, file path, rotation

#### config/kpi_weights.yaml (~60 lines)
**KPI Weighting System**

Structure:
- `tier_1_foundation` (25% total)
  - network_access_success (0.125)
  - call_completion_rate (0.125)
- `tier_2_revenue` (50% total)
  - download_speed (0.15)
  - upload_speed (0.10)
  - active_users (0.15)
  - network_throughput (0.10)
- `tier_3_experience` (25% total)
  - download_quality (0.15)
  - call_quality (0.10)

Per KPI:
- Weight, unit, target, min, warning, critical thresholds

#### config/.env.template (~15 lines)
**Environment Variables Template**

Variables:
- HUAWEI_BASE_URL
- HUAWEI_USERNAME
- HUAWEI_PASSWORD
- DATABASE_PATH
- LOG_LEVEL
- DEBUG_MODE
- STREAMLIT_SERVER_PORT

---

### DATA/ (3+ items)

#### data/lz_network.db (SQLite)
**Unified Database**

3 Main Tables:

1. **kpi_data** - Time-series KPI data
   - timestamp, site_name, cell_id
   - 7 KPI columns (network_access_success, download_speed, etc.)

2. **optimization_history** - Past optimizations
   - timestamp, site_name, cell_id
   - kpi_issue, recommended_changes, mml_commands
   - baseline_kpis, post_change_kpis, weighted_improvement
   - success, rollback_reason, executed_by

3. **network_elements** - Site and cell inventory
   - site_name (UNIQUE), site_id, region
   - cells (JSON array with cell_id, cell_name)

#### data/historical_data.csv
**Historical KPI Archive**

- Columns: timestamp, site_name, cell_id, 7 KPI columns
- Updated daily, retained for 12 months
- Used for trend analysis and historical pattern matching

#### data/migrations/
**Database Schema Migrations**

- `001_initial_schema.py` - Create initial tables
- `002_optimization_history.py` - Add optimization tracking

---

### TESTS/ (800+ lines across 8+ files)

#### tests/conftest.py (~100 lines)
**Pytest Configuration and Fixtures**

Fixtures:
- `mock_huawei_client` - Mocked Huawei API client
- `sample_kpi_data` - Sample KPI dictionary
- `temp_database` - Temporary test database
- `llm_instance` - Fake LLM for testing agents
- `sample_mml_responses` - Mock MML responses

#### tests/test_agents/test_config_agent.py (~150 lines)
- test_analyze_kpi_issue()
- test_generate_recommendations()
- test_few_shot_prompting()

#### tests/test_agents/test_validation_agent.py (~150 lines)
- test_validate_parameter_range()
- test_baseline_collection()
- test_execute_and_rollback()

#### tests/test_tools/test_huawei_tools.py (~100 lines)
- test_connect_huawei_api()
- test_query_huawei_parameter()
- test_execute_mml_command()
- test_error_handling()

#### tests/test_domain/test_parameters.py (~80 lines)
- test_parameter_validation()
- test_parameter_ranges()
- test_parameter_correlation()

#### tests/test_domain/test_kpis.py (~80 lines)
- test_kpi_normalization()
- test_weighted_scoring()
- test_alert_thresholds()

#### tests/test_integration/test_end_to_end.py (~150 lines)
- test_full_optimization_workflow()
- test_monitoring_and_escalation()
- test_validation_and_rollback()

#### tests/integration/test_api_connectivity.py (~100 lines)
- test_real_api_connection() (if API available)
- test_mml_command_execution()
- test_kpi_collection()

---

### SCRIPTS/ (200+ lines)

#### scripts/setup.py
**Project Setup** - Install dependencies and initialize

#### scripts/init_database.py
**Database Initialization** - Create schema and load seed data

#### scripts/deploy.sh
**Docker Deployment** - Build and run containers

#### scripts/run_tests.sh
**Test Runner** - Execute tests with coverage reporting

#### scripts/reset_database.py
**Database Reset** - Development utility to clear data

---

## Module Organization

### Import Hierarchy

```
ui/app.py (top-level user interface)
    ↓
agents/workflow.py (orchestration)
    ↓
agents/*.py (6 specialized agents)
    ↓
tools/*.py (4 tool modules)
    ├─ huawei_tools.py
    │   └─ network/huawei_client.py
    ├─ sql_tools.py
    │   └─ data/lz_network.db
    ├─ calculation_tools.py
    │   └─ domain/kpis.py
    └─ validation_tools.py
        └─ domain/parameters.py
    ↓
prompts/*.py (prompt builders)
    └─ domain/*.py (domain knowledge)
    ↓
domain/*.py (core knowledge)
    ├─ parameters.py
    ├─ kpis.py
    ├─ optimization_rules.py
    └─ mml_commands.py
    ↓
network/*.py (API integration)
    ├─ huawei_client.py
    └─ kpi_collector.py
    ↓
config/*.yaml (external configuration)
```

### Agent Responsibilities Matrix

| Agent | Input | Output | Key Tools | Dependencies |
|-------|-------|--------|-----------|--------------|
| Config | Query + KPIs | Recommendations + MML | hist_sql, live_kpis, scoring | domain/ |
| Validation | Changes + MML | Success/Failure + metrics | mml_exec, kpi_collect, scoring | domain/ |
| Monitoring | Site + Cell | Alerts + escalation | live_kpis, sql, scoring | domain/ |
| KPI Analytics | Issue + Duration | Root cause + patterns | hist_sql, live_sql, scoring | domain/ |
| Network Connector | Credentials | Connection + inventory | huawei_connect, status | network/ |
| MML Executor | Command + Site | Execution result | mml_exec, parsing, validation | domain/ |

---

## File Size Estimates

| Module | File | Lines | Type |
|--------|------|-------|------|
| agents | config_agent.py | 350 | Agent |
| | validation_agent.py | 450 | Agent |
| | monitoring_agent.py | 400 | Agent |
| | kpi_analytics_agent.py | 350 | Agent |
| | network_connector_agent.py | 250 | Agent |
| | mml_executor_agent.py | 300 | Agent |
| | workflow.py | 300 | Orchestration |
| **agents** | **total** | **2,400** | |
| tools | huawei_tools.py | 280 | Tools |
| | sql_tools.py | 150 | Tools |
| | calculation_tools.py | 200 | Tools |
| | validation_tools.py | 150 | Tools |
| **tools** | **total** | **780** | |
| prompts | system_prompts.py | 180 | Prompts |
| | few_shot_examples.py | 150 | Examples |
| | context_builders.py | 70 | Builders |
| **prompts** | **total** | **400** | |
| domain | parameters.py | 200 | Domain |
| | kpis.py | 180 | Domain |
| | optimization_rules.py | 180 | Domain |
| | mml_commands.py | 150 | Domain |
| **domain** | **total** | **710** | |
| network | huawei_client.py | 250 | Client |
| | kpi_collector.py | 150 | Collector |
| **network** | **total** | **400** | |
| ui | app.py | 150 | UI |
| | pages/ (5 files) | 450 | UI |
| | components/ (3 files) | 150 | UI |
| **ui** | **total** | **750** | |
| | config files | 155 | Config |
| | tests | 800+ | Tests |
| | scripts | 200+ | Scripts |
| **GRAND TOTAL** | | **~8,500** | ~30 files |

---

## Phase 2 Implementation Order

### Week 1: Foundation (Files 1-10)

**Step 1: Domain Knowledge** (Files 1-5, ~900 lines)
1. `domain/__init__.py`
2. `domain/parameters.py` - 5 Huawei parameters with ranges
3. `domain/kpis.py` - 7 KPIs with 3-tier weighting
4. `domain/optimization_rules.py` - 10 optimization scenarios
5. `domain/mml_commands.py` - MML templates and builders

**Step 2: Network Integration** (Files 6-7, ~400 lines)
6. `network/__init__.py`
7. `network/huawei_client.py` - Huawei API client
8. `network/kpi_collector.py` - KPI aggregation

**Step 3: Tools Foundation** (Files 9-13, ~600 lines)
9. `tools/__init__.py`
10. `tools/huawei_tools.py` - 5 API tools
11. `tools/sql_tools.py` - 2 database tools
12. `tools/calculation_tools.py` - 2 calculation tools
13. `tools/validation_tools.py` - 2 validation tools

### Week 2: Agents & Prompts (Files 14-20)

**Step 4: Prompts** (Files 14-16, ~400 lines)
14. `prompts/__init__.py`
15. `prompts/system_prompts.py` - 6 agent prompts
16. `prompts/few_shot_examples.py` - 15-20 optimization examples
17. `prompts/context_builders.py` - Dynamic prompt assembly

**Step 5: Core Agents** (Files 18-20, ~1,200 lines)
18. `agents/__init__.py`
19. `agents/config_agent.py` - Configuration agent
20. `agents/validation_agent.py` - Validation agent
21. `agents/monitoring_agent.py` - Monitoring agent

**Step 6: Extension Agents** (Files 21-24, ~900 lines)
22. `agents/kpi_analytics_agent.py` - Analytics agent
23. `agents/network_connector_agent.py` - Connector agent
24. `agents/mml_executor_agent.py` - MML executor agent
25. `agents/workflow.py` - Agent orchestration

### Week 3: Configuration & Data (Files 25-30)

**Step 7: Configuration** (Files 25-27, ~155 lines)
26. `config/config.yaml` - Main config
27. `config/kpi_weights.yaml` - 3-tier weights
28. `config/.env.template` - Environment template

**Step 8: Database** (Files 28-30, ~150 lines)
29. `data/lz_network.db` - Initialize SQLite
30. `data/migrations/001_initial_schema.py` - Schema
31. `data/migrations/002_optimization_history.py` - Optimization tracking

### Week 4: UI, Testing & Scripts (Files 31+)

**Step 9: UI Framework** (Files 31-39, ~750 lines)
32. `ui/__init__.py`
33. `ui/app.py` - Main Streamlit app
34. `ui/pages/__init__.py`
35. `ui/pages/1_dashboard.py` - Dashboard
36. `ui/pages/2_optimization.py` - Optimizer UI
37. `ui/pages/3_validation.py` - Validation UI
38. `ui/pages/4_analytics.py` - Analytics UI
39. `ui/pages/5_settings.py` - Settings UI
40. `ui/components/` (3 files) - Reusable components

**Step 10: Testing & Deployment** (Files 40+, ~1,000 lines)
41. `tests/conftest.py` - Test configuration
42. `tests/test_agents/` (7 files) - Agent tests
43. `tests/test_tools/` (4 files) - Tool tests
44. `tests/test_domain/` (3 files) - Domain tests
45. `tests/test_network/` (2 files) - Network tests
46. `tests/integration/` (2 files) - Integration tests
47. `scripts/setup.py` - Project setup
48. `scripts/init_database.py` - DB init
49. `scripts/deploy.sh` - Docker deployment
50. `main.py` - Entry point
51. `requirements.txt` - Dependencies
52. `Dockerfile`, `docker-compose.yaml` - Containers

---

## Key Implementation Checkpoints

**After Week 1**:
- Domain knowledge complete and unit tested
- Huawei API client can authenticate and fetch KPIs
- All 10 tools functional with basic error handling

**After Week 2**:
- 3 core agents working with few-shot examples
- 3 extension agents integrated
- Workflow orchestration tested with mock data

**After Week 3**:
- Configuration system active with real Huawei credentials
- Database initialized with proper schema
- Tool integration tests passing

**After Week 4**:
- UI fully functional with real Huawei integration
- End-to-end workflow tested
- Production deployment ready

---

## Summary

**This document defines:**

- **30 files** (~8,500 lines) across 10 modules
- **~2,400 lines** of agents (6 agents + workflow)
- **~600 lines** of tools (10 tools across 4 files)
- **~400 lines** of prompts (system + few-shot)
- **~710 lines** of domain knowledge (parameters + KPIs + rules)
- **~400 lines** of network integration
- **~750 lines** of UI (multi-page Streamlit app)
- **~800+ lines** of tests
- **~200+ lines** of scripts and config

**Built on:**
- Nvidia Telco Network Configuration Blueprint (baseline)
- Huawei iMaster MAE API (live 4G network)
- Liquid Zimbabwe network context (Zimbabwe operations)
- +40% complexity through domain expansion

**Ready for:**
- Phased 4-week implementation
- Clear module boundaries
- Independent testing
- Production deployment

