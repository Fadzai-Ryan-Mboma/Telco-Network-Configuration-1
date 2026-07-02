"""
NetGenix optimization workflow service.

This bridges the FastAPI routes to the existing agent workflow while keeping
execution dry-run first and independent of the old Streamlit `ui/` package.
"""

import logging
import sys
import json
import re
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LLMParameterRecommendation(BaseModel):
    parameter: str
    recommended_value: str
    unit: str = ""
    description: str = ""


class LLMKPIComparison(BaseModel):
    kpi: str
    current_value: float
    baseline: float
    status: str = Field(description="one of: above_baseline, at_baseline, below_baseline")


class LLMOptimizationResponse(BaseModel):
    """Schema enforced via Gemini structured output (with_structured_output).

    Using native JSON-schema constrained decoding instead of a prompt-only
    JSON request means Gemini cannot silently omit required fields the way
    it did under free-text prompting (e.g. dropping risk_score or
    kpi_comparison on some runs while including them on others).
    """

    issue: str
    detailed_issue: str = ""
    recommendations: List[LLMParameterRecommendation] = Field(default_factory=list)
    detailed_recommendations: str = ""
    risk_score: float = Field(description="0-10, 0 when recommendations is empty")
    expected_impact: str = ""
    detailed_impact: str = ""
    detailed_risk: str = ""
    kpi_issue: str = ""
    kpi_comparison: List[LLMKPIComparison] = Field(default_factory=list)
    clarifying_question: Optional[str] = None

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Add product root to path so copied agents/tools/domain packages can import.
sys.path.insert(0, str(PROJECT_ROOT))

LLM_PARAMETER_CATALOG = {
    "reference_signal_power_pdschcfg": {"label": "Signal Power", "unit": "dBm"},
    "a3_event_offset": {"label": "A3 Offset", "unit": "dB"},
    "t310_timer": {"label": "T310 Timer", "unit": "ms"},
    "p0_nominal_pusch": {"label": "P0 PUSCH", "unit": "dBm"},
    "pdcch_aggregation_level": {"label": "PDCCH Agg", "unit": ""},
}

LLM_PARAMETER_ALIASES = {
    "signal power": "reference_signal_power_pdschcfg",
    "reference signal power": "reference_signal_power_pdschcfg",
    "reference_signal_power_pdschcfg": "reference_signal_power_pdschcfg",
    "rs power": "reference_signal_power_pdschcfg",
    "a3 offset": "a3_event_offset",
    "a3_event_offset": "a3_event_offset",
    "t310 timer": "t310_timer",
    "t310_timer": "t310_timer",
    "p0 pusch": "p0_nominal_pusch",
    "p0 nominal pusch": "p0_nominal_pusch",
    "p0_nominal_pusch": "p0_nominal_pusch",
    "pdcch agg": "pdcch_aggregation_level",
    "pdcch aggregation level": "pdcch_aggregation_level",
    "pdcch_aggregation_level": "pdcch_aggregation_level",
}

# Normalized (underscore/whitespace-insensitive) lookup so any spelling the LLM
# or catalog uses - "reference_signal_power_pdschcfg" or "Reference Signal Power" -
# resolves to the same canonical key, instead of requiring both forms to be
# listed verbatim above.
_NORMALIZED_PARAMETER_LOOKUP = {
    re.sub(r"[_\s]+", " ", alias.strip().lower()): canonical
    for alias, canonical in LLM_PARAMETER_ALIASES.items()
}
_NORMALIZED_PARAMETER_LOOKUP.update(
    {re.sub(r"[_\s]+", " ", key.strip().lower()): key for key in LLM_PARAMETER_CATALOG}
)


def _allow_optimizer_fallback() -> bool:
    return os.getenv("NETGENIX_ALLOW_OPTIMIZER_FALLBACK", "false").strip().lower() in {"1", "true", "yes"}


def _canonical_parameter_key(value: Any) -> str | None:
    normalized = re.sub(r"[_\s]+", " ", str(value or "").strip().lower())
    return _NORMALIZED_PARAMETER_LOOKUP.get(normalized)


# KPIs where a lower value is better (matches frontend/src/constants/kpis.ts
# lowerIsBetter flags for the same underlying MAE counters).
KPI_LOWER_IS_BETTER = {"control_channel_load", "feedback_channel_load"}


def _collect_llm_context(site_name: str) -> Dict[str, Any]:
    from backend.netgenix.services.database import get_kpi_history, get_kpi_threshold, get_site_kpis, get_site_parameters

    current_kpis = get_site_kpis(site_name) or {}
    parameter_values = get_site_parameters(site_name) or {}
    kpi_names = (
        "network_access_success",
        "download_speed",
        "upload_speed",
        "download_quality",
        "upload_quality",
        "control_channel_load",
        "feedback_channel_load",
    )
    history = {
        kpi_name: [
            {"date": row_date, "value": row_value}
            for row_date, row_value in get_kpi_history(site_name, kpi_name, 7)
            if row_value is not None
        ]
        for kpi_name in kpi_names
    }
    # Operating-average baselines calibrated from this network's own historical
    # data (see database.get_kpi_threshold) — the same numbers the dashboard's
    # "Operating Average" / HEALTHY-WATCH badges are computed against. Without
    # these the LLM has no calibrated notion of "good" and will guess.
    baselines = {
        kpi_name: {
            "operating_average": get_kpi_threshold(kpi_name),
            "lower_is_better": kpi_name in KPI_LOWER_IS_BETTER,
        }
        for kpi_name in kpi_names
    }
    return {
        "current_kpis": current_kpis,
        "history": history,
        "baselines": baselines,
        "parameters": {
            key: {
                "label": meta["label"],
                "unit": meta["unit"],
                "value": parameter_values.get(key),
            }
            for key, meta in LLM_PARAMETER_CATALOG.items()
        },
    }


def _normalize_llm_recommendations(
    raw_recommendations: List[Dict[str, Any]],
    current_parameters: Dict[str, Any],
) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_recommendations:
        if not isinstance(raw, dict):
            continue
        key = _canonical_parameter_key(raw.get("parameter") or raw.get("key"))
        if not key or key in seen:
            continue
        seen.add(key)
        meta = LLM_PARAMETER_CATALOG[key]
        current_value = current_parameters.get(key)
        normalized.append(
            {
                "parameter": meta["label"],
                "parameter_key": key,
                "current_value": current_value if current_value is not None else "N/A",
                "recommended_value": raw.get("recommended_value"),
                "unit": raw.get("unit") or meta["unit"],
                "description": str(raw.get("description") or "").strip(),
            }
        )
    return normalized


