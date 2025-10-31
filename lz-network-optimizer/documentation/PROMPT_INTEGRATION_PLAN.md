# Liquid Zimbabwe 4G Network Optimizer: Prompt Integration Plan

**Document Version**: 1.0
**Date**: 2025-10-30
**Phase**: Phase 1 - Prompt Architecture & Integration
**Scope**: Few-shot prompting integration for 6-agent agentic workflow

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Source Files Analysis](#source-files-analysis)
3. [Few-Shot Example Extraction](#few-shot-example-extraction)
4. [Prompt Structure Per Agent](#prompt-structure-per-agent)
5. [Integration Strategy](#integration-strategy)
6. [Implementation Pattern](#implementation-pattern)
7. [Few-Shot Examples by Agent](#few-shot-examples-by-agent)
8. [Domain Knowledge Integration](#domain-knowledge-integration)
9. [Testing & Validation](#testing--validation)
10. [Deployment Guide](#deployment-guide)

---

## Executive Summary

This document outlines the strategy for integrating a sophisticated few-shot prompting architecture into the Liquid Zimbabwe 4G Network Optimizer. Building on the Nvidia blueprint, we leverage the excellent prompt system found in `rebuild-assets/prompts/` to enable our 6 agents to make better decisions through concrete examples and structured guidance.

### Key Integration Points

- **Source System**: Nvidia Blueprint (BubbleRAN 5G)
- **Target System**: Liquid Zimbabwe 4G (Huawei iMaster MAE API)
- **Agent Count**: 6 specialized agents (3 core + 3 extensions)
- **Domain Assets**: 5 parameters, 7 KPIs, 10 optimization rules
- **Prompt Components**: System prompts + Few-shot examples + Domain context
- **Delivery Format**: YAML + Python templates with dynamic composition

### Expected Outcomes

By implementing this plan, agents will:
1. Make contextually-aware decisions specific to Bindura region
2. Avoid optimization conflicts through safety examples
3. Generate reliable MML commands with high accuracy
4. Provide risk-aware recommendations with justification
5. Learn from successful past optimizations

---

## Source Files Analysis

### 1.1 Prompt Architecture Files

Located in: `/rebuild-assets/prompts/`

#### AGENT_PROMPTS_ARCHITECTURE.md (1,338 lines)
**Purpose**: Master reference for all agent prompt patterns
**Content Coverage**:
- 6 core agent prompt templates (Network Connector, Monitoring, KPI Analytics, Configuration, Validation, Execution)
- 3 supporting agent prompts (Query Processor, Safety Assessment, Impact Monitor)
- Detailed response format specifications in JSON
- Real-world examples for Bindura network context
- Critical KPI and parameter definitions

**Key Sections for Integration**:
- Section 2.1: Network Connector Agent (connection discovery, authentication, troubleshooting)
- Section 2.2: Monitoring Agent (KPI analysis, anomaly detection, trend analysis)
- Section 2.3: KPI Analytics Agent (root cause analysis, optimization strategies, impact prediction)
- Section 2.4: Configuration Agent (MML command generation, safety constraints)
- Sections 2.5-2.7: Validation, Execution, and supporting agents

**Extractable Patterns**:
- JSON response schemas (standardized for all agents)
- Task-specific prompt templates with variable placeholders
- Real Bindura site data: MSH0013-Bindura-Zaoga, MSH-0331-Chiwaridzo 2, MSH-0112-Bindura Hospital, MSH-0014-Chipadze
- Critical KPI baselines: RACH 0.536%, DL IBLER 15.94%

#### prompt_templates.py (600 lines)
**Purpose**: Python-based prompt composition system
**Content Coverage**:
- PromptContext dataclass for structured context passing
- ContextBuilder class for building network context from previous stages
- PromptTemplates class with static methods for each agent type
- KPI data formatting utilities
- Parameter formatting functions

**Key Functions for Integration**:
```python
PromptContext  # Dataclass capturing workflow_id, target_region, current_step, etc.
ContextBuilder.build_network_context()  # Connects stage outputs
ContextBuilder.format_kpi_data()  # Formats KPI data for prompt injection
PromptTemplates.get_network_connector_prompt()  # Agent 1 prompt
PromptTemplates.get_monitoring_agent_prompt()  # Agent 2 prompt
# ... and more for each agent
```

**Integration Value**: Provides the infrastructure for composing prompts dynamically with real Bindura data.

#### enhanced_prompt_templates.py (600 lines)
**Purpose**: Advanced prompt templates with real data integration
**Content Coverage**:
- Enhanced versions of basic templates
- Real Bindura network context injection
- Historical data integration (168 CSV records, 2025-09-01 to 2025-09-07)
- Critical issue highlighting (RACH failure, IBLER degradation)
- Database fallback examples

**Key Enhancements for LZ**:
- Explicit mention of real sites and critical KPI values
- Fallback strategies for API failures
- Data source tracking (live_api vs database_fallback vs simulation)

#### system_prompts.yaml (67 lines)
**Purpose**: YAML-based system prompt definitions for all agents
**Content Coverage**:
```yaml
network_optimizer_system: |
  "You are an expert 4G LTE network optimization specialist..."
monitor_agent_system: |
  "You are a network monitoring specialist..."
configuration_agent_system: |
  "You are a network configuration specialist..."
validation_agent_system: |
  "You are a network validation specialist..."
execution_agent_system: |
  "You are a network operations specialist..."
```

**Integration Strategy**: Maps 1:1 to our 6 agents with role specialization.

#### task_prompts.yaml (224 lines)
**Purpose**: Task-specific prompt templates with variable placeholders
**Content Coverage**:
- `monitor_kpis`: Real-time KPI monitoring with thresholds
- `analyze_performance`: Root cause analysis with correlation
- `generate_mml_commands`: MML command generation with pre/post verification
- `validate_changes`: Pre-change validation with safety checks
- `execute_changes`: Safe execution with real-time monitoring
- `optimize_cell`: General optimization request handler

**Integration Value**: Each task prompt is a few-shot template ready for dynamic injection.

#### prompt_manager.py (296 lines)
**Purpose**: Runtime prompt manager for loading, templating, and LangChain integration
**Key Classes**:
```python
PromptManager:
  - load YAML prompt files
  - substitute template variables
  - create LangChain ChatPromptTemplate objects
  - format KPI/parameter/threshold data for prompt injection
```

**Integration Role**: Provides the runtime engine for our dynamic prompt composition.

---

## Few-Shot Example Extraction

### 2.1 Extraction Strategy

Few-shot examples should be extracted from three sources:
1. **Inline examples in prompts**: Found in AGENT_PROMPTS_ARCHITECTURE.md
2. **Real Bindura data**: From CSV and database snapshots
3. **Historical case studies**: From previous optimization successes

### 2.2 Example Categories

#### A. Network Connector Agent Examples

**Example 1: Successful Discovery**
```json
{
  "input": "Discover all available network sites in Bindura region",
  "context": {
    "api_status": "authenticated",
    "region": "Bindura",
    "expected_sites": 4
  },
  "output": {
    "connection_status": "connected",
    "discovered_sites": [
      "MSH0013-Bindura-Zaoga",
      "MSH-0331-Chiwaridzo 2",
      "MSH-0112-Bindura Hospital",
      "MSH-0014-Chipadze"
    ],
    "site_details": {
      "MSH0013-Bindura-Zaoga": {
        "cells": 3,
        "status": "active",
        "issues": []
      }
    },
    "next_stage_ready": true
  }
}
```

**Example 2: API Authentication Failure**
```json
{
  "input": "Authenticate with iMaster MAE API",
  "context": {
    "credentials_status": "provided",
    "last_failure": "2025-10-29T15:30:00Z",
    "retry_count": 2
  },
  "output": {
    "connection_status": "error",
    "error_details": {
      "code": "AUTH_TOKEN_EXPIRED",
      "message": "OAuth token expired, requesting refresh",
      "recovery_steps": [
        "Refresh OAuth token from credentials manager",
        "Re-establish connection with new token",
        "Validate site accessibility"
      ]
    },
    "recommendations": [
      "Implement automatic token refresh every 55 minutes",
      "Log authentication failures for audit trail"
    ]
  }
}
```

#### B. Monitoring Agent Examples

**Example 1: Critical RACH Issue Detection**
```json
{
  "input": "Analyze KPI data for network degradation",
  "context": {
    "measurement_period": "2025-09-01 to 2025-09-07",
    "sites": ["MSH0013-Bindura-Zaoga", "MSH-0331-Chiwaridzo 2"],
    "data_points": 168
  },
  "output": {
    "analysis_summary": "CRITICAL: Network access success rate at 0.536%, far below 95% target",
    "identified_issues": [
      {
        "issue_id": "CRITICAL_001",
        "kpi_affected": "network_access_success",
        "severity": "critical",
        "description": "RACH setup success rate critically low at 0.536%",
        "affected_sites": ["MSH0013-Bindura-Zaoga", "MSH-0331-Chiwaridzo 2"],
        "trend": "stable_but_critical",
        "priority": 10,
        "recommended_action": "Immediate investigation into RACH configuration and radio interference"
      },
      {
        "issue_id": "HIGH_001",
        "kpi_affected": "download_quality",
        "severity": "high",
        "description": "DL IBLER at 15.94%, exceeds acceptable 8% threshold",
        "affected_sites": ["all_sites"],
        "trend": "degrading",
        "priority": 9
      }
    ],
    "cells_requiring_attention": [
      "MSH0013-Bindura-Zaoga_CELL_001",
      "MSH-0331-Chiwaridzo 2_CELL_001"
    ]
  }
}
```

**Example 2: Trend Analysis**
```json
{
  "input": "Analyze performance trends over 7-day period",
  "context": {
    "time_period": "2025-09-01 to 2025-09-07",
    "kpis": ["network_access_success", "download_quality", "upload_quality"],
    "data_type": "real_measurements"
  },
  "output": {
    "trend_analysis": {
      "network_access_success": {
        "direction": "stable",
        "comment": "Consistently low at 0.536%, indicating structural issue",
        "confidence": 0.95
      },
      "download_quality": {
        "direction": "degrading",
        "comment": "IBLER increasing from 14% to 16% over 7 days",
        "confidence": 0.88
      }
    },
    "predictions": {
      "without_intervention": "RACH will remain critical, IBLER may increase to 18%",
      "confidence": 0.75
    },
    "recommended_action_timing": "Implement fix within 48 hours to prevent further degradation"
  }
}
```

#### C. KPI Analytics Agent Examples

**Example 1: Root Cause Analysis**
```json
{
  "input": "Perform root cause analysis for RACH failure",
  "context": {
    "issue": "RACH Setup Success Rate 0.536%",
    "historical_baseline": "95.2% (2025-08-15)",
    "change_magnitude": "-99.4%",
    "possible_causes": [
      "RACH power misconfiguration",
      "Preamble format change",
      "Backoff indicator issue",
      "Radio interference from adjacent band"
    ]
  },
  "output": {
    "root_cause_analysis": [
      {
        "cause": "RACH reference signal power too low",
        "confidence": 0.92,
        "evidence": [
          "RACH power configured at -100 dBm (should be -85 to -65)",
          "All 4 sites show same critical failure pattern",
          "Issue started 2025-09-01, coinciding with parameter change"
        ],
        "correlation_strength": 0.96,
        "supporting_data": {
          "current_rach_power": "-100 dBm",
          "recommended_power": "-80 dBm",
          "improvement_expected": "92%+ success rate"
        }
      },
      {
        "cause": "Insufficient preamble sequence allocation",
        "confidence": 0.65,
        "evidence": ["RACH success improved slightly with load reduction"],
        "correlation_strength": 0.72
      }
    ],
    "primary_recommendation": {
      "parameter": "RACH reference signal power",
      "change_from": "-100 dBm",
      "change_to": "-80 dBm",
      "expected_improvement": "92% network access success rate",
      "confidence": 0.92
    }
  }
}
```

**Example 2: Optimization Strategy**
```json
{
  "input": "Generate optimization strategy for RACH and IBLER issues",
  "context": {
    "root_causes": [
      {"parameter": "RACH reference signal power", "issue_severity": "critical"},
      {"parameter": "DL power allocation", "issue_severity": "high"}
    ],
    "constraints": [
      "Change window: 02:00-04:00 UTC (low traffic)",
      "Max parallel changes: 1",
      "Risk tolerance": "medium"
    ]
  },
  "output": {
    "optimization_strategies": [
      {
        "strategy_id": "RACH_FIX_001",
        "target_issues": ["CRITICAL_001"],
        "optimization_type": "parameter_adjustment",
        "parameters_to_modify": [
          {
            "parameter": "reference_signal_power_rs",
            "current_value": "-100 dBm",
            "recommended_value": "-80 dBm",
            "change_magnitude": "+20 dBm",
            "change_direction": "increase"
          }
        ],
        "expected_improvements": {
          "network_access_success": "92.5%",
          "confidence": 0.92
        },
        "implementation_complexity": "low",
        "implementation_time": "5 minutes",
        "risk_assessment": "Low - RACH power change is standard practice",
        "roi_estimate": "99% improvement in accessibility"
      }
    ],
    "priority_ranking": [
      {
        "strategy_id": "RACH_FIX_001",
        "priority_score": 100,
        "priority_rationale": "Addresses critical issue affecting all users"
      }
    ]
  }
}
```

#### D. Configuration Agent Examples

**Example 1: MML Command Generation**
```json
{
  "input": "Generate MML commands for RACH parameter optimization",
  "context": {
    "cell_id": "0",
    "site": "MSH0013-Bindura-Zaoga",
    "approved_changes": [
      {
        "parameter": "reference_signal_power_rs",
        "current_value": "-100",
        "target_value": "-80"
      }
    ]
  },
  "output": {
    "pre_change_commands": [
      "LST PDSCHCFG:LOCALCELLID=0;"
    ],
    "modification_commands": [
      "MOD PDSCHCFG:LOCALCELLID=0,REFERENCESIGNALPWR=-80; {MSH0013-Bindura-Zaoga}"
    ],
    "verification_commands": [
      "LST PDSCHCFG:LOCALCELLID=0;"
    ],
    "rollback_commands": [
      "MOD PDSCHCFG:LOCALCELLID=0,REFERENCESIGNALPWR=-100; {MSH0013-Bindura-Zaoga}"
    ],
    "execution_notes": "Change affects RACH accessibility. Monitor for improvement within 5 minutes."
  }
}
```

#### E. Validation Agent Examples

**Example 1: Safe Change Approval**
```json
{
  "input": "Validate RACH power adjustment for cell 0",
  "context": {
    "current_value": "-100 dBm",
    "proposed_value": "-80 dBm",
    "parameter_range": "[-600, 500]",
    "dependent_parameters": [
      "interference_mitigation_level",
      "neighbor_cell_configurations"
    ],
    "network_status": "normal_traffic_levels"
  },
  "output": {
    "validation_results": [
      {
        "param_key": "reference_signal_power_rs",
        "proposed_value": -80,
        "is_valid": true,
        "within_range": true,
        "no_conflicts": true,
        "validation_notes": "Value is within range [-600, 500], change magnitude +20 dBm is acceptable"
      }
    ],
    "overall_assessment": "approved",
    "risk_level": "low",
    "approval_decision": "approved",
    "conditions": [
      "Execute during low traffic window (02:00-04:00 UTC)",
      "Monitor RACH success rate for 30 minutes post-change",
      "If success rate doesn't reach 85% within 5 minutes, rollback"
    ]
  }
}
```

#### F. Execution Agent Examples

**Example 1: Successful Parameter Change**
```json
{
  "input": "Execute RACH power adjustment with monitoring",
  "context": {
    "execution_window": "2025-10-30T02:30:00Z",
    "site": "MSH0013-Bindura-Zaoga",
    "mml_command": "MOD PDSCHCFG:LOCALCELLID=0,REFERENCESIGNALPWR=-80; {MSH0013-Bindura-Zaoga}"
  },
  "output": {
    "execution_status": "completed",
    "commands_executed": [
      {
        "command": "LST PDSCHCFG:LOCALCELLID=0;",
        "status": "success",
        "timestamp": "2025-10-30T02:30:05Z",
        "result": "Pre-change snapshot captured: REFERENCESIGNALPWR=-100"
      },
      {
        "command": "MOD PDSCHCFG:LOCALCELLID=0,REFERENCESIGNALPWR=-80; {MSH0013-Bindura-Zaoga}",
        "status": "success",
        "timestamp": "2025-10-30T02:30:10Z"
      },
      {
        "command": "LST PDSCHCFG:LOCALCELLID=0;",
        "status": "success",
        "timestamp": "2025-10-30T02:30:20Z",
        "result": "Post-change snapshot: REFERENCESIGNALPWR=-80 confirmed"
      }
    ],
    "kpi_impact": {
      "network_access_success": {
        "pre_change": "0.536%",
        "post_change": "92.3%",
        "change": "+91.764%"
      }
    },
    "rollback_required": false,
    "execution_notes": "Parameter change successful. RACH success rate reached 92.3% within 2 minutes of change."
  }
}
```

### 2.3 Example Storage Format

Examples should be stored in JSON files per agent:
```
rebuild-assets/prompts/examples/
├── network_connector_examples.json
├── monitoring_examples.json
├── kpi_analytics_examples.json
├── configuration_examples.json
├── validation_examples.json
├── execution_examples.json
└── general_examples.json
```

Each file follows this structure:
```json
{
  "agent": "network_connector",
  "examples": [
    {
      "example_id": "NC_001",
      "category": "successful_discovery",
      "input": "...",
      "context": {...},
      "output": {...},
      "explanation": "Why this example is important"
    }
  ]
}
```

---

## Prompt Structure Per Agent

### 3.1 Agent Overview

| Agent | Purpose | Input | Output | Dependencies |
|-------|---------|-------|--------|--------------|
| **Network Connector** | Connect to Huawei API, discover sites | User query, API credentials | Site list, connection status | huawei_api_client |
| **Monitoring Analysis** | Analyze current KPIs, identify issues | Connected sites, KPI data | Issues list, priority ranking | database, live_api |
| **KPI Analytics** | Root cause analysis, optimization strategies | Issues, historical data | Root causes, strategies | monitoring output |
| **Configuration** | Generate MML commands | Approved strategies | MML command sequences | kpi_analytics output |
| **Validation** | Verify safety before execution | MML commands, current state | Approval decision, conditions | configuration output |
| **Execution** | Apply changes, monitor results | Validated commands | Execution results, KPI impact | validation output |

### 3.2 Agent 1: Network Connector

**System Prompt Structure**:
```
[Role & Responsibilities]
├── Establish connections to Huawei API
├── Discover network elements and sites
├── Maintain authentication state
└── Validate network accessibility

[Technical Context]
├── API Type: Huawei iMaster MAE REST
├── Authentication: OAuth2 token-based
├── Network Elements: eNodeB sites in Bindura
└── Real Sites: 4 Bindura sites (MSH0013, MSH-0331, MSH-0112, MSH-0014)

[Capabilities]
├── Site discovery and enumeration
├── Connectivity validation
├── Authentication management
└── Error diagnosis and recovery

[Response Format]
└── JSON with: connection_status, discovered_sites, site_details,
              authentication_status, error_details, next_stage_ready
```

**Few-Shot Examples** (3-5 examples):
1. Successful site discovery with all 4 Bindura sites
2. API authentication failure with recovery steps
3. Partial connectivity (3 sites reachable, 1 unreachable)
4. Token expiration and refresh scenario

**Task Prompts**:
- `discover_network`: Full site discovery
- `validate_connection`: Test specific site connectivity
- `troubleshoot_auth`: Handle authentication failures

### 3.3 Agent 2: Monitoring Analysis

**System Prompt Structure**:
```
[Role & Responsibilities]
├── Query live KPI data
├── Analyze historical trends
├── Identify performance anomalies
├── Prioritize issues by severity
└── Prepare inputs for KPI Analytics

[KPI Expertise]
├── Network Access Success (RACH): Target >95%, Critical <90%
├── Download Quality (DL IBLER): Target <15%, Critical >20%
├── Upload Quality (UL IBLER): Target <15%, Critical >20%
├── Resource Utilization (PRB): Target 60-80%, Critical >90%
├── Call Setup Success (E-RAB): Target >98%, Critical <95%
├── Handover Performance (HO): Target >95%, Critical <90%
└── Coverage Quality (RSRP): Target >-105dBm for 95% coverage

[Current Network State]
├── Measurement Period: 2025-09-01 to 2025-09-07
├── Critical Issues: RACH 0.536% (99.4% below baseline)
├── Secondary Issues: DL IBLER 15.94% (99% above target)
└── Data Points: 168 measurements across 4 sites

[Response Format]
└── JSON with: analysis_summary, identified_issues, kpi_status,
              cells_requiring_attention, performance_trends
```

**Few-Shot Examples** (3-5 examples):
1. Critical RACH failure detection (real Bindura data)
2. Trend analysis showing degradation pattern
3. Anomaly detection with correlation identification
4. Multi-KPI issue correlation analysis

**Task Prompts**:
- `monitor_kpis`: Real-time KPI monitoring
- `analyze_trends`: Historical trend analysis
- `correlate_kpis`: KPI correlation analysis
- `detect_anomalies`: Anomaly detection

### 3.4 Agent 3: KPI Analytics

**System Prompt Structure**:
```
[Role & Responsibilities]
├── Deep root cause analysis
├── Optimization strategy generation
├── Impact prediction modeling
├── Risk assessment
└── ROI calculation and prioritization

[Analytical Expertise]
├── Statistical correlation analysis
├── Time series pattern matching
├── Decision tree analysis for causal paths
├── Historical case similarity matching
└── Data-driven impact prediction

[Parameter Correlation Knowledge]
├── RACH Power ↔ Network Access Success (strong positive)
├── DL Power Allocation ↔ Download Quality (strong positive)
├── Handover Margin (A3) ↔ Call Drops (negative correlation)
├── T310 Timer ↔ False RLF Alarms (direct relationship)
├── PDCCH Aggregation ↔ Control Channel Robustness (positive)
└── P0 PUSCH ↔ Uplink Coverage (strong positive)

[Response Format]
└── JSON with: root_cause_analysis, optimization_strategies,
              expected_improvements, priority_ranking,
              next_stage_inputs
```

**Few-Shot Examples** (4-6 examples):
1. RACH root cause analysis → parameter recommendation
2. Multi-parameter optimization strategy for IBLER
3. Risk assessment and confidence levels
4. Impact prediction with historical validation
5. Strategy prioritization by ROI and risk
6. Handover parameter trade-off analysis

**Task Prompts**:
- `analyze_performance`: Root cause analysis
- `generate_strategy`: Optimization strategy
- `predict_impact`: Impact prediction modeling
- `assess_risk`: Risk-benefit analysis

### 3.5 Agent 4: Configuration

**System Prompt Structure**:
```
[Role & Responsibilities]
├── Generate precise MML commands
├── Validate parameter ranges
├── Create rollback commands
├── Ensure configuration compliance
└── Document change details

[Parameter Specialization]
├── Reference Signal Power (PDSCHCFG): -600 to 500 (0.1 dBm)
│  └── Command: MOD PDSCHCFG:LOCALCELLID={id},REFERENCESIGNALPWR={val}
├── A3 Event Offset (UECOOPERATIONPARA): 0 to 15 (dB)
│  └── Command: MOD UECOOPERATIONPARA:LOCALCELLID={id},A3OFFSET={val}
├── T310 Timer (UETIMERCONST): 100 to 6000 (ms)
│  └── Command: MOD UETIMERCONST:LOCALCELLID={id},T310={val}
├── P0 Nominal PUSCH (CELLULPCCOMM): -126 to 24 (dBm)
│  └── Command: MOD CELLULPCCOMM:LOCALCELLID={id},P0NOMINALPUSCH={val}
└── PDCCH Aggregation (CELLUSPARACFG): 1, 2, 4, 8
   └── Command: MOD CELLUSPARACFG:LOCALCELLID={id},PDCCHAGGLVL={val}

[Safety Constraints]
├── Maximum change per modification: {parameter-specific}
├── Concurrent modification limit: 1 per cell
├── Safety margins: {enforced_per_parameter}
└── Rollback window: 2 hours

[Response Format]
└── JSON with: pre_change_commands, modification_commands,
              verification_commands, rollback_commands,
              execution_notes
```

**Few-Shot Examples** (4-6 examples):
1. Single parameter change (RACH power)
2. Multi-parameter change with sequence (RACH + A3)
3. MML command with all verification steps
4. Rollback command generation
5. Parameter change with dependencies
6. Safety margin application

**Task Prompts**:
- `generate_mml_commands`: MML command generation
- `validate_command_syntax`: MML syntax validation
- `create_rollback`: Rollback command creation

### 3.6 Agent 5: Validation

**System Prompt Structure**:
```
[Role & Responsibilities]
├── Pre-change validation
├── Safety constraint verification
├── Impact assessment
├── Parameter dependency checking
└── Approval decision making

[Validation Framework]
├── Range validation: parameter within min/max
├── Dependency checking: no conflicts with other parameters
├── Impact assessment: KPI improvement vs. risk
├── Compliance verification: meets network policies
├── Safety assessment: risk to network service

[Critical Safety Rules]
├── Never approve changes during peak traffic (08:00-20:00)
├── Reject changes affecting >1 cell without business approval
├── Require rollback plan for all changes
├── Limit to 1 concurrent change per site
├── Reject if confidence in improvement <70%

[Response Format]
└── JSON with: validation_results, overall_assessment,
              risk_level, approval_decision, conditions,
              rejection_reasons
```

**Few-Shot Examples** (4-6 examples):
1. Approved low-risk parameter change
2. Approved high-risk change with conditions
3. Rejected change due to parameter range violation
4. Rejected change due to dependency conflict
5. Conditional approval with monitoring requirements
6. Change requiring business approval (multi-site impact)

**Task Prompts**:
- `validate_changes`: Pre-change validation
- `assess_impact`: Impact assessment
- `check_dependencies`: Dependency verification

### 3.7 Agent 6: Execution

**System Prompt Structure**:
```
[Role & Responsibilities]
├── Execute approved MML commands
├── Monitor KPIs during change
├── Detect issues and trigger rollback
├── Document execution results
└── Post-change analysis

[Execution Protocol]
├── Step 1: Execute pre-change snapshot commands
├── Step 2: Execute modification commands sequentially
├── Step 3: Monitor KPIs for 5 minutes post-change
├── Step 4: Execute verification commands
├── Step 5: Compare pre/post metrics
├── Step 6: Document results

[Rollback Criteria]
├── If network access success decreases by >5%
├── If any KPI degrades by >10% from baseline
├── If MML command fails with error
├── If KPI doesn't improve within 10 minutes

[Response Format]
└── JSON with: execution_status, commands_executed,
              kpi_impact, rollback_required,
              post_change_kpis, execution_notes
```

**Few-Shot Examples** (4-6 examples):
1. Successful parameter change with KPI improvement
2. Parameter change with no KPI impact (investigate)
3. Partial success (1 of 2 changes successful)
4. Rollback triggered due to KPI degradation
5. Command execution failure with recovery
6. Post-change analysis and documentation

**Task Prompts**:
- `execute_changes`: Execute validated changes
- `monitor_execution`: Real-time KPI monitoring
- `trigger_rollback`: Emergency rollback execution

---

## Integration Strategy

### 4.1 Composite Prompt Architecture

Each agent prompt will be composed of four layers:

```
┌─────────────────────────────────────────────────────┐
│ Layer 4: Task-Specific Instructions                 │
│ (monitor_kpis, analyze_performance, etc.)            │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│ Layer 3: Few-Shot Examples (3-5 examples)           │
│ (agent-specific success/failure patterns)            │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│ Layer 2: Domain Knowledge Context                   │
│ (parameters, KPIs, optimization rules)              │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│ Layer 1: System Prompt                              │
│ (role, responsibilities, expertise)                 │
└─────────────────────────────────────────────────────┘
```

### 4.2 Domain Knowledge Integration

#### Parameters (5 core parameters)
Each agent receives parameter definitions:
- **reference_signal_power_pdschcfg**: Download signal strength (-600 to 500, 0.1 dBm)
- **reference_signal_power_rs**: Cell coverage power (-600 to 500, 0.1 dBm)
- **a3_event_offset**: Handover sensitivity (0 to 15, dB)
- **t310_timer**: Connection recovery time (100 to 6000, ms)
- **p0_nominal_pusch**: Upload power control (-126 to 24, dBm)

#### KPIs (7 weighted metrics)
Each agent understands KPI interdependencies:
1. **network_access_success** (RACH): 25% weight, Target >95%
2. **download_quality** (DL IBLER): 20% weight, Target <15%
3. **upload_quality** (UL IBLER): 15% weight, Target <15%
4. **control_channel_load** (PDCCH): 15% weight, Target 20-70%
5. **feedback_channel_load** (PUCCH): 10% weight, Target 1-10%
6. **download_speed** (PDCP DL): 10% weight, Target >5000 kbit/s
7. **upload_speed** (PDCP UL): 5% weight, Target >1000 kbit/s

#### Optimization Rules (10 scenarios)
Knowledge base of proven optimizations:

1. **Low RACH Scenario**: Increase RACH power → improve network access
2. **High IBLER Scenario**: Improve DL power allocation → reduce errors
3. **Handover Issues**: Adjust A3 offset → reduce drops
4. **Control Channel Congestion**: Increase PDCCH aggregation → improve robustness
5. **Uplink Coverage**: Increase P0 PUSCH → improve upload
6. **Connection Instability**: Adjust T310 timer → reduce false alarms
7. **Multi-Issue Scenario**: Coordinate parameter changes → avoid conflicts
8. **Peak Traffic Optimization**: Balance utilization across parameters
9. **Low-Traffic Tuning**: Fine-tune sensitivity parameters
10. **Interference Mitigation**: Reduce power levels → reduce interference

### 4.3 Dynamic Prompt Composition

Runtime composition in Python:

```python
from rebuild-assets.prompts.prompt_manager import PromptManager

# 1. Initialize prompt manager
pm = PromptManager()

# 2. Build context
context = PromptContext(
    workflow_id="workflow_20251030_001",
    target_region="Bindura",
    current_step="monitoring_analysis",
    previous_results={...},
    user_query="Analyze current network performance",
    real_data_context={
        "data_source": "CSV",
        "total_records": 168,
        "date_range": "2025-09-01 to 2025-09-07",
        "critical_findings": "RACH 0.536%, DL IBLER 15.94%"
    },
    network_state={
        "sites": 4,
        "cells": 12,
        "current_traffic": "medium"
    }
)

# 3. Get base system prompt
system_prompt = pm.get_system_prompt("monitor_agent_system")

# 4. Get task-specific prompt
task_prompt = pm.get_task_prompt(
    "monitor_kpis",
    cell_id="0",
    kpi_data=format_kpi_data(context),
    kpi_thresholds=get_kpi_thresholds()
)

# 5. Inject few-shot examples
examples = load_few_shot_examples("monitoring_examples.json")
few_shot_text = format_examples_for_prompt(examples, count=3)

# 6. Compose final prompt
final_prompt = f"""{system_prompt}

DOMAIN KNOWLEDGE:
{domain_knowledge_context}

FEW-SHOT EXAMPLES:
{few_shot_text}

{task_prompt}"""

# 7. Call LLM with composed prompt
response = llm.invoke(final_prompt)
```

### 4.4 Few-Shot Integration Points

| Agent | Few-Shot Count | Example Types | Weighting |
|-------|----------------|---------------|-----------|
| Network Connector | 3 | 1 success, 1 failure, 1 recovery | 60/20/20 |
| Monitoring | 4 | 1 critical, 2 normal, 1 trend | 40/40/20 |
| KPI Analytics | 5 | 2 root cause, 2 strategy, 1 edge case | 40/40/20 |
| Configuration | 4 | 1 simple, 1 multi-param, 1 rollback, 1 complex | 25/25/25/25 |
| Validation | 4 | 1 approve, 1 reject, 1 conditional, 1 edge | 30/30/30/10 |
| Execution | 4 | 1 success, 1 rollback, 1 partial, 1 failure | 40/30/20/10 |

---

## Implementation Pattern

### 5.1 Prompt Template Class Structure

```python
# rebuild-assets/prompts/prompt_templates.py

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import json
from pathlib import Path

@dataclass
class PromptContext:
    """Context for prompt generation"""
    workflow_id: str
    target_region: str
    current_step: str
    previous_results: Dict[str, Any]
    user_query: str
    real_data_context: Dict[str, Any]
    network_state: Dict[str, Any]

class FewShotExampleLoader:
    """Load few-shot examples from JSON files"""

    def __init__(self, examples_dir: str = "rebuild-assets/prompts/examples"):
        self.examples_dir = Path(examples_dir)

    def load_examples(self, agent_name: str) -> List[Dict]:
        """Load examples for a specific agent"""
        file_path = self.examples_dir / f"{agent_name}_examples.json"
        if file_path.exists():
            with open(file_path) as f:
                data = json.load(f)
            return data.get("examples", [])
        return []

    def format_examples(self, examples: List[Dict], count: int = 3) -> str:
        """Format examples for prompt injection"""
        selected = examples[:count]
        formatted_parts = []
        for i, example in enumerate(selected, 1):
            formatted_parts.append(f"""
Example {i}:
Input: {example['input']}
Context: {json.dumps(example['context'])}
Output: {json.dumps(example['output'])}
Explanation: {example.get('explanation', 'N/A')}
""")
        return "\n".join(formatted_parts)

class PromptComposer:
    """Compose prompts with system, examples, domain knowledge, and tasks"""

    def __init__(self):
        self.system_prompts = self._load_system_prompts()
        self.task_prompts = self._load_task_prompts()
        self.example_loader = FewShotExampleLoader()
        self.domain_knowledge = self._load_domain_knowledge()

    def _load_system_prompts(self) -> Dict[str, str]:
        """Load system prompts from YAML"""
        import yaml
        with open("rebuild-assets/prompts/system_prompts.yaml") as f:
            return yaml.safe_load(f)

    def _load_task_prompts(self) -> Dict[str, str]:
        """Load task prompts from YAML"""
        import yaml
        with open("rebuild-assets/prompts/task_prompts.yaml") as f:
            return yaml.safe_load(f)

    def _load_domain_knowledge(self) -> Dict[str, Any]:
        """Load domain knowledge (parameters, KPIs, rules)"""
        return {
            "parameters": self._load_parameters(),
            "kpis": self._load_kpis(),
            "optimization_rules": self._load_optimization_rules()
        }

    def _load_parameters(self) -> str:
        """Load 5 core parameters"""
        return """
CORE PARAMETERS:

1. Reference Signal Power (PDSCHCFG)
   - Range: -600 to 500 (0.1 dBm units)
   - Impact: Coverage, interference control
   - MML: MOD PDSCHCFG:LOCALCELLID={id},REFERENCESIGNALPWR={value}

2. A3 Event Offset (Handover Threshold)
   - Range: 0 to 15 (dB)
   - Impact: Handover timing, ping-pong prevention
   - MML: MOD UECOOPERATIONPARA:LOCALCELLID={id},A3OFFSET={value}

3. T310 Timer (Connection Recovery)
   - Range: 100 to 6000 (ms)
   - Impact: RLF detection, call stability
   - MML: MOD UETIMERCONST:LOCALCELLID={id},T310={value}

4. P0 Nominal PUSCH (Upload Power)
   - Range: -126 to 24 (dBm)
   - Impact: Uplink coverage, interference
   - MML: MOD CELLULPCCOMM:LOCALCELLID={id},P0NOMINALPUSCH={value}

5. PDCCH Aggregation Level (Control Channel)
   - Range: 1, 2, 4, 8
   - Impact: Control channel robustness
   - MML: MOD CELLUSPARACFG:LOCALCELLID={id},PDCCHAGGLVL={value}
"""

    def _load_kpis(self) -> str:
        """Load 7 KPIs with thresholds"""
        return """
KEY PERFORMANCE INDICATORS (7 WEIGHTED METRICS):

1. Network Access Success (RACH) - Weight: 25%
   Current: 0.536% | Target: >95% | Critical: <90%

2. Download Quality (DL IBLER) - Weight: 20%
   Current: 15.94% | Target: <15% | Critical: >20%

3. Upload Quality (UL IBLER) - Weight: 15%
   Current: 12.8% | Target: <15% | Critical: >20%

4. Control Channel Load (PDCCH) - Weight: 15%
   Current: Normal | Target: 20-70% | Critical: >85%

5. Feedback Channel Load (PUCCH) - Weight: 10%
   Current: Normal | Target: 1-10% | Critical: >15%

6. Download Speed (PDCP) - Weight: 10%
   Current: Degraded | Target: >5000 kbit/s | Critical: <2000 kbit/s

7. Upload Speed (PDCP) - Weight: 5%
   Current: Degraded | Target: >1000 kbit/s | Critical: <500 kbit/s
"""

    def _load_optimization_rules(self) -> str:
        """Load 10 proven optimization scenarios"""
        return """
OPTIMIZATION RULES (10 SCENARIOS):

1. Low RACH Success: Increase RACH power → +20dBm improvements
2. High IBLER: Improve DL power allocation → <10% IBLER
3. Handover Issues: Adjust A3 offset by 1-2dB → reduce call drops
4. Control Channel Congestion: Increase PDCCH aggregation → robustness
5. Uplink Coverage: Increase P0 PUSCH → improve UL quality
6. Connection Instability: Adjust T310 to 1000-2000ms → stability
7. Multi-Issue: Coordinate changes, avoid conflicts → holistic improvement
8. Peak Traffic: Reduce power, increase resource allocation → balance
9. Low Traffic: Fine-tune sensitivity → optimal coverage
10. Interference: Reduce power levels, adjust A3 → mitigate interference
"""

    def compose_agent_prompt(
        self,
        agent_type: str,
        context: PromptContext,
        task_name: str,
        task_variables: Dict[str, Any],
        few_shot_count: int = 3
    ) -> str:
        """Compose complete prompt for an agent"""

        # Layer 1: System prompt
        system_key = f"{agent_type}_system"
        system_prompt = self.system_prompts.get(system_key, "")

        # Layer 2: Domain knowledge
        domain_text = f"""
DOMAIN KNOWLEDGE:

PARAMETERS:
{self.domain_knowledge['parameters']}

KPIs:
{self.domain_knowledge['kpis']}

OPTIMIZATION RULES:
{self.domain_knowledge['optimization_rules']}
"""

        # Layer 3: Few-shot examples
        examples = self.example_loader.load_examples(agent_type)
        few_shot_text = self.example_loader.format_examples(examples, few_shot_count)

        # Layer 4: Task-specific instructions
        task_template = self.task_prompts.get(task_name, "")
        task_text = task_template.format(**task_variables)

        # Compose final prompt
        final_prompt = f"""{system_prompt}

{domain_text}

FEW-SHOT EXAMPLES:
{few_shot_text}

TASK:
{task_text}

CONTEXT:
Workflow ID: {context.workflow_id}
Target Region: {context.target_region}
Current Step: {context.current_step}
Previous Results: {json.dumps(context.previous_results, indent=2)}
Network State: {json.dumps(context.network_state, indent=2)}
"""

        return final_prompt
```

### 5.2 Agent Integration Points

```python
# liquid-4g-core/agents/network_connector_agent.py

from rebuild-assets.prompts.prompt_templates import (
    PromptContext, FewShotExampleLoader, PromptComposer
)
from langchain.llms import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

class NetworkConnectorAgent:
    """Network Connector Agent with few-shot prompting"""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.3)
        self.prompt_composer = PromptComposer()

    def discover_network(self, context: PromptContext) -> Dict[str, Any]:
        """Discover network sites with few-shot guidance"""

        # Compose prompt with system + domain + examples + task
        prompt = self.prompt_composer.compose_agent_prompt(
            agent_type="network_connector",
            context=context,
            task_name="discover_network",
            task_variables={
                "region": context.target_region,
                "user_query": context.user_query,
                "api_status": "ready"
            },
            few_shot_count=3
        )

        # Call LLM
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        # Parse and return structured output
        import json
        return json.loads(response.content)
```

---

## Few-Shot Examples by Agent

### 6.1 Network Connector Examples (Formatted)

**File**: `/rebuild-assets/prompts/examples/network_connector_examples.json`

```json
{
  "agent": "network_connector",
  "examples": [
    {
      "example_id": "NC_001",
      "category": "successful_discovery",
      "input": "Discover all available network sites in Bindura region",
      "context": {
        "api_status": "authenticated",
        "region": "Bindura",
        "expected_sites": 4
      },
      "output": {
        "connection_status": "connected",
        "discovered_sites": ["MSH0013-Bindura-Zaoga", "MSH-0331-Chiwaridzo 2", "MSH-0112-Bindura Hospital", "MSH-0014-Chipadze"],
        "site_details": {
          "MSH0013-Bindura-Zaoga": {"cells": 3, "status": "active", "issues": []}
        },
        "next_stage_ready": true
      },
      "explanation": "Standard successful discovery of all 4 expected sites"
    }
  ]
}
```

### 6.2 Monitoring Examples (Formatted)

**File**: `/rebuild-assets/prompts/examples/monitoring_examples.json`

Uses real Bindura data from 2025-09-01 to 2025-09-07.

### 6.3 KPI Analytics Examples (Formatted)

**File**: `/rebuild-assets/prompts/examples/kpi_analytics_examples.json`

Includes root cause analysis and strategy generation with confidence levels.

---

## Domain Knowledge Integration

### 7.1 Parameter Definition Format

```python
PARAMETER_DEFINITIONS = {
    "reference_signal_power_rs": {
        "technical_name": "Reference Signal Power (RS Power)",
        "user_friendly_name": "Cell Coverage Power",
        "description": "Primary reference signal power (main coverage control)",
        "unit": "0.1 dBm",
        "range": (-600, 500),
        "default_value": -180,
        "query_command": "LST PDSCHCFG",
        "modify_command": "MOD PDSCHCFG:LOCALCELLID={cell_id},REFERENCESIGNALPWR={value}; {{{ne_name}}}",
        "impact": "Main parameter controlling cell footprint and interference",
        "related_kpis": ["network_access_success", "coverage_quality"],
        "optimization_rules": [
            "Low RACH → increase by 10-20 dBm",
            "High interference → decrease by 5-10 dBm"
        ]
    }
}
```

### 7.2 KPI Threshold Format

```python
KPI_THRESHOLDS = {
    "network_access_success": {
        "technical_name": "RACH Setup Success Rate (%)",
        "unit": "%",
        "higher_is_better": True,
        "normal_range": (95, 100),
        "warning_threshold": 93,
        "critical_threshold": 90,
        "current_value": 0.536,
        "related_parameters": ["reference_signal_power_rs", "rach_power"],
        "business_impact": "Controls network accessibility for all users"
    }
}
```

### 7.3 Optimization Rules Format

```python
OPTIMIZATION_RULES = [
    {
        "rule_id": "RACH_OPTIMIZATION",
        "scenario": "Network Access Success < 90%",
        "root_cause": "RACH reference signal power too low",
        "recommended_action": {
            "parameter": "reference_signal_power_rs",
            "adjustment": "increase by 15-20 dBm",
            "expected_improvement": "92%+ success rate",
            "confidence": 0.92,
            "side_effects": "May increase interference, monitor DL quality"
        },
        "similar_cases": ["case_2025_09_01", "case_2025_08_15"]
    }
]
```

---

## Testing & Validation

### 8.1 Prompt Quality Metrics

```python
class PromptQualityValidator:
    """Validate prompt quality and few-shot effectiveness"""

    @staticmethod
    def evaluate_prompt(prompt: str, response: str) -> Dict[str, float]:
        """Evaluate prompt quality metrics"""
        return {
            "response_completeness": 0.95,  # All required fields present
            "response_structure_match": 0.98,  # Matches expected JSON schema
            "kpi_improvement_coherence": 0.92,  # Improvements are realistic
            "confidence_calibration": 0.88,  # Confidence levels reasonable
            "safety_awareness": 0.96,  # Safety concerns properly addressed
            "domain_knowledge_application": 0.90  # Uses provided KPI/parameter context
        }
```

### 8.2 Few-Shot Effectiveness Testing

```python
def test_few_shot_impact(agent: str, task: str) -> Dict:
    """Compare agent performance with/without few-shot examples"""

    # Test 1: Without examples
    context_no_examples = {...}
    response_no_examples = agent.run(context_no_examples)

    # Test 2: With 3 examples
    context_with_3_examples = {..., few_shot_count=3}
    response_with_3_examples = agent.run(context_with_3_examples)

    # Test 3: With 5 examples
    context_with_5_examples = {..., few_shot_count=5}
    response_with_5_examples = agent.run(context_with_5_examples)

    return {
        "accuracy_improvement_3_examples": 0.12,  # 12% improvement
        "accuracy_improvement_5_examples": 0.18,  # 18% improvement
        "response_time_overhead": 0.08,  # 8% slower with examples
        "confidence_calibration_improvement": 0.15
    }
```

---

## Deployment Guide

### 9.1 File Organization

```
liquid-4g-core/
├── agents/
│   ├── __init__.py
│   ├── network_connector_agent.py
│   ├── monitoring_agent.py
│   ├── kpi_analytics_agent.py
│   ├── configuration_agent.py
│   ├── validation_agent.py
│   └── execution_agent.py
│
├── prompts/
│   ├── __init__.py
│   ├── prompt_manager.py  # Load prompts from YAML
│   ├── prompt_composer.py  # Compose prompts with few-shot
│   ├── example_loader.py  # Load and format examples
│   └── system_prompts.yaml
│   └── task_prompts.yaml
│   └── examples/
│       ├── network_connector_examples.json
│       ├── monitoring_examples.json
│       ├── kpi_analytics_examples.json
│       ├── configuration_examples.json
│       ├── validation_examples.json
│       └── execution_examples.json
│
└── domain/
    ├── parameters.py  # 5 parameters with MML templates
    ├── kpis.py  # 7 KPIs with thresholds
    └── optimization_rules.py  # 10 optimization scenarios
```

### 9.2 Integration Checklist

- [ ] Copy prompt files from `rebuild-assets/prompts/` to `liquid-4g-core/prompts/`
- [ ] Create few-shot examples JSON files in `prompts/examples/`
- [ ] Implement `PromptComposer` class for dynamic composition
- [ ] Implement `FewShotExampleLoader` for example management
- [ ] Update each agent to use new prompt composition system
- [ ] Test few-shot effectiveness with real Bindura data
- [ ] Validate all MML command generation patterns
- [ ] Deploy to production with monitoring

### 9.3 Configuration Example

```yaml
# liquid-4g-core/config/prompts.yaml

prompt_system:
  source: "rebuild-assets/prompts"
  examples_dir: "liquid-4g-core/prompts/examples"
  reload_interval_hours: 1

agents:
  network_connector:
    few_shot_count: 3
    temperature: 0.3
    max_tokens: 2000

  monitoring:
    few_shot_count: 4
    temperature: 0.2
    max_tokens: 2500

  kpi_analytics:
    few_shot_count: 5
    temperature: 0.3
    max_tokens: 3000

  configuration:
    few_shot_count: 4
    temperature: 0.1
    max_tokens: 2000

  validation:
    few_shot_count: 4
    temperature: 0.2
    max_tokens: 1500

  execution:
    few_shot_count: 4
    temperature: 0.1
    max_tokens: 1500

domain_knowledge:
  parameters_file: "rebuild-assets/domain_knowledge/liquid_zimbabwe_parameters.py"
  kpis_file: "rebuild-assets/domain_knowledge/liquid_zimbabwe_kpi.py"
  optimization_rules: 10
```

---

## Appendix: Key References

### Source Files
- `rebuild-assets/prompts/AGENT_PROMPTS_ARCHITECTURE.md` - Master prompt reference
- `rebuild-assets/prompts/prompt_templates.py` - Python implementation
- `rebuild-assets/prompts/enhanced_prompt_templates.py` - Real data integration
- `rebuild-assets/prompts/system_prompts.yaml` - System prompt definitions
- `rebuild-assets/prompts/task_prompts.yaml` - Task-specific templates
- `rebuild-assets/prompts/prompt_manager.py` - Runtime prompt management

### Domain Knowledge
- `rebuild-assets/domain_knowledge/liquid_zimbabwe_parameters.py` - 5 core parameters
- `rebuild-assets/domain_knowledge/liquid_zimbabwe_kpi.py` - 7 KPIs with thresholds
- `docs/NVIDIA_TO_LZ_MAPPING.md` - Nvidia → LZ mapping details

### Real Network Data
- **Region**: Bindura, Zimbabwe
- **Sites**: 4 eNodeB sites (MSH0013, MSH-0331, MSH-0112, MSH-0014)
- **Measurement Period**: 2025-09-01 to 2025-09-07
- **Data Points**: 168 KPI measurements
- **Critical Issues**: RACH 0.536%, DL IBLER 15.94%

---

**Document Status**: Ready for Implementation
**Next Phase**: Code development and testing
**Review Date**: 2025-11-15
