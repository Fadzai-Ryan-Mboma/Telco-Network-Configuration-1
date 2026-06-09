"""
Liquid Zimbabwe 4G Network Optimizer - Optimization Rules
Purpose: Define rules and logic for parameter optimization based on KPI issues
Created: 2025-10-30

This module contains the 10 core optimization rules that map KPI problems to parameter adjustments.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


# ============================================================================
# OPTIMIZATION RULE DATA STRUCTURE
# ============================================================================

@dataclass
class OptimizationRule:
    """Represents a single optimization rule."""
    rule_id: str
    kpi_issue: str
    parameter_name: str
    adjustment_direction: str  # 'increase' or 'decrease'
    adjustment_magnitude: str  # 'small', 'medium', 'large'
    confidence: float  # 0.0 to 1.0
    expected_improvement: str
    side_effects: List[str]
    risk_level: int  # 1-10 scale
    description: str


# ============================================================================
# 10 CORE OPTIMIZATION RULES
# ============================================================================

OPTIMIZATION_RULES = {
    # ========================================================================
    # RULE 1: Low Network Access Success → Increase Reference Signal Power
    # ========================================================================
    "rule_01": OptimizationRule(
        rule_id="rule_01",
        kpi_issue="low_network_access_success",
        parameter_name="reference_signal_power_pdschcfg",
        adjustment_direction="increase",
        adjustment_magnitude="medium",
        confidence=0.85,
        expected_improvement="Network access success rate should improve by 2-5% as UEs can detect cell more easily",
        side_effects=[
            "Increased power consumption",
            "Potential interference to neighboring cells",
            "May slightly increase download speed as well"
        ],
        risk_level=4,
        description="Increasing reference signal power improves cell coverage and makes it easier for UEs to detect and access the network"
    ),

    # ========================================================================
    # RULE 2: Low Download Speed → Increase Reference Signal Power
    # ========================================================================
    "rule_02": OptimizationRule(
        rule_id="rule_02",
        kpi_issue="low_download_speed",
        parameter_name="reference_signal_power_pdschcfg",
        adjustment_direction="increase",
        adjustment_magnitude="medium",
        confidence=0.80,
        expected_improvement="Download speed should improve by 10-20% due to better SINR at cell edge",
        side_effects=[
            "Increased power consumption",
            "Potential interference to neighboring cells",
            "Network access success may also improve"
        ],
        risk_level=4,
        description="Higher reference signal power improves SINR, especially for cell-edge users, leading to better throughput"
    ),

    # ========================================================================
    # RULE 3: High Handover Failures → Adjust A3 Event Offset
    # ========================================================================
    "rule_03": OptimizationRule(
        rule_id="rule_03",
        kpi_issue="high_handover_failures",
        parameter_name="a3_event_offset",
        adjustment_direction="decrease",
        adjustment_magnitude="small",
        confidence=0.75,
        expected_improvement="Earlier handover triggering should reduce handover failures and dropped calls",
        side_effects=[
            "May increase handover ping-pong if set too low",
            "Slight increase in signaling overhead",
            "Network access success rate may improve"
        ],
        risk_level=5,
        description="Reducing A3 offset triggers handovers earlier, preventing late handovers and dropped calls"
    ),

    # ========================================================================
    # RULE 4: Frequent Radio Link Failures → Increase T310 Timer
    # ========================================================================
    "rule_04": OptimizationRule(
        rule_id="rule_04",
        kpi_issue="frequent_radio_link_failures",
        parameter_name="t310_timer",
        adjustment_direction="increase",
        adjustment_magnitude="small",
        confidence=0.80,
        expected_improvement="More tolerance for temporary signal degradation, reducing unnecessary RRC re-establishments",
        side_effects=[
            "Longer time to detect actual radio link failures",
            "May delay handovers in some cases",
            "Improved network access success rate"
        ],
        risk_level=3,
        description="Longer T310 timer gives UE more time to recover from temporary signal issues before declaring radio link failure"
    ),

    # ========================================================================
    # RULE 5: Low Upload Speed → Increase P0 Nominal PUSCH
    # ========================================================================
    "rule_05": OptimizationRule(
        rule_id="rule_05",
        kpi_issue="low_upload_speed",
        parameter_name="p0_nominal_pusch",
        adjustment_direction="increase",
        adjustment_magnitude="medium",
        confidence=0.85,
        expected_improvement="Upload speed should improve by 15-25% due to increased UE transmit power",
        side_effects=[
            "Increased UE battery consumption",
            "Potential uplink interference",
            "Upload quality may also improve"
        ],
        risk_level=4,
        description="Higher P0 nominal PUSCH increases UE transmit power, improving uplink throughput especially for cell-edge users"
    ),

    # ========================================================================
    # RULE 6: Poor Upload Quality → Increase P0 Nominal PUSCH
    # ========================================================================
    "rule_06": OptimizationRule(
        rule_id="rule_06",
        kpi_issue="poor_upload_quality",
        parameter_name="p0_nominal_pusch",
        adjustment_direction="increase",
        adjustment_magnitude="small",
        confidence=0.80,
        expected_improvement="Upload IBLER should decrease by 2-4% due to improved uplink SINR",
        side_effects=[
            "Increased UE battery consumption",
            "Potential uplink interference",
            "Upload speed may also improve"
        ],
        risk_level=3,
        description="Higher UE transmit power improves uplink SINR, reducing uplink error rates"
    ),

    # ========================================================================
    # RULE 7: High Control Channel Load → Increase PDCCH Aggregation Level
    # ========================================================================
    "rule_07": OptimizationRule(
        rule_id="rule_07",
        kpi_issue="high_control_channel_load",
        parameter_name="pdcch_aggregation_level",
        adjustment_direction="increase",
        adjustment_magnitude="small",
        confidence=0.70,
        expected_improvement="Better PDCCH decoding reliability may reduce retransmissions and improve resource utilization",
        side_effects=[
            "Uses more CCE resources per transmission",
            "May reduce total PDCCH capacity",
            "Download quality may improve slightly"
        ],
        risk_level=5,
        description="Higher aggregation level improves PDCCH decoding reliability but uses more resources per user"
    ),

    # ========================================================================
    # RULE 8: Poor Download Quality → Increase PDCCH Aggregation Level
    # ========================================================================
    "rule_08": OptimizationRule(
        rule_id="rule_08",
        kpi_issue="poor_download_quality",
        parameter_name="pdcch_aggregation_level",
        adjustment_direction="increase",
        adjustment_magnitude="small",
        confidence=0.65,
        expected_improvement="Better control channel decoding may reduce scheduling errors and improve download IBLER by 1-3%",
        side_effects=[
            "Increased control channel resource usage",
            "May reduce total PDCCH capacity"
        ],
        risk_level=4,
        description="More reliable PDCCH decoding ensures scheduling grants are received correctly, reducing retransmissions"
    ),

    # ========================================================================
    # RULE 9: Excessive Handovers (Ping-Pong) → Increase A3 Event Offset
    # ========================================================================
    "rule_09": OptimizationRule(
        rule_id="rule_09",
        kpi_issue="excessive_handovers",
        parameter_name="a3_event_offset",
        adjustment_direction="increase",
        adjustment_magnitude="small",
        confidence=0.75,
        expected_improvement="Reduced handover frequency and ping-pong effects by 20-30%",
        side_effects=[
            "Handovers triggered later",
            "May increase late handover failures if set too high",
            "Reduced signaling overhead"
        ],
        risk_level=5,
        description="Higher A3 offset requires stronger neighbor signal before triggering handover, reducing ping-pong"
    ),

    # ========================================================================
    # RULE 10: Low Network Access + Low Upload → Increase P0 and Ref Signal
    # ========================================================================
    "rule_10": OptimizationRule(
        rule_id="rule_10",
        kpi_issue="low_access_and_upload",
        parameter_name="reference_signal_power_pdschcfg",  # Primary adjustment
        adjustment_direction="increase",
        adjustment_magnitude="medium",
        confidence=0.80,
        expected_improvement="Both network access and upload should improve by 10-20% through better coverage",
        side_effects=[
            "Increased power consumption",
            "Potential interference",
            "Should also adjust P0 nominal PUSCH as secondary action"
        ],
        risk_level=5,
        description="Combined coverage and uplink power issue requires improving downlink reference signal first"
    ),

    # ========================================================================
    # TA-BASED RULES: Coverage Optimization
    # ========================================================================

    # ========================================================================
    # RULE 11: High TA Overshoot → Reduce Power + Alert for Downtilt
    # ========================================================================
    "rule_11": OptimizationRule(
        rule_id="rule_11",
        kpi_issue="high_ta_overshoot",
        parameter_name="reference_signal_power_pdschcfg",
        adjustment_direction="decrease",
        adjustment_magnitude="medium",
        confidence=0.85,
        expected_improvement="Overshoot percentage should decrease by 20-30%, reducing interference to neighbors",
        side_effects=[
            "Slightly reduced cell-edge coverage (acceptable trade-off)",
            "Lower power consumption (beneficial)",
            "Manual antenna downtilt may still be needed for optimal results"
        ],
        risk_level=4,
        description="High overshoot (Index 0, 10, 11 >10%) indicates antenna overshooting nearby area or excessive far coverage. Reduce power and alert engineer for manual antenna adjustment."
    ),

    # ========================================================================
    # RULE 12: High Cell Edge Loading → Increase Power
    # ========================================================================
    "rule_12": OptimizationRule(
        rule_id="rule_12",
        kpi_issue="high_cell_edge",
        parameter_name="reference_signal_power_pdschcfg",
        adjustment_direction="increase",
        adjustment_magnitude="medium",
        confidence=0.80,
        expected_improvement="Cell edge percentage should decrease by 10-20% as coverage extends, improving SINR for distant UEs",
        side_effects=[
            "Increased power consumption",
            "Potential interference to neighboring cells (monitor neighbors)",
            "May slightly increase handover rate"
        ],
        risk_level=5,
        description="High cell edge loading (Index 9-11 >20%) indicates too many UEs at cell boundary, suggesting coverage gap. Increase power to extend healthy coverage zone."
    ),

    # ========================================================================
    # RULE 13: Low Average TA → Manual Antenna Adjustment Alert (NOT Automated)
    # ========================================================================
    "rule_13": OptimizationRule(
        rule_id="rule_13",
        kpi_issue="low_avg_ta",
        parameter_name="None",  # No automated parameter change
        adjustment_direction="alert_only",
        adjustment_magnitude="none",
        confidence=0.90,
        expected_improvement="Manual antenna downtilt adjustment will improve coverage distribution",
        side_effects=[
            "No automated action - requires engineer intervention"
        ],
        risk_level=0,
        description="Low average TA index (<3.0) indicates excessive overshooting. This requires MANUAL antenna adjustment (downtilt), not automated parameter changes. Alert engineer."
    )
}


# ============================================================================
# KPI ISSUE DETECTION
# ============================================================================

def detect_kpi_issues(kpis: Dict[str, float], thresholds: Dict[str, float]) -> List[str]:
    """
    Detect KPI issues by comparing current values against thresholds.

    Args:
        kpis: Dictionary of current KPI values
        thresholds: Dictionary of threshold values

    Returns:
        List of detected KPI issue identifiers
    """
    issues = []

    # Network Access Success
    if kpis.get('network_access_success', 100) < thresholds.get('network_access_success_min', 95.0):
        issues.append('low_network_access_success')

    # Download Speed
    if kpis.get('download_speed', 100) < thresholds.get('download_speed_min', 50.0):
        issues.append('low_download_speed')

    # Upload Speed
    if kpis.get('upload_speed', 100) < thresholds.get('upload_speed_min', 20.0):
        issues.append('low_upload_speed')

    # Download Quality
    if kpis.get('download_quality', 100) < thresholds.get('download_quality_min', 95.0):
        issues.append('poor_download_quality')

    # Upload Quality
    if kpis.get('upload_quality', 100) < thresholds.get('upload_quality_min', 95.0):
        issues.append('poor_upload_quality')

    # Control Channel Load
    if kpis.get('control_channel_load', 0) > thresholds.get('control_channel_load_max', 80.0):
        issues.append('high_control_channel_load')

    # TA-Based Issues
    # High TA Overshoot
    if kpis.get('ta_overshoot_percentage', 0) > thresholds.get('ta_overshoot_max', 10.0):
        issues.append('high_ta_overshoot')

    # High Cell Edge Loading
    if kpis.get('cell_edge_percentage', 0) > thresholds.get('cell_edge_max', 20.0):
        issues.append('high_cell_edge')

    # Low Average TA (overshooting)
    if kpis.get('avg_timing_advance', 10) < thresholds.get('avg_ta_min', 3.0):
        issues.append('low_avg_ta')

    # Combined issues
    if 'low_network_access_success' in issues and 'low_upload_speed' in issues:
        issues.append('low_access_and_upload')

    return issues


# ============================================================================
# RULE MATCHING
# ============================================================================

def find_applicable_rules(kpi_issues: List[str]) -> List[OptimizationRule]:
    """
    Find optimization rules applicable to detected KPI issues.

    Args:
        kpi_issues: List of detected KPI issue identifiers

    Returns:
        List of applicable OptimizationRule objects, sorted by confidence
    """
    applicable_rules = []

    for rule_id, rule in OPTIMIZATION_RULES.items():
        if rule.kpi_issue in kpi_issues:
            applicable_rules.append(rule)

    # Sort by confidence (highest first)
    applicable_rules.sort(key=lambda r: r.confidence, reverse=True)

    return applicable_rules


def recommend_parameter_changes(
    kpi_issues: List[str],
    current_parameters: Dict[str, Any],
    parameter_limits: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generate parameter change recommendations based on KPI issues.

    Args:
        kpi_issues: List of detected KPI issues
        current_parameters: Current parameter values
        parameter_limits: Parameter range limits and constraints

    Returns:
        List of parameter change recommendations
    """
    recommendations = []

    applicable_rules = find_applicable_rules(kpi_issues)

    for rule in applicable_rules:
        param_name = rule.parameter_name
        current_value = current_parameters.get(param_name)

        if current_value is None:
            continue

        # Get parameter limits
        limits = parameter_limits.get(param_name, {})
        param_range = limits.get('range', (None, None))
        max_change = limits.get('max_change', None)

        # Calculate adjustment value
        adjustment = calculate_adjustment(
            current_value=current_value,
            direction=rule.adjustment_direction,
            magnitude=rule.adjustment_magnitude,
            param_range=param_range,
            max_change=max_change
        )

        new_value = current_value + adjustment

        # Validate new value is within range
        if param_range[0] is not None and new_value < param_range[0]:
            new_value = param_range[0]
        if param_range[1] is not None and new_value > param_range[1]:
            new_value = param_range[1]

        recommendation = {
            'rule_id': rule.rule_id,
            'kpi_issue': rule.kpi_issue,
            'parameter_name': param_name,
            'current_value': current_value,
            'recommended_value': new_value,
            'adjustment': adjustment,
            'confidence': rule.confidence,
            'expected_improvement': rule.expected_improvement,
            'side_effects': rule.side_effects,
            'risk_level': rule.risk_level,
            'description': rule.description
        }

        recommendations.append(recommendation)

    return recommendations