def _run_real_llm_optimization(site_name: str, cell_id: int, user_query: str) -> Dict[str, Any]:
    from langchain_core.messages import HumanMessage, SystemMessage

    from backend.netgenix.services.database import log_optimization_query
    from utils.llm_factory import get_llm_client

    context = _collect_llm_context(site_name)
    if not context["current_kpis"]:
        raise RuntimeError(f"No site KPI data is available for {site_name}")
    if not any(context["history"].values()):
        raise RuntimeError(f"No per-site KPI history is available for {site_name}")

    llm = get_llm_client(temperature=0.2, max_tokens=2200, timeout=120)
    # Structured output uses Gemini's native JSON-schema constrained decoding
    # (langchain-google-genai>=3.1's with_structured_output), so required
    # fields like risk_score/kpi_comparison are guaranteed present instead of
    # relying on the model to follow prose JSON instructions every time.
    structured_llm = llm.with_structured_output(LLMOptimizationResponse)
    system_prompt = (
        "You are NetGenix, a telecom optimization assistant for LTE radio networks. "
        "Use the supplied per-site current KPIs, seven-day KPI history, per-KPI operating-average "
        "baselines, and five current parameters. The baselines are calibrated from this network's own "
        "historical data — treat them as the definitive bar for 'healthy', not generic textbook LTE targets. "
        "Each baseline has a lower_is_better flag: for lower_is_better KPIs a value ABOVE the baseline is "
        "the problem; for all others a value BELOW the baseline is the problem. "
        "Recommend only conservative read-write changes for these parameters: "
        "Signal Power, A3 Offset, T310 Timer, P0 PUSCH, PDCCH Agg. "
        "Populate kpi_comparison for every KPI supplied, healthy or not, so the operator can see the "
        "actual numbers behind your verdict. "
        "If the site looks healthy, leave recommendations empty and explain specifically which KPIs "
        "support that conclusion and by how much, citing the real numbers — do not just say 'all KPIs "
        "are healthy' without the figures. risk_score should be 0 when recommendations is empty. "
        "If the operator's request is too vague to act on (e.g. 'suggest optimisation' with no target KPI, "
        "symptom, or goal), still complete the full KPI-vs-baseline health check as above, but also set "
        "clarifying_question to a short, specific question that would let you give a more targeted answer "
        "next time (e.g. asking which KPI or user complaint prompted the request). Leave clarifying_question "
        "null when the request was already specific enough."
    )
    human_prompt = (
        f"Site: {site_name}\n"
        f"Cell ID: {cell_id}\n"
        f"Operator request: {user_query}\n\n"
        f"Current KPIs:\n{json.dumps(context['current_kpis'], indent=2, default=str)}\n\n"
        f"Per-KPI operating-average baselines (calibrated from this network's real data):\n"
        f"{json.dumps(context['baselines'], indent=2, default=str)}\n\n"
        f"7-day KPI history:\n{json.dumps(context['history'], indent=2, default=str)}\n\n"
        f"Current parameters:\n{json.dumps(context['parameters'], indent=2, default=str)}"
    )
    # Gemini occasionally fails to produce output matching the schema (e.g.
    # wraps it in a markdown code fence instead of raw JSON) even under
    # constrained decoding; with_structured_output returns None rather than
    # raising when that happens, so a bare retry recovers most of the time
    # instead of crashing the whole request.
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
    payload: LLMOptimizationResponse | None = structured_llm.invoke(messages)
    if payload is None:
        logger.warning("Structured LLM output was None for %s, retrying once", site_name)
        payload = structured_llm.invoke(messages)
    if payload is None:
        raise RuntimeError(
            "The AI model returned a response that could not be parsed into a structured "
            "recommendation. Please try rephrasing your request."
        )

    recommendations = _normalize_llm_recommendations(
        [rec.model_dump() for rec in payload.recommendations],
        {key: value["value"] for key, value in context["parameters"].items()},
    )
    risk_score = max(0.0, min(10.0, payload.risk_score))
    detailed_recommendations = payload.detailed_recommendations or "\n".join(
        f"- {item['parameter']}: {item['current_value']} -> {item['recommended_value']} {item['unit']}".strip()
        for item in recommendations
    )
    result = {
        "status": "success",
        "issue": payload.issue or "Optimization review completed",
        "detailed_issue": payload.detailed_issue,
        "recommendations": recommendations,
        "detailed_recommendations": detailed_recommendations,
        # risk_level is always derived from risk_score rather than asking the
        # model for a separate label, so the two can never disagree.
        "risk_level": categorize_risk(risk_score),
        "risk_score": risk_score,
        "detailed_risk": payload.detailed_risk,
        "expected_impact": payload.expected_impact,
        "detailed_impact": payload.detailed_impact or payload.expected_impact,
        "mml_commands": extract_mml_commands("", recommendations),
        "kpi_issue": payload.kpi_issue,
        "kpi_comparison": [kpi.model_dump() for kpi in payload.kpi_comparison],
        "clarifying_question": payload.clarifying_question,
        "validation_status": "LLM_ANALYZED",
        "message": "Optimization analysis completed with live site data and historical KPI context.",
    }

    log_optimization_query(
        site_name=site_name,
        user_query=user_query,
        status="approved",
        recommendation_summary=result["issue"],
        kpi_issue=result["kpi_issue"] or result["issue"],
        parameters_recommended=json.dumps(recommendations),
        validation_status=result["validation_status"],
    )
    return result


def run_optimization(site_name: str, cell_id: int, user_query: str) -> Dict[str, Any]:
    """
    Run the complete optimization workflow for a site.

    Args:
        site_name: Name of the site to optimize
        cell_id: Cell ID for the site
        user_query: Natural language query from user

    Returns:
        Dict with workflow results including:
        - status: "success", "error", "rejected"
        - issue: Description of identified issue
        - recommendations: List of parameter changes
        - risk_level: "LOW", "MEDIUM", "HIGH"
        - risk_score: Float 0-10
        - expected_impact: Description of expected improvement
        - mml_commands: List of MML commands to execute
        - error_message: Error description if status is "error"
    """
    try:
        logger.info(f"Starting optimization workflow for {site_name}")
        logger.info(f"User query: {user_query}")
        return _run_real_llm_optimization(site_name, cell_id, user_query)
    except Exception as exc:
        logger.exception("Real LLM optimization failed for %s", site_name)
        if _allow_optimizer_fallback():
            return run_rule_based_optimization(
                site_name,
                cell_id,
                user_query,
                fallback_reason=f"Real LLM optimization failed: {exc}",
            )
        return {
            "status": "error",
            "error_message": f"Real LLM optimization is unavailable: {exc}",
            "issue": "",
            "recommendations": [],
            "risk_level": "HIGH",
            "risk_score": 10.0,
            "expected_impact": "",
            "mml_commands": [],
        }


