# COMPLETE FINAL REBUILD PLAN
## Liquid Zimbabwe 4G Network Optimizer - Ground-Up Rebuild from Nvidia Blueprint

**Project**: Clean rebuild using Nvidia Telco Network Configuration Blueprint
**Timeline**: 4-5 weeks (23 days) to production-ready demo
**Approach**: Phased with mandatory testing gates and interactive troubleshooting
**Architecture**: 6-agent simplified workflow with Huawei 4G integration
**Date Created**: October 30, 2025
**Version**: 1.0 - Final Approved Plan

---

## EXECUTIVE SUMMARY

### Approved Decisions
✅ **KPI Weighting**: 3-tier system (25% foundation, 50% revenue/experience, 25% efficiency)
✅ **Docker Deployment**: Phase 2.5 containerization for deploy-anywhere capability
✅ **Agent Architecture**: Keep 6 agents, simplify implementation
✅ **Advanced Features**: Option B - Few-shot prompting now, dynamic weighting later
✅ **Prompt Foundation**: Use existing AGENT_PROMPTS_ARCHITECTURE.md + OG-FILES prompts

### What We're Building

**Core System Components:**
1. **6-Agent Workflow** (Nvidia 3 + LZ 3 extensions)
   - Configuration Agent - Parameter optimization recommendations
   - Validation Agent - Safe change application with rollback
   - Monitoring Agent - Continuous KPI tracking
   - **KPI Analytics Agent** - Deep performance analysis
   - **Network Connector Agent** - Huawei API management
   - **MML Executor Agent** - Safe command execution

2. **Domain Knowledge** (Preserved exactly):
   - 5 Huawei 4G parameters with MML commands
   - 7 KPIs with weighted scoring (NEW)
   - Parameter optimization rules (10 scenarios)
   - Safety validation system
   - Impact scoring

3. **Few-Shot Prompting** (NEW - Using your blueprint):
   - MML command examples
   - KPI analysis scenarios
   - Optimization decision patterns
   - From AGENT_PROMPTS_ARCHITECTURE.md + OG-FILES/prompts/

4. **Simple Branded UI**:
   - Cassava logo and colors
   - Natural language query interface
   - Network connection controls
   - Results display (recommendations, validation)

5. **Docker Deployment**:
   - One-command deployment
   - Deploy anywhere (dev, staging, production)
   - Persistent data and logs

---

## PHASE 0: PREPARATION & CREDENTIAL EXTRACTION (2 days)

### Goal
Secure credentials, extract working components, create memorial

### Day 1: Asset Extraction

#### Tasks

**1. Create Secure Credentials File (gitignored)**
```
CREDENTIALS_SECURE.txt
---
NVIDIA API Key: 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
Huawei API URL: https://41.174.191.214:31127
Huawei Username: cassava.ai
Huawei Password: #Pass123#
```

**2. Extract Working Components to `/rebuild-assets/`**
```
/rebuild-assets/
├── domain_knowledge/
│   ├── liquid_zimbabwe_parameters.py (from liquid-4g-core/agents/)
│   ├── liquid_zimbabwe_kpi.py (from liquid-4g-core/agents/)
│   └── optimization_rules.md (extracted from parameters.py)
│
├── prompts/
│   ├── AGENT_PROMPTS_ARCHITECTURE.md (from OG-FILES/)
│   ├── system_prompts.yaml (from OG-FILES/liquid-4g-prod/config/)
│   ├── task_prompts.yaml (from OG-FILES/liquid-4g-prod/config/)
│   ├── prompt_templates.py (from OG-FILES/liquid-4g-demo/)
│   ├── enhanced_prompt_templates.py (from OG-FILES/liquid-4g-demo/)
│   └── prompt_manager.py (from OG-FILES/liquid-4g-prod/src/)
│
├── api/
│   └── huawei_api_client.py (from liquid-4g-core/network/)
│
├── branding/
│   ├── cassava-logo.svg
│   └── streamlit_config.toml
│
├── data/
│   └── historical_data.csv
│
└── mml_commands/
    ├── HUAWEI_MML_COMMANDS_COMPLETE.md
    └── MML_COMMANDS_REFERENCE.md
```

**3. Security Review of huawei_api_client.py**
- Remove any hardcoded credentials
- Verify SSL handling
- Check token refresh logic

### Day 2: Memorial & Git Setup

#### Tasks

**4. Create `LESSONS_LEARNED.md`**
```markdown
# Lessons Learned - First Implementation Attempt

## What Didn't Work
- Scope creep: 400%+ feature expansion beyond blueprint
- No testing gates between phases
- BubbleRAN simulation distraction (not useful for 4G)
- 6-agent design created but not fully integrated
- Excellent prompts designed but not implemented
- Multiple file versions created confusion

## What Worked Well
- Domain knowledge encoding (parameters, KPIs, MML)
- Safety validation architecture
- Impact scoring system
- Huawei API authentication patterns
- Agent orchestration concept

## What We'll Do Differently
- Build in phases with mandatory testing
- Start simple, add complexity incrementally
- No simulation - direct Huawei integration
- Use existing prompt architecture
- Interactive troubleshooting at every issue
```