def calculate_adjustment(
    current_value: float,
    direction: str,
    magnitude: str,
    param_range: Tuple[Optional[float], Optional[float]],
    max_change: Optional[float]
) -> float:
    """
    Calculate parameter adjustment amount.

    Args:
        current_value: Current parameter value
        direction: 'increase' or 'decrease'
        magnitude: 'small', 'medium', or 'large'
        param_range: (min, max) tuple for parameter
        max_change: Maximum allowed change

    Returns:
        Adjustment value (positive for increase, negative for decrease)
    """
    # Define magnitude as percentage of range or max_change
    magnitude_percentages = {
        'small': 0.10,    # 10%
        'medium': 0.20,   # 20%
        'large': 0.30     # 30%
    }

    percentage = magnitude_percentages.get(magnitude, 0.20)

    # Calculate adjustment based on range or max_change
    if max_change is not None:
        adjustment = max_change * percentage
    elif param_range[0] is not None and param_range[1] is not None:
        range_size = param_range[1] - param_range[0]
        adjustment = range_size * percentage
    else:
        # Fallback: 10% of current value
        adjustment = abs(current_value) * 0.10

    # Apply direction
    if direction == 'decrease':
        adjustment = -adjustment

    return adjustment


# ============================================================================
# RISK ASSESSMENT
# ============================================================================

