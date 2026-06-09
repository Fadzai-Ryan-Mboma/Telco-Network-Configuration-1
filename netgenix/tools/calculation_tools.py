"""
Liquid Zimbabwe 4G Network Optimizer - Calculation Tools
Purpose: LangChain tools for KPI scoring and trend analysis
Created: 2025-10-30

These tools perform calculations for weighted KPI scoring and trend analysis.
"""

from langchain_core.tools import tool
from typing import Annotated, Dict, List, Any
import os
import sys
import logging
import yaml
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logger = logging.getLogger(__name__)

# Load KPI weights configuration
KPI_WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "kpi_weights.yaml")


# ============================================================================
# TOOL 1: calc_weighted_kpi_score
# ============================================================================

@tool
def calc_weighted_kpi_score(
    network_access_success: Annotated[float, "Network access success rate (%)"],
    download_speed: Annotated[float, "Download speed (Mbps)"],
    download_quality: Annotated[float, "Download quality (%)"],
    upload_speed: Annotated[float, "Upload speed (Mbps)"],
    upload_quality: Annotated[float, "Upload quality (%)"],
    control_channel_load: Annotated[float, "Control channel load (%)"],
    feedback_channel_load: Annotated[float, "Feedback channel load (%)"]
) -> str:
    """
    Calculate weighted KPI score using 3-tier weighting system.

    This tool implements the Liquid Zimbabwe 3-tier KPI weighting:
    - Tier 1 (Foundation): 25% - Network Access Success
    - Tier 2 (Revenue & Experience): 50% - Download/Upload Speed & Quality
    - Tier 3 (Efficiency): 25% - Channel Load

    Scoring method:
    1. Each KPI is normalized to 0-100 based on threshold bands
    2. Normalized score is multiplied by KPI weight
    3. All weighted scores are summed (0-100 final score)

    Score interpretation:
    - 90-100: Excellent
    - 80-89: Good
    - 70-79: Fair
    - 60-69: Poor
    - <60: Critical

    Args:
        network_access_success: RACH success rate (%)
        download_speed: DL throughput (Mbps)
        download_quality: DL quality = 100 - IBLER (%)
        upload_speed: UL throughput (Mbps)
        upload_quality: UL quality = 100 - IBLER (%)
        control_channel_load: PDCCH usage (%)
        feedback_channel_load: PUCCH usage (%)

    Returns:
        String containing weighted score and detailed breakdown

    Example:
        calc_weighted_kpi_score(96.0, 75.0, 97.0, 30.0, 96.0, 55.0, 40.0)
        Returns: "Weighted KPI Score: 84.0 (GOOD)..."
    """
    try:
        # Load KPI weights configuration
        with open(KPI_WEIGHTS_PATH, 'r') as f:
            config = yaml.safe_load(f)

        kpi_weights = config['kpi_weights']
        scoring_config = config['scoring']

        # KPI values
        kpis = {
            'network_access_success': network_access_success,
            'download_speed': download_speed,
            'download_quality': download_quality,
            'upload_speed': upload_speed,
            'upload_quality': upload_quality,
            'control_channel_load': control_channel_load,
            'feedback_channel_load': feedback_channel_load
        }

        # Calculate normalized scores
        normalized_scores = {}
        weighted_scores = {}
        total_weighted_score = 0.0

        result = "Weighted KPI Score Calculation:\n"
        result += "=" * 80 + "\n\n"

        for kpi_name, kpi_value in kpis.items():
            kpi_config = kpi_weights[kpi_name]
            weight = kpi_config['weight']
            thresholds = kpi_config['thresholds']
            invert_scoring = kpi_config.get('invert_scoring', False)

            # Normalize KPI value to 0-100 score
            normalized_score = normalize_kpi_value(
                kpi_value,
                thresholds,
                invert_scoring,
                scoring_config
            )

            # Calculate weighted contribution
            weighted_score = normalized_score * weight * 100

            normalized_scores[kpi_name] = normalized_score
            weighted_scores[kpi_name] = weighted_score
            total_weighted_score += weighted_score

            # Add to result string
            tier = kpi_config['tier']
            priority = kpi_config['priority']
            result += f"{kpi_name}:\n"
            result += f"  Raw Value: {kpi_value:.2f} {kpi_config['unit']}\n"
            result += f"  Normalized Score: {normalized_score:.2f}/100\n"
            result += f"  Weight: {weight*100:.1f}% (Tier {tier}, {priority} priority)\n"
            result += f"  Weighted Contribution: {weighted_score:.2f}\n\n"

        # Overall score interpretation
        overall_thresholds = scoring_config['overall_score']
        if total_weighted_score >= overall_thresholds['excellent']:
            status = "EXCELLENT"
        elif total_weighted_score >= overall_thresholds['good']:
            status = "GOOD"
        elif total_weighted_score >= overall_thresholds['fair']:
            status = "FAIR"
        elif total_weighted_score >= overall_thresholds['poor']:
            status = "POOR"
        else:
            status = "CRITICAL"

        result += "=" * 80 + "\n"
        result += f"TOTAL WEIGHTED KPI SCORE: {total_weighted_score:.2f}/100 ({status})\n"
        result += "=" * 80 + "\n\n"

        # Tier breakdown
        tier1_score = weighted_scores['network_access_success']
        tier2_score = (weighted_scores['download_speed'] +
                      weighted_scores['download_quality'] +
                      weighted_scores['upload_speed'])
        tier3_score = (weighted_scores['upload_quality'] +
                      weighted_scores['control_channel_load'] +
                      weighted_scores['feedback_channel_load'])

        result += "Tier Breakdown:\n"
        result += f"  Tier 1 (Foundation):           {tier1_score:.2f}/25 (Network Access)\n"
        result += f"  Tier 2 (Revenue & Experience): {tier2_score:.2f}/50 (Speed & Quality)\n"
        result += f"  Tier 3 (Efficiency):           {tier3_score:.2f}/25 (Resource Usage)\n\n"

        # Recommendations
        if status in ["POOR", "CRITICAL"]:
            result += "⚠️  RECOMMENDATION: Immediate optimization required\n"
            # Identify worst performing KPIs
            worst_kpis = sorted(normalized_scores.items(), key=lambda x: x[1])[:3]
            result += "   Focus on improving:\n"
            for kpi, score in worst_kpis:
                result += f"   - {kpi}: {score:.0f}/100\n"
        elif status == "FAIR":
            result += "ℹ️  RECOMMENDATION: Consider optimization to improve performance\n"
        else:
            result += "✓  STATUS: Performance is good, continue monitoring\n"

        return result

    except Exception as e:
        logger.error(f"Error calculating weighted KPI score: {e}")
        return f"ERROR: {str(e)}"