**5. Git Backup**
```bash
git checkout -b archive/pre-reset-backup-2025-10-30
git add -A
git commit -m "Memorial backup: Complete state before Nvidia blueprint reset

Preserving:
- Excellent prompt architecture (AGENT_PROMPTS_ARCHITECTURE.md)
- Domain knowledge (5 params, 7 KPIs, optimization rules)
- Safety validation system
- 6-agent orchestration design
- Huawei API integration patterns

Context: Resetting to rebuild from Nvidia blueprint with incremental approach"

git push origin archive/pre-reset-backup-2025-10-30
git tag v2.0.0-before-reset -a -m "Last state before blueprint reset"
git push --tags
```

**6. Create Clean Working Branch**
```bash
git checkout -b rebuild/lz-nvidia-hybrid
```

### Success Criteria
- ✅ All credentials secured and gitignored
- ✅ Working components extracted to rebuild-assets/
- ✅ Memorial documentation complete
- ✅ Git backup created with descriptive tag
- ✅ Clean branch ready for rebuild

### Deliverables
- `CREDENTIALS_SECURE.txt` (gitignored)
- `/rebuild-assets/` directory (7 subdirectories, ~20 files)
- `LESSONS_LEARNED.md`
- Git tag `v2.0.0-before-reset`
- Clean branch `rebuild/lz-nvidia-hybrid`

### CHECKPOINT #0
Review extracted assets before proceeding

---

## PHASE 1: NVIDIA BLUEPRINT STUDY & ARCHITECTURE DESIGN (3 days)

### Goal
Understand Nvidia blueprint, create LZ adaptation plan (NO simulation deployment)

### Day 1: Blueprint Architecture Study

#### Tasks

**1. Clone Nvidia Blueprint for Reference**
```bash
git clone https://github.com/bubbleran/Telco-Network-Configuration.git nvidia-reference
cd nvidia-reference
git log --oneline -20  # Review commit history
```

**2. Study Agent Architecture**
- Read `nvidia-reference/agentic_llm_workflow/agents.py`
- Document: Configuration Agent, Validation Agent, Monitoring Agent
- Understand State management (TypedDict pattern)
- Note LangGraph workflow structure
- Review tool binding patterns

**3. Study Tools Architecture**
- Read `nvidia-reference/agentic_llm_workflow/tools.py`
- Document: SQL tools, calculation tools, network tools
- Note @tool decorator pattern
- Review response formatting

**4. Study UI Structure**
- Read `nvidia-reference/telco_planner_ui.py`
- Identify minimal UI components
- Note Streamlit session state usage
- Extract query interface pattern

### Day 2: Create LZ Adaptation Blueprint

#### Tasks

**5. Create Mapping Document: `NVIDIA_TO_LZ_MAPPING.md`**

Content includes:

**Network Stack Mapping**
- BubbleRAN 5G O-RAN → Huawei 4G iMaster MAE
- Docker compose network → Direct API integration
- RF-Sim mode → Live network only
- xApp database → Huawei API + SQLite

**Agent Mapping (3 → 6 agents)**

*Core Agents (From Nvidia):*
1. **Configuration Agent** → Enhanced with LZ optimization rules
   - Input: User query + KPI issues
   - Output: Parameter recommendations with MML commands
   - Tools: Historical SQL, KPI analysis, weighted scoring

2. **Validation Agent** → Enhanced with Huawei MML execution
   - Input: Recommended parameter changes
   - Output: Validation results + rollback if needed
   - Tools: Huawei API, live KPI collection, comparison

3. **Monitoring Agent** → Enhanced with 7 KPI tracking
   - Input: Site information
   - Output: KPI status + degradation alerts
   - Tools: KPI SQL, trend analysis, threshold checking

*Extension Agents (From LZ Design):*
4. **KPI Analytics Agent** (NEW)
   - Input: Historical + live KPI data
   - Output: Root cause analysis, correlations
   - Tools: Statistical analysis, pattern matching

5. **Network Connector Agent** (NEW)
   - Input: Connection request
   - Output: API status, network element discovery
   - Tools: Huawei API auth, health check

6. **MML Executor Agent** (NEW)
   - Input: Validated MML commands
   - Output: Execution results + safety validation
   - Tools: MML command execution, rollback

**Tool Mapping**

*BubbleRAN → Huawei:*
- `start_network()` → `connect_huawei_api()`
- `stop_network()` → `disconnect_huawei_api()`
- `check_network_status()` → `check_api_status()`
- `execute_xapp_sql()` → `execute_lz_kpi_sql()`
- `find_value_in_gnb()` → `query_huawei_parameter()`
- `update_value_in_gnb()` → `execute_mml_command()`

*Keep Same:*
- `execute_historical_sql()` (works with historical_data.csv)
- `calc_weighted_average()` (use with LZ KPI weights)

**Parameter Mapping (5G → 4G)**

*BubbleRAN Parameters (NOT USED):*
- p0_nominal (5G power control)
- att_tx/att_rx (5G attenuation)
- dl/ul_carrierBandwidth (5G bandwidth)

*LZ Parameters (USE THESE):*
1. reference_signal_power_pdschcfg (-600 to 500, default -200)
2. a3_event_offset (0 to 15 dB, default 3)
3. t310_timer (100-6000 ms, default 1000)
4. p0_nominal_pusch (-126 to 24, default -70)
5. pdcch_aggregation_level (0 to 30, default 12)

