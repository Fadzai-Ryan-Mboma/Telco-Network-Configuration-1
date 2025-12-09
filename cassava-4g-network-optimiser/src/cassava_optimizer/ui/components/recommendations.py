"""
Recommendation display components for the Streamlit UI.

Renders optimization recommendations with approval workflow,
risk indicators, and execution controls.
"""

from typing import Any, Callable, Optional

import streamlit as st

from cassava_optimizer.ui.theme import COLORS, CASSAVA_GREEN, CASSAVA_NAVY


def render_recommendation_card(
    recommendation: dict[str, Any],
    index: int = 0,
    show_approval: bool = True,
    on_approve: Optional[Callable[[dict], None]] = None,
    on_reject: Optional[Callable[[dict], None]] = None,
) -> bool:
    """
    Render a single recommendation card with approval controls.
    
    Args:
        recommendation: Recommendation dictionary
        index: Index for unique key generation
        show_approval: Whether to show approval buttons
        on_approve: Callback when approved
        on_reject: Callback when rejected
        
    Returns:
        True if approved, False otherwise
    """
    param_name = recommendation.get("parameter_name", "Unknown")
    current_value = recommendation.get("current_value", "N/A")
    recommended_value = recommendation.get("recommended_value", "N/A")
    confidence = recommendation.get("confidence", 0)
    risk_level = recommendation.get("risk_level", "medium")
    reasoning = recommendation.get("reasoning", "")
    expected_improvement = recommendation.get("expected_improvement", 0)
    kpi_name = recommendation.get("kpi_name", "")
    category = recommendation.get("category", "")
    
    # Risk level styling
    risk_colors = {
        "low": (CASSAVA_GREEN, "Low Risk"),
        "medium": (COLORS["warning"], "Medium Risk"),
        "high": (COLORS["error"], "High Risk"),
    }
    risk_color, risk_text = risk_colors.get(risk_level, (COLORS["warning"], "Unknown Risk"))
    
    # Card border color based on risk
    border_color = CASSAVA_GREEN if risk_level == "low" else (
        COLORS["warning"] if risk_level == "medium" else COLORS["error"]
    )
    
    # Confidence styling
    confidence_bg = "rgba(0, 241, 156, 0.2)" if confidence >= 80 else (
        "rgba(245, 158, 11, 0.2)" if confidence >= 60 else "rgba(239, 68, 68, 0.2)"
    )
    confidence_color = CASSAVA_GREEN if confidence >= 80 else (
        COLORS["warning"] if confidence >= 60 else COLORS["error"]
    )
    
    st.markdown(
        f"""
        <div class="recommendation-card" style="border-left-color: {border_color};">
            <div class="recommendation-header">
                <div class="recommendation-title">{param_name}</div>
                <div class="recommendation-confidence" style="background: {confidence_bg}; color: {confidence_color};">
                    {confidence:.0f}% confidence
                </div>
            </div>
            <div class="recommendation-details">
                <div class="recommendation-detail">
                    <span class="label">Current: </span>
                    <span class="value">{current_value}</span>
                </div>
                <div class="recommendation-detail">
                    <span class="label">Recommended: </span>
                    <span class="value" style="color: {CASSAVA_GREEN};">{recommended_value}</span>
                </div>
                <div class="recommendation-detail">
                    <span class="label">Expected Improvement: </span>
                    <span class="value">+{expected_improvement:.1f}%</span>
                </div>
                <div class="recommendation-detail">
                    <span class="label">Risk Level: </span>
                    <span class="value" style="color: {risk_color};">{risk_text}</span>
                </div>
                {f'<div class="recommendation-detail"><span class="label">Target KPI: </span><span class="value">{kpi_name}</span></div>' if kpi_name else ''}
                {f'<div class="recommendation-detail"><span class="label">Category: </span><span class="value">{category.title()}</span></div>' if category else ''}
            </div>
            <div class="recommendation-reasoning">
                <strong>Reasoning:</strong> {reasoning}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    approved = False
    
    if show_approval:
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("✓ Approve", key=f"approve_{index}", type="primary"):
                approved = True
                if on_approve:
                    on_approve(recommendation)
        with col2:
            if st.button("✗ Reject", key=f"reject_{index}"):
                if on_reject:
                    on_reject(recommendation)
    
    return approved


def render_recommendations_list(
    recommendations: list[dict[str, Any]],
    show_approval: bool = True,
    batch_approval: bool = True,
) -> list[dict[str, Any]]:
    """
    Render a list of recommendations with batch approval option.
    
    Args:
        recommendations: List of recommendation dictionaries
        show_approval: Whether to show individual approval buttons
        batch_approval: Whether to show batch approval controls
        
    Returns:
        List of approved recommendations
    """
    if not recommendations:
        st.info("No recommendations available")
        return []
    
    approved_recommendations = []
    
    # Summary header
    total = len(recommendations)
    low_risk = sum(1 for r in recommendations if r.get("risk_level") == "low")
    high_confidence = sum(1 for r in recommendations if r.get("confidence", 0) >= 80)
    
    st.markdown(
        f"""
        <div class="card">
            <div class="card-header">
                <span>💡</span>
                <span>Optimization Recommendations</span>
            </div>
            <div style="display: flex; gap: 20px; color: {COLORS['text_secondary']}; font-size: 0.9rem;">
                <span><strong>{total}</strong> Total</span>
                <span><strong>{low_risk}</strong> Low Risk</span>
                <span><strong>{high_confidence}</strong> High Confidence</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Batch approval controls
    if batch_approval and len(recommendations) > 1:
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 2, 4])
        with col1:
            if st.button("✓ Approve All Low Risk", type="primary"):
                approved_recommendations = [
                    r for r in recommendations if r.get("risk_level") == "low"
                ]
                st.success(f"Approved {len(approved_recommendations)} low-risk recommendations")
        with col2:
            if st.button("✓ Approve All"):
                approved_recommendations = recommendations.copy()
                st.success(f"Approved all {len(approved_recommendations)} recommendations")
    
    # Individual recommendations
    for i, rec in enumerate(recommendations):
        if render_recommendation_card(
            recommendation=rec,
            index=i,
            show_approval=show_approval and not batch_approval,
        ):
            approved_recommendations.append(rec)
    
    return approved_recommendations


