"""
Liquid Zimbabwe 4G Network Optimizer - Few-Shot Examples
Purpose: Few-shot learning examples for Configuration Agent
Created: 2025-10-30

These examples teach the agent how to optimize parameters based on past successes.
"""

from typing import List, Dict


# ============================================================================
# FEW-SHOT EXAMPLES FOR CONFIGURATION AGENT
# ============================================================================

FEW_SHOT_EXAMPLES = [
    # Example 1: Low Download Speed Optimization
    {
        "scenario": "Low Download Speed at MSH0013-Bindura-Zaoga",
        "initial_kpis": {
            "download_speed": 42.5,  # Below 50 Mbps threshold
            "network_access_success": 94.2,
            "download_quality": 96.1,
            "upload_speed": 22.0,
            "weighted_score": 78.5  # FAIR
        },
        "kpi_issue": "low_download_speed",
        "current_parameters": {
            "reference_signal_power_pdschcfg": -220
        },
        "recommended_change": {
            "parameter": "reference_signal_power_pdschcfg",
            "from_value": -220,
            "to_value": -180,
            "change": +40,
            "reasoning": "Increasing reference signal power by 40 units (4 dBm) improves cell-edge SINR, leading to better download throughput"
        },
        "expected_outcome": {
            "download_speed": "+15-25%",
            "network_access_success": "+1-2%",
            "side_effects": ["Increased power consumption", "Potential interference to neighbors"]
        },
        "actual_outcome": {
            "download_speed": 58.3,  # +37% improvement
            "network_access_success": 95.8,  # +1.6%
            "weighted_score": 85.2,  # GOOD
            "success": True
        },
        "confidence": 0.85
    },

    # Example 2: Low Network Access Success Optimization
    {
        "scenario": "Poor RACH Success at MSH0014-Mutare-CBD",
        "initial_kpis": {
            "network_access_success": 92.1,  # Below 95% threshold
            "download_speed": 55.0,
            "upload_speed": 25.0,
            "weighted_score": 82.3  # GOOD but access degrading
        },
        "kpi_issue": "low_network_access_success",
        "current_parameters": {
            "reference_signal_power_pdschcfg": -240,
            "t310_timer": 1000
        },
        "recommended_change": {
            "parameter": "reference_signal_power_pdschcfg",
            "from_value": -240,
            "to_value": -200,
            "change": +40,
            "reasoning": "Increasing reference signal power improves cell coverage, making it easier for UEs to detect and access the network"
        },
        "expected_outcome": {
            "network_access_success": "+2-5%",
            "download_speed": "+5-10%",
            "side_effects": ["Higher power consumption", "May affect neighbor cell coverage"]
        },
        "actual_outcome": {
            "network_access_success": 96.5,  # +4.4% improvement
            "download_speed": 61.2,  # +11.3%
            "weighted_score": 88.7,  # GOOD
            "success": True
        },
        "confidence": 0.85
    },

    # Example 3: Low Upload Speed Optimization
    {
        "scenario": "Poor Uplink Performance at MSH0015-Harare-North",
        "initial_kpis": {
            "upload_speed": 15.2,  # Below 20 Mbps threshold
            "upload_quality": 93.5,  # Also below 95%
            "download_speed": 65.0,
            "network_access_success": 96.0,
            "weighted_score": 81.0  # GOOD but uplink poor
        },
        "kpi_issue": "low_upload_speed",
        "current_parameters": {
            "p0_nominal_pusch": -95
        },
        "recommended_change": {
            "parameter": "p0_nominal_pusch",
            "from_value": -95,
            "to_value": -85,
            "change": +10,
            "reasoning": "Increasing P0 nominal PUSCH raises UE transmit power, improving uplink SINR and throughput especially for cell-edge users"
        },
        "expected_outcome": {
            "upload_speed": "+15-25%",
            "upload_quality": "+1-3%",
            "side_effects": ["Increased UE battery drain", "Potential uplink interference"]
        },
        "actual_outcome": {
            "upload_speed": 21.8,  # +43% improvement
            "upload_quality": 95.8,  # +2.3%
            "weighted_score": 86.5,  # GOOD
            "success": True
        },
        "confidence": 0.85
    },

    # Example 4: High Control Channel Load Optimization
    {
        "scenario": "PDCCH Congestion at MSH0016-Bulawayo-West",
        "initial_kpis": {
            "control_channel_load": 85.0,  # Above 80% threshold
            "download_quality": 92.0,  # Below 95%
            "download_speed": 48.0,
            "network_access_success": 95.5,
            "weighted_score": 79.5  # FAIR
        },
        "kpi_issue": "high_control_channel_load",
        "current_parameters": {
            "pdcch_aggregation_level": 2
        },
        "recommended_change": {
            "parameter": "pdcch_aggregation_level",
            "from_value": 2,
            "to_value": 4,
            "change": +2,
            "reasoning": "Increasing aggregation level improves PDCCH decoding reliability, reducing retransmissions and overall resource usage"
        },
        "expected_outcome": {
            "control_channel_load": "-10-15%",
            "download_quality": "+2-4%",
            "side_effects": ["Uses more CCEs per transmission", "May reduce max concurrent users"]
        },
        "actual_outcome": {
            "control_channel_load": 72.0,  # -13 pp reduction
            "download_quality": 95.5,  # +3.5%
            "weighted_score": 84.8,  # GOOD
            "success": True
        },
        "confidence": 0.70
    },

    # Example 5: Combined Issue - Low Access + Low Upload
    {
        "scenario": "Coverage and Uplink Issues at MSH0017-Gweru-Central",
        "initial_kpis": {
            "network_access_success": 93.0,  # Below 95%
            "upload_speed": 18.5,  # Below 20 Mbps
            "download_speed": 52.0,
            "weighted_score": 77.0  # FAIR
        },
        "kpi_issue": "low_access_and_upload",
        "current_parameters": {
            "reference_signal_power_pdschcfg": -230,
            "p0_nominal_pusch": -92
        },
        "recommended_change": [
            {
                "parameter": "reference_signal_power_pdschcfg",
                "from_value": -230,
                "to_value": -190,
                "change": +40,
                "reasoning": "Primary: Improve coverage for better access success"
            },
            {
                "parameter": "p0_nominal_pusch",
                "from_value": -92,
                "to_value": -87,
                "change": +5,
                "reasoning": "Secondary: Boost uplink power (smaller change due to combined optimization)"
            }
        ],
        "expected_outcome": {
            "network_access_success": "+2-4%",
            "upload_speed": "+10-15%",
            "download_speed": "+5-10%",
            "side_effects": ["Higher power consumption (both DL and UL)", "Increased interference risk"]
        },
        "actual_outcome": {
            "network_access_success": 96.2,  # +3.2%
            "upload_speed": 22.3,  # +20.5%
            "download_speed": 57.5,  # +10.6%
            "weighted_score": 86.0,  # GOOD
            "success": True
        },
        "confidence": 0.80
    }
]