def run_rule_based_optimization(
    site_name: str,
    cell_id: int,
    user_query: str,
    *,
    fallback_reason: str = "AI workflow unavailable",
) -> Dict[str, Any]:
    """
    Deterministic telco optimizer fallback.

    This keeps the AI Assistant operational when optional LLM dependencies,
    credentials, or remote model calls are unavailable. It is intentionally
    conservative: it uses local KPI evidence, recommends small changes, and
    still routes generated MML through the dry-run execution gate.
    """
    try:
        from backend.netgenix.services.database import get_site_kpis, get_site_parameters

        kpis = get_site_kpis(site_name) or {}
        params = get_site_parameters(site_name) or {}
        query = (user_query or "").lower()

        issues = detect_kpi_issues(kpis, query)
        primary_issue = select_primary_issue(issues, query)
        issue_text = summarize_optimization_issue(site_name, kpis, issues, primary_issue, fallback_reason)
        recommendations = build_rule_based_recommendations(primary_issue, params, query)
        mml_commands = extract_mml_commands("", recommendations)
        risk_score = calculate_risk_from_recommendations(recommendations)

        detailed_recommendations = "\n".join(
            f"- {rec['parameter']}: {rec['current_value']} -> {rec['recommended_value']} {rec.get('unit', '')}. "
            f"{rec.get('description', '')}".strip()
            for rec in recommendations
        )

        detailed_impact = build_rule_based_impact(primary_issue, kpis)
        detailed_risk = (
            "Safe optimizer mode: recommendations are deterministic, conservative, "
            "and execution remains dry-run unless live MML is explicitly enabled."
        )

        try:
            from backend.netgenix.services.database import log_optimization_query

            log_optimization_query(
                site_name=site_name,
                user_query=user_query,
                status="fallback",
                recommendation_summary=issue_text,
                kpi_issue=primary_issue,
                parameters_recommended=json.dumps(recommendations),
                validation_status="REVIEW",
            )
        except Exception as log_error:
            logger.warning("Failed to log fallback optimization query: %s", log_error)

        return {
            "status": "success",
            "issue": readable_issue(primary_issue),
            "message": "Optimizer completed in deterministic safe mode.",
            "recommendations": recommendations,
            "risk_level": categorize_risk(risk_score),
            "risk_score": risk_score,
            "expected_impact": detailed_impact,
            "mml_commands": mml_commands,
            "validation_status": "REVIEW",
            "detailed_issue": issue_text,
            "detailed_recommendations": detailed_recommendations,
            "detailed_risk": detailed_risk,
            "detailed_impact": detailed_impact,
            "kpi_issue": primary_issue,
        }
    except Exception as fallback_error:
        logger.error("Rule-based optimizer failed: %s", fallback_error)
        return {
            "status": "error",
            "error_message": f"{fallback_reason}; fallback failed: {fallback_error}",
        }