def render_approval_panel(
    recommendations: list[dict[str, Any]],
    on_execute: Optional[Callable[[list[dict]], None]] = None,
    on_cancel: Optional[Callable[[], None]] = None,
) -> None:
    """
    Render an approval panel for executing recommendations.
    
    Args:
        recommendations: List of recommendations to approve
        on_execute: Callback when execute is clicked
        on_cancel: Callback when cancel is clicked
    """
    if not recommendations:
        st.warning("No recommendations selected for execution")
        return
    
    # Summary of what will be executed
    st.markdown(
        f"""
        <div class="card" style="border: 2px solid {COLORS['warning']};">
            <div class="card-header" style="color: {COLORS['warning']};">
                <span>⚠️</span>
                <span>Confirm Execution</span>
            </div>
            <p style="color: {COLORS['text_secondary']};">
                You are about to execute <strong>{len(recommendations)}</strong> parameter changes.
                This will modify the network configuration.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Show summary of changes
    st.markdown("**Changes to be applied:**")
    for rec in recommendations:
        risk_emoji = "🟢" if rec.get("risk_level") == "low" else (
            "🟡" if rec.get("risk_level") == "medium" else "🔴"
        )
        st.markdown(
            f"- {risk_emoji} **{rec.get('parameter_name')}**: "
            f"`{rec.get('current_value')}` → `{rec.get('recommended_value')}`"
        )
    
    st.markdown("---")
    
    # Confirmation checkbox
    confirmed = st.checkbox(
        "I understand the risks and want to proceed with these changes",
        key="execution_confirmation",
    )
    
    col1, col2, col3 = st.columns([2, 2, 4])
    with col1:
        execute_disabled = not confirmed
        if st.button(
            "⚡ Execute Changes",
            type="primary",
            disabled=execute_disabled,
        ):
            if on_execute:
                on_execute(recommendations)
    with col2:
        if st.button("Cancel"):
            if on_cancel:
                on_cancel()


def render_execution_results(
    results: list[dict[str, Any]],
) -> None:
    """
    Render the results of recommendation execution.
    
    Args:
        results: List of execution result dictionaries
    """
    if not results:
        return
    
    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]
    
    # Summary
    if failed:
        st.error(f"⚠️ {len(failed)} of {len(results)} changes failed")
    else:
        st.success(f"✅ All {len(results)} changes executed successfully")
    
    # Details
    if successful:
        with st.expander(f"✅ Successful ({len(successful)})", expanded=not failed):
            for r in successful:
                st.markdown(
                    f"- **{r.get('parameter_name')}**: {r.get('message', 'Success')}"
                )
    
    if failed:
        with st.expander(f"❌ Failed ({len(failed)})", expanded=True):
            for r in failed:
                st.markdown(
                    f"- **{r.get('parameter_name')}**: {r.get('error', 'Unknown error')}"
                )


def render_rollback_option(
    executed_changes: list[dict[str, Any]],
    on_rollback: Optional[Callable[[list[dict]], None]] = None,
) -> None:
    """
    Render rollback option for executed changes.
    
    Args:
        executed_changes: List of changes that were executed
        on_rollback: Callback when rollback is requested
    """
    st.markdown(
        f"""
        <div class="card" style="border: 1px solid {COLORS['warning']};">
            <div class="card-header">
                <span>↩️</span>
                <span>Rollback Option</span>
            </div>
            <p style="color: {COLORS['text_secondary']};">
                If the changes are not producing expected results, you can rollback 
                to the previous configuration.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    if st.button("↩️ Rollback All Changes", type="secondary"):
        if on_rollback:
            on_rollback(executed_changes)
