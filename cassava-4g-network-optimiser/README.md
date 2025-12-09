# Cassava 4G Network Optimiser

AI-powered 4G LTE network optimization for Huawei eNodeB infrastructure, built on NVIDIA NIM and LangGraph.

![Cassava Technologies](ui/assets/logos/cassava-logo.svg)

## Overview

The Cassava 4G Network Optimiser is an intelligent system that analyzes network performance, identifies optimization opportunities, and generates actionable MML (Man-Machine Language) commands for Huawei eNodeB equipment.

### Key Features

- **Real-time KPI Analysis**: Monitors and analyzes 15+ network KPIs across 3 tiers
- **AI-Powered Recommendations**: Uses NVIDIA NIM (Llama 3.1 70B) for intelligent analysis
- **Agentic Workflow**: 6-agent pipeline for comprehensive optimization
- **Safe Command Generation**: Validated MML commands with rollback support
- **Historical Correlation**: Leverages historical data for pattern recognition
- **Modern UI**: Streamlit-based interface with dark/light mode

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit UI                              │
│  (Site Selection → Query Input → Agent Progress → Results)      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LangGraph Orchestrator                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Data    │→│   KPI    │→│  Root    │→│  Recommendation  │ │
│  │Collector │  │ Analyzer │  │  Cause   │  │     Engine       │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
│                                                    │             │
│                              ┌──────────┐  ┌──────────────────┐ │
│                              │Validation│←│    Execution     │ │
│                              │  Agent   │  │     Agent        │ │
│                              └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ Huawei MAE   │ │   SQLite     │ │  NVIDIA NIM  │
        │    API       │ │   Database   │ │    LLM       │
        └──────────────┘ └──────────────┘ └──────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- NVIDIA NIM API key
- Huawei iMaster MAE credentials

### Installation

```bash
# Clone the repository
git clone https://github.com/cassava/4g-network-optimiser.git
cd cassava-4g-network-optimiser

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python -m cassava_optimizer.scripts.init_db

# Run the application
streamlit run ui/app.py
```

### Docker

```bash
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NVIDIA_API_KEY` | NVIDIA NIM API key | Yes |
| `HUAWEI_MAE_HOST` | Huawei iMaster MAE hostname | Yes |
| `HUAWEI_MAE_USERNAME` | MAE username | Yes |
| `HUAWEI_MAE_PASSWORD` | MAE password | Yes |
| `DATABASE_URL` | SQLite database path | No (default: `./data/cassava_network.db`) |
| `LOG_LEVEL` | Logging level | No (default: `INFO`) |

### KPI Weights

The system uses a 3-tier KPI weighting system:

- **Foundation KPIs (25%)**: RRC Success Rate, E-RAB Setup Success Rate
- **Revenue/Experience KPIs (50%)**: Throughput, Latency, Handover Success
- **Efficiency KPIs (25%)**: PRB Utilization, Spectral Efficiency

Configure in `config/kpi_weights.yaml`.

## Agents

| Agent | Purpose |
|-------|---------|
| **Data Collector** | Fetches live metrics from Huawei MAE API |
| **KPI Analyzer** | Evaluates KPIs against thresholds and historical baselines |
| **Root Cause Agent** | Identifies underlying issues using LLM analysis |
| **Recommendation Agent** | Generates optimization recommendations |
| **Validation Agent** | Validates recommendations against safety rules |
| **Execution Agent** | Generates MML commands and tracks execution |

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=cassava_optimizer

# Type checking
mypy src/

# Linting
ruff check src/ tests/
ruff format src/ tests/
```

## Project Structure

```
cassava-4g-network-optimiser/
├── src/cassava_optimizer/
│   ├── config/           # Configuration management
│   ├── domain/           # Domain models and business logic
│   ├── infrastructure/   # External integrations (DB, API, LLM)
│   ├── agents/           # LangGraph agents
│   ├── workflow/         # Workflow orchestration
│   ├── tools/            # LangChain tools
│   └── utils/            # Utilities
├── ui/                   # Streamlit UI
├── tests/                # Test suite
├── docker/               # Docker configuration
└── data/                 # Database and data files
```

## License

Proprietary - Cassava Technologies © 2024

## Support

For support, contact: network-ai@cassavatech.com