# ============================================================================
# FEW-SHOT FORMATTING FUNCTIONS
# ============================================================================

def format_few_shot_examples(kpi_issue: str, top_n: int = 3) -> str:
    """
    Format few-shot examples relevant to a specific KPI issue.

    Args:
        kpi_issue: KPI issue to match (e.g., 'low_download_speed')
        top_n: Number of examples to return

    Returns:
        Formatted string of few-shot examples
    """
    # Filter examples matching the KPI issue
    relevant_examples = [ex for ex in FEW_SHOT_EXAMPLES if ex["kpi_issue"] == kpi_issue]

    # If no exact matches, return all examples
    if not relevant_examples:
        relevant_examples = FEW_SHOT_EXAMPLES

    # Limit to top_n
    examples = relevant_examples[:top_n]

    # Format as string
    formatted = "\n" + "=" * 80 + "\n"
    formatted += "PAST SUCCESSFUL OPTIMIZATIONS (Learn from these):\n"
    formatted += "=" * 80 + "\n\n"

    for i, example in enumerate(examples, 1):
        formatted += f"Example {i}: {example['scenario']}\n"
        formatted += "-" * 80 + "\n"

        formatted += f"KPI Issue: {example['kpi_issue']}\n"
        formatted += f"Initial KPIs:\n"
        for kpi, value in example['initial_kpis'].items():
            formatted += f"  - {kpi}: {value}\n"

        formatted += f"\nCurrent Parameters:\n"
        for param, value in example['current_parameters'].items():
            formatted += f"  - {param}: {value}\n"

        formatted += f"\nRecommended Change:\n"
        if isinstance(example['recommended_change'], list):
            for change in example['recommended_change']:
                formatted += f"  - {change['parameter']}: {change['from_value']} → {change['to_value']} (Δ {change['change']:+})\n"
                formatted += f"    Reasoning: {change['reasoning']}\n"
        else:
            change = example['recommended_change']
            formatted += f"  - {change['parameter']}: {change['from_value']} → {change['to_value']} (Δ {change['change']:+})\n"
            formatted += f"    Reasoning: {change['reasoning']}\n"

        formatted += f"\nExpected Outcome:\n"
        for kpi, improvement in example['expected_outcome'].items():
            if kpi != 'side_effects':
                formatted += f"  - {kpi}: {improvement}\n"

        formatted += f"\nActual Outcome (SUCCESS):\n"
        for kpi, value in example['actual_outcome'].items():
            if kpi != 'success':
                formatted += f"  - {kpi}: {value}\n"

        formatted += f"\nConfidence: {example['confidence']*100:.0f}%\n"
        formatted += "\n" + "=" * 80 + "\n\n"

    formatted += "Based on these successful examples, recommend parameter changes that follow similar patterns.\n"

    return formatted


def get_all_few_shot_examples() -> str:
    """Get all few-shot examples formatted for prompts."""
    return format_few_shot_examples("", top_n=5)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Get few-shot examples for low download speed
    examples = format_few_shot_examples("low_download_speed", top_n=2)
    print(examples)

    print("\n\n")
    print("All KPI issues covered:")
    issues = set(ex['kpi_issue'] for ex in FEW_SHOT_EXAMPLES)
    for issue in issues:
        print(f"  - {issue}")