def detect_kpi_issues(kpis: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    thresholds = {
        "network_access_success": ("low_network_access_success", 95.0, "min", "%"),
        "download_speed": ("low_download_speed", 50.0, "min", "Mbps"),
        "upload_speed": ("low_upload_speed", 20.0, "min", "Mbps"),
        "download_quality": ("poor_download_quality", 95.0, "min", "%"),
        "upload_quality": ("poor_upload_quality", 95.0, "min", "%"),
        "control_channel_load": ("high_control_channel_load", 80.0, "max", "%"),
        "feedback_channel_load": ("high_feedback_channel_load", 80.0, "max", "%"),
    }

    issues = []
    for kpi_name, (code, threshold, mode, unit) in thresholds.items():
        value = kpis.get(kpi_name)
        if value is None:
            continue
        is_issue = value < threshold if mode == "min" else value > threshold
        if is_issue:
            issues.append(
                {
                    "code": code,
                    "kpi": kpi_name,
                    "value": round(float(value), 2),
                    "threshold": threshold,
                    "unit": unit,
                }
            )

    if not issues and any(word in query for word in ["optimize", "optimise", "improve", "fix", "tune"]):
        inferred = infer_issue_from_query(query)
        issues.append({"code": inferred, "kpi": "user_request", "value": "requested", "threshold": "review", "unit": ""})

    return issues


def infer_issue_from_query(query: str) -> str:
    if any(word in query for word in ["upload", "ul", "pusch"]):
        return "low_upload_speed"
    if any(word in query for word in ["access", "rach", "handover", "drop", "call"]):
        return "low_network_access_success"
    if any(word in query for word in ["quality", "bler", "sinr", "interference"]):
        return "poor_download_quality"
    if any(word in query for word in ["coverage", "rsrp", "overshoot", "ta", "timing"]):
        return "coverage_imbalance"
    return "low_download_speed"


def select_primary_issue(issues: List[Dict[str, Any]], query: str) -> str:
    """
    Pick the issue to optimize first.

    Operator intent wins when it maps to a detected issue; otherwise we use the
    strongest available KPI breach. This keeps the assistant aligned with the
    user's question instead of blindly optimizing the first threshold failure.
    """
    inferred = infer_issue_from_query(query)
    detected_codes = [issue["code"] for issue in issues]

    if inferred in detected_codes:
        return inferred

    if inferred and any(word in query for word in ["optimize", "optimise", "improve", "fix", "tune"]):
        return inferred

    return detected_codes[0] if detected_codes else inferred


def readable_issue(issue_code: str) -> str:
    return {
        "low_network_access_success": "Low network access success detected",
        "low_download_speed": "Low download speed detected",
        "low_upload_speed": "Low upload speed detected",
        "poor_download_quality": "Poor downlink quality detected",
        "poor_upload_quality": "Poor uplink quality detected",
        "high_control_channel_load": "High control channel load detected",
        "high_feedback_channel_load": "High feedback channel load detected",
        "coverage_imbalance": "Coverage imbalance or overshoot review",
    }.get(issue_code, "Network optimization review")


def summarize_optimization_issue(
    site_name: str,
    kpis: Dict[str, Any],
    issues: List[Dict[str, Any]],
    primary_issue: str,
    fallback_reason: str,
) -> str:
    evidence = []
    for issue in issues[:5]:
        evidence.append(
            f"{issue['kpi']}={issue['value']}{issue['unit']} "
            f"(threshold {issue['threshold']}{issue['unit']})"
        )

    if not evidence and kpis:
        evidence.append("No KPI threshold breach found; optimizer used the operator request as intent.")
    elif not evidence:
        evidence.append("No KPI evidence available in local DB; optimizer used conservative intent-based rules.")

    return (
        f"Optimizer safe-mode assessment for {site_name}. "
        f"Primary issue: {readable_issue(primary_issue)}. "
        f"Evidence: {'; '.join(evidence)}. "
        f"Reason safe mode was used: {fallback_reason}."
    )


def build_rule_based_recommendations(
    primary_issue: str,
    params: Dict[str, Any],
    query: str,
) -> List[Dict[str, Any]]:
    current_power = params.get("reference_signal_power_pdschcfg", -180)
    current_a3 = params.get("a3_event_offset", 3)
    current_t310 = params.get("t310_timer", 1000)
    current_p0 = params.get("p0_nominal_pusch", -96)

    if primary_issue in {"low_download_speed", "poor_download_quality", "coverage_imbalance"}:
        return [
            {
                "parameter": "Reference Signal Power",
                "current_value": current_power,
                "recommended_value": safe_numeric_shift(current_power, 10),
                "unit": "0.1 dBm",
                "description": "Small downlink coverage/quality lift for weak-cell or throughput symptoms.",
            }
        ]

    if primary_issue == "low_upload_speed":
        return [
            {
                "parameter": "P0 Nominal PUSCH",
                "current_value": current_p0,
                "recommended_value": safe_numeric_shift(current_p0, 3),
                "unit": "dBm",
                "description": "Small uplink power-control lift to improve UL throughput and reliability.",
            }
        ]

    if primary_issue == "low_network_access_success":
        return [
            {
                "parameter": "A3 Event Offset",
                "current_value": current_a3,
                "recommended_value": safe_numeric_shift(current_a3, -1),
                "unit": "dB",
                "description": "Slightly earlier handover trigger to reduce access/handover instability.",
            },
            {
                "parameter": "T310 Timer",
                "current_value": current_t310,
                "recommended_value": "MS2000_T310",
                "unit": "ms",
                "description": "Increase radio-link failure tolerance for unstable access conditions.",
            },
        ]

    if primary_issue in {"high_control_channel_load", "high_feedback_channel_load"}:
        return [
            {
                "parameter": "A3 Event Offset",
                "current_value": current_a3,
                "recommended_value": safe_numeric_shift(current_a3, 1),
                "unit": "dB",
                "description": "Reduce unnecessary mobility churn while channel load is high; validate with neighbor/load review.",
            }
        ]

    return [
        {
            "parameter": "Reference Signal Power",
            "current_value": current_power,
            "recommended_value": safe_numeric_shift(current_power, 5),
            "unit": "0.1 dBm",
            "description": f"Conservative first-pass optimization for request: {query[:80]}",
        }
    ]


def safe_numeric_shift(value: Any, delta: float) -> Any:
    try:
        original = float(value)
        shifted = original + delta
        return int(shifted) if shifted.is_integer() else round(shifted, 2)
    except (TypeError, ValueError):
        return value


def build_rule_based_impact(primary_issue: str, kpis: Dict[str, Any]) -> str:
    current = []
    if kpis:
        for key in ["network_access_success", "download_speed", "upload_speed", "download_quality", "control_channel_load"]:
            if kpis.get(key) is not None:
                current.append(f"{key}={round(float(kpis[key]), 2)}")

    focus = readable_issue(primary_issue).lower()
    baseline = f" Current evidence: {', '.join(current)}." if current else ""
    return (
        f"Expected to improve {focus} after field validation. "
        "Treat this as an engineering recommendation, not an automatic live change."
        f"{baseline}"
    )


def parse_workflow_results(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse workflow state into UI-friendly format.

    Args:
        state: Final workflow state from agents

    Returns:
        Formatted results dict
    """
    # Extract agent outputs
    agent_outputs = state.get("agent_outputs", {})

    # Determine if optimization is needed
    needs_optimization = state.get("needs_optimization", False)

    if not needs_optimization:
        return {
            "status": "success",
            "issue": "No optimization needed",
            "message": "All KPIs are within acceptable thresholds. Network performance is good.",
            "recommendations": [],
            "risk_level": "NONE",
            "risk_score": 0.0,
            "expected_impact": "No changes recommended",
            "mml_commands": []
        }

    # Get primary issue
    primary_issue = state.get("primary_kpi_issue", "unknown")
    issue_descriptions = {
        "low_download_speed": "Low download speed detected",
        "low_network_access_success": "Low network access success rate",
        "low_upload_speed": "Low upload speed detected",
        "poor_quality": "Poor signal quality detected",
        "high_channel_load": "High channel load detected"
    }
    issue_desc = issue_descriptions.get(primary_issue, "Performance issue detected")

    # Parse configuration output for recommendations
    config_output = state.get("config_output", "")
    recommendations = parse_recommendations(config_output)

    # Get validation status
    validation_status = state.get("validation_status", "PENDING")

    if validation_status == "REJECTED":
        return {
            "status": "rejected",
            "issue": issue_desc,
            "message": "Proposed changes were rejected due to safety concerns.",
            "recommendations": recommendations,
            "risk_level": "HIGH",
            "risk_score": 9.0,
            "expected_impact": "Changes not approved",
            "mml_commands": []
        }

    # Get all agent outputs
    kpi_output = state.get("kpi_output", "")
    validation_output = agent_outputs.get("validation", "")

    # ==========================================================================
    # RISK SCORE: Extract from validation OR calculate from recommendations
    # ==========================================================================
    risk_score = extract_risk_score(validation_output)

    # If extraction returned default (5.0) and we have recommendations, calculate real risk
    # This ensures we get a grounded risk score based on actual parameter changes
    if risk_score == 5.0 and recommendations:
        calculated_risk = calculate_risk_from_recommendations(recommendations)
        risk_score = calculated_risk
        logger.info(f"Using calculated risk score: {risk_score}/10 (based on {len(recommendations)} recommendations)")

    risk_level = categorize_risk(risk_score)

    # ==========================================================================
    # MML COMMANDS: Extract from text OR generate from recommendations
    # ==========================================================================
    mml_commands = extract_mml_commands(config_output, recommendations)

    # Extract expected impact
    expected_impact = extract_expected_impact(config_output)
    
    # Parse detailed sections from all agent outputs
    kpi_sections = parse_detailed_sections(kpi_output)
    config_sections = parse_detailed_sections(config_output)
    validation_sections = parse_detailed_sections(validation_output)

    # Combine sections - prefer more detailed output
    detailed_issue = kpi_sections.get("issue", "") or config_sections.get("issue", "") or issue_desc
    detailed_recommendations = config_sections.get("recommendations", "")
    detailed_risk = validation_sections.get("risk", "") or config_sections.get("risk", "")
    detailed_impact = (config_sections.get("impact", "") or 
                      validation_sections.get("impact", "") or 
                      expected_impact)

    return {
        "status": "success",
        "issue": issue_desc,
        "recommendations": recommendations,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "expected_impact": expected_impact,
        "mml_commands": mml_commands,
        "validation_status": validation_status,
        "detailed_issue": detailed_issue,
        "detailed_recommendations": detailed_recommendations,
        "detailed_risk": detailed_risk,
        "detailed_impact": detailed_impact
    }


def parse_recommendations(config_output: str) -> List[Dict[str, Any]]:
    """
    Parse parameter recommendations from configuration output.

    Args:
        config_output: Raw output from configuration agent

    Returns:
        List of dicts with parameter changes including current and recommended values
    """
    recommendations = []

    # Parameter mappings with display names and units
    param_mappings = {
        "reference_signal_power": {"name": "Reference Signal Power", "unit": "dBm", "key": "reference_signal_power_pdschcfg"},
        "pdschcfg": {"name": "Reference Signal Power", "unit": "dBm", "key": "reference_signal_power_pdschcfg"},
        "referencesignalpower": {"name": "Reference Signal Power", "unit": "dBm", "key": "reference_signal_power_pdschcfg"},
        "a3_event_offset": {"name": "A3 Event Offset", "unit": "dB", "key": "a3_event_offset"},
        "a3offset": {"name": "A3 Event Offset", "unit": "dB", "key": "a3_event_offset"},
        "a3 offset": {"name": "A3 Event Offset", "unit": "dB", "key": "a3_event_offset"},
        "t310_timer": {"name": "T310 Timer", "unit": "ms", "key": "t310_timer"},
        "t310": {"name": "T310 Timer", "unit": "ms", "key": "t310_timer"},
        "p0_nominal_pusch": {"name": "P0 Nominal PUSCH", "unit": "dBm", "key": "p0_nominal_pusch"},
        "p0nominal": {"name": "P0 Nominal PUSCH", "unit": "dBm", "key": "p0_nominal_pusch"},
        "p0 nominal": {"name": "P0 Nominal PUSCH", "unit": "dBm", "key": "p0_nominal_pusch"},
        "pdcch_aggregation": {"name": "PDCCH Aggregation Level", "unit": "", "key": "pdcch_aggregation_level"},
        "aggregation_level": {"name": "PDCCH Aggregation Level", "unit": "", "key": "pdcch_aggregation_level"},
        "pdcch": {"name": "PDCCH Aggregation Level", "unit": "", "key": "pdcch_aggregation_level"}
    }

    # Track which parameters we've already added (by key)
    added_params = set()

    # FIRST: Try to extract from structured LLM output format
    # Format: "PRIMARY PARAMETER: ...\n  Current: X\n  Recommended: Y"
    structured_patterns = [
        # Match "Current: 152 (15.2 dBm)" or "Current: 152" followed by "Recommended: 172"
        r'(?:PRIMARY|SECONDARY)\s+PARAMETER[:\s]+[^\n]*?(reference.?signal|a3.?offset|t310|p0.?nominal|pdcch)[^\n]*\n[^\n]*?Current[:\s]+(\d+\.?\d*)[^\n]*\n[^\n]*?Recommended[:\s]+(\d+\.?\d*)',
        # Also try without the label
        r'(reference.?signal|a3.?offset|t310|p0.?nominal|pdcch)[^\n]*\n[^\n]*?Current[:\s]+(\d+\.?\d*)[^\n]*\n[^\n]*?Recommended[:\s]+(\d+\.?\d*)',
    ]

    for pattern in structured_patterns:
        matches = re.findall(pattern, config_output, re.IGNORECASE | re.DOTALL)
        for match in matches:
            param_text = match[0].lower().replace("_", "").replace(" ", "")
            current_val = match[1]
            new_val = match[2]

            # Find matching parameter
            for key_pattern, param_info in param_mappings.items():
                key_clean = key_pattern.replace("_", "").replace(" ", "")
                if key_clean in param_text or param_text in key_clean:
                    if param_info["key"] not in added_params:
                        recommendations.append({
                            "parameter": param_info["name"],
                            "current_value": current_val,
                            "recommended_value": new_val,
                            "unit": param_info["unit"],
                            "description": f"Adjust {param_info['name']} to optimize performance"
                        })
                        added_params.add(param_info["key"])
                    break

    # SECOND: Try inline patterns like "param: 100 → 120" or "param from 100 to 120"
    value_patterns = [
        r'(\w+)[:\s]+(-?\d+\.?\d*)\s*(?:→|->|to)\s*(-?\d+\.?\d*)',  # param: 100 → 120
        r'(\w+)\s+from\s+(-?\d+\.?\d*)\s+to\s+(-?\d+\.?\d*)',  # param from 100 to 120
    ]

    config_lower = config_output.lower()

    for pattern in value_patterns:
        matches = re.findall(pattern, config_lower, re.IGNORECASE)
        for match in matches:
            param_text = match[0].lower().replace("_", "").replace("-", "").replace(" ", "")

            # Find matching parameter
            for key_pattern, param_info in param_mappings.items():
                key_clean = key_pattern.replace("_", "").replace(" ", "")
                if key_clean in param_text or param_text in key_clean:
                    if param_info["key"] not in added_params:
                        current_val = match[1]
                        new_val = match[2]

                        recommendations.append({
                            "parameter": param_info["name"],
                            "current_value": current_val,
                            "recommended_value": new_val,
                            "unit": param_info["unit"],
                            "description": f"Adjust {param_info['name']} to optimize performance"
                        })
                        added_params.add(param_info["key"])
                    break

    # THIRD: Look for Current/Recommended pairs anywhere in the text for any parameter
    if not recommendations:
        # Generic extraction: find any "Current: X" followed by "Recommended: Y"
        current_rec_pattern = r'Current[:\s]+(\d+\.?\d*)[^\n]*(?:\n[^\n]*)*?Recommended[:\s]+(\d+\.?\d*)'
        matches = re.findall(current_rec_pattern, config_output, re.IGNORECASE)

        for i, match in enumerate(matches):
            if i < len(param_mappings):  # Limit to reasonable number
                recommendations.append({
                    "parameter": f"Parameter {i+1}",
                    "current_value": match[0],
                    "recommended_value": match[1],
                    "unit": "",
                    "description": "Parameter adjustment based on KPI analysis"
                })

    # FOURTH: Check for parameter mentions without specific values (with fallback values)
    if not recommendations:
        for key_pattern, param_info in param_mappings.items():
            if param_info["key"] not in added_params:
                if key_pattern in config_lower or key_pattern.replace("_", " ") in config_lower:
                    # Try to find ANY numbers near this parameter mention
                    param_section = re.search(
                        rf'{key_pattern}[^\n]*?(\d+\.?\d*)[^\n]*?(\d+\.?\d*)?',
                        config_lower, re.IGNORECASE
                    )
                    if param_section and param_section.group(1):
                        current_val = param_section.group(1)
                        new_val = param_section.group(2) if param_section.group(2) else "optimized"
                    else:
                        current_val = "current"
                        new_val = "optimized"

                    recommendations.append({
                        "parameter": param_info["name"],
                        "current_value": current_val,
                        "recommended_value": new_val,
                        "unit": param_info["unit"],
                        "description": f"Adjust {param_info['name']} based on KPI analysis"
                    })
                    added_params.add(param_info["key"])

    # Final fallback - but with better message
    if not recommendations:
        recommendations.append({
            "parameter": "Network Optimization",
            "current_value": "current",
            "recommended_value": "optimized",
            "unit": "",
            "description": "See detailed analysis for specific parameter recommendations"
        })

    return recommendations


def calculate_risk_from_recommendations(recommendations: List[Dict[str, Any]]) -> float:
    """
    Calculate risk score based on actual parameter changes.
    Uses same logic as validation_agent.py TIER 2 for consistency.

    Args:
        recommendations: List of parameter recommendations with current/new values

    Returns:
        Risk score (0-10) based on:
        - Parameter type (power changes = higher risk)
        - Magnitude of change
        - Base risk of 3 points
    """
    if not recommendations:
        return 5.0  # Medium risk default when no recommendations

    risk = 3  # Base risk (same as validation_agent.py)

    high_risk_params = ['reference_signal_power', 'p0_nominal', 'p0nominal', 'pdschcfg']
    medium_risk_params = ['a3_event_offset', 'a3_offset', 'a3offset', 't310', 'timer']

    for rec in recommendations:
        param_lower = rec.get("parameter", "").lower().replace(" ", "_")
        current = rec.get("current_value")
        new = rec.get("recommended_value")

        # Skip non-numeric recommendations
        if new in ["optimized", "current", None, ""]:
            continue

        # Parameter type risk
        if any(p in param_lower for p in high_risk_params):
            risk += 2
        elif any(p in param_lower for p in medium_risk_params):
            risk += 1

        # Magnitude risk (if we have numeric values)
        try:
            # Clean numeric values
            current_str = str(current).replace('dBm', '').replace('dB', '').replace('ms', '').replace('MS', '').strip()
            new_str = str(new).replace('dBm', '').replace('dB', '').replace('ms', '').replace('MS', '').strip()

            # Handle T310 timer format like "MS1000_T310" -> extract 1000
            if 'MS' in str(current).upper():
                import re
                match = re.search(r'(\d+)', str(current))
                if match:
                    current_str = match.group(1)
            if 'MS' in str(new).upper():
                import re
                match = re.search(r'(\d+)', str(new))
                if match:
                    new_str = match.group(1)

            current_float = float(current_str)
            new_float = float(new_str)

            if current_float != 0:
                change_pct = abs((new_float - current_float) / current_float) * 100
                if change_pct > 30:
                    risk += 3
                elif change_pct > 20:
                    risk += 2
                elif change_pct > 10:
                    risk += 1

                logger.debug(f"Risk calc for {param_lower}: {current_float} -> {new_float} ({change_pct:.1f}% change)")
        except (ValueError, TypeError) as e:
            logger.debug(f"Could not calculate magnitude risk for {param_lower}: {e}")

    final_risk = min(risk, 10.0)
    logger.info(f"Calculated risk score from recommendations: {final_risk}/10")
    return final_risk


def extract_risk_score(validation_output: str) -> float:
    """
    Extract risk score from validation output.

    Args:
        validation_output: Output from validation agent

    Returns:
        Risk score (0-10)
    """
    if not validation_output:
        return 5.0  # Default to medium risk if no output

    # Patterns ordered from most specific to least specific
    patterns = [
        r'(?:Maximum\s+)?Risk\s+Score[:\s]+(\d+\.?\d*)\s*/\s*10',  # "Maximum Risk Score: 7/10"
        r'Risk\s+Score[:\s]+(\d+\.?\d*)',  # "Risk Score: 7"
        r'risk[:\s]+(\d+\.?\d*)\s*/\s*10',  # "risk: 7/10"
        r'risk.*?(\d+\.?\d*)\s*out\s*of\s*10',  # "risk 7 out of 10"
        r'risk.*?(\d+)\s*/\s*10',  # "risk 7/10"
        r'risk.*?score.*?(\d+\.?\d*)',  # "risk score 7"
        r'score.*?(\d+\.?\d*)\s*/\s*10',  # "score: 7/10"
        r'(\d+\.?\d*)\s*/\s*10\s*risk',  # "7/10 risk"
        r'risk.*?(\d+\.?\d*)',  # generic "risk: 7"
        r'score.*?(\d+\.?\d*)',  # generic "score: 7"
    ]

    validation_lower = validation_output.lower()

    for pattern in patterns:
        match = re.search(pattern, validation_lower)
        if match:
            try:
                score = float(match.group(1))
                # Validate it's a reasonable risk score (0-10)
                if 0.0 <= score <= 10.0:
                    return score
                # If score > 10, might be percentage or other format
                elif score <= 100:
                    return score / 10.0  # Convert percentage to 0-10
            except (ValueError, IndexError):
                pass

    # Try to infer from risk level keywords
    if "high risk" in validation_lower or "critical" in validation_lower:
        return 8.0
    elif "medium risk" in validation_lower or "moderate" in validation_lower:
        return 5.0
    elif "low risk" in validation_lower or "minimal" in validation_lower:
        return 3.0

    # Default to medium risk if can't extract - this is a safe default
    return 5.0


def categorize_risk(risk_score: float) -> str:
    """
    Categorize numeric risk score into level.

    Args:
        risk_score: Numeric score 0-10

    Returns:
        Risk level: "LOW", "MEDIUM", "HIGH"
    """
    if risk_score <= 3.0:
        return "LOW"
    elif risk_score <= 7.0:
        return "MEDIUM"
    else:
        return "HIGH"


def extract_mml_commands(config_output: str, recommendations: List[Dict[str, Any]] = None) -> List[str]:
    """
    Extract MML commands from configuration output, or GENERATE them from recommendations.

    Args:
        config_output: Output from configuration agent
        recommendations: Optional list of parameter recommendations to generate MML from

    Returns:
        List of MML command strings
    """
    commands = []

    # First, strip markdown code block markers
    cleaned_output = config_output if config_output else ""
    cleaned_output = re.sub(r'```\w*\n?', '', cleaned_output)  # Remove ```python, ```mml, etc.
    cleaned_output = re.sub(r'`([^`]+)`', r'\1', cleaned_output)  # Remove inline code markers

    # MML command prefixes (Huawei format)
    mml_prefixes = ['MOD', 'ADD', 'LST', 'SET', 'ALM', 'DSP', 'DEL', 'ACT', 'DEA', 'BLK', 'UBL']

    # Look for lines that look like MML commands
    for line in cleaned_output.split('\n'):
        line = line.strip()

        # Skip empty lines and comment lines
        if not line or line.startswith('#') or line.startswith('//'):
            continue

        # Remove leading numbers/bullets (e.g., "1. MOD..." or "- MOD...")
        line = re.sub(r'^[\d\.\-\*\s]+', '', line).strip()

        # Check if line starts with MML command prefix
        line_upper = line.upper()
        for prefix in mml_prefixes:
            if line_upper.startswith(prefix):
                # Clean up the command
                clean_cmd = line.strip()
                if clean_cmd and clean_cmd not in commands:
                    commands.append(clean_cmd)
                break

    # Also look for commands in code block format that might have been missed
    code_block_match = re.findall(r'(?:MOD|ADD|SET|LST)[A-Z0-9_]+:[^;]+;', config_output or "", re.IGNORECASE)
    for cmd in code_block_match:
        cmd = cmd.strip()
        if cmd and cmd not in commands:
            commands.append(cmd)

    # ==========================================================================
    # GENERATE MML COMMANDS FROM RECOMMENDATIONS (if none found in text)
    # ==========================================================================
    if not commands and recommendations:
        logger.info("No MML commands found in text - generating from recommendations...")

        try:
            from domain.mml_commands import build_modify_command, MML_COMMANDS
        except ImportError:
            logger.warning("Could not import mml_commands module for MML generation")
            return commands

        # Map display names back to internal parameter keys
        param_name_map = {
            "Reference Signal Power": "reference_signal_power_pdschcfg",
            "reference signal power": "reference_signal_power_pdschcfg",
            "A3 Event Offset": "a3_event_offset",
            "a3 event offset": "a3_event_offset",
            "A3 Offset": "a3_event_offset",
            "T310 Timer": "t310_timer",
            "t310 timer": "t310_timer",
            "T310": "t310_timer",
            "P0 Nominal PUSCH": "p0_nominal_pusch",
            "p0 nominal pusch": "p0_nominal_pusch",
            "P0 Nominal": "p0_nominal_pusch",
            "P0 PUSCH": "p0_nominal_pusch",
            "p0 pusch": "p0_nominal_pusch",
            "PDCCH Aggregation Level": "pdcch_aggregation_level",
            "pdcch aggregation level": "pdcch_aggregation_level",
            "PDCCH Agg": "pdcch_aggregation_level",
            "pdcch agg": "pdcch_aggregation_level",
        }

        for rec in recommendations:
            param_name = rec.get("parameter", "")
            new_value = rec.get("recommended_value")

            # Skip non-actionable recommendations
            if new_value in ["optimized", "current", None, ""]:
                logger.debug(f"Skipping non-numeric recommendation: {param_name} = {new_value}")
                continue

            # Prefer the canonical key already resolved by the LLM path;
            # fall back to fuzzy label matching for the rule-based path.
            internal_name = rec.get("parameter_key")
            if not internal_name:
                internal_name = param_name_map.get(param_name)
            if not internal_name:
                # Try case-insensitive match
                internal_name = param_name_map.get(param_name.lower())
            if not internal_name:
                # Try converting display name to snake_case
                internal_name = param_name.lower().replace(" ", "_")

            # Check if this parameter is supported for modification
            if internal_name not in MML_COMMANDS:
                logger.warning(f"Parameter '{internal_name}' not found in MML_COMMANDS")
                continue

            if MML_COMMANDS[internal_name].get("modify") is None:
                logger.warning(f"Parameter '{internal_name}' is read-only (no modify command)")
                continue

            try:
                # Clean the value for MML command
                clean_value = str(new_value).strip()

                # Handle T310 timer format - needs to be like "MS1000_T310"
                if internal_name == "t310_timer":
                    if not clean_value.upper().startswith("MS"):
                        # Extract numeric value and format correctly
                        match = re.search(r'(\d+)', clean_value)
                        if match:
                            ms_value = match.group(1)
                            clean_value = f"MS{ms_value}_T310"

                # Generate commands for all 6 cells at the site
                for cell_id in [1, 2, 3, 4, 5, 6]:
                    cmd = build_modify_command(internal_name, clean_value, cell_id)
                    if cmd and cmd not in commands:
                        commands.append(cmd)

                logger.info(f"Generated 6 MML commands for {internal_name} = {clean_value}")

            except Exception as e:
                logger.warning(f"Could not generate MML for {param_name}: {e}")

    if commands:
        logger.info(f"Total MML commands: {len(commands)}")
    else:
        logger.warning("No MML commands extracted or generated")

    return commands


def extract_expected_impact(config_output: str) -> str:
    """
    Extract expected impact description from output.

    Args:
        config_output: Output from configuration agent

    Returns:
        Impact description string
    """
    # Look for impact-related keywords
    impact_keywords = ['improve', 'increase', 'decrease', 'enhance', 'optimize', 'mbps', 'performance']

    for line in config_output.split('\n'):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in impact_keywords):
            if len(line) > 10 and len(line) < 200:  # Reasonable length
                return line.strip()

    # Default impact message
    return "Expected improvement in network KPIs based on parameter optimization"


def parse_detailed_sections(config_output: str) -> Dict[str, str]:
    """
    Parse the detailed technical sections from configuration output.
    
    Extracts content from:
    - PRIMARY ISSUE / Issue Identified
    - PRIMARY PARAMETER / SECONDARY PARAMETER / Recommended Changes
    - Risk Factors / Risk Assessment
    - Expected Impact / Expected KPI Improvements
    
    Args:
        config_output: Raw configuration output with technical sections
        
    Returns:
        Dictionary with parsed sections
    """
    sections = {
        "issue": "",
        "recommendations": "",
        "risk": "",
        "impact": ""
    }
    
    if not config_output:
        return sections
    
    lines = config_output.split('\n')
    current_section = None
    section_content = []
    
    for line in lines:
        line_upper = line.upper()
        
        # Check for section headers (support both old and new formats)
        if ("PRIMARY ISSUE:" in line_upper or "ISSUE IDENTIFIED" in line_upper):
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            current_section = "issue"
            section_content = [line]  # Include the header
            
        elif ("PRIMARY PARAMETER:" in line_upper or "SECONDARY PARAMETER:" in line_upper or 
              "RECOMMENDED CHANGES" in line_upper or "💡 RECOMMENDED CHANGES" in line_upper):
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            current_section = "recommendations"
            if not section_content:  # Only add if starting fresh
                section_content = [line]
            else:
                section_content.append(line)
            
        elif ("RISK FACTORS:" in line_upper or "RISK ASSESSMENT" in line_upper or 
              "⚠️ RISK ASSESSMENT" in line_upper):
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            current_section = "risk"
            section_content = [line]
            
        elif ("EXPECTED IMPACT" in line_upper or "EXPECTED KPI IMPROVEMENTS" in line_upper or
              "📈 EXPECTED IMPACT" in line_upper or "PERFORMANCE IMPROVEMENTS:" in line_upper):
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            current_section = "impact"
            section_content = [line]
            
        elif "EXECUTION MODE" in line_upper or "NEXT STEP" in line_upper or "=====" in line:
            # End of section - save and stop
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content).strip()
            if "=====" in line and "CONFIGURATION RECOMMENDATIONS" not in line_upper:
                break
            
        elif current_section and line.strip() and not line.startswith('━'):
            # Stop impact section when hitting other major sections
            if current_section == "impact":
                stop_keywords = [
                    "RISK MITIGATION", "MITIGATION PLAN", "MONITORING PLAN",
                    "ROLLBACK", "DECISION:", "OVERALL DECISION", "RECOMMENDATION:",
                    "SAFETY CHECK", "VALIDATION", "METHOD:", "PARAMETER #",
                    "MULTI-PARAMETER", "CONFLICT ANALYSIS"
                ]
                if any(kw in line.upper() for kw in stop_keywords):
                    sections[current_section] = '\n'.join(section_content).strip()
                    current_section = None
                    section_content = []
                    continue

            # Add content to current section (skip separator lines)
            section_content.append(line)

    # Capture last section if any
    if current_section and section_content:
        sections[current_section] = '\n'.join(section_content).strip()

    # ==========================================================================
    # POST-PROCESSING: Clean up and limit impact section
    # ==========================================================================
    if sections.get("impact"):
        lines = sections["impact"].split('\n')
        # Keep only lines that look like impact statements (contain improvement keywords)
        impact_lines = []
        impact_keywords = ['improve', 'increase', 'decrease', 'reduce', 'enhance',
                          '%', 'mbps', 'ms', 'db', 'kpi', 'throughput', 'latency',
                          'speed', 'access', 'success', 'rate', 'quality']

        for line in lines:
            if len(impact_lines) >= 10:  # Max 10 lines
                break
            line_clean = line.strip()
            if not line_clean:
                continue
            # Skip header/separator lines
            if line_clean.startswith('━') or line_clean.startswith('=') or line_clean.startswith('-'*5):
                continue
            # Skip lines that are just headers
            if line_clean.upper() in ['EXPECTED IMPACT', 'EXPECTED KPI IMPROVEMENTS', 'PERFORMANCE IMPROVEMENTS:']:
                continue
            # Include lines that have impact-related keywords
            if any(kw in line_clean.lower() for kw in impact_keywords):
                # Clean up bullet points
                line_clean = re.sub(r'^[•\-\*\d\.]+\s*', '', line_clean)
                if line_clean:
                    impact_lines.append(line_clean)

        sections["impact"] = '\n'.join(impact_lines[:10]) if impact_lines else ""
        logger.debug(f"Impact section limited to {len(impact_lines)} lines")

    return sections


def execute_optimization(
    site_name: str,
    recommendations: list,
    mml_commands: list,
    *,
    execute_live: bool = False,
) -> Dict[str, Any]:
    """
    Execute approved optimization recommendations.

    Args:
        site_name: Name of the site
        recommendations: List of approved parameter changes
        mml_commands: List of MML commands to execute

    Returns:
        Dict with execution results:
        - status: "success", "partial", "error"
        - executed: Number of commands executed
        - failed: Number of commands failed
        - details: List of execution details per command
        - message: Summary message
    """
    try:
        # Import tools
        from tools.rollback_manager import capture_rollback_state
        from agents.mml_executor_agent import mml_executor_agent

        logger.info(f"Executing optimization for {site_name}")
        logger.info(f"Commands to execute: {len(mml_commands)}")

        # Check if in dry-run mode
        import yaml
        config_path = PROJECT_ROOT / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        yaml_dry_run = config.get('agents', {}).get('mml_executor', {}).get('dry_run', True)
        live_mml_allowed = os.getenv("NETGENIX_ALLOW_LIVE_MML", "").lower() in {"1", "true", "yes"}
        dry_run = yaml_dry_run or not execute_live or not live_mml_allowed

        if dry_run:
            logger.info("DRY RUN MODE - Simulating execution")
            reason = "YAML dry_run enabled"
            if not execute_live:
                reason = "request did not set execute_live=true"
            elif not live_mml_allowed:
                reason = "NETGENIX_ALLOW_LIVE_MML is not enabled"
            return {
                "status": "success",
                "executed": len(mml_commands),
                "failed": 0,
                "details": [
                    {"command": cmd, "status": "simulated", "message": f"[DRY RUN] Would execute command ({reason})"}
                    for cmd in mml_commands
                ],
                "message": f"[DRY RUN] Would execute {len(mml_commands)} commands. No actual changes made. Reason: {reason}.",
                "dry_run": True
            }

        # Execute with MML executor agent.
        # mml_executor_agent's task prompt reads state["validation_output"] for the
        # approved changes (not config_output/recommended_changes), so it must be
        # populated here or the agent receives a blank "Approved Changes" section
        # and has nothing to act on.
        approved_changes_summary = "\n".join(
            f"- {rec.get('parameter')}: {rec.get('current_value')} -> {rec.get('recommended_value')} {rec.get('unit', '')}".strip()
            for rec in recommendations
        )
        validation_output = (
            f"{approved_changes_summary}\n\nMML commands:\n" + "\n".join(mml_commands)
        )
        execution_state = {
            "site_name": site_name,
            "cell_id": 1,  # Will be handled by batch execution
            "user_query": "Execute approved optimizations",
            "config_output": "\n".join(mml_commands),
            "validation_status": "APPROVED",
            "validation_output": validation_output,
            "is_validated": True,
            "recommended_changes": recommendations
        }

        result_state = mml_executor_agent(execution_state)

        executor_output = result_state.get("executor_output", "")
        modify_results = result_state.get("modify_results") or []

        if modify_results:
            # Reliable path: counts are derived from the actual modify-tool
            # call outcomes (SUCCESS:/FAILURE:/ERROR: prefixes returned by
            # huawei_tools), not from string-matching the agent's prose report.
            executed = sum(1 for r in modify_results if r["outcome"] == "success")
            failed = sum(1 for r in modify_results if r["outcome"] in ("failed", "unknown"))
            partial = sum(1 for r in modify_results if r["outcome"] == "partial")

            if failed == 0 and partial == 0:
                status = "success"
                message = f"Successfully executed {executed} commands"
            elif executed > 0 or partial > 0:
                status = "partial"
                message = f"Executed {executed} commands, {failed} failed, {partial} partial"
            else:
                status = "error"
                message = f"Failed to execute commands: {executor_output[:200]}"

            details = [
                {"command": r["tool"], "status": r["outcome"], "message": r["message"][:300]}
                for r in modify_results
            ]
        else:
            # No modify tool was ever called (e.g. rollback capture failed and
            # the agent aborted before making changes, or execution timed out).
            executed = 0
            failed = 0
            status = "error"
            message = f"No parameter changes were executed: {executor_output[:200]}"
            details = []

        return {
            "status": status,
            "executed": executed,
            "failed": failed,
            "details": details,
            "message": message,
            "dry_run": False
        }

    except Exception as e:
        logger.error(f"Execution error: {e}")
        return {
            "status": "error",
            "executed": 0,
            "failed": len(mml_commands),
            "details": [],
            "message": f"Execution failed: {str(e)}",
            "dry_run": False
        }
