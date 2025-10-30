# Liquid Zimbabwe 4G System - Final Architecture

## Directory Structure (Post Strip-Down)

```
liquid_zimbabwe_optimizer/
├── README.md                                    # LZ-specific documentation
├── config.yaml                                 # Simplified LZ-only configuration
├── requirements.txt                             # Streamlined dependencies
├── docker-compose.yaml                         # Minimal container setup
├── Dockerfile                                  # Lightweight container
├── start_optimizer.py                          # Main entry point
│
├── core/                                       # Core system components
│   ├── __init__.py
│   ├── lz_agents.py                           # Pure LZ agents (no BubbleRAN)
│   ├── lz_orchestrator.py                     # LangGraph orchestration
│   └── lz_state.py                            # State management
│
├── network/                                    # Network integration layer
│   ├── __init__.py
│   ├── huawei_api.py                          # Huawei iMaster MAE client
│   ├── lz_connector.py                        # LZ network connector
│   ├── kpi_manager.py                         # 7 core KPIs management
│   ├── parameter_manager.py                   # 5 core parameters
│   └── mml_executor.py                        # MML command execution
│
├── tools/                                      # LZ-specific agent tools
│   ├── __init__.py
│   ├── lz_sql_tools.py                        # LZ database queries
│   ├── mml_tools.py                           # MML command generation
│   ├── kpi_calculation_tools.py               # KPI analysis tools
│   └── parameter_optimization_tools.py        # Parameter suggestion tools
│
├── ui/                                         # User interface
│   ├── __init__.py
│   ├── lz_dashboard.py                        # Main Streamlit dashboard
│   ├── cassava_theme.py                       # Cassava branding
│   ├── kpi_visualization.py                   # KPI charts and graphs
│   └── parameter_controls.py                  # Parameter adjustment UI
│
├── data/                                       # Data storage
│   ├── lz_kpis.db                            # LZ KPI database
│   ├── lz_parameters.db                       # Parameter history
│   └── optimization_history.db                # Agent decisions log
│
├── config/                                     # Configuration files
│   ├── kpi_definitions.yaml                   # 7 core KPI definitions
│   ├── parameter_definitions.yaml             # 5 core parameter definitions
│   ├── mml_templates.yaml                     # MML command templates
│   └── optimization_weights.yaml              # Optimization preferences
│
└── tests/                                      # Comprehensive test suite
    ├── unit/                                  # Unit tests
    ├── integration/                           # Integration tests
    ├── end_to_end/                           # E2E workflow tests
    └── performance/                           # Performance benchmarks
```