def normalize_kpi_value(
    value: float,
    thresholds: Dict[str, float],
    invert_scoring: bool,
    scoring_config: Dict[str, Any]
) -> float:
    """
    Normalize KPI value to 0-100 score based on threshold bands.

    Args:
        value: Raw KPI value
        thresholds: Threshold configuration
        invert_scoring: If True, lower values = better (for load metrics)
        scoring_config: Scoring configuration from kpi_weights.yaml

    Returns:
        Normalized score (0-100)
    """
    # Get threshold-based scoring values
    if invert_scoring:
        score_map = scoring_config['normalization']['inverted_scoring']
    else:
        score_map = scoring_config['normalization']['threshold_scoring']

    # Determine which threshold band the value falls into
    if invert_scoring:
        # For inverted scoring (lower is better)
        if value <= thresholds['excellent']:
            return score_map['excellent']
        elif value <= thresholds['good']:
            return score_map['good']
        elif value <= thresholds['fair']:
            return score_map['fair']
        elif value <= thresholds['poor']:
            return score_map['poor']
        elif value <= thresholds['critical']:
            return score_map['critical']
        else:
            return score_map['above_critical']
    else:
        # For normal scoring (higher is better)
        if value >= thresholds['excellent']:
            return score_map['excellent']
        elif value >= thresholds['good']:
            return score_map['good']
        elif value >= thresholds['fair']:
            return score_map['fair']
        elif value >= thresholds['poor']:
            return score_map['poor']
        elif value >= thresholds['critical']:
            return score_map['critical']
        else:
            return score_map['below_critical']


# ============================================================================
# TOOL 2: calc_kpi_trend
# ============================================================================

