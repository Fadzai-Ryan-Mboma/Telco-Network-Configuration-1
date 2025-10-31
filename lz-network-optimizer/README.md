# Liquid Zimbabwe 4G Network Optimizer

**AI-Powered Network Optimization System**
Built with LangGraph, NVIDIA AI, and Huawei 4G Integration

---

## 🎯 Overview

The Liquid Zimbabwe 4G Network Optimizer is an agentic AI system that automatically monitors, analyzes, and optimizes 4G network performance across Liquid Zimbabwe's eNodeB sites. It uses a 6-agent workflow powered by NVIDIA's Llama 3.1 70B Instruct to make intelligent optimization decisions.

**Current Status:** ✅ Phase 2 Complete - Ready for Testing

---

## 🏗️ Architecture

### 6-Agent Workflow

```
┌─────────────────────┐
│ User Query          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. NETWORK CONNECTOR AGENT                                      │
│    • Queries Huawei API or historical database                  │
│    • Retrieves current KPIs and parameter values                │
│    • Automatic fallback if API unavailable                      │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. MONITORING AGENT                                             │
│    • Calculates weighted KPI scores (3-tier: 25/50/25)          │
│    • Compares against thresholds                                │
│    • Decides: OPTIMIZE or CONTINUE_MONITORING                   │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼ (if optimization needed)
┌─────────────────────────────────────────────────────────────────┐
│ 3. KPI ANALYTICS AGENT                                          │
│    • Analyzes 7-day KPI trends                                  │
│    • Identifies primary KPI issue                               │
│    • Prioritizes by tier weight (Tier 1 > Tier 2 > Tier 3)     │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. CONFIGURATION AGENT                                          │
│    • Uses 10 optimization rules                                 │
│    • Applies few-shot learning (5 past successes)               │
│    • Recommends parameter changes with justification            │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. VALIDATION AGENT                                             │
│    • Validates parameter ranges                                 │
│    • Assesses risk scores (1-10 scale)                          │
│    • Decides: APPROVED, REVIEW, or REJECTED                     │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼ (if approved)
┌─────────────────────────────────────────────────────────────────┐
│ 6. MML EXECUTOR AGENT                                           │
│    • Executes Huawei MML commands                               │
│    • Logs changes to database                                   │
│    • Verifies KPI improvements                                  │
│    • Automatic rollback on failure                              │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼
     ┌──────────┐
     │  RESULT  │
     └──────────┘
```

---

## 🔧 Technical Stack

### Core Technologies
- **LangGraph**: Multi-agent workflow orchestration
- **LangChain**: Tool integration and agent patterns
- **NVIDIA AI**: Llama 3.1 70B Instruct LLM
- **Huawei API**: iMaster MAE 4G network management
- **SQLite**: Unified database (KPIs, parameters, history)
- **Python 3**: Core implementation language

### Key Features
- 🤖 **10 LangChain Tools**: Huawei API, SQL, calculations, validation
- 📊 **3-Tier KPI Weighting**: Foundation (25%), Revenue (50%), Efficiency (25%)
- 🎓 **Few-Shot Learning**: 5 past optimization examples
- 🛡️ **Risk Assessment**: 1-10 scale safety scoring
- 🔄 **Automatic Fallback**: Works offline with historical data
- 📝 **MML Command Execution**: Direct Huawei eNodeB configuration

---

## 📁 Project Structure

