"""
LangChain tools for KPI analysis and recommendation generation.

These tools provide analytical capabilities for the agents to
evaluate network performance and generate optimization strategies.
"""

from datetime import datetime
from typing import Any, Optional

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from cassava_optimizer.domain.kpi_definitions import get_kpi_registry, get_kpi_definition, get_all_kpi_names
from cassava_optimizer.domain.optimization_rules import get_applicable_rules

logger = structlog.get_logger(__name__)


# Pydantic models for tool inputs
class TrendAnalysisInput(BaseModel):
    """Input for analyze_kpi_trends tool."""
    
    kpi_data: dict[str, list[dict[str, Any]]] = Field(
        description="Historical KPI data organized by KPI name"
    )
    window_hours: int = Field(
        default=24,
        description="Analysis window in hours"
    )


class HealthScoreInput(BaseModel):
    """Input for calculate_health_score tool."""
    
    kpis: dict[str, float] = Field(
        description="Current KPI values"
    )
    weights: Optional[dict[str, float]] = Field(
        default=None,
        description="Optional custom weights for each KPI"
    )


class AnomalyDetectionInput(BaseModel):
    """Input for detect_anomalies tool."""
    
    kpi_data: dict[str, list[dict[str, Any]]] = Field(
        description="Historical KPI data"
    )
    threshold_std: float = Field(
        default=2.0,
        description="Number of standard deviations for anomaly threshold"
    )


class BaselineComparisonInput(BaseModel):
    """Input for compare_with_baseline tool."""
    
    current_kpis: dict[str, float] = Field(
        description="Current KPI values"
    )
    baseline_kpis: dict[str, float] = Field(
        description="Baseline KPI values for comparison"
    )


class RecommendationInput(BaseModel):
    """Input for generate_recommendations tool."""
    
    issues: list[dict[str, Any]] = Field(
        description="List of identified issues"
    )
    current_config: dict[str, Any] = Field(
        description="Current cell configuration"
    )
    kpi_analysis: dict[str, Any] = Field(
        description="KPI analysis results"
    )
    optimization_type: str = Field(
        default="full",
        description="Type of optimization to generate"
    )


