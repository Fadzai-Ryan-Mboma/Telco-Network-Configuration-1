# Liquid Zimbabwe 4G Network Optimizer - System Architecture

**Document Version:** 1.0
**Date:** 2025-11-25
**Last Updated:** Phase 5 - Production Deployment with Fixes

---

## Table of Contents
1. [High-Level Architecture](#high-level-architecture)
2. [Component Diagram](#component-diagram)
3. [Data Flow Diagram](#data-flow-diagram)
4. [Agent Workflow](#agent-workflow)
5. [Database Schema](#database-schema)
6. [API Integration](#api-integration)
7. [Deployment Architecture](#deployment-architecture)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LZ 4G NETWORK OPTIMIZER                          │
│                    (AI-Powered Network Optimization)                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
       ┌────────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
       │   User Layer    │  │  Agent       │  │  Network         │
       │                 │  │  Framework   │  │  Integration     │
       │  • Streamlit UI │  │              │  │                  │
       │  • REST API     │  │  • NVIDIA    │  │  • Huawei API    │
       │  • ngrok Tunnel │  │    NIM       │  │  • MML Commands  │
       │  • nginx Proxy  │  │  • LangGraph │  │  • OAuth2        │
       └─────────────────┘  └──────────────┘  └──────────────────┘
                │                   │                   │
                └───────────────────┼───────────────────┘
                                    │
                         ┌──────────▼──────────┐
                         │   Data Layer        │
                         │                     │
                         │  • SQLite DB        │
                         │  • KPI History      │
                         │  • Optimization Log │
                         │  • Parameter Changes│
                         └─────────────────────┘
```

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐         ┌──────────────────┐                        │
│  │  Streamlit UI    │         │   Nginx Proxy    │                        │
│  │  (app.py)        │◄────────┤   (Port 80)      │                        │
│  │                  │         │                  │                        │
│  │  • Site Selector │         │  • Reverse Proxy  │                        │
│  │  • Query Input   │         │  • WebSocket      │                        │
│  │  • Results View  │         │  • SSL Support    │                        │
│  │  • Agent Logs    │         └──────────────────┘                        │
│  │  • Port 8501     │                  ▲                                   │
│  └────────┬─────────┘                  │                                   │
│           │                            │                                   │
│           │         ┌──────────────────┴────────┐                          │
│           │         │   ngrok Tunnel            │                          │
│           │         │   (Internet Access)       │                          │
│           │         │                           │                          │
│           │         │  • https://<random>.      │                          │
│           │         │    ngrok-free.app         │                          │
│           │         │  • Port Forwarding        │                          │
│           │         └───────────────────────────┘                          │
│           │                                                                 │
└───────────┼─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          WORKFLOW ORCHESTRATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Workflow Interface (workflow_interface.py)                          │  │
│  │                                                                      │  │
│  │  • Input: {site_name, cell_id, user_query}                          │  │
│  │  • Output: {status, recommendations, mml_commands, risk_level}      │  │
│  │  • Handles state management                                         │  │
│  │  • Routes to agent workflow                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  LangGraph Workflow (agents/workflow.py)                            │  │
│  │                                                                      │  │
│  │   START → Monitoring → Decision → KPI Analytics →                   │  │
│  │           Configuration → Validation → MML Executor → END           │  │
│  │                                                                      │  │
│  │   Routing Logic:                                                    │  │
│  │   • needs_optimization = True  → Continue to KPI Analytics          │  │
│  │   • needs_optimization = False → END workflow                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AGENT FRAMEWORK (6 Agents)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐      ┌─────────────────────┐                     │
│  │  1. Monitoring      │      │  2. KPI Analytics   │                     │
│  │     Agent           │──────▶│     Agent           │                     │
│  │                     │      │                     │                     │
│  │  • Query KPIs       │      │  • Calculate Score  │                     │
│  │  • Check Thresholds │      │  • Analyze Trends   │                     │
│  │  • Detect Issues    │      │  • Identify Root    │                     │
│  │  • FALLBACK: Direct │      │    Cause            │                     │
│  │    DB Query         │      │  • Prioritize KPIs  │                     │
│  │  • User Intent      │      │  • Weighted Scoring │                     │
│  │    Detection        │      │    (3-Tier)         │                     │
│  └─────────────────────┘      └─────────────────────┘                     │
│           │                              │                                │
│           │                              ▼                                 │
│           │         ┌─────────────────────────────────────┐                │
│           │         │  3. Configuration Agent             │                │
│           │         │                                     │                │
│           │         │  • Apply Optimization Rules (10)    │                │
│           │         │  • Few-Shot Learning                │                │
│           │         │  • Calculate Parameter Changes      │                │
│           │         │  • Expected Impact Prediction       │                │
│           │         └─────────────────────────────────────┘                │
│           │                              │                                  │
│           │                              ▼                                  │
│           │         ┌─────────────────────────────────────┐                │
│           │         │  4. Validation Agent                │                │
│           │         │                                     │                │
│           │         │  • Safety Checks                    │                │
│           │         │  • Risk Scoring (1-10)              │                │
│           │         │  • Range Validation                 │                │
│           │         │  • Conflict Detection               │                │
│           │         │  • Approval Decision                │                │
│           │         └─────────────────────────────────────┘                │
│           │                              │                                  │
│           │                              ▼                                  │
│           │         ┌─────────────────────────────────────┐                │
│           │         │  5. MML Executor Agent              │                │
│           │         │                                     │                │
│           │         │  • Generate MML Commands            │                │
│           │         │  • Execute (6 per parameter)        │                │
│           │         │  • Log to Database                  │                │
│           │         │  • Rollback on Failure              │                │
│           │         │  • Verify Changes                   │                │
│           │         └─────────────────────────────────────┘                │
│           │                                                                 │
└───────────┼─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TOOLS & UTILITIES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │  SQL Tools       │  │  Huawei Tools    │  │  Calculation     │         │
│  │                  │  │                  │  │  Tools           │         │
│  │  • execute_lz_   │  │  • query_huawei_ │  │                  │         │
│  │    kpi_sql       │  │    parameter     │  │  • calc_weighted_│         │
│  │  • get_latest_   │  │  • modify_huawei_│  │    kpi_score     │         │
│  │    kpis_direct   │  │    parameter     │  │  • calc_kpi_     │         │
│  │    (FALLBACK)    │  │  • query_huawei_ │  │    trend         │         │
│  │  • execute_      │  │    kpi           │  │  • validate_     │         │
│  │    historical_   │  │  • execute_mml_  │  │    parameter_    │         │
│  │    sql           │  │    command       │  │    range         │         │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘         │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Rollback Manager (rollback_manager.py)                              │  │
│  │                                                                      │  │
│  │  • capture_pre_state()  - Save current values (6 cells)             │  │
│  │  • execute_changes()    - Apply modifications                       │  │
│  │  • rollback_changes()   - Restore original values                   │  │
│  │  • verify_rollback()    - Confirm restoration                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL INTEGRATIONS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────┐              ┌──────────────────────┐            │
│  │  NVIDIA NIM API      │              │  Huawei iMaster MAE  │            │
│  │                      │              │  API                 │            │
│  │  • Model: Llama 3.1  │              │                      │            │
│  │    70B Instruct      │              │  • OAuth2 Token Auth │            │
│  │  • Temperature: 0.5  │              │  • MML Command Exec  │            │
│  │  • Used by all       │              │  • Cell-by-Cell Mod  │            │
│  │    6 agents          │              │  • Site-Wide Query   │            │
│  │  • ReAct Framework   │              │  • Real-time KPIs    │            │
│  └──────────────────────┘              └──────────────────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  SQLite Database: lz_network.db                                    │    │
│  │                                                                    │    │
│  │  ┌─────────────────────┐    ┌─────────────────────┐              │    │
│  │  │  kpi_data           │    │  parameter_changes  │              │    │
│  │  │                     │    │                     │              │    │
│  │  │  • site_name        │    │  • site_name        │              │    │
│  │  │  • cell_id          │    │  • cell_id          │              │    │
│  │  │  • timestamp        │    │  • timestamp        │              │    │
│  │  │  • network_access   │    │  • parameter_name   │              │    │
│  │  │  • download_speed   │    │  • old_value        │              │    │
│  │  │  • upload_speed     │    │  • new_value        │              │    │
│  │  │  • download_quality │    │  • reason           │              │    │
│  │  │  • upload_quality   │    │  • agent_id         │              │    │
│  │  │  • control_load     │    │  • success          │              │    │
│  │  │  • feedback_load    │    └─────────────────────┘              │    │
│  │  │  • data_source      │                                          │    │
│  │  └─────────────────────┘    ┌─────────────────────┐              │    │
│  │                             │  optimization_      │              │    │
│  │  ┌─────────────────────┐    │  history            │              │    │
│  │  │  sites              │    │                     │              │    │
│  │  │                     │    │  • site_name        │              │    │
│  │  │  • site_id          │    │  • timestamp        │              │    │
│  │  │  • site_name        │    │  • issue            │              │    │
│  │  │  • location         │    │  • recommendations  │              │    │
│  │  │  • cell_count       │    │  • mml_commands     │              │    │
│  │  │  • active           │    │  • success          │              │    │
│  │  └─────────────────────┘    │  • pre_kpis         │              │    │
│  │                             │  • post_kpis        │              │    │
│  │                             └─────────────────────┘              │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

### User Query to Optimization Workflow

```
┌─────────┐
│  USER   │
│ Input   │
└────┬────┘
     │
     │ 1. User submits query
     │    "improve speed for MSH-0014-Chipadze"
     │
     ▼
┌─────────────────────┐
│  Streamlit UI       │
│  (ui/app.py)        │
└──────────┬──────────┘
           │
           │ 2. Parse input
           │    site_name = "MSH-0014-Chipadze"
           │    user_query = "improve speed..."
           │
           ▼
┌─────────────────────────────┐
│  Workflow Interface         │
│  (workflow_interface.py)    │
└──────────┬──────────────────┘
           │
           │ 3. Initialize state
           │    {site_name, cell_id, user_query,
           │     needs_optimization: False}
           │
           ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                       AGENT WORKFLOW                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┐  4. Query KPIs                                      │
│  │  Monitoring     │◄──────────────┐                                     │
│  │  Agent          │               │                                     │
│  └────────┬────────┘               │                                     │
│           │                        │                                     │
│           │ 5. SQL Error?          │                                     │
│           │                        │                                     │
│           ├─── YES ────────────────┘                                     │
│           │    Use get_latest_kpis_direct()                              │
│           │    (FALLBACK)                                                │
│           │                                                              │
│           │ 6. Check thresholds                                          │
│           │    • download_speed: 45 Mbps < 50 Mbps (BELOW)              │
│           │                                                              │
│           │ 7. Check user query                                          │
│           │    • "IMPROVE" ✓                                             │
│           │    • "SPEED" ✓                                               │
│           │                                                              │
│           │ 8. DECISION:                                                 │
│           │    needs_optimization = TRUE                                 │
│           │    (keyword match OR threshold violation)                    │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐  9. Calculate weighted score                       │
│  │  KPI Analytics  │     Analyze trends                                 │
│  │  Agent          │     Identify primary issue                         │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           │ 10. Primary KPI Issue: Download Speed                        │
│           │     Weighted Score: 72 (FAIR)                                │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐  11. Apply Optimization Rules                      │
│  │  Configuration  │      Rule: Low download speed                      │
│  │  Agent          │      → Increase reference signal power             │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           │ 12. Recommendation:                                          │
│           │     reference_signal_power: -200 → -180                      │
│           │     Expected improvement: +10 Mbps                           │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐  13. Safety checks                                 │
│  │  Validation     │      Risk score: 4/10 (MEDIUM)                     │
│  │  Agent          │      Range check: VALID                            │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           │ 14. Status: APPROVED                                         │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐  15. Generate 6 MML commands                       │
│  │  MML Executor   │      (one per cell)                                │
│  │  Agent          │      Execute or Dry-Run mode                       │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           │ 16. Commands:                                                │
│           │     MOD PDSCHCFG:LOCALCELLID=1,REFERENCESIGNALPWR=-180;     │
│           │     MOD PDSCHCFG:LOCALCELLID=2,REFERENCESIGNALPWR=-180;     │
│           │     ... (6 total)                                            │
│           │                                                              │
└───────────┼───────────────────────────────────────────────────────────────┘
            │
            │ 17. Return result
            │     {status, recommendations,
            │      mml_commands, risk_level}
            │
            ▼
┌─────────────────────────────┐
│  Workflow Interface         │
│  Format response            │
└──────────┬──────────────────┘
           │
           │ 18. Display to user
           │
           ▼
┌─────────────────────┐
│  Streamlit UI       │
│  Show results       │
└─────────────────────┘
```

---

## Agent Workflow - Detailed State Machine

```
                              ┌────────────┐
                              │   START    │
                              └─────┬──────┘
                                    │
                                    │ State: {site_name, cell_id,
                                    │         user_query, ...}
                                    │
                                    ▼
                   ┌────────────────────────────────┐
                   │     MONITORING AGENT           │
                   │                                │
                   │  Tools:                        │
                   │  • execute_lz_kpi_sql          │
                   │  • get_latest_kpis_direct ⚡   │
                   │  • calc_weighted_kpi_score     │
                   │  • calc_kpi_trend              │
                   │                                │
                   │  Decision Logic:               │
                   │  needs_opt = (                 │
                   │    "OPTIMIZE" in output OR     │
                   │    "BELOW" in output OR        │
                   │    "IMPROVE" in user_query OR  │
                   │    "SPEED" in user_query OR    │
                   │    "COVERAGE" in user_query    │
                   │  )                             │
                   └────────────┬───────────────────┘
                                │
                                │ Update state:
                                │ needs_optimization = True/False
                                │
                                ▼
                   ┌────────────────────────────────┐
                   │   ROUTING DECISION             │
                   │                                │
                   │   if needs_optimization:       │
                   │       → KPI Analytics          │
                   │   else:                        │
                   │       → END                    │
                   └────────┬───────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
        needs_opt=True           needs_opt=False
              │                           │
              ▼                           ▼
┌─────────────────────────┐      ┌────────────────┐
│  KPI ANALYTICS AGENT    │      │      END       │
│                         │      │                │
│ Tools:                  │      │ Return:        │
│ • calc_weighted_kpi_    │      │ "No optimization
│   score                 │      │  needed"       │
│ • calc_kpi_trend        │      └────────────────┘
│ • execute_lz_kpi_sql    │
│                         │
│ Output:                 │
│ • Primary KPI issue     │
│ • Weighted score        │
│ • Tier breakdown        │
└──────────┬──────────────┘
           │
           │ State: primary_kpi_issue
           │
           ▼
┌─────────────────────────────┐
│  CONFIGURATION AGENT        │
│                             │
│ Tools:                      │
│ • query_huawei_parameter    │
│ • execute_historical_sql    │
│ • validate_parameter_range  │
│                             │
│ Apply Optimization Rules:   │
│ • Low speed → ↑ signal pwr  │
│ • High load → ↑ aggregation │
│ • Poor quality → ↑ PDCCH    │
│                             │
│ Output:                     │
│ • Parameter changes         │
│ • Expected improvements     │
│ • Confidence level          │
└──────────┬──────────────────┘
           │
           │ State: config_output
           │
           ▼
┌─────────────────────────────┐
│  VALIDATION AGENT           │
│                             │
│ Tools:                      │
│ • validate_parameter_range  │
│ • assess_risk_score         │
│ • validate_optimization_    │
│   safety                    │
│                             │
│ Checks:                     │
│ • Range validation          │
│ • Risk scoring (1-10)       │
│ • Conflict detection        │
│ • Side effect analysis      │
│                             │
│ Decision:                   │
│ • APPROVED (risk ≤ 7)       │
│ • REVIEW (risk = 8)         │
│ • REJECTED (risk ≥ 9)       │
└──────────┬──────────────────┘
           │
           │ State: validation_status
           │
           ▼
┌─────────────────────────────┐
│  MML EXECUTOR AGENT         │
│                             │
│ Tools:                      │
│ • modify_huawei_parameter   │
│ • execute_mml_command       │
│ • query_huawei_kpi          │
│                             │
│ Process:                    │
│ 1. Generate 6 MML commands  │
│    (one per cell)           │
│ 2. Execute sequentially     │
│ 3. Log to database          │
│ 4. Verify changes           │
│ 5. Rollback on failure      │
│                             │
│ Output:                     │
│ • Execution status          │
│ • Pre/post KPI comparison   │
│ • Success metrics           │
└──────────┬──────────────────┘
           │
           │ State: optimization_success
           │
           ▼
     ┌────────────┐
     │    END     │
     │            │
     │  Return    │
     │  final     │
     │  state     │
     └────────────┘
```

---

## Database Schema

```
┌─────────────────────────────────────────────────────────────────────┐
│                         lz_network.db                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TABLE: sites                                                       │
│  ┌───────────────┬──────────────┬──────────────┐                   │
│  │ site_id (PK)  │ site_name    │ location     │                   │
│  │ INT           │ VARCHAR(100) │ VARCHAR(100) │                   │
│  ├───────────────┼──────────────┼──────────────┤                   │
│  │ 1             │ MSH-0014-    │ Chipadze     │                   │
│  │               │ Chipadze     │              │                   │
│  └───────────────┴──────────────┴──────────────┘                   │
│                                                                     │
│  TABLE: kpi_data (7 KPIs per cell)                                 │
│  ┌────────┬───────────┬─────────┬──────────────┬────────────┐     │
│  │ id(PK) │ timestamp │site_name│ cell_id      │data_source │     │
│  │ INT    │ DATETIME  │VARCHAR  │ INT          │VARCHAR     │     │
│  ├────────┼───────────┼─────────┼──────────────┼────────────┤     │
│  │ 1      │2025-11-25 │MSH-0014 │ 1            │ live       │     │
│  │        │14:00:00   │-Chipadze│              │            │     │
│  └────────┴───────────┴─────────┴──────────────┴────────────┘     │
│                                                                     │
│  ┌──────────────────────┬───────────────┬─────────────────┐       │
│  │ network_access_      │download_speed │ download_quality│       │
│  │ success (%)          │ (Mbps)        │ (%)             │       │
│  ├──────────────────────┼───────────────┼─────────────────┤       │
│  │ 96.5                 │ 45.2          │ 94.8            │       │
│  └──────────────────────┴───────────────┴─────────────────┘       │
│                                                                     │
│  ┌──────────────┬──────────────────┬──────────────────────┐       │
│  │upload_speed  │ upload_quality   │ control_channel_load │       │
│  │ (Mbps)       │ (%)              │ (%)                  │       │
│  ├──────────────┼──────────────────┼──────────────────────┤       │
│  │ 18.5         │ 93.2             │ 65.4                 │       │
│  └──────────────┴──────────────────┴──────────────────────┘       │
│                                                                     │
│  ┌──────────────────────┐                                          │
│  │ feedback_channel_load│                                          │
│  │ (%)                  │                                          │
│  ├──────────────────────┤                                          │
│  │ 45.3                 │                                          │
│  └──────────────────────┘                                          │
│                                                                     │
│  TABLE: parameter_changes                                          │
│  ┌────────┬───────────┬─────────┬────────────┬─────────────┐      │
│  │ id(PK) │timestamp  │site_name│ cell_id    │parameter_   │      │
│  │ INT    │ DATETIME  │VARCHAR  │ INT        │name VARCHAR │      │
│  ├────────┼───────────┼─────────┼────────────┼─────────────┤      │
│  │ 1      │2025-11-25 │MSH-0014 │ 1          │reference_   │      │
│  │        │14:30:00   │-Chipadze│            │signal_power │      │
│  └────────┴───────────┴─────────┴────────────┴─────────────┘      │
│                                                                     │
│  ┌───────────┬───────────┬────────┬─────────┬─────────┐           │
│  │ old_value │ new_value │ reason │agent_id │ success │           │
│  │ REAL      │ REAL      │VARCHAR │VARCHAR  │ BOOLEAN │           │
│  ├───────────┼───────────┼────────┼─────────┼─────────┤           │
│  │ -200      │ -180      │Agent   │mml_exec │ 1       │           │
│  │           │           │Optim   │         │         │           │
│  └───────────┴───────────┴────────┴─────────┴─────────┘           │
│                                                                     │
│  TABLE: optimization_history                                       │
│  ┌────────┬───────────┬─────────┬─────────┬──────────────┐        │
│  │ id(PK) │timestamp  │site_name│ issue   │recommendations        │
│  │ INT    │ DATETIME  │VARCHAR  │ TEXT    │ JSON         │        │
│  ├────────┼───────────┼─────────┼─────────┼──────────────┤        │
│  │ 1      │2025-11-25 │MSH-0014 │Low DL   │[{param:..}]  │        │
│  │        │14:30:00   │-Chipadze│speed    │              │        │
│  └────────┴───────────┴─────────┴─────────┴──────────────┘        │
│                                                                     │
│  ┌──────────────┬─────────┬──────────┬─────────┐                  │
│  │ mml_commands │ success │ pre_kpis │post_kpis│                  │
│  │ JSON         │ BOOLEAN │ JSON     │ JSON    │                  │
│  ├──────────────┼─────────┼──────────┼─────────┤                  │
│  │ [{cmd:...}]  │ 1       │{dl:45.2} │{dl:55.8}│                  │
│  └──────────────┴─────────┴──────────┴─────────┘                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## API Integration Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                   HUAWEI iMASTER MAE API INTEGRATION                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Authentication Flow                                          │  │
│  │                                                               │  │
│  │  1. Initial Auth Request                                     │  │
│  │     PUT /api/rest/securityManagement/v1/oauth/token          │  │
│  │     Body: {                                                  │  │
│  │       "grantType": "password",                               │  │
│  │       "userName": "cassava.ai",                              │  │
│  │       "value": "#Pass123#"                                   │  │
│  │     }                                                         │  │
│  │                                                               │  │
│  │  2. Token Response                                           │  │
│  │     {                                                         │  │
│  │       "accessSession": "x-il1c05...",                        │  │
│  │       "roaRand": "34833e9426...",                            │  │
│  │       "expires": 1800  // 30 minutes                         │  │
│  │     }                                                         │  │
│  │                                                               │  │
│  │  3. Subsequent Requests                                      │  │
│  │     Header: X-Auth-Token: {accessSession}                    │  │
│  │                                                               │  │
│  │  4. Token Refresh (before expiry)                            │  │
│  │     Auto-refresh at 25 minutes                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  MML Command Execution                                        │  │
│  │                                                               │  │
│  │  Endpoint: POST /api/rest/mmlManagement/v1/command           │  │
│  │                                                               │  │
│  │  Request Body:                                               │  │
│  │  {                                                            │  │
│  │    "command": "LST PDSCHCFG: LOCALCELLID=1;",               │  │
│  │    "neNames": ["MSH-0014-Chipadze"]                         │  │
│  │  }                                                            │  │
│  │                                                               │  │
│  │  Query Operations (Site-Wide):                              │  │
│  │  • LST PDSCHCFG:;                                            │  │
│  │  • LST UECOOPERATIONPARA:;                                  │  │
│  │  • LST PMDATA: OBJECTTYPE=CELL;                             │  │
│  │  → Returns data for ALL 6 cells                              │  │
│  │                                                               │  │
│  │  Modify Operations (Cell-by-Cell):                          │  │
│  │  • MOD PDSCHCFG:LOCALCELLID=1,REFERENCESIGNALPWR=-180;      │  │
│  │  • Must execute 6 separate commands for site-wide changes    │  │
│  │                                                               │  │
│  │  Response:                                                   │  │
│  │  {                                                            │  │
│  │    "result": 0,  // 0 = success                              │  │
│  │    "message": "Execution successful",                        │  │
│  │    "output": "..." // MML command output                     │  │
│  │  }                                                            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  5 Tunable Parameters                                         │  │
│  │                                                               │  │
│  │  1. reference_signal_power_pdschcfg                          │  │
│  │     Range: -600 to 500 (0.1 dBm units)                       │  │
│  │     Command: MOD PDSCHCFG:LOCALCELLID={id},                  │  │
│  │              REFERENCESIGNALPWR={value};                     │  │
│  │                                                               │  │
│  │  2. a3_event_offset                                          │  │
│  │     Range: 0 to 30 dB                                        │  │
│  │     Command: MOD CELLEVENTA3PARA:LOCALCELLID={id},           │  │
│  │              A3OFFSET={value};                               │  │
│  │                                                               │  │
│  │  3. t310_timer                                               │  │
│  │     Range: 0 to 10000 ms                                     │  │
│  │     Command: MOD CELLRLFTMRCFG:LOCALCELLID={id},             │  │
│  │              T310={value};                                   │  │
│  │                                                               │  │
│  │  4. p0_nominal_pusch                                         │  │
│  │     Range: -126 to -40 dBm                                   │  │
│  │     Command: MOD ULPCPARA:LOCALCELLID={id},                  │  │
│  │              P0NOMINALPUSCH={value};                         │  │
│  │                                                               │  │
│  │  5. pdcch_aggregation_level                                  │  │
│  │     Range: 1, 2, 4, 8                                        │  │
│  │     Command: MOD PDCCHCFG:LOCALCELLID={id},                  │  │
│  │              AGGREGATIONLEVEL={value};                       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DEPLOYMENT OPTIONS                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  OPTION 1: Local Development (Current)                                 │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │   ┌──────────────┐         ┌──────────────┐                      │ │
│  │   │  macOS       │         │   Internet   │                      │ │
│  │   │  localhost   │         │              │                      │ │
│  │   │              │         │              │                      │ │
│  │   │  Port 8501   │◄────────┤  ngrok       │                      │ │
│  │   │  Streamlit   │         │  Tunnel      │                      │ │
│  │   │              │         │              │                      │ │
│  │   │  Port 80     │         │  https://    │                      │ │
│  │   │  nginx       │         │  xxxxxxxx.   │                      │ │
│  │   │              │         │  ngrok-free  │                      │ │
│  │   │  SQLite DB   │         │  .app        │                      │ │
│  │   │              │         │              │                      │ │
│  │   └──────────────┘         └──────────────┘                      │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  OPTION 2: Docker Containerized (Phase 5.2)                            │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │   ┌─────────────────────────────────────────────────────────┐   │ │
│  │   │  Docker Container: lz-network-optimizer                  │   │ │
│  │   │                                                          │   │ │
│  │   │  ┌──────────────┐    ┌──────────────┐                  │   │ │
│  │   │  │  Streamlit   │    │  SQLite DB   │                  │   │ │
│  │   │  │  Port 8501   │    │  /app/data/  │                  │   │ │
│  │   │  │              │    │              │                  │   │ │
│  │   │  │  Python 3.13 │    │  Volume      │                  │   │ │
│  │   │  │  Dependencies│    │  Mounted     │                  │   │ │
│  │   │  └──────────────┘    └──────────────┘                  │   │ │
│  │   │                                                          │   │ │
│  │   └──────────────┬───────────────────────────────────────────┘   │ │
│  │                  │                                               │ │
│  │                  │ Port mapping: 8501:8501                       │ │
│  │                  ▼                                               │ │
│  │         ┌─────────────────┐                                     │ │
│  │         │  Host Network   │                                     │ │
│  │         │  nginx/ngrok    │                                     │ │
│  │         └─────────────────┘                                     │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  OPTION 3: Cloud Deployment (Future)                                   │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │   ┌──────────────┐                                               │ │
│  │   │  Load        │                                               │ │
│  │   │  Balancer    │                                               │ │
│  │   └──────┬───────┘                                               │ │
│  │          │                                                        │ │
│  │    ┌─────┴─────┐                                                 │ │
│  │    │           │                                                 │ │
│  │    ▼           ▼                                                 │ │
│  │  ┌───────┐  ┌───────┐                                           │ │
│  │  │ App 1 │  │ App 2 │  Kubernetes/ECS                           │ │
│  │  │       │  │       │  Auto-scaling                             │ │
│  │  └───┬───┘  └───┬───┘                                           │ │
│  │      │          │                                                │ │
│  │      └──────┬───┘                                                │ │
│  │             │                                                    │ │
│  │             ▼                                                    │ │
│  │      ┌────────────┐                                              │ │
│  │      │ PostgreSQL │  Managed DB                                 │ │
│  │      │ RDS/Cloud  │  Backup & HA                                │ │
│  │      │ SQL        │                                              │ │
│  │      └────────────┘                                              │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Key Architecture Features

### 1. **3-Tier Fallback Mechanism (NEW - Phase 5 Fix)**
- **Tier 1:** LLM Agent with SQL query generation
- **Tier 2:** Direct database query (`get_latest_kpis_direct()`)
- **Tier 3:** User intent detection (keyword matching)

### 2. **Cell-by-Cell Modifications**
- Query operations: Site-wide (1 command, 6 cells returned)
- Modify operations: Cell-specific (6 commands required)
- Rollback support: 6 commands per parameter

### 3. **Weighted KPI Scoring (3-Tier)**
- **Tier 1 (Foundation - 25%):** Network Access Success
- **Tier 2 (Revenue/Experience - 50%):** Speed & Quality
- **Tier 3 (Efficiency - 25%):** Channel Load

### 4. **10 Optimization Rules**
- Rule-based decision making
- Few-shot learning from history
- Parameter range validation
- Risk assessment (1-10 scale)

### 5. **Security & Reliability**
- OAuth2 token authentication
- Token auto-refresh (25 min)
- Rollback on failure
- Comprehensive logging
- Error handling at every layer

---

## File Structure Map

```
lz-network-optimizer/
├── agents/
│   ├── monitoring_agent.py         ⭐ Decision logic + Fallback
│   ├── kpi_analytics_agent.py
│   ├── configuration_agent.py
│   ├── validation_agent.py
│   ├── mml_executor_agent.py
│   └── workflow.py                 ⭐ LangGraph orchestration
│
├── tools/
│   ├── sql_tools.py                ⭐ Direct DB fallback
│   ├── huawei_tools.py
│   ├── calculation_tools.py
│   └── rollback_manager.py
│
├── network/
│   └── huawei_api_client.py        ⭐ API authentication & MML
│
├── domain/
│   └── mml_commands.py
│
├── ui/
│   ├── app.py                      ⭐ Streamlit interface
│   └── workflow_interface.py       ⭐ Workflow execution
│
├── config/
│   └── kpi_weights.yaml            ⭐ Thresholds & weights
│
├── data/
│   └── lz_network.db               ⭐ SQLite database
│
├── documentation/
│   ├── SYSTEM_ARCHITECTURE_DIAGRAM.md  ⭐ This file
│   ├── OPTIMIZATION_DECISION_FIX.md    ⭐ Phase 5 fixes
│   └── PHASE_5_ARCHITECTURE_CORRECTIONS.md
│
└── docker/
    └── docker-compose.yml
```

---

## Version History

| Version | Date       | Changes                                  |
|---------|------------|------------------------------------------|
| 1.0     | 2025-11-25 | Initial comprehensive architecture doc   |
|         |            | Added 3-tier fallback mechanism          |
|         |            | Added deployment options                 |
|         |            | Added detailed data flow diagrams        |

---

**Document End** | System Architecture Diagram v1.0 | 2025-11-25
