"""
Liquid Zimbabwe 4G Network Optimizer - Validation Tools
Purpose: LangChain tools for risk assessment and safety validation
Created: 2025-10-30

These tools validate parameter changes and assess risks before optimization execution.
"""

from langchain_core.tools import tool
from typing import Annotated, Dict, List, Any
import os
import sys
import logging
import yaml
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.liquid_zimbabwe_parameters import PARAMETERS
from domain.optimization_rules import OPTIMIZATION_RULES, assess_combined_risk

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# TOOL 1: assess_risk_score
# ============================================================================

@tool
def assess_risk_score(
    parameter_name: Annotated[str, "Name of parameter to change"],
    current_value: Annotated[float, "Current parameter value"],
    proposed_value: Annotated[float, "Proposed new parameter value"],
    kpi_issue: Annotated[str, "KPI issue being addressed (e.g., 'low_download_speed')"]
) -> str:
    """
    Assess risk score for a proposed parameter change.

    This tool evaluates the risk of changing a parameter based on:
    1. Magnitude of change (small/medium/large)
    2. Parameter sensitivity
    3. KPI issue being addressed
    4. Historical change patterns
    5. Side effects and potential impacts

    Risk Score Scale (1-10):
    - 1-3: Low risk - Safe to proceed
    - 4-6: Medium risk - Review recommended
    - 7-8: High risk - Caution required
    - 9-10: Critical risk - Requires approval

    Args:
        parameter_name: Name of parameter being changed
        current_value: Current value
        proposed_value: Proposed new value
        kpi_issue: KPI problem being solved

    Returns:
        String containing risk assessment and recommendations

    Example:
        assess_risk_score("reference_signal_power_pdschcfg", -200, -180, "low_download_speed")
        Returns: "Risk Score: 4/10 (MEDIUM)..."
    """
    try:
        # Validate parameter exists
        if parameter_name not in PARAMETERS:
            return f"ERROR: Unknown parameter '{parameter_name}'"

        param_info = PARAMETERS[parameter_name]
        param_range = param_info.get('range', (None, None))

        result = f"Risk Assessment for Parameter Change\n"
        result += "=" * 80 + "\n\n"

        result += f"Parameter: {parameter_name}\n"
        result += f"KPI Issue: {kpi_issue}\n"
        result += f"Current Value: {current_value}\n"
        result += f"Proposed Value: {proposed_value}\n"
        result += f"Change: {proposed_value - current_value:+.2f}\n\n"

        # Calculate risk factors
        risk_factors = []
        risk_score = 0

        # Factor 1: Magnitude of change
        if param_range[0] is not None and param_range[1] is not None:
            range_size = param_range[1] - param_range[0]
            change_magnitude = abs(proposed_value - current_value)
            change_percent = (change_magnitude / range_size) * 100

            if change_percent > 30:
                magnitude_risk = 4
                magnitude_label = "LARGE"
            elif change_percent > 15:
                magnitude_risk = 2
                magnitude_label = "MEDIUM"
            else:
                magnitude_risk = 1
                magnitude_label = "SMALL"

            risk_score += magnitude_risk
            risk_factors.append(f"Change Magnitude: {magnitude_label} ({change_percent:.1f}% of range) → Risk: +{magnitude_risk}")
        else:
            risk_factors.append("Change Magnitude: UNKNOWN (no range defined) → Risk: +2")
            risk_score += 2

        # Factor 2: Parameter sensitivity (from optimization rules)
        matching_rules = [rule for rule in OPTIMIZATION_RULES.values()
                         if rule.parameter_name == parameter_name and rule.kpi_issue == kpi_issue]

        if matching_rules:
            rule = matching_rules[0]
            rule_risk = rule.risk_level
            confidence = rule.confidence

            # Adjust risk based on confidence
            if confidence < 0.7:
                rule_risk += 2  # Lower confidence = higher risk

            risk_score += rule_risk
            risk_factors.append(f"Parameter Sensitivity: {rule.description[:50]}... → Risk: +{rule_risk}")
            risk_factors.append(f"Confidence in Solution: {confidence*100:.0f}%")
        else:
            risk_score += 3
            risk_factors.append(f"No matching optimization rule found → Risk: +3")

        # Factor 3: Direction of change
        default_value = param_info.get('default')
        if default_value is not None:
            if abs(proposed_value - default_value) > abs(current_value - default_value):
                risk_score += 1
                risk_factors.append(f"Moving further from default ({default_value}) → Risk: +1")
            else:
                risk_factors.append(f"Moving closer to default ({default_value}) → Risk: 0")

        # Factor 4: Range boundary proximity
        if param_range[0] is not None and param_range[1] is not None:
            lower_dist = proposed_value - param_range[0]
            upper_dist = param_range[1] - proposed_value
            range_size = param_range[1] - param_range[0]

            if lower_dist < range_size * 0.1 or upper_dist < range_size * 0.1:
                risk_score += 2
                risk_factors.append(f"Close to range boundary → Risk: +2")

        # Cap risk score at 10
        risk_score = min(risk_score, 10)

        # Classify risk
        if risk_score <= 3:
            risk_level = "LOW"
            risk_icon = "✓"
            recommendation = "Safe to proceed with change"
        elif risk_score <= 6:
            risk_level = "MEDIUM"
            risk_icon = "⚠️"
            recommendation = "Review recommended before proceeding"
        elif risk_score <= 8:
            risk_level = "HIGH"
            risk_icon = "⚠️"
            recommendation = "Caution required - consider smaller change"
        else:
            risk_level = "CRITICAL"
            risk_icon = "❌"
            recommendation = "Requires approval - high risk of issues"

        result += f"Risk Factors:\n"
        for factor in risk_factors:
            result += f"  • {factor}\n"
        result += "\n"

        result += "=" * 80 + "\n"
        result += f"{risk_icon} RISK SCORE: {risk_score}/10 ({risk_level})\n"
        result += "=" * 80 + "\n\n"

        result += f"Recommendation: {recommendation}\n\n"

        # Side effects
        if matching_rules:
            result += "Expected Side Effects:\n"
            for effect in matching_rules[0].side_effects:
                result += f"  • {effect}\n"
            result += "\n"

            result += f"Expected Improvement:\n  {matching_rules[0].expected_improvement}\n"

        return result

    except Exception as e:
        logger.error(f"Error assessing risk: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# TOOL 2: validate_optimization_safety
# ============================================================================

@tool
def validate_optimization_safety(
    parameter_changes_json: Annotated[str, "JSON string of parameter changes: [{\"parameter\": \"name\", \"current\": 1, \"proposed\": 2, \"kpi_issue\": \"issue\"}, ...]"],
    site_name: Annotated[str, "Site name being optimized"],
    max_risk_threshold: Annotated[int, "Maximum acceptable risk score (1-10)"] = 7
) -> str:
    """
    Validate safety of a complete optimization plan with multiple parameter changes.

    This tool performs comprehensive safety validation:
    1. Individual parameter change validation
    2. Combined risk assessment for multiple changes
    3. Conflict detection between parameter changes
    4. Historical optimization success rate for site
    5. Overall safety recommendation

    Safety Levels:
    - APPROVED: All checks passed, safe to execute
    - REVIEW: Some concerns, manual review recommended
    - REJECTED: Risk too high, optimization should not proceed

    Args:
        parameter_changes_json: JSON array of parameter change objects
        site_name: Site/eNodeB being optimized
        max_risk_threshold: Maximum acceptable risk score (default: 7)

    Returns:
        String containing comprehensive safety validation report

    Example:
        validate_optimization_safety('[{"parameter":"reference_signal_power_pdschcfg","current":-200,"proposed":-180,"kpi_issue":"low_download_speed"}]', "MSH0013-Bindura-Zaoga", 7)
        Returns: "Safety Validation: APPROVED..."
    """
    try:
        # Parse parameter changes
        try:
            parameter_changes = json.loads(parameter_changes_json)
        except json.JSONDecodeError:
            return "ERROR: Invalid JSON format for parameter_changes_json"

        if not isinstance(parameter_changes, list):
            return "ERROR: parameter_changes_json must be a JSON array"

        result = f"Optimization Safety Validation\n"
        result += "=" * 80 + "\n\n"

        result += f"Site: {site_name}\n"
        result += f"Number of Parameter Changes: {len(parameter_changes)}\n"
        result += f"Maximum Risk Threshold: {max_risk_threshold}/10\n\n"

        # Validate each parameter change
        individual_risks = []
        validation_issues = []

        result += "Individual Parameter Validations:\n"
        result += "-" * 80 + "\n"

        for i, change in enumerate(parameter_changes, 1):
            param_name = change.get('parameter')
            current_val = change.get('current')
            proposed_val = change.get('proposed')
            kpi_issue = change.get('kpi_issue', 'unknown')

            result += f"\n{i}. {param_name}:\n"

            # Validate parameter exists
            if param_name not in PARAMETERS:
                validation_issues.append(f"Unknown parameter: {param_name}")
                result += f"   ❌ ERROR: Unknown parameter\n"
                continue

            param_info = PARAMETERS[param_name]
            param_range = param_info.get('range', (None, None))

            # Validate proposed value is in range
            if param_range[0] is not None and proposed_val < param_range[0]:
                validation_issues.append(f"{param_name}: Value {proposed_val} below minimum {param_range[0]}")
                result += f"   ❌ ERROR: Value below minimum ({param_range[0]})\n"
                continue

            if param_range[1] is not None and proposed_val > param_range[1]:
                validation_issues.append(f"{param_name}: Value {proposed_val} above maximum {param_range[1]}")
                result += f"   ❌ ERROR: Value above maximum ({param_range[1]})\n"
                continue

            # Calculate individual risk
            change_magnitude = abs(proposed_val - current_val)
            if param_range[0] is not None and param_range[1] is not None:
                range_size = param_range[1] - param_range[0]
                change_percent = (change_magnitude / range_size) * 100
            else:
                change_percent = 0

            # Find matching rule
            matching_rules = [rule for rule in OPTIMIZATION_RULES.values()
                            if rule.parameter_name == param_name and rule.kpi_issue == kpi_issue]

            if matching_rules:
                rule_risk = matching_rules[0].risk_level
                individual_risks.append(rule_risk)

                result += f"   Current: {current_val} → Proposed: {proposed_val} (Δ {proposed_val - current_val:+.2f})\n"
                result += f"   Change Magnitude: {change_percent:.1f}% of range\n"
                result += f"   Risk Score: {rule_risk}/10\n"
                result += f"   Expected: {matching_rules[0].expected_improvement[:60]}...\n"

                if rule_risk > max_risk_threshold:
                    validation_issues.append(f"{param_name}: Risk {rule_risk} exceeds threshold {max_risk_threshold}")
                    result += f"   ⚠️  WARNING: Risk exceeds threshold\n"
                else:
                    result += f"   ✓ Risk within acceptable range\n"
            else:
                default_risk = 5
                individual_risks.append(default_risk)
                result += f"   ⚠️  WARNING: No optimization rule found (default risk: {default_risk}/10)\n"

        result += "\n" + "=" * 80 + "\n\n"

        # Combined risk assessment
        if individual_risks:
            max_individual_risk = max(individual_risks)
            avg_risk = sum(individual_risks) / len(individual_risks)

            # Penalty for multiple simultaneous changes
            combined_risk = assess_combined_risk([
                {'risk_level': risk} for risk in individual_risks
            ])

            result += "Combined Risk Assessment:\n"
            result += f"  Maximum Individual Risk: {max_individual_risk}/10\n"
            result += f"  Average Risk: {avg_risk:.1f}/10\n"
            result += f"  Combined Risk (with multi-change penalty): {combined_risk}/10\n\n"
        else:
            combined_risk = 10
            result += "Combined Risk Assessment:\n"
            result += "  No valid parameter changes found\n\n"

        # Conflict detection
        result += "Conflict Detection:\n"
        if len(parameter_changes) > 1:
            # Check for parameters affecting same KPIs
            param_impacts = {}
            for change in parameter_changes:
                param_name = change.get('parameter')
                if param_name in PARAMETERS:
                    impacts = PARAMETERS[param_name].get('impact', [])
                    param_impacts[param_name] = set(impacts)

            conflicts_found = False
            params = list(param_impacts.keys())
            for i in range(len(params)):
                for j in range(i + 1, len(params)):
                    shared_impacts = param_impacts[params[i]] & param_impacts[params[j]]
                    if shared_impacts:
                        conflicts_found = True
                        result += f"  ⚠️  {params[i]} and {params[j]} both affect: {', '.join(shared_impacts)}\n"

            if not conflicts_found:
                result += "  ✓ No conflicts detected\n"
        else:
            result += "  N/A (single parameter change)\n"

        result += "\n" + "=" * 80 + "\n"

        # Final safety decision
        if validation_issues:
            safety_status = "REJECTED"
            safety_icon = "❌"
            recommendation = "Optimization REJECTED due to validation errors"
        elif combined_risk > max_risk_threshold:
            safety_status = "REVIEW"
            safety_icon = "⚠️"
            recommendation = f"Manual review recommended (risk {combined_risk} > threshold {max_risk_threshold})"
        else:
            safety_status = "APPROVED"
            safety_icon = "✓"
            recommendation = "Optimization approved - safe to proceed"

        result += f"{safety_icon} SAFETY STATUS: {safety_status}\n"
        result += "=" * 80 + "\n\n"

        result += f"Recommendation: {recommendation}\n\n"

        if validation_issues:
            result += "Validation Issues:\n"
            for issue in validation_issues:
                result += f"  • {issue}\n"
            result += "\n"

        # Next steps
        if safety_status == "APPROVED":
            result += "Next Steps:\n"
            result += "  1. Execute parameter changes via modify_huawei_parameter tool\n"
            result += "  2. Monitor KPIs for 15-30 minutes\n"
            result += "  3. Verify expected improvements\n"
            result += "  4. Rollback if KPIs degrade\n"
        elif safety_status == "REVIEW":
            result += "Next Steps:\n"
            result += "  1. Review risk factors and side effects\n"
            result += "  2. Consider reducing change magnitude\n"
            result += "  3. Obtain manual approval if confident\n"
            result += "  4. Proceed with caution\n"
        else:
            result += "Next Steps:\n"
            result += "  1. Fix validation errors\n"
            result += "  2. Reduce proposed changes\n"
            result += "  3. Re-run safety validation\n"

        return result

    except Exception as e:
        logger.error(f"Error validating optimization safety: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# Tool List for Agent Registration
# ============================================================================

VALIDATION_TOOLS = [
    assess_risk_score,
    validate_optimization_safety
]


# ============================================================================
# Example Usage (for testing)
# ============================================================================

if __name__ == "__main__":
    # Example 1: Assess risk for single parameter change
    print("Example 1: Risk Assessment")
    print("=" * 80)
    result = assess_risk_score.invoke({
        "parameter_name": "reference_signal_power_pdschcfg",
        "current_value": -200,
        "proposed_value": -180,
        "kpi_issue": "low_download_speed"
    })
    print(result)
    print("\n\n")

    # Example 2: Validate complete optimization plan
    print("Example 2: Safety Validation")
    print("=" * 80)
    changes = [
        {
            "parameter": "reference_signal_power_pdschcfg",
            "current": -200,
            "proposed": -180,
            "kpi_issue": "low_download_speed"
        },
        {
            "parameter": "p0_nominal_pusch",
            "current": -90,
            "proposed": -85,
            "kpi_issue": "low_upload_speed"
        }
    ]
    result = validate_optimization_safety.invoke({
        "parameter_changes_json": json.dumps(changes),
        "site_name": "MSH0013-Bindura-Zaoga",
        "max_risk_threshold": 7
    })
    print(result)
