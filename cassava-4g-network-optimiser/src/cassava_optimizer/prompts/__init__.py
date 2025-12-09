"""
Few-shot examples for LLM optimization prompts.

These examples guide the LLM to generate appropriate recommendations
and MML commands for different network optimization scenarios.
"""

# =============================================================================
# Scenario 1: Low RACH Success Rate
# =============================================================================
RACH_OPTIMIZATION_EXAMPLE = {
    "scenario": "Low RACH Success Rate",
    "kpi_data": {
        "site_name": "MSH0013-Bindura-Zaoga",
        "rach_success_rate": 92.3,  # Below 99% target
        "preamble_format": 0,
        "power_ramping_step": 2,
        "preamble_initial_power": -104,
    },
    "analysis": """
The RACH Setup Success Rate of 92.3% is significantly below the target of 99%.
This indicates UEs are having difficulty completing the Random Access procedure.

Root Cause Analysis:
1. Preamble initial power (-104 dBm) may be too low for cell-edge users
2. Power ramping step (2 dB) may be insufficient for quick convergence
3. Current preamble format may not suit the cell's delay spread

Recommended Optimizations:
1. Increase preamble initial power by 4 dB to improve initial access attempts
2. Increase power ramping step to 4 dB for faster convergence
""",
    "recommendations": [
        {
            "parameter": "PREAMBLEINITIALRECEIVEDTARGETPOWER",
            "current_value": -104,
            "recommended_value": -100,
            "impact": "Improve cell-edge RACH success by 3-5%",
            "risk": "LOW",
        },
        {
            "parameter": "POWERRAMPINGSTEP",
            "current_value": 2,
            "recommended_value": 4,
            "impact": "Faster power convergence, reduce RACH attempts",
            "risk": "LOW",
        },
    ],
    "mml_commands": [
        "MOD RACHCFG:LOCALCELLID=1,PREAMBLEINITIALRECEIVEDTARGETPOWER=-100;",
        "MOD RACHCFG:LOCALCELLID=1,POWERRAMPINGSTEP=4;",
    ],
}

# =============================================================================
# Scenario 2: High PDCCH CCE Congestion
# =============================================================================
PDCCH_CONGESTION_EXAMPLE = {
    "scenario": "High PDCCH CCE Congestion",
    "kpi_data": {
        "site_name": "MSH-0331-Chiwaridzo 2",
        "pdcch_cce_usage": 78.5,  # Above 50% threshold
        "dl_prb_utilization": 85.2,
        "connected_ues": 245,
        "cfi_value": 2,
    },
    "analysis": """
PDCCH CCE Usage Rate at 78.5% is critically high, risking scheduling failures.
The high DL PRB utilization (85.2%) with 245 connected UEs confirms heavy load.

Root Cause Analysis:
1. CFI=2 limits control region to 2 OFDM symbols
2. High aggregation levels being used due to poor channel conditions
3. Insufficient CCE resources for current load

Recommended Optimizations:
1. Increase CFI to 3 during peak hours to expand control region
2. Enable dynamic CFI adjustment for load-based optimization
""",
    "recommendations": [
        {
            "parameter": "PDCCHCFI",
            "current_value": 2,
            "recommended_value": 3,
            "impact": "50% more CCE resources, reduce blocking by 20-30%",
            "risk": "MEDIUM - reduces data region slightly",
        },
        {
            "parameter": "DYNAMICCFISW",
            "current_value": "OFF",
            "recommended_value": "ON",
            "impact": "Automatic CFI adjustment based on load",
            "risk": "LOW",
        },
    ],
    "mml_commands": [
        "MOD PDCCHCFG:LOCALCELLID=1,PDCCHCFI=3;",
        "MOD PDCCHALGOSW:LOCALCELLID=1,DYNAMICCFISW=ON;",
    ],
}