**KPI Mapping**

*BubbleRAN KPIs (NOT USED):*
- DL/UL Bitrate
- SNR
- MCS
- LDPC iterations

*LZ KPIs (USE THESE - with weights):*
1. Network Access Success - 25% weight
2. Download Speed - 20% weight
3. Download Quality - 15% weight
4. Upload Speed - 15% weight
5. Upload Quality - 10% weight
6. Control Channel Load - 10% weight
7. Feedback Channel Load - 5% weight

**Database Mapping**
- BubbleRAN: xapp_db (Docker container)
- LZ: lz_network.db (SQLite local)

Schema:
- kpi_data (timestamp, site, cell_id, 7 KPI columns)
- parameter_changes (audit trail)
- optimization_history (before/after comparison)

**6. Create Prompt Integration Plan: `PROMPT_INTEGRATION_PLAN.md`**

Content includes:

**Source Prompts (OG-FILES)**

*System Prompts (system_prompts.yaml):*
- Extract agent role definitions
- Extract safety constraints
- Extract response format specifications

*Task Prompts (task_prompts.yaml):*
- Extract optimization task prompts
- Extract validation task prompts
- Extract monitoring task prompts

*Enhanced Templates (enhanced_prompt_templates.py):*
- Extract few-shot examples
- Extract MML command templates
- Extract KPI analysis patterns

**Integration Strategy**
1. **Base Prompts**: Use AGENT_PROMPTS_ARCHITECTURE.md structure
2. **Few-Shot Examples**: Extract from enhanced_prompt_templates.py
3. **Dynamic Context**: Use prompt_manager.py pattern
4. **LZ Customization**: Inject from liquid_zimbabwe_*.py files

**Prompt Components for Each Agent**

*Configuration Agent:*
- System: Role definition from blueprint
- Context: 5 LZ parameters, 10 optimization rules
- Few-Shot: 3-5 optimization examples
- Output: Structured recommendation format

*Validation Agent:*
- System: Safety-first role definition
- Context: Parameter ranges, impact levels
- Few-Shot: 2-3 validation scenarios (success/rollback)
- Output: Validation results + decision

*Monitoring Agent:*
- System: Continuous monitoring role
- Context: 7 KPIs with thresholds and weights
- Few-Shot: 2-3 degradation detection examples
- Output: Alert format with priority

### Day 3: Project Structure Design

#### Tasks

**7. Design Directory Structure**
```
/lz-network-optimizer/
│
├── agents/
│   ├── __init__.py
│   ├── config_agent.py           # Configuration recommendations
│   ├── validation_agent.py       # Safe parameter changes
│   ├── monitoring_agent.py       # KPI tracking
│   ├── kpi_analytics_agent.py    # Deep analysis
│   ├── network_connector_agent.py # API management
│   ├── mml_executor_agent.py     # Command execution
│   └── workflow.py               # LangGraph orchestration
│
├── tools/
│   ├── __init__.py
│   ├── sql_tools.py              # Database queries
│   ├── huawei_tools.py           # Huawei API tools
│   ├── calculation_tools.py      # Weighted scoring
│   └── validation_tools.py       # Safety checks
│
├── prompts/
│   ├── __init__.py
│   ├── system_prompts.py         # Agent role definitions
│   ├── few_shot_examples.py      # Training examples
│   └── context_builders.py       # Dynamic context injection
│
├── domain/
│   ├── __init__.py
│   ├── parameters.py             # From rebuild-assets
│   ├── kpis.py                   # From rebuild-assets
│   ├── mml_commands.py           # MML templates
│   └── optimization_rules.py     # 10 scenario rules
│
├── network/
│   ├── __init__.py
│   ├── huawei_client.py          # API client (from rebuild-assets)
│   └── kpi_collector.py          # KPI data collection
│
├── ui/
│   ├── app.py                    # Streamlit main app
│   ├── .streamlit/
│   │   └── config.toml           # Cassava branding
│   └── assets/
│       └── logos/
│           └── cassava-logo.svg
│
├── data/
│   ├── historical_data.csv       # From rebuild-assets
│   └── lz_network.db            # Created at runtime
│
├── config/
│   ├── config.yaml               # Main configuration
│   ├── .env.template             # Credential template
│   └── kpi_weights.yaml          # KPI weighting config
│
├── tests/
│   ├── test_agents.py
│   ├── test_tools.py
│   ├── test_huawei_api.py
│   └── test_weighted_scoring.py
│
├── docs/
│   ├── README.md
│   ├── USER_GUIDE.md
│   ├── ARCHITECTURE.md
│   └── mml_reference/
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── requirements.txt
├── .env.template
├── .gitignore
└── README.md
```

**8. Create Initial `requirements.txt`**
```
# Core Dependencies
python>=3.10,<3.14

# LLM & Agent Framework
langgraph>=0.2.0
langchain-core>=0.2.0
langchain-nvidia-ai-endpoints>=0.1.0

# UI
streamlit>=1.28.0

# Data & Database
pandas>=2.0.0
numpy>=1.24.0
pydantic>=2.0.0

# API & Network
requests>=2.31.0
urllib3>=2.0.0

# Configuration
pyyaml>=6.0
python-dotenv>=1.0.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Utilities
python-dateutil>=2.8.0
```