@tool
def calc_kpi_trend(
    kpi_name: Annotated[str, "Name of KPI to analyze (e.g., 'download_speed')"],
    current_value: Annotated[float, "Current KPI value"],
    historical_values: Annotated[str, "Comma-separated historical values (oldest to newest)"],
    days: Annotated[int, "Number of days of historical data"] = 7
) -> str:
    """
    Calculate KPI trend over time to determine if performance is improving or degrading.

    This tool analyzes historical KPI data to determine:
    1. Trend direction (improving, stable, degrading)
    2. Rate of change (% per day)
    3. Volatility (standard deviation)
    4. Prediction for next period

    Trend classification:
    - Improving: Positive trend with >5% improvement
    - Stable: Trend within ±5%
    - Degrading: Negative trend with >5% decline

    Args:
        kpi_name: Name of KPI being analyzed
        current_value: Most recent KPI value
        historical_values: Comma-separated string of historical values (e.g., "45.2,47.1,46.8,48.5")
        days: Number of days represented by historical data

    Returns:
        String containing trend analysis and recommendations

    Example:
        calc_kpi_trend("download_speed", 50.0, "45.0,46.5,47.2,48.1,49.0", 5)
        Returns: "Trend: IMPROVING (+2.5%/day)..."
    """
    try:
        # Parse historical values
        try:
            hist_values = [float(v.strip()) for v in historical_values.split(',')]
        except ValueError:
            return "ERROR: Invalid historical_values format. Use comma-separated numbers (e.g., '45.0,46.5,47.2')"

        if len(hist_values) < 2:
            return "ERROR: Need at least 2 historical values to calculate trend"

        # Add current value to series
        all_values = hist_values + [current_value]

        result = f"KPI Trend Analysis: {kpi_name}\n"
        result += "=" * 80 + "\n\n"

        # Calculate basic statistics
        import statistics

        avg_value = statistics.mean(all_values)
        std_dev = statistics.stdev(all_values) if len(all_values) > 1 else 0
        min_value = min(all_values)
        max_value = max(all_values)

        result += f"Time Period: Last {days} days ({len(all_values)} data points)\n"
        result += f"Current Value: {current_value:.2f}\n"
        result += f"Average: {avg_value:.2f}\n"
        result += f"Range: {min_value:.2f} - {max_value:.2f}\n"
        result += f"Std Dev: {std_dev:.2f}\n\n"

        # Calculate trend (simple linear regression)
        n = len(all_values)
        x = list(range(n))  # Time indices
        y = all_values

        # Calculate slope using least squares
        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        # Calculate daily rate of change
        daily_change = slope
        percent_change_per_day = (daily_change / avg_value) * 100 if avg_value != 0 else 0

        # Overall percent change
        if hist_values[0] != 0:
            overall_change = ((current_value - hist_values[0]) / hist_values[0]) * 100
        else:
            overall_change = 0

        result += f"Trend Analysis:\n"
        result += f"  Slope: {slope:.4f} units/day\n"
        result += f"  Daily Change: {percent_change_per_day:.2f}%/day\n"
        result += f"  Overall Change: {overall_change:.2f}% over {days} days\n\n"

        # Classify trend
        if abs(percent_change_per_day) < 0.5:  # Less than 0.5% per day
            trend_status = "STABLE"
            trend_icon = "→"
        elif percent_change_per_day > 0:
            trend_status = "IMPROVING"
            trend_icon = "↑"
        else:
            trend_status = "DEGRADING"
            trend_icon = "↓"

        # Volatility assessment
        coefficient_of_variation = (std_dev / avg_value * 100) if avg_value != 0 else 0
        if coefficient_of_variation < 10:
            volatility = "Low"
        elif coefficient_of_variation < 20:
            volatility = "Moderate"
        else:
            volatility = "High"

        result += f"Trend Classification: {trend_icon} {trend_status}\n"
        result += f"Volatility: {volatility} (CV = {coefficient_of_variation:.1f}%)\n\n"

        # Predict next value (simple linear extrapolation)
        predicted_next = current_value + slope
        result += f"Predicted Next Value: {predicted_next:.2f}\n\n"

        # Recommendations
        result += "Recommendations:\n"
        if trend_status == "DEGRADING":
            result += f"⚠️  KPI is degrading at {abs(percent_change_per_day):.2f}%/day\n"
            result += "   → Immediate investigation and optimization recommended\n"
            if volatility == "High":
                result += "   → High volatility indicates unstable performance\n"
        elif trend_status == "STABLE":
            result += "✓  KPI is stable\n"
            if volatility == "High":
                result += "   ℹ️  High volatility - monitor for sudden changes\n"
            else:
                result += "   → Continue current configuration\n"
        else:  # IMPROVING
            result += f"✓  KPI is improving at {percent_change_per_day:.2f}%/day\n"
            result += "   → Recent optimizations are working\n"
            result += "   → Monitor to ensure sustained improvement\n"

        return result

    except Exception as e:
        logger.error(f"Error calculating KPI trend: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# Tool List for Agent Registration
# ============================================================================

CALCULATION_TOOLS = [
    calc_weighted_kpi_score,
    calc_kpi_trend
]


# ============================================================================
# Example Usage (for testing)
# ============================================================================

if __name__ == "__main__":
    # Example 1: Calculate weighted KPI score
    print("Example 1: Weighted KPI Score Calculation")
    print("=" * 80)
    result = calc_weighted_kpi_score.invoke({
        "network_access_success": 96.0,
        "download_speed": 75.0,
        "download_quality": 97.0,
        "upload_speed": 30.0,
        "upload_quality": 96.0,
        "control_channel_load": 55.0,
        "feedback_channel_load": 40.0
    })
    print(result)
    print("\n\n")

    # Example 2: Calculate KPI trend
    print("Example 2: KPI Trend Analysis")
    print("=" * 80)
    result = calc_kpi_trend.invoke({
        "kpi_name": "download_speed",
        "current_value": 50.0,
        "historical_values": "45.0,46.5,47.2,48.1,49.0",
        "days": 5
    })
    print(result)