@tool(args_schema=TrendAnalysisInput)
def analyze_kpi_trends(
    kpi_data: dict[str, list[dict[str, Any]]],
    window_hours: int = 24,
) -> dict[str, Any]:
    """
    Analyze KPI trends to identify patterns and degradation.
    
    Performs:
    - Linear trend analysis (improving/degrading/stable)
    - Rate of change calculation
    - Volatility assessment
    - Peak/trough identification
    
    Args:
        kpi_data: Historical KPI data organized by KPI name
        window_hours: Analysis window in hours
        
    Returns:
        Trend analysis results for each KPI
    """
    logger.info(
        "Analyzing KPI trends",
        kpi_count=len(kpi_data),
        window_hours=window_hours,
    )
    
    trends: dict[str, dict[str, Any]] = {}
    
    for kpi_name, data_points in kpi_data.items():
        if not data_points:
            continue
        
        # Extract values
        values = [p.get("value") for p in data_points if p.get("value") is not None]
        
        if len(values) < 2:
            trends[kpi_name] = {
                "trend": "insufficient_data",
                "data_points": len(values),
            }
            continue
        
        # Calculate basic statistics
        avg_value = sum(values) / len(values)
        min_value = min(values)
        max_value = max(values)
        
        # Calculate volatility (coefficient of variation)
        if avg_value != 0:
            variance = sum((v - avg_value) ** 2 for v in values) / len(values)
            std_dev = variance ** 0.5
            volatility = std_dev / abs(avg_value) * 100
        else:
            std_dev = 0
            volatility = 0
        
        # Determine trend direction
        # Compare first third average to last third average
        third = max(1, len(values) // 3)
        early_avg = sum(values[:third]) / third
        late_avg = sum(values[-third:]) / third
        
        change_pct = ((late_avg - early_avg) / abs(early_avg) * 100) if early_avg != 0 else 0
        
        # Get KPI definition to understand if higher is better
        kpi_def = get_kpi_definition(kpi_name)
        higher_is_better = kpi_def.higher_is_better if kpi_def else True
        
        # Determine trend classification
        if abs(change_pct) < 2:
            trend = "stable"
        elif change_pct > 0:
            trend = "improving" if higher_is_better else "degrading"
        else:
            trend = "degrading" if higher_is_better else "improving"
        
        # Calculate rate of change per hour
        rate_per_hour = change_pct / window_hours if window_hours > 0 else 0
        
        trends[kpi_name] = {
            "trend": trend,
            "change_percent": round(change_pct, 2),
            "rate_per_hour": round(rate_per_hour, 3),
            "average": round(avg_value, 3),
            "min": round(min_value, 3),
            "max": round(max_value, 3),
            "std_dev": round(std_dev, 3),
            "volatility_percent": round(volatility, 2),
            "data_points": len(values),
            "higher_is_better": higher_is_better,
        }
    
    # Generate summary
    degrading_kpis = [k for k, v in trends.items() if v.get("trend") == "degrading"]
    improving_kpis = [k for k, v in trends.items() if v.get("trend") == "improving"]
    high_volatility = [k for k, v in trends.items() if v.get("volatility_percent", 0) > 20]
    
    logger.info(
        "Trend analysis complete",
        degrading=len(degrading_kpis),
        improving=len(improving_kpis),
    )
    
    return {
        "success": True,
        "trends": trends,
        "summary": {
            "total_kpis": len(trends),
            "degrading_kpis": degrading_kpis,
            "improving_kpis": improving_kpis,
            "high_volatility_kpis": high_volatility,
            "analysis_window_hours": window_hours,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@tool(args_schema=HealthScoreInput)
def calculate_health_score(
    kpis: dict[str, float],
    weights: Optional[dict[str, float]] = None,
) -> dict[str, Any]:
    """
    Calculate an overall network health score from KPIs.
    
    Scoring approach:
    - Each KPI is normalized to 0-100 based on thresholds
    - Weighted average produces final score
    - Critical KPI failures cap the maximum score
    
    Score interpretation:
    - 90-100: Excellent - Network performing optimally
    - 75-89: Good - Minor improvements possible
    - 50-74: Fair - Optimization recommended
    - 25-49: Poor - Immediate attention needed
    - 0-24: Critical - Urgent intervention required
    
    Args:
        kpis: Current KPI values
        weights: Optional custom weights
        
    Returns:
        Health score and component breakdown
    """
    logger.info(
        "Calculating health score",
        kpi_count=len(kpis),
    )
    
    # Default weights by KPI category
    default_weights = {
        "rrc_setup_success_rate": 1.5,
        "erab_setup_success_rate": 1.5,
        "handover_success_rate": 1.2,
        "cqi_average": 1.0,
        "prb_utilization_dl": 0.8,
        "prb_utilization_ul": 0.8,
        "rsrp_average": 1.0,
        "rsrq_average": 0.9,
        "sinr_average": 1.0,
        "latency_average": 1.0,
        "packet_loss_rate": 1.2,
        "throughput_dl": 0.7,
        "throughput_ul": 0.7,
    }
    
    effective_weights = weights or default_weights
    
    # Calculate normalized scores for each KPI
    kpi_scores: dict[str, dict[str, Any]] = {}
    critical_failures: list[str] = []
    
    for kpi_name, value in kpis.items():
        kpi_def = get_kpi_definition(kpi_name)
        
        if not kpi_def:
            # Unknown KPI - skip
            continue
        
        # Normalize to 0-100 scale
        target = kpi_def.target
        critical = kpi_def.critical_threshold
        higher_is_better = kpi_def.higher_is_better
        
        if higher_is_better:
            # For KPIs where higher is better (e.g., success rates)
            if value >= target:
                normalized = 100
            elif value <= critical:
                normalized = 0
                critical_failures.append(kpi_name)
            else:
                normalized = (value - critical) / (target - critical) * 100
        else:
            # For KPIs where lower is better (e.g., packet loss)
            if value <= target:
                normalized = 100
            elif value >= critical:
                normalized = 0
                critical_failures.append(kpi_name)
            else:
                normalized = (critical - value) / (critical - target) * 100
        
        weight = effective_weights.get(kpi_name, 1.0)
        
        kpi_scores[kpi_name] = {
            "raw_value": round(value, 3),
            "normalized_score": round(normalized, 1),
            "weight": weight,
            "weighted_score": round(normalized * weight, 2),
            "status": "critical" if kpi_name in critical_failures else (
                "good" if normalized >= 75 else (
                    "fair" if normalized >= 50 else "poor"
                )
            ),
        }
    
    # Calculate weighted average
    total_weight = sum(s["weight"] for s in kpi_scores.values())
    weighted_sum = sum(s["weighted_score"] for s in kpi_scores.values())
    
    if total_weight > 0:
        health_score = weighted_sum / total_weight
    else:
        health_score = 0
    
    # Cap score if critical failures exist
    if critical_failures:
        health_score = min(health_score, 49)
    
    # Determine overall status
    if health_score >= 90:
        status = "excellent"
    elif health_score >= 75:
        status = "good"
    elif health_score >= 50:
        status = "fair"
    elif health_score >= 25:
        status = "poor"
    else:
        status = "critical"
    
    logger.info(
        "Health score calculated",
        score=round(health_score, 1),
        status=status,
    )
    
    return {
        "success": True,
        "health_score": round(health_score, 1),
        "status": status,
        "kpi_scores": kpi_scores,
        "critical_failures": critical_failures,
        "summary": {
            "total_kpis": len(kpi_scores),
            "critical_count": len(critical_failures),
            "good_count": sum(1 for s in kpi_scores.values() if s["status"] == "good"),
            "needs_attention": sum(1 for s in kpi_scores.values() if s["status"] in ("fair", "poor")),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@tool(args_schema=AnomalyDetectionInput)
def detect_anomalies(
    kpi_data: dict[str, list[dict[str, Any]]],
    threshold_std: float = 2.0,
) -> dict[str, Any]:
    """
    Detect anomalies in KPI data using statistical analysis.
    
    Detection methods:
    - Z-score analysis (deviation from mean)
    - Sudden change detection (point-to-point jumps)
    - Pattern breaks (trend reversals)
    
    Args:
        kpi_data: Historical KPI data
        threshold_std: Standard deviation threshold for anomalies
        
    Returns:
        Detected anomalies with severity and timing
    """
    logger.info(
        "Detecting anomalies",
        kpi_count=len(kpi_data),
        threshold=threshold_std,
    )
    
    anomalies: dict[str, list[dict[str, Any]]] = {}
    
    for kpi_name, data_points in kpi_data.items():
        if not data_points or len(data_points) < 5:
            continue
        
        values = [p.get("value") for p in data_points if p.get("value") is not None]
        timestamps = [p.get("timestamp") for p in data_points if p.get("value") is not None]
        
        if len(values) < 5:
            continue
        
        # Calculate statistics
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        std = variance ** 0.5 if variance > 0 else 0.001
        
        kpi_anomalies = []
        
        for i, (value, ts) in enumerate(zip(values, timestamps)):
            # Z-score check
            z_score = abs(value - avg) / std if std > 0 else 0
            
            if z_score > threshold_std:
                kpi_anomalies.append({
                    "type": "outlier",
                    "timestamp": ts,
                    "value": value,
                    "z_score": round(z_score, 2),
                    "severity": "high" if z_score > 3 else "medium",
                    "description": f"Value {value:.2f} is {z_score:.1f} std devs from mean {avg:.2f}",
                })
            
            # Sudden change detection
            if i > 0:
                prev_value = values[i - 1]
                if prev_value != 0:
                    change_pct = abs(value - prev_value) / abs(prev_value) * 100
                    if change_pct > 30:  # More than 30% sudden change
                        kpi_anomalies.append({
                            "type": "sudden_change",
                            "timestamp": ts,
                            "value": value,
                            "previous_value": prev_value,
                            "change_percent": round(change_pct, 1),
                            "severity": "high" if change_pct > 50 else "medium",
                            "description": f"Sudden {change_pct:.0f}% change from {prev_value:.2f} to {value:.2f}",
                        })
        
        if kpi_anomalies:
            anomalies[kpi_name] = kpi_anomalies
    
    # Generate summary
    total_anomalies = sum(len(a) for a in anomalies.values())
    high_severity = sum(
        1 for kpi_list in anomalies.values()
        for a in kpi_list if a.get("severity") == "high"
    )
    
    logger.info(
        "Anomaly detection complete",
        total_anomalies=total_anomalies,
        high_severity=high_severity,
    )
    
    return {
        "success": True,
        "anomalies": anomalies,
        "summary": {
            "total_anomalies": total_anomalies,
            "high_severity_count": high_severity,
            "affected_kpis": list(anomalies.keys()),
            "threshold_std": threshold_std,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@tool(args_schema=BaselineComparisonInput)
def compare_with_baseline(
    current_kpis: dict[str, float],
    baseline_kpis: dict[str, float],
) -> dict[str, Any]:
    """
    Compare current KPIs against a baseline (historical average or target).
    
    Identifies:
    - Improvements since baseline
    - Degradations since baseline
    - Significant deviations
    
    Args:
        current_kpis: Current KPI values
        baseline_kpis: Baseline values for comparison
        
    Returns:
        Comparison results with deviation analysis
    """
    logger.info(
        "Comparing with baseline",
        current_count=len(current_kpis),
        baseline_count=len(baseline_kpis),
    )
    
    comparisons: dict[str, dict[str, Any]] = {}
    
    for kpi_name, current in current_kpis.items():
        baseline = baseline_kpis.get(kpi_name)
        
        if baseline is None:
            continue
        
        # Calculate deviation
        if baseline != 0:
            deviation_pct = (current - baseline) / abs(baseline) * 100
        else:
            deviation_pct = 0 if current == 0 else 100
        
        # Get KPI definition
        kpi_def = get_kpi_definition(kpi_name)
        higher_is_better = kpi_def.higher_is_better if kpi_def else True
        
        # Determine status
        if abs(deviation_pct) < 2:
            status = "unchanged"
        elif deviation_pct > 0:
            status = "improved" if higher_is_better else "degraded"
        else:
            status = "degraded" if higher_is_better else "improved"
        
        # Determine severity of degradation
        severity = None
        if status == "degraded":
            if abs(deviation_pct) > 20:
                severity = "critical"
            elif abs(deviation_pct) > 10:
                severity = "high"
            elif abs(deviation_pct) > 5:
                severity = "medium"
            else:
                severity = "low"
        
        comparisons[kpi_name] = {
            "current": round(current, 3),
            "baseline": round(baseline, 3),
            "deviation_percent": round(deviation_pct, 2),
            "absolute_change": round(current - baseline, 3),
            "status": status,
            "severity": severity,
            "higher_is_better": higher_is_better,
        }
    
    # Generate summary
    improved = [k for k, v in comparisons.items() if v["status"] == "improved"]
    degraded = [k for k, v in comparisons.items() if v["status"] == "degraded"]
    critical = [k for k, v in comparisons.items() if v.get("severity") == "critical"]
    
    logger.info(
        "Baseline comparison complete",
        improved=len(improved),
        degraded=len(degraded),
    )
    
    return {
        "success": True,
        "comparisons": comparisons,
        "summary": {
            "total_compared": len(comparisons),
            "improved_kpis": improved,
            "degraded_kpis": degraded,
            "critical_degradations": critical,
            "improvement_count": len(improved),
            "degradation_count": len(degraded),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@tool(args_schema=RecommendationInput)
def generate_recommendations(
    issues: list[dict[str, Any]],
    current_config: dict[str, Any],
    kpi_analysis: dict[str, Any],
    optimization_type: str = "full",
) -> dict[str, Any]:
    """
    Generate optimization recommendations based on identified issues.
    
    Uses domain knowledge rules to map issues to specific
    parameter adjustments with expected outcomes.
    
    Recommendation types:
    - coverage: RF power, tilt, neighbor relations
    - capacity: PRB allocation, scheduling, admission control
    - interference: PCI, frequency, power control
    - full: All of the above
    
    Args:
        issues: List of identified issues
        current_config: Current cell configuration
        kpi_analysis: KPI analysis results
        optimization_type: Type of optimization
        
    Returns:
        Prioritized recommendations with confidence scores
    """
    logger.info(
        "Generating recommendations",
        issue_count=len(issues),
        optimization_type=optimization_type,
    )
    
    recommendations: list[dict[str, Any]] = []
    
    for issue in issues:
        issue_type = issue.get("type", "unknown")
        severity = issue.get("severity", "medium")
        kpi_name = issue.get("kpi_name", "")
        
        # Get applicable rules for this issue
        applicable_rules = get_applicable_rules(
            issue_type=issue_type,
            optimization_type=optimization_type,
        )
        
        for rule in applicable_rules:
            # Get current value from config
            param_name = rule.parameter_name
            current_value = current_config.get(param_name)
            
            if current_value is None:
                # Check in nested cell parameters
                for cell in current_config.get("cells", []):
                    if param_name in cell.get("parameters", {}):
                        current_value = cell["parameters"][param_name]
                        break
            
            # Calculate recommended value
            if rule.adjustment_type == "increase":
                recommended_value = current_value + rule.adjustment_step if current_value else rule.default_value
                recommended_value = min(recommended_value, rule.max_value)
            elif rule.adjustment_type == "decrease":
                recommended_value = current_value - rule.adjustment_step if current_value else rule.default_value
                recommended_value = max(recommended_value, rule.min_value)
            else:
                recommended_value = rule.default_value
            
            # Calculate confidence based on rule priority and issue severity
            base_confidence = rule.confidence_base
            severity_multiplier = {
                "critical": 1.2,
                "high": 1.1,
                "medium": 1.0,
                "low": 0.9,
            }.get(severity, 1.0)
            confidence = min(base_confidence * severity_multiplier, 100)
            
            recommendations.append({
                "parameter_name": param_name,
                "current_value": current_value,
                "recommended_value": recommended_value,
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "issue_type": issue_type,
                "kpi_name": kpi_name,
                "expected_improvement": rule.expected_improvement,
                "confidence": round(confidence, 1),
                "risk_level": rule.risk_level,
                "reasoning": rule.reasoning,
                "rollback_procedure": rule.rollback_procedure,
                "priority": rule.priority,
                "category": rule.category,
            })
    
    # Sort by priority and confidence
    recommendations.sort(
        key=lambda r: (-r["priority"], -r["confidence"]),
    )
    
    # Remove duplicates (same parameter)
    seen_params: set[str] = set()
    unique_recommendations = []
    for rec in recommendations:
        if rec["parameter_name"] not in seen_params:
            seen_params.add(rec["parameter_name"])
            unique_recommendations.append(rec)
    
    logger.info(
        "Recommendations generated",
        total=len(unique_recommendations),
    )
    
    return {
        "success": True,
        "recommendations": unique_recommendations,
        "summary": {
            "total_recommendations": len(unique_recommendations),
            "high_confidence": sum(1 for r in unique_recommendations if r["confidence"] >= 80),
            "low_risk": sum(1 for r in unique_recommendations if r["risk_level"] == "low"),
            "categories": list(set(r["category"] for r in unique_recommendations)),
        },
        "optimization_type": optimization_type,
        "timestamp": datetime.utcnow().isoformat(),
    }