### Success Criteria
- ✅ Understand Nvidia blueprint agent architecture
- ✅ Clear mapping from BubbleRAN → Huawei
- ✅ Project structure designed and documented
- ✅ Prompt integration strategy defined
- ✅ No time wasted on simulation setup

### Deliverables
- `NVIDIA_TO_LZ_MAPPING.md` (comprehensive mapping)
- `PROMPT_INTEGRATION_PLAN.md` (few-shot strategy)
- Project directory structure created (empty files)
- `requirements.txt`

### CHECKPOINT #1
Review architecture before coding
- Present mapping document for validation
- Approve agent design
- Discuss any adjustments needed

---

## PHASE 2: CORE AGENT IMPLEMENTATION WITH FEW-SHOT PROMPTING (8 days)

### Goal
Build 6 agents with Huawei integration, domain knowledge, and few-shot examples

### Week 1 (Days 1-4): Foundation & Domain Integration

#### Day 1: Project Setup & Database

**Tasks:**

**1. Initialize Project**
```bash
cd rebuild/lz-nvidia-hybrid
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Copy Domain Knowledge**
```bash
cp rebuild-assets/domain_knowledge/*.py domain/
cp rebuild-assets/mml_commands/*.md docs/mml_reference/
```

**3. Create Database Schema (`data/schema.sql`)**
```sql
CREATE TABLE kpi_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    site_name TEXT NOT NULL,
    cell_id INTEGER NOT NULL,

    -- 7 KPIs
    network_access_success REAL,      -- RACH Setup Success Rate (%)
    download_quality REAL,            -- DL IBLER (%)
    upload_quality REAL,              -- UL IBLER (%)
    control_channel_load REAL,        -- PDCCH CCE Usage (%)
    feedback_channel_load REAL,       -- PUCCH Usage (%)
    download_speed REAL,              -- DL Throughput (kbit/s)
    upload_speed REAL,                -- UL Throughput (kbit/s)

    -- Metadata
    data_source TEXT DEFAULT 'live',  -- 'live' or 'historical'

    INDEX idx_site_timestamp (site_name, timestamp),
    INDEX idx_data_source (data_source)
);

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

CREATE TABLE optimization_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    site_name TEXT NOT NULL,
    cell_id INTEGER NOT NULL,

    -- Issue identification
    kpi_issue TEXT NOT NULL,           -- JSON array of issue types
    trigger_reason TEXT,

    -- Changes made
    parameters_changed TEXT NOT NULL,  -- JSON: [{param, old, new}, ...]
    mml_commands TEXT,                 -- JSON array of commands

    -- Before/after KPIs
    kpi_before TEXT NOT NULL,          -- JSON: all 7 KPIs
    kpi_after TEXT,                    -- JSON: all 7 KPIs (null if pending)

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

**4. Import Historical Data**
Create and run `scripts/import_historical_data.py`

#### Day 2: Configuration Files & Prompts Foundation

**Tasks:**

**5. Create `config/config.yaml`**
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
  ssl_verify: false
  timeout: 30
  retry_attempts: 3

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

**6. Create `config/kpi_weights.yaml`**
```yaml
# KPI Weighting Configuration
# Tier 1: Foundation (25%)
# Tier 2: Revenue & Experience (50%)
# Tier 3: Efficiency (25%)

static_weights:
  network_access_success: 0.25   # TIER 1 - Critical foundation
  download_speed: 0.20           # TIER 2 - Revenue driver
  download_quality: 0.15         # TIER 2 - User experience
  upload_speed: 0.15             # TIER 2 - Important but less critical
  upload_quality: 0.10           # TIER 2 - Background services
  control_channel_load: 0.10     # TIER 3 - Network efficiency
  feedback_channel_load: 0.05    # TIER 3 - Fine-tuning

# KPI Thresholds (from domain knowledge)
thresholds:
  network_access_success:
    normal_min: 95.0
    critical: 90.0
    higher_is_better: true

  download_speed:
    normal_min: 5000.0
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

**7. Extract Few-Shot Examples**
Create `prompts/few_shot_examples.py` with examples from OG-FILES

Key examples to include:
- Low download speed optimization
- High control channel load optimization
- Poor upload quality optimization
- Successful validation scenario
- Failed validation with rollback
- Normal monitoring vs degradation alert

#### Days 3-4: Huawei Integration Layer

**Tasks:**

**8. Create Huawei Tools (`tools/huawei_tools.py`)**

Implement:
- `@tool connect_huawei_api()` - Authenticate to Huawei API
- `@tool query_huawei_parameter()` - Query current parameter values
- `@tool execute_mml_command()` - Execute MML with safety validation
- `@tool collect_live_kpis()` - Collect KPI data for duration
- `@tool check_api_status()` - Health check

**9. Create SQL Tools (`tools/sql_tools.py`)**

Implement:
- `@tool execute_kpi_sql()` - Query KPI database
- `@tool execute_historical_sql()` - Query historical data

**10. Create Calculation Tools (`tools/calculation_tools.py`)**

Implement:
- `@tool calc_weighted_kpi_score()` - Calculate weighted score (0-100)

### Week 2 (Days 5-8): Agent Implementation

#### Day 5-6: Configuration Agent

**Tasks:**

**11. Implement Configuration Agent with Few-Shot Prompting**

Create `agents/config_agent.py` with:
- State management (TypedDict)
- System prompt builder with few-shot examples
- Domain knowledge injection (5 parameters, 7 KPIs, optimization rules)
- LangGraph react agent with tools
- Structured output parsing

Key components:
- `build_configuration_prompt()` - Builds system prompt with examples
- `config_agent(state)` - Main agent function
- Tool integration: historical SQL, KPI SQL, query parameter, weighted scoring

#### Day 7: Validation & Monitoring Agents

**Tasks:**

**12. Implement Validation Agent**
Similar pattern to Configuration Agent with validation-specific prompts and tools

**13. Implement Monitoring Agent**
Similar pattern with monitoring-specific prompts and continuous tracking logic

#### Day 8: Extension Agents & Workflow

**Tasks:**

**14. Implement Extension Agents**
- KPI Analytics Agent
- Network Connector Agent
- MML Executor Agent

**15. Create LangGraph Workflow (`agents/workflow.py`)**
```python
workflow = StateGraph(State)

# Add 6 agent nodes
workflow.add_node("network_connector", network_connector_agent)
workflow.add_node("monitoring", monitoring_agent)
workflow.add_node("kpi_analytics", kpi_analytics_agent)
workflow.add_node("config", config_agent)
workflow.add_node("validation", validation_agent)
workflow.add_node("mml_executor", mml_executor_agent)

# Define edges (simplified orchestration)
workflow.add_edge(START, "network_connector")
workflow.add_edge("network_connector", "monitoring")
workflow.add_conditional_edges("monitoring", ...)
# ... etc

app = workflow.compile()
```

### Success Criteria
- ✅ All 6 agents implemented with few-shot prompting
- ✅ Can query parameters via Huawei API
- ✅ Can collect KPIs (live or historical)
- ✅ Weighted scoring calculation works
- ✅ LangGraph workflow compiles
- ✅ Natural language queries produce structured recommendations

### Testing
Test with historical data (no live API required):
```python
test_state = {
    "messages": [HumanMessage("Download speed is low at Bindura Hospital")],
    "site_name": "MSH-0112-Bindura Hospital",
    "cell_id": 1,
    "kpi_issues": ["low_download_speed"],
}
result = app.invoke(test_state)
# Should return recommendation from few-shot learning
```

### Deliverables
- 6 agent files with few-shot prompting
- Huawei tools integrated
- Weighted KPI scoring implemented
- LangGraph workflow operational
- Test results showing recommendations

### CHECKPOINT #2
Demo agent functionality
- Run test queries with historical data
- Review recommendation quality
- Verify few-shot examples are being followed
- Approve before moving to UI

**Interactive Troubleshooting:**
If issues arise, I'll present options and wait for your decision.

---

## PHASE 2.5: DOCKER CONTAINERIZATION (1 day)

### Goal
Package system for deploy-anywhere capability

### Tasks

**1. Create `docker/Dockerfile`**
```dockerfile
FROM python:3.10-slim

LABEL maintainer="Liquid Zimbabwe <support@liquid.co.zw>"
LABEL description="Liquid Zimbabwe 4G Network Optimizer"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc sqlite3 curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY agents/ ./agents/
COPY tools/ ./tools/
COPY prompts/ ./prompts/
COPY domain/ ./domain/
COPY network/ ./network/
COPY ui/ ./ui/
COPY config/ ./config/
COPY data/ ./data/

# Create runtime directories
RUN mkdir -p /app/data /app/logs

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**2. Create `docker/docker-compose.yml`**
```yaml
version: '3.8'

services:
  lz-optimizer:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: lz-network-optimizer
    image: lz-network-optimizer:latest

    ports:
      - "8501:8501"

    environment:
      - NVIDIA_API_KEY=${NVIDIA_API_KEY}
      - HUAWEI_API_URL=${HUAWEI_API_URL}
      - HUAWEI_USERNAME=${HUAWEI_USERNAME}
      - HUAWEI_PASSWORD=${HUAWEI_PASSWORD}

    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

    restart: unless-stopped

    networks:
      - lz-network

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  lz-network:
    driver: bridge
```

**3. Create `.env.template`**
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

**4. Create Deployment Script (`scripts/deploy.sh`)**
```bash
#!/bin/bash
echo "🚀 Liquid Zimbabwe 4G Network Optimizer - Deployment"
echo "=================================================="

if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.template to .env and configure"
    exit 1
fi

echo "📦 Building Docker image..."
docker-compose -f docker/docker-compose.yml build

echo "🚀 Starting container..."
docker-compose -f docker/docker-compose.yml up -d

echo "✅ Deployment complete!"
echo "🌐 Access UI at: http://localhost:8501"
```

**5. Test Docker Deployment**
```bash
cd docker
docker-compose build
docker-compose up -d
docker-compose ps
curl http://localhost:8501/_stcore/health
docker-compose logs -f
docker-compose down
```

### Success Criteria
- ✅ Docker image builds successfully
- ✅ Container starts and passes health check
- ✅ UI accessible at localhost:8501
- ✅ Data persists in mounted volumes
- ✅ Credentials loaded from .env
- ✅ One-command deployment works

### Deliverables
- `docker/Dockerfile`
- `docker/docker-compose.yml`
- `.env.template`
- `scripts/deploy.sh`
- Deployment documentation

### CHECKPOINT #2.5
Docker deployment test
- Deploy to local machine
- Deploy to test server
- Verify persistence and restart

---

## PHASE 3: SIMPLE UI WITH CASSAVA BRANDING (4 days)

### Goal
Clean Streamlit interface with natural language query and branding

### Days 1-2: Core UI Implementation

#### Tasks

**1. Create `ui/app.py` (Target: ~400 lines)**

Key components:
- Page config with Cassava branding
- Custom CSS for Cassava colors
- Cassava logo display
- Sidebar: Network connection controls
- Sidebar: Site selection
- Main area: Natural language query interface
- Results display: Analysis, recommendations, KPIs
- Apply & validate flow
- Current KPIs view (collapsible)
- Footer with branding

**2. Apply Cassava Branding (`ui/.streamlit/config.toml`)**
```toml
[theme]
primaryColor = "#FF6B35"           # Cassava orange
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#1A1A1A"
font = "sans serif"

[server]
port = 8501
enableCORS = false
enableXsrfProtection = true
```

### Days 3-4: UI Polish & Integration

#### Tasks

**3. Add Features**
- Optimization history view
- Simple KPI trend charts (Streamlit native)
- Error handling and user feedback
- Loading states and progress indicators

**4. Test All UI Flows**
- Connection → Query → Analysis → Recommendation
- Apply → Validation → Results
- Error scenarios
- API unavailable fallback

### Success Criteria
- ✅ UI loads with Cassava branding
- ✅ Natural language query works
- ✅ Recommendations display clearly
- ✅ Apply & validate flow functional
- ✅ KPI metrics visible
- ✅ Clean, simple design (<500 lines)

### Deliverables
- `ui/app.py` (~400 lines)
- Branded interface
- Working query→analysis→recommendation flow

### CHECKPOINT #3
UI review
- Screenshot walkthrough
- Test query interface
- Branding verification
- Adjustments as needed

---

## PHASE 4: TESTING, DOCUMENTATION & DEMO PREP (5 days)

### Goal
Validate system, create docs, prepare demo

### Days 1-2: Testing

#### Tasks

**1. Create Test Suite (`tests/test_agents.py`)**

Tests:
- Configuration Agent produces valid recommendations
- Weighted scoring calculation correct
- Parameter validation (valid/invalid values)
- MML command formatting
- Agent workflow integration

**2. Run Integration Tests**
- Test with historical data
- Test agent workflow end-to-end
- Test error handling

**3. Test Huawei API (if available)**
- Query parameter values
- Collect KPIs
- Verify data format

### Days 3-4: Documentation

#### Tasks

**4. Create `README.md`**

Sections:
- Project overview
- Features
- Quick start (prerequisites, installation, deployment, access)
- Architecture (6-agent workflow, parameters, KPIs)
- Usage examples
- Development setup
- Testing
- License
- Support

**5. Create `docs/USER_GUIDE.md`**

Content:
- Connecting to network
- Querying network status
- Applying optimizations
- Understanding results

**6. Create `docs/ARCHITECTURE.md`**

Content:
- Differences from NVIDIA blueprint
- Parameter definitions
- KPI definitions
- Optimization logic
- Few-shot prompting approach
- Weighted scoring system

### Day 5: Demo Preparation

#### Tasks

**7. Create Demo Script (10 minutes)**

Structure:
- Setup (1 min) - Show UI, branding, purpose
- Connect to Network (1 min) - API connection, site selection
- Query #1: Network Status (2 min) - Analyze KPIs, show weighted score
- Query #2: Optimization Request (3 min) - Get recommendation with MML
- Apply Change (2 min) - Validation flow, results
- Wrap-up (1 min) - History, Docker deployment, Q&A

**8. Test Demo Flow End-to-End**

**9. Prepare Presentation Materials**
- Screenshots of UI
- Architecture diagram
- Results comparison

### Success Criteria
- ✅ All tests pass
- ✅ Documentation complete and clear
- ✅ Demo runs smoothly (<10 min)
- ✅ System handles API unavailability gracefully
- ✅ Ready to present to stakeholders

### Deliverables
- Test suite with passing results
- Complete documentation (README, USER_GUIDE, ARCHITECTURE)
- Demo script and materials
- System ready for production pilot

### CHECKPOINT #4
Final review
- Run demo script
- Identify rough edges
- Final polish
- Approval for deployment

---

## TIMELINE SUMMARY

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 0** | 2 days | Credentials, assets extracted, git backup |
| **Phase 1** | 3 days | Architecture mapping, project structure |
| **Phase 2** | 8 days | 6 agents with few-shot prompting |
| **Phase 2.5** | 1 day | Docker containerization |
| **Phase 3** | 4 days | Branded UI with query interface |
| **Phase 4** | 5 days | Tests, docs, demo prep |
| **TOTAL** | **23 days** | **Production-ready system** |

---

## COMPLEXITY COMPARISON

| Component | Nvidia Blueprint | Your Build | Current (Pre-Reset) |
|-----------|-----------------|------------|---------------------|
| Python Files | 20 files | ~30 files | 179 files |
| Agents | 3 agents | 6 agents | 6 agents (unused) |
| Prompts | Basic | Few-shot enhanced | Designed but not used |
| UI Lines | ~300 lines | ~400 lines | 1,505 lines |
| Parameters | 5 (5G) | 5 (4G, yours) | 5 (same) |
| KPIs | Variable | 7 (weighted) | 7 (equal weight) |
| Network | BubbleRAN | Huawei API | Huawei API |
| Docker | No | Yes | Partial |
| **Total Complexity** | Baseline | **+40%** | +400% |

---

## PRESERVED COMPONENTS FROM CURRENT WORK

### From `rebuild-assets/`:

**1. Domain Knowledge (KEEP EXACTLY)**
- `liquid_zimbabwe_parameters.py` - 5 parameters with MML
- `liquid_zimbabwe_kpi.py` - 7 KPIs with thresholds
- Optimization rules (10 scenarios)

**2. Prompts (USE AS FOUNDATION)**
- `AGENT_PROMPTS_ARCHITECTURE.md` - System prompt structure
- `prompt_templates.py` - Few-shot examples
- `enhanced_prompt_templates.py` - MML examples
- `prompt_manager.py` - Dynamic context building

**3. API Integration (SECURITY REVIEWED)**
- `huawei_api_client.py` - Authentication patterns

**4. Branding**
- Cassava logo (SVG)
- Streamlit color config

**5. Data**
- `historical_data.csv` - For testing

---

## KPI WEIGHTING SYSTEM (3-TIER)

### Tier 1: Foundation (25%)
**network_access_success: 25%**
- Critical foundation metric
- Affects all users
- Direct churn impact

### Tier 2: Revenue & Experience (50%)
- **download_speed: 20%** - Revenue driver
- **download_quality: 15%** - User experience
- **upload_speed: 15%** - Important but less critical
- **upload_quality: 10%** - Background services

### Tier 3: Efficiency (25%)
- **control_channel_load: 10%** - Network optimization
- **feedback_channel_load: 5%** - Fine-tuning only

**Rationale:**
- Aligns with telecom industry standards (3GPP, NGMN)
- Prioritizes customer-facing metrics
- Balances quality vs capacity
- Reflects Zimbabwean market (data-heavy usage)

---

## INTERACTIVE TROUBLESHOOTING PROTOCOL

At **every issue**, I will:

1. **STOP** work immediately
2. **DESCRIBE** clearly:
   - What I expected
   - What actually happened
   - Relevant logs/errors
3. **PRESENT OPTIONS** (2-3 solutions):
   - Option A: Quick fix (pros/cons)
   - Option B: Proper fix (pros/cons)
   - Option C: Workaround (pros/cons)
4. **WAIT** for your decision
5. **IMPLEMENT** chosen solution
6. **VALIDATE** before continuing

**No assumptions. No guessing. You decide.**

---

## SUCCESS METRICS

### Technical
- ✅ All 6 agents operational with few-shot prompting
- ✅ Huawei API integration working
- ✅ Weighted KPI scoring (3-tier: 25/50/25)
- ✅ Natural language query→recommendation→validation flow
- ✅ Docker one-command deployment
- ✅ Safety validation preventing dangerous changes
- ✅ Audit trail of all parameter changes

### Business
- ✅ Demo-ready in 23 days
- ✅ Can optimize real Liquid Zimbabwe sites
- ✅ Reduces optimization time from hours to minutes
- ✅ Clear ROI tracking via weighted scores
- ✅ Deployable anywhere (cloud, on-premise, laptop)

---

## RISK MITIGATION

### Risk 1: Huawei API Issues
**Mitigation:**
- Use historical_data.csv for development
- Test API connectivity in Phase 0
- Graceful fallback to CSV mode

**If API unavailable:**
- Continue with CSV testing
- Request API docs from LZ team
- Complete system works offline

### Risk 2: Parameter Mapping Issues
**Mitigation:**
- Using YOUR parameter definitions (already tested)
- All MML commands documented
- Test each parameter separately

### Risk 3: LLM Not Understanding Context
**Mitigation:**
- Few-shot examples guide LLM
- Optimization rules provide fallback
- Test with historical data first

### Risk 4: Timeline Pressure
**Mitigation:**
- 4 testing checkpoints prevent surprises
- Each phase has clear success criteria
- Can skip polish if needed for quick demo

---

## LESSONS FROM PREVIOUS ATTEMPT

### What Not to Do
❌ Add features without testing
❌ Build complex architecture before validating basics
❌ Pursue simulation mode that doesn't match use case
❌ Create multiple file versions
❌ Design prompts but not implement them

### What to Do
✅ Test at every phase gate
✅ Build incrementally
✅ Focus on actual use case (Huawei 4G)
✅ Single source of truth
✅ Implement designs, don't just document

---

## NEXT STEPS

**Ready to Begin Phase 0:**

1. Create `CREDENTIALS_SECURE.txt`
2. Extract assets to `/rebuild-assets/`
3. Review OG-FILES prompts
4. Create `LESSONS_LEARNED.md`
5. Git backup with tag

**Estimated time: 2 days**

---

## APPENDIX A: FEW-SHOT PROMPTING EXAMPLES

### Configuration Agent Example

**Scenario:** Low download speed with poor network access

**Input:**
```
Site: Bindura Hospital
KPIs:
  - download_speed: 3200 kbit/s (threshold: 5000)
  - network_access_success: 88% (threshold: 95%)
Query: "Why is download speed low and how can we fix it?"
```

**Analysis:**
```
Issue Pattern: Both metrics below thresholds
Root Cause: Weak signal coverage
Correlation: Metrics degrade together due to coverage
Historical: Similar issue at Chiwaridzo resolved with power increase
```

**Recommendation:**
```
Parameter: reference_signal_power_pdschcfg
Current: -200 (0.1 dBm)
Suggested: -150 (0.1 dBm)
Rationale: Increases coverage area, addresses both issues
Trade-off: Slight interference increase (acceptable)
Expected: Speed 7000-9000 kbit/s, Access 95-97%
MML: MOD PDSCHCFG:LOCALCELLID=1,REFERENCESIGNALPWR=-150;
```

### Validation Agent Example

**Scenario:** Successful validation

**Process:**
1. Record baseline KPIs
2. Execute MML command
3. Collect KPIs for 5 minutes
4. Calculate weighted improvement
5. Decision: Keep or Rollback

**Before:**
- download_speed: 3200 kbit/s
- network_access_success: 88%
- weighted_score: 72.5

**After:**
- download_speed: 8500 kbit/s
- network_access_success: 96%
- weighted_score: 89.2

**Decision:** KEEP_CHANGE (16.7 point improvement)

### Monitoring Agent Example

**Scenario:** Degradation detected

**Input:**
```
Site: Chiwaridzo_2
KPIs:
  - network_access_success: 89% (CRITICAL)
  - download_speed: 4200 kbit/s (below threshold)
  - weighted_score: 68.5 (dropped from 85)
```

**Analysis:**
```
ALERT: Performance degradation detected
- Network Access: 89% (critical: 90%)
- Download Speed: 4200 kbit/s (threshold: 5000)
- Score drop: 16.5 points from baseline
- Trend: Declining over past 2 hours
```

**Action:** TRIGGER_CONFIGURATION_AGENT

---

## APPENDIX B: MML COMMAND REFERENCE

### Reference Signal Power
```
Query:  LST PDSCHCFG: LOCALCELLID=1;
Modify: MOD PDSCHCFG:LOCALCELLID=1,REFERENCESIGNALPWR=-150; {site_name}
Range:  -600 to 500 (0.1 dBm units)
Default: -200
```

### A3 Event Offset
```
Query:  LST UECOOPERATIONPARA: LOCALCELLID=1;
Modify: MOD UECOOPERATIONPARA:LOCALCELLID=1,A3OFFSET=dB3; {site_name}
Range:  0 to 15 dB
Default: 3
Format: dB prefix required (e.g., dB3, dB5)
```

### T310 Timer
```
Query:  LST UETIMERCONST: LOCALCELLID=1;
Modify: MOD UETIMERCONST:LOCALCELLID=1,T310=MS1000_T310; {site_name}
Range:  100 to 6000 ms
Default: 1000
Format: MS prefix + _T310 suffix (e.g., MS1000_T310)
```

### P0 Nominal PUSCH
```
Query:  LST CELLULPCCOMM: LOCALCELLID=1;
Modify: MOD CELLULPCCOMM:LOCALCELLID=1,P0NOMINALPUSCH=-67; {site_name}
Range:  -126 to 24 dBm
Default: -70
```

### PDCCH Aggregation Level
```
Query:  LST CELLUSPARACFG: LOCALCELLID=1;
Modify: MOD CELLUSPARACFG:LOCALCELLID=1,USDATAPDCCHSINROFFSET=12; {site_name}
Range:  0 to 30
Default: 12
```

---

## APPENDIX C: CHECKPOINT DETAILS

### CHECKPOINT #0 (End of Phase 0)
**Review:**
- Verify all credentials extracted
- Check rebuild-assets/ structure
- Review LESSONS_LEARNED.md
- Confirm git backup created

**Approval Required:** Yes - before Phase 1

### CHECKPOINT #1 (End of Phase 1)
**Review:**
- NVIDIA_TO_LZ_MAPPING.md accuracy
- PROMPT_INTEGRATION_PLAN.md feasibility
- Project structure completeness
- Requirements.txt adequacy

**Approval Required:** Yes - before Phase 2

### CHECKPOINT #2 (End of Phase 2)
**Demo:**
- Test queries with historical data
- Review recommendations from few-shot learning
- Verify weighted scoring works
- Check MML command generation

**Approval Required:** Yes - before Phase 2.5

### CHECKPOINT #2.5 (End of Phase 2.5)
**Test:**
- Docker build successful
- Container deployment working
- Health checks passing
- Persistence verified

**Approval Required:** Yes - before Phase 3

### CHECKPOINT #3 (End of Phase 3)
**Review:**
- UI screenshots
- Cassava branding accuracy
- Query interface usability
- Recommendation display clarity

**Approval Required:** Yes - before Phase 4

### CHECKPOINT #4 (End of Phase 4)
**Demo:**
- Full 10-minute demo script
- Documentation completeness
- Test results review
- Production readiness assessment

**Approval Required:** Yes - before deployment

---

## DOCUMENT HISTORY

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-30 | Initial complete plan | Claude + Fadzai |

---

**END OF REBUILD PLAN**

Ready to implement when you approve.