def assess_combined_risk(recommendations: List[Dict[str, Any]]) -> int:
    """
    Assess combined risk of multiple parameter changes.

    Args:
        recommendations: List of parameter change recommendations

    Returns:
        Combined risk score (1-10)
    """
    if not recommendations:
        return 0

    # Maximum risk among all recommendations
    max_risk = max(rec['risk_level'] for rec in recommendations)

    # Add risk penalty for multiple changes
    num_changes = len(recommendations)
    if num_changes > 1:
        risk_penalty = min(num_changes - 1, 3)  # Max penalty of 3
        max_risk = min(max_risk + risk_penalty, 10)

    return max_risk


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Detect KPI issues
    kpis = {
        'network_access_success': 92.5,  # Below 95% threshold
        'download_speed': 45.0,          # Below 50 Mbps threshold
        'upload_speed': 22.0,            # OK
        'download_quality': 96.0,        # OK
        'upload_quality': 94.0,          # Below 95% threshold
        'control_channel_load': 55.0,    # OK
        'feedback_channel_load': 25.0    # OK
    }

    thresholds = {
        'network_access_success_min': 95.0,
        'download_speed_min': 50.0,
        'upload_speed_min': 20.0,
        'download_quality_min': 95.0,
        'upload_quality_min': 95.0,
        'control_channel_load_max': 80.0
    }

    issues = detect_kpi_issues(kpis, thresholds)
    print("Detected KPI Issues:", issues)
    # Output: ['low_network_access_success', 'low_download_speed', 'poor_upload_quality']

    # Example: Find applicable rules
    rules = find_applicable_rules(issues)
    print(f"\nFound {len(rules)} applicable optimization rules:")
    for rule in rules:
        print(f"  - {rule.rule_id}: {rule.description}")

    # Example: Generate recommendations (using Bindura Zaoga baseline)
    current_params = {
        'reference_signal_power_pdschcfg': 152,  # Bindura Zaoga: 15.2 dBm
        'p0_nominal_pusch': -67  # Bindura Zaoga: -67 dBm
    }

    param_limits = {
        'reference_signal_power_pdschcfg': {
            'range': (-600, 500),
            'max_change': 100
        },
        'p0_nominal_pusch': {
            'range': (-126, -40),
            'max_change': 10
        }
    }

    recommendations = recommend_parameter_changes(issues, current_params, param_limits)
    print(f"\n{len(recommendations)} Parameter Change Recommendations:")
    for rec in recommendations:
        print(f"  - {rec['parameter_name']}: {rec['current_value']} → {rec['recommended_value']}")
        print(f"    Reason: {rec['kpi_issue']}")
        print(f"    Confidence: {rec['confidence']*100:.0f}%, Risk: {rec['risk_level']}/10")