```
lz-network-optimizer/
├── agents/                  # 6 LangGraph agents
│   ├── network_connector_agent.py
│   ├── monitoring_agent.py
│   ├── kpi_analytics_agent.py
│   ├── config_agent.py
│   ├── validation_agent.py
│   ├── mml_executor_agent.py
│   └── workflow.py          # LangGraph orchestration
├── tools/                   # 10 LangChain tools
│   ├── huawei_tools.py      # 5 Huawei API tools
│   ├── sql_tools.py         # 2 database query tools
│   ├── calculation_tools.py # 2 KPI calculation tools
│   └── validation_tools.py  # 2 safety validation tools
├── prompts/                 # 4-layer prompt system
│   ├── system_prompts.py    # Agent role definitions
│   ├── few_shot_examples.py # 5 optimization examples
│   └── context_builders.py  # Domain knowledge injection
├── domain/                  # Domain knowledge
│   ├── liquid_zimbabwe_parameters.py  # 5 Huawei parameters
│   ├── liquid_zimbabwe_kpi.py         # 7 KPI definitions
│   ├── mml_commands.py                # MML templates
│   └── optimization_rules.py          # 10 optimization rules
├── network/                 # Network integration
│   ├── huawei_api_client.py # API client (security-reviewed)
│   └── kpi_collector.py     # KPI collection with fallback
├── config/                  # Configuration files
│   ├── config.yaml          # System configuration
│   └── kpi_weights.yaml     # 3-tier KPI weights
├── data/                    # Database and data
│   ├── schema.sql           # Database schema (3 tables)
│   ├── lz_network.db        # SQLite database (168 records)
│   └── historical_data.csv  # Historical KPI data
├── docker/                  # 🐳 Docker containerization (Phase 2.5)
│   ├── Dockerfile           # Production container definition
│   ├── docker-compose.yml   # Container orchestration
│   ├── .dockerignore        # Exclude unnecessary files
│   ├── healthcheck.py       # Container health check
│   └── entrypoint.sh        # Startup script
├── deployment/              # 📚 Deployment documentation
│   └── DOCKER_DEPLOYMENT_GUIDE.md  # Complete deployment guide
├── scripts/                 # Utility scripts
│   └── import_historical_data.py
├── tests/                   # Test suite
│   ├── test_workflow.py     # Integration tests
│   └── test_with_api.py     # NVIDIA API test
├── requirements.txt         # Python dependencies
├── main.py                  # CLI entry point
└── TESTING_GUIDE.md         # Complete testing guide
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set NVIDIA API Key

```bash
export NVIDIA_API_KEY='nvapi-your-key-here'
```

Get your key from: https://build.nvidia.com/

### 3. Run Tests

```bash
cd lz-network-optimizer

# Quick API test (30 seconds)
python3 test_with_api.py

# Full integration test (3-5 minutes)
python3 test_workflow.py
```

### 4. Run Optimization (CLI or Web UI)

**Option A: Web UI (Recommended - Phase 3)**
```bash
# Start Streamlit dashboard
streamlit run ui/app.py

# Open browser to http://localhost:8501
# 1. Select site from dropdown
# 2. Enter natural language query
# 3. Click "Run Optimization"
# 4. Review AI recommendations
```

**Option B: Command Line**
```bash
# List available sites
python3 main.py --list-sites

# Optimize a site
python3 main.py --site "MSH0013-Bindura-Zaoga" --query "Optimize download speed"
```

---

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# 1. Configure environment
cp .env.template .env
# Edit .env with your NVIDIA API key and Huawei credentials

# 2. Build container
docker compose -f docker/docker-compose.yml build

# 3. Run tests in container
docker compose -f docker/docker-compose.yml run --rm lz-optimizer \
  python3 test_workflow.py

# 4. Optimize a site
docker compose -f docker/docker-compose.yml run --rm lz-optimizer \
  python3 main.py optimize --site MSH0013-Bindura-Zaoga
```

### What's Included

- **Base Image:** python:3.11-slim (~600MB)
- **Security:** Non-root user execution
- **Health Checks:** Automatic container monitoring
- **Volume Mounts:** Database and config persistence
- **Resource Limits:** 2GB RAM, 2 CPUs

### Features

✅ Single-command deployment
✅ Automatic environment setup
✅ Database persistence via volumes
✅ Health monitoring
✅ Production-ready configuration

### Complete Guide

See [deployment/DOCKER_DEPLOYMENT_GUIDE.md](deployment/DOCKER_DEPLOYMENT_GUIDE.md) for:
- Detailed build instructions
- Configuration options
- Production deployment
- Troubleshooting
- Maintenance procedures

---