# =============================================================================
# Scenario 3: High DL BLER
# =============================================================================
DL_BLER_EXAMPLE = {
    "scenario": "High Downlink Block Error Rate",
    "kpi_data": {
        "site_name": "MSH-0112-Bindura Hospital",
        "dl_bler": 18.5,  # Above 10% threshold
        "sinr_avg": 8.2,
        "reference_signal_power": -15,
        "pa_value": -3,
    },
    "analysis": """
DL IBLER at 18.5% is well above the 10% target, indicating transmission quality issues.
Average SINR of 8.2 dB suggests moderate but improvable signal quality.

Root Cause Analysis:
1. Reference signal power (-15 dBm) may be suboptimal for coverage
2. PA value of -3 dB reduces PDSCH power relative to RS
3. Possible interference from neighboring cells

Recommended Optimizations:
1. Adjust PA to increase PDSCH power relative to reference signals
2. Fine-tune PB for better power distribution between OFDM symbols
""",
    "recommendations": [
        {
            "parameter": "PA",
            "current_value": -3,
            "recommended_value": 0,
            "impact": "Increase PDSCH power by 3dB, improve SINR 2-3dB",
            "risk": "MEDIUM - may increase neighbor interference",
        },
        {
            "parameter": "PB",
            "current_value": 1,
            "recommended_value": 0,
            "impact": "Equal power across OFDM symbols",
            "risk": "LOW",
        },
    ],
    "mml_commands": [
        "MOD PDSCHCFG:LOCALCELLID=1,PA=0;",
        "MOD PDSCHCFG:LOCALCELLID=1,PB=0;",
    ],
}

# =============================================================================
# Scenario 4: Low DL Throughput
# =============================================================================
DL_THROUGHPUT_EXAMPLE = {
    "scenario": "Low Downlink Throughput",
    "kpi_data": {
        "site_name": "MSH-0014-Chipadze",
        "dl_throughput_mbps": 8.5,  # Below 20 Mbps target
        "dl_prb_utilization": 45.2,
        "cqi_avg": 7,
        "mimo_mode": "2x2",
    },
    "analysis": """
DL throughput at 8.5 Mbps is below the 20 Mbps target despite moderate PRB usage.
CQI average of 7 indicates suboptimal channel quality.

Root Cause Analysis:
1. Current MIMO mode (2x2) may not be optimal for traffic pattern
2. CQI reporting configuration may need tuning
3. Resource scheduling may be conservative

Recommended Optimizations:
1. Enable 4x4 MIMO if hardware supports it
2. Adjust CQI reporting to improve link adaptation
3. Enable carrier aggregation if multiple carriers available
""",
    "recommendations": [
        {
            "parameter": "TRANSMISSIONMODE",
            "current_value": "TM3",
            "recommended_value": "TM4",
            "impact": "Enable closed-loop spatial multiplexing",
            "risk": "LOW",
        },
        {
            "parameter": "CQIPERIODICITY",
            "current_value": 40,
            "recommended_value": 20,
            "impact": "Faster CQI updates, better link adaptation",
            "risk": "LOW - slight increase in uplink overhead",
        },
    ],
    "mml_commands": [
        "MOD PDSCHCFG:LOCALCELLID=1,TRANSMISSIONMODE=TM4;",
        "MOD CELLCQIRPTCFG:LOCALCELLID=1,CQIPERIODICITY=20;",
    ],
}

