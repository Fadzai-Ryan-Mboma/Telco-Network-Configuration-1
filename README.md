# Liquid Zimbabwe 4G Network Optimizer

**Intelligent AI-powered network optimization for Liquid Zimbabwe's 4G infrastructure**

Powered by NVIDIA AI and built on the [Telco Network Configuration Blueprint](https://build.nvidia.com/nvidia/telco-network-configuration)

---

## Project Status

**Phase**: Phase 1 Complete - Architecture Design
**Next**: Phase 2 - Core Agent Implementation (8 days)
**Timeline**: 23 days to production-ready demo

### Current Progress
- ✅ Phase 0: Credentials extracted, assets preserved (2 days)
- ✅ Phase 1: Architecture designed, documentation complete (3 days)
- ⏳ Phase 2: Agent implementation with few-shot prompting (8 days)
- ⏳ Phase 2.5: Docker containerization (1 day)
- ⏳ Phase 3: UI with Cassava branding (4 days)
- ⏳ Phase 4: Testing & demo prep (5 days)

---

## Overview

### What It Does
Automates 4G network parameter optimization for Liquid Zimbabwe sites using AI agents that:
- **Monitor** network KPIs in real-time
- **Analyze** performance issues with root cause identification
- **Recommend** parameter changes with MML commands
- **Validate** changes safely with automatic rollback
- **Execute** optimizations on live Huawei 4G network

### Technology Stack
- **AI/LLM**: NVIDIA NIM (Llama 3.1 70B Instruct) via LangGraph agents
- **Network**: Huawei iMaster MAE API (4G LTE)
- **UI**: Streamlit with Cassava branding
- **Database**: SQLite (unified KPI + optimization history)
- **Deployment**: Docker (one-command deployment)

---

## Architecture

### 6-Agent Workflow
```
┌────────────┐     ┌─────────────┐     ┌──────────────┐
│  Network   │────▶│ Monitoring  │────▶│ KPI Analytics│
│ Connector  │     │    Agent    │     │    Agent     │
└────────────┘     └─────────────┘     └──────────────┘
                            │                    │
                            ▼                    ▼
                   ┌─────────────┐      ┌──────────────┐
                   │Configuration│────▶ │  Validation  │
                   │    Agent    │      │    Agent     │
                   └─────────────┘      └──────────────┘
                            │                    │
                            ▼                    ▼
                   ┌─────────────┐
                   │ MML Executor│
                   │    Agent    │
                   └─────────────┘
```

**Core Agents** (Enhanced from Nvidia Blueprint):
1. **Configuration Agent** - Recommends parameter changes based on KPI issues
2. **Validation Agent** - Safely applies changes with rollback capability
3. **Monitoring Agent** - Continuous KPI tracking with weighted scoring

**Extension Agents** (New for LZ):
4. **KPI Analytics Agent** - Deep analysis and root cause identification
5. **Network Connector Agent** - Huawei API connection management
6. **MML Executor Agent** - Safe MML command execution

### Domain Knowledge
- **5 Huawei 4G Parameters**: reference_signal_power, a3_event_offset, t310_timer, p0_nominal_pusch, pdcch_aggregation_level
- **7 Weighted KPIs**: Network Access Success (25%), Download Speed (20%), Download Quality (15%), Upload Speed (15%), Upload Quality (10%), Control Channel Load (10%), Feedback Channel Load (5%)
- **10 Optimization Rules**: Proven parameter-to-KPI mappings
- **Real Network Data**: Bindura Hospital, Chiwaridzo, and other LZ sites

---

## Documentation

### Phase 1 Documentation (Complete)
- **[REBUILD_PLAN_COMPLETE.md](docs/REBUILD_PLAN_COMPLETE.md)** - 23-page comprehensive rebuild plan
- **[LESSONS_LEARNED.md](docs/LESSONS_LEARNED.md)** - Memorial retrospective from first attempt
- **[NVIDIA_TO_LZ_MAPPING.md](docs/NVIDIA_TO_LZ_MAPPING.md)** - 50-page mapping from Nvidia blueprint to LZ
- **[PROMPT_INTEGRATION_PLAN.md](docs/PROMPT_INTEGRATION_PLAN.md)** - Few-shot prompting strategy
- **[PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Complete directory design (~30 files)
- **[PHASE_0_COMPLETE.md](docs/PHASE_0_COMPLETE.md)** - Phase 0 completion report

### Reference Materials
- **[rebuild-assets/](rebuild-assets/)** - Extracted production-ready assets (287KB)
  - Domain knowledge (parameters, KPIs, optimization rules)
  - Prompt architecture (1,338-line AGENT_PROMPTS_ARCHITECTURE.md)
  - Huawei API client (security reviewed: 5/5 stars)
  - Cassava branding assets
  - Historical data

---

## Quick Start (Phase 2 and Beyond)

### Prerequisites
- Python 3.10-3.13
- NVIDIA API key
- Huawei iMaster MAE API credentials
- Git

### Installation (Future - Phase 2)
```bash
# Clone repository
git clone [repository-url]
cd Telco-Network-Configuration

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.template .env
# Edit .env with your credentials

# Run application
streamlit run ui/app.py
```

### Docker Deployment (Future - Phase 2.5)
```bash
# One-command deployment
./scripts/deploy.sh

# Access UI
open http://localhost:8501
```

---

## Project Structure

```
/Telco-Network-Configuration/
├── legacy/                    # Previous implementation (reference only)
├── docs/                      # Current documentation
├── rebuild-assets/            # Extracted production assets
├── nvidia-reference/          # Nvidia blueprint (reference)
├── CREDENTIALS_SECURE.txt     # Secure credentials (gitignored)
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── .gitignore

Future structure (Phase 2):
├── lz-network-optimizer/      # New implementation
│   ├── agents/                # 6 agents + workflow
│   ├── tools/                 # 10 tools (Huawei, SQL, calc, validation)
│   ├── prompts/               # Few-shot prompting system
│   ├── domain/                # Parameters, KPIs, optimization rules
│   ├── network/               # Huawei API client
│   ├── ui/                    # Streamlit app with Cassava branding
│   ├── config/                # Configuration files
│   ├── data/                  # Database and historical data
│   └── tests/                 # Test suite
```

---

## Development Roadmap

### Phase 2: Core Agent Implementation (8 days) - NEXT
**Objectives**:
- Implement 6 agents with few-shot prompting
- Integrate Huawei API tools
- Build weighted KPI scoring system
- Create LangGraph workflow

**Deliverables**:
- Working agent system with historical data
- Natural language query → MML recommendation flow
- Test coverage for all agents

### Phase 2.5: Docker Containerization (1 day)
**Objectives**:
- Package application in Docker
- One-command deployment
- Persistent data volumes

### Phase 3: UI with Branding (4 days)
**Objectives**:
- Clean Streamlit interface (~400 lines)
- Cassava orange branding
- Natural language query interface
- Results visualization

### Phase 4: Testing & Demo (5 days)
**Objectives**:
- Comprehensive test suite
- Demo script (<10 minutes)
- Production readiness validation
- Documentation completion

---

## Key Features

### Intelligent Optimization
- ✅ **Few-Shot Learning**: AI learns from past optimizations
- ✅ **Weighted KPI Scoring**: 3-tier business-aligned metrics
- ✅ **Root Cause Analysis**: Deep performance issue diagnosis
- ✅ **Safety Validation**: Parameter range checks + rollback
- ✅ **Audit Trail**: Complete optimization history

### Production-Ready
- ✅ **Live Network Integration**: Direct Huawei 4G API
- ✅ **Secure Authentication**: OAuth2 token-based
- ✅ **Graceful Fallback**: Works offline with historical data
- ✅ **Rate Limiting**: API protection
- ✅ **Error Recovery**: Retry logic + exponential backoff

### User Experience
- ✅ **Natural Language Queries**: "Download speed is low at Bindura Hospital"
- ✅ **Clear Recommendations**: MML commands with explanations
- ✅ **Risk Assessment**: Low/Medium/High risk scoring
- ✅ **Transparent Decisions**: Show reasoning and expected improvements
- ✅ **Cassava Branding**: Professional enterprise look

---

## API Credentials

**Required Credentials** (in CREDENTIALS_SECURE.txt):
- NVIDIA API Key: For LLM inference
- Huawei API URL: iMaster MAE endpoint
- Huawei Username/Password: Authentication

**Security Note**: CREDENTIALS_SECURE.txt is gitignored. Use .env.template for deployment.

---

## KPI Weighting System

### 3-Tier Weighted Scoring

**Tier 1: Foundation (25%)**
- Network Access Success: 25% (RACH Setup Success Rate)

**Tier 2: Revenue & Experience (50%)**
- Download Speed: 20% (DL Throughput)
- Download Quality: 15% (DL IBLER)
- Upload Speed: 15% (UL Throughput)
- Upload Quality: 10% (UL IBLER)

**Tier 3: Efficiency (25%)**
- Control Channel Load: 10% (PDCCH CCE Usage)
- Feedback Channel Load: 5% (PUCCH Usage)

**Rationale**: Aligns with telecom industry standards (3GPP, NGMN) and Zimbabwean market (data-heavy usage)

---

## Contributing

### Git Workflow
- **Main Branch**: `rebuild/lz-nvidia-hybrid`
- **Archive Branch**: `archive/pre-reset-backup-2025-10-30`
- **Tag**: `v2.0.0-before-reset` (memorial backup)

### Testing Requirements
All PRs must include:
- Unit tests for new functionality
- Integration tests for agent workflows
- Documentation updates
- No decrease in code coverage

### Code Style
- Python: PEP 8 (black formatting)
- Type hints required for public APIs
- Docstrings for all public functions
- Maximum line length: 120 characters

---

## License

Copyright © 2025 Liquid Zimbabwe / Cassava AI

*License details to be determined*

---

## Support

**Project Team**: Liquid Zimbabwe Network Optimization
**Technical Lead**: [Contact Information]
**Documentation**: See `docs/` folder for detailed guides

---

## Acknowledgments

- **NVIDIA**: Base blueprint and NIM infrastructure
- **BubbleRAN**: Open RAN reference architecture
- **Liquid Zimbabwe**: Domain expertise and network access
- **Cassava AI**: AI/ML development and deployment

---

## Status & Milestones

| Milestone | Status | Date | Notes |
|-----------|--------|------|-------|
| Phase 0: Preparation | ✅ Complete | 2025-10-30 | Asset extraction complete |
| Phase 1: Architecture | ✅ Complete | 2025-10-30 | Documentation complete |
| Phase 2: Implementation | ⏳ Pending | TBD | 8 days estimated |
| Phase 2.5: Docker | ⏳ Pending | TBD | 1 day estimated |
| Phase 3: UI | ⏳ Pending | TBD | 4 days estimated |
| Phase 4: Testing | ⏳ Pending | TBD | 5 days estimated |
| **Production Demo** | ⏳ Pending | **TBD** | **23 days total** |

---

**Last Updated**: 2025-10-30
**Project Phase**: Phase 1 Complete - Ready for Phase 2 Implementation