## 📊 KPI System

### 7 Monitored KPIs

**Tier 1: Foundation (25% weight)**
- Network Access Success (RACH) - 25%

**Tier 2: Revenue & Experience (50% weight)**
- Download Speed - 20%
- Download Quality - 15%
- Upload Speed - 15%

**Tier 3: Efficiency (25% weight)**
- Upload Quality - 10%
- Control Channel Load - 10%
- Feedback Channel Load - 5%

### Thresholds
- Network Access: ≥ 95%
- Download Speed: ≥ 50 Mbps
- Upload Speed: ≥ 20 Mbps
- Quality: ≥ 95%
- Load: ≤ 80%

---

## ⚙️ Parameters

### 5 Tunable Huawei 4G Parameters

1. **reference_signal_power_pdschcfg**
   - Range: -600 to 500 (0.1 dBm units)
   - Impact: Network access, download speed

2. **a3_event_offset**
   - Range: 0 to 30 dB
   - Impact: Handover performance

3. **t310_timer**
   - Range: 0 to 10000 ms
   - Impact: Radio link failure tolerance

4. **p0_nominal_pusch**
   - Range: -126 to -40 dBm
   - Impact: Upload speed and quality

5. **pdcch_aggregation_level**
   - Values: 1, 2, 4, 8
   - Impact: Control channel load, download quality

---

## 🧪 Testing

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive testing instructions.

**Test Coverage:**
- ✅ Database connectivity (4 sites, 168 records)
- ✅ Tool functionality (10 tools)
- ✅ Prompt system (6 agents, 5 examples)
- ⚠️ Workflow orchestration (requires NVIDIA_API_KEY)

---

## 📈 Statistics

- **Code**: ~9,000 lines Python
- **Files**: 43 files across 8 modules
- **Agents**: 6 (744 lines)
- **Tools**: 10 (2,096 lines)
- **Prompts**: 3 layers (954 lines)
- **Database**: 3 tables, 168 historical records
- **Sites**: 4 test sites in Zimbabwe

---

## 🔒 Security

- ✅ No hardcoded credentials
- ✅ Environment variable configuration
- ✅ SQL injection prevention (parameterized queries)
- ✅ Read-only database tools
- ✅ Parameter range validation
- ✅ Risk scoring before execution
- ✅ API client security reviewed (5/5 stars)

---

## 📝 Example Usage

### Check Network Status
```bash
python3 main.py --site "MSH0013-Bindura-Zaoga" --offline
```

### Optimize Specific Issue
```bash
python3 main.py --site "MSH-0014-Chipadze" --query "Fix low download speed"
```

### Verbose Logging
```bash
python3 main.py --site "MSH0013-Bindura-Zaoga" --verbose
```

---

## 🎯 Next Steps

- [ ] **Phase 2.5**: Docker containerization (1 day)
- [ ] **Checkpoint #2**: Demo to stakeholders
- [ ] **Phase 3**: Streamlit UI development
- [ ] **Production**: Deploy to Liquid Zimbabwe network

---

## 📚 Documentation

- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Complete testing instructions
- [config/config.yaml](config/config.yaml) - System configuration
- [config/kpi_weights.yaml](config/kpi_weights.yaml) - KPI weighting system
- [data/schema.sql](data/schema.sql) - Database schema

---

## 🏆 Achievements

✅ **Phase 0**: Preparation & asset extraction
✅ **Phase 1**: Architecture design & documentation
✅ **Phase 2**: Core implementation (Days 1-8)
- Day 1: Project setup & database ✅
- Days 2-3: Tools implementation ✅
- Day 4: Prompts layer ✅
- Days 5-8: Agents & workflow ✅

**Current Status**: Ready for NVIDIA API testing

---

## 🤝 Credits

Built with Claude Code
Based on NVIDIA Telco Network Configuration Blueprint
Powered by Llama 3.1 70B Instruct
Integrated with Huawei iMaster MAE API

---

## 📄 License

Proprietary - Liquid Zimbabwe / Cassava Technologies