# =============================================================================
# Scenario 5: High UL BLER with Low Throughput
# =============================================================================
UL_OPTIMIZATION_EXAMPLE = {
    "scenario": "High UL BLER and Low Throughput",
    "kpi_data": {
        "site_name": "MSH0013-Bindura-Zaoga",
        "ul_bler": 15.2,  # Above 10% target
        "ul_throughput_mbps": 3.2,  # Below 10 Mbps target
        "pucch_usage": 65.3,
        "pusch_power_control": "OPEN_LOOP",
    },
    "analysis": """
UL IBLER at 15.2% with throughput at 3.2 Mbps indicates uplink quality issues.
High PUCCH usage (65.3%) suggests control channel congestion.

Root Cause Analysis:
1. Open-loop power control may not adapt quickly to channel variations
2. PUCCH format configuration may be inefficient
3. UE transmit power may be insufficient at cell edge

Recommended Optimizations:
1. Enable closed-loop power control for better adaptation
2. Adjust PUCCH format for current traffic pattern
3. Increase P0 nominal to improve cell-edge UE performance
""",
    "recommendations": [
        {
            "parameter": "ULDPCSW",
            "current_value": "OFF",
            "recommended_value": "ON",
            "impact": "Enable uplink closed-loop power control",
            "risk": "LOW",
        },
        {
            "parameter": "P0NOMINALPUSCH",
            "current_value": -85,
            "recommended_value": -80,
            "impact": "Increase UE transmit power target by 5dB",
            "risk": "MEDIUM - may increase inter-cell interference",
        },
    ],
    "mml_commands": [
        "MOD ULPCCOMMCFG:LOCALCELLID=1,ULDPCSW=ON;",
        "MOD ULPCCOMMCFG:LOCALCELLID=1,P0NOMINALPUSCH=-80;",
    ],
}


# =============================================================================
# Combined Examples for System Prompt
# =============================================================================
ALL_EXAMPLES = [
    RACH_OPTIMIZATION_EXAMPLE,
    PDCCH_CONGESTION_EXAMPLE,
    DL_BLER_EXAMPLE,
    DL_THROUGHPUT_EXAMPLE,
    UL_OPTIMIZATION_EXAMPLE,
]


def format_example_for_prompt(example: dict) -> str:
    """Format an example for inclusion in an LLM prompt."""
    return f"""
### Example: {example['scenario']}

**Input KPI Data:**
```json
{example['kpi_data']}
```

**Analysis:**
{example['analysis']}

**Recommendations:**
{chr(10).join(f"- {r['parameter']}: {r['current_value']} → {r['recommended_value']} ({r['impact']})" for r in example['recommendations'])}

**MML Commands:**
```
{chr(10).join(example['mml_commands'])}
```
"""


def get_few_shot_prompt() -> str:
    """Get formatted few-shot examples for the optimization prompt."""
    examples_text = "\n\n".join(format_example_for_prompt(ex) for ex in ALL_EXAMPLES)
    
    return f"""
## Optimization Examples

The following examples demonstrate the expected analysis format and MML command generation:

{examples_text}

---
Now analyze the following network data and provide recommendations in the same format:
"""


def get_relevant_examples(kpi_issues: list[str]) -> list[dict]:
    """
    Get examples relevant to the detected KPI issues.
    
    Args:
        kpi_issues: List of issue types like ["rach", "dl_bler", "throughput"]
        
    Returns:
        List of relevant example dictionaries
    """
    issue_map = {
        "rach": RACH_OPTIMIZATION_EXAMPLE,
        "pdcch": PDCCH_CONGESTION_EXAMPLE,
        "cce": PDCCH_CONGESTION_EXAMPLE,
        "dl_bler": DL_BLER_EXAMPLE,
        "dl_ibler": DL_BLER_EXAMPLE,
        "throughput": DL_THROUGHPUT_EXAMPLE,
        "dl_throughput": DL_THROUGHPUT_EXAMPLE,
        "ul_bler": UL_OPTIMIZATION_EXAMPLE,
        "ul_ibler": UL_OPTIMIZATION_EXAMPLE,
        "ul_throughput": UL_OPTIMIZATION_EXAMPLE,
        "pucch": UL_OPTIMIZATION_EXAMPLE,
    }
    
    relevant = []
    for issue in kpi_issues:
        issue_lower = issue.lower()
        for key, example in issue_map.items():
            if key in issue_lower and example not in relevant:
                relevant.append(example)
                break
    
    return relevant if relevant else [ALL_EXAMPLES[0]]  # Default to first example
