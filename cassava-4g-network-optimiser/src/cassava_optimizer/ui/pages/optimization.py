"""
Optimization page for the Cassava 4G Network Optimizer.

Handles the optimization workflow with agent progress tracking,
recommendations display, and execution controls.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

import streamlit as st

from cassava_optimizer.ui.theme import (
    CASSAVA_GREEN,
    CASSAVA_NAVY,
    CASSAVA_PURPLE,
    COLORS,
    get_custom_css,
)
from cassava_optimizer.ui.components import (
    render_site_selector,
    render_agent_progress,
    render_workflow_timeline,
    render_recommendations_list,
    render_approval_panel,
    render_execution_results,
    render_command_list,
    render_error_banner,
)
from cassava_optimizer.services import get_site_service

logger = logging.getLogger(__name__)


def render_optimization_page(
    optimization_service: Any = None,
    site_service: Any = None,
) -> None:
    """
    Render the optimization workflow page.
    
    Args:
        optimization_service: Service for running optimizations
        site_service: Service for site data operations (uses default if None)
    """
    # Use default site service if not provided
    if site_service is None:
        site_service = get_site_service()
    
    # Apply custom CSS (already includes <style> tags)
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Header
    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <h1 style="color: {COLORS['text_primary']}; margin: 0;">
                🚀 Network Optimization
            </h1>
            <p style="color: {COLORS['text_secondary']}; margin: 4px 0 0 0;">
                AI-powered parameter optimization workflow
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Initialize session state
    if "optimization_state" not in st.session_state:
        st.session_state.optimization_state = "idle"  # idle, running, complete, error
    if "optimization_results" not in st.session_state:
        st.session_state.optimization_results = None
    if "agent_statuses" not in st.session_state:
        st.session_state.agent_statuses = {}
    if "approved_recommendations" not in st.session_state:
        st.session_state.approved_recommendations = []
    
    # Site Selection Section
    st.markdown("### 🏢 Site Selection")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Get sites from service
        try:
            sites = asyncio.run(site_service.list_sites())
            if not sites:
                st.info("📥 No sites found. Import CSV data or connect to Huawei API.")
                sites = []
        except Exception as e:
            render_error_banner(f"Failed to load sites: {e}")
            sites = []
        
        selected_site = render_site_selector(
            sites=sites,
            selected_site=st.session_state.get("selected_site"),
            key="optimization_site_selector",
        )
        
        if selected_site:
            st.session_state["selected_site"] = selected_site
    
    with col2:
        optimization_disabled = (
            not selected_site or 
            st.session_state.optimization_state == "running"
        )
        
        if st.button(
            "▶️ Start Optimization",
            type="primary",
            disabled=optimization_disabled,
            use_container_width=True,
        ):
            st.session_state.optimization_state = "running"
            st.session_state.agent_statuses = {
                "data_collector": "running",
                "analyzer": "pending",
                "strategy_planner": "pending",
                "validator": "pending",
                "commander": "pending",
                "reviewer": "pending",
            }
            st.rerun()
    
    st.markdown("---")
    
    # Natural Language Query Input
    st.markdown("### 💬 Natural Language Query")
    st.markdown(
        f"""
        <p style="color: {COLORS['text_secondary']}; font-size: 0.9rem; margin-bottom: 12px;">
            Describe what you want to optimize in plain English. The AI will analyze your request
            and suggest appropriate parameter changes.
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    # Example queries for user guidance
    example_queries = [
        "Improve RACH success rate for this site",
        "Fix high DL BLER on cells 1-3",
        "Optimize throughput for better user experience",
        "Reduce PDCCH CCE congestion during peak hours",
        "Address poor uplink quality at cell edge",
    ]
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_query = st.text_area(
            "Enter your optimization request",
            placeholder="e.g., 'Improve RACH success rate' or 'Fix high DL BLER on cells 1-3'",
            key="optimization_query",
            height=100,
            label_visibility="collapsed",
        )
    
    with col2:
        st.markdown(
            f"""
            <div style="
                background: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
                font-size: 0.8rem;
            ">
                <strong style="color: {COLORS['text_primary']};">Examples:</strong>
                <ul style="color: {COLORS['text_secondary']}; margin: 8px 0 0 0; padding-left: 16px;">
                    {''.join(f'<li style="margin: 4px 0;">{q}</li>' for q in example_queries[:3])}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # Store query in session state for workflow
    if user_query:
        st.session_state["user_query"] = user_query
    
    st.markdown("---")
    
    # Optimization Configuration
    if st.session_state.optimization_state == "idle":
        st.markdown("### ⚙️ Optimization Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(
                f"""
                <div class="card" style="
                    background: {COLORS['card_bg']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                    padding: 20px;
                ">
                    <h4 style="color: {COLORS['text_primary']}; margin-top: 0;">
                        🎯 Target KPIs
                    </h4>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            kpi_options = [
                "Call Setup Success Rate",
                "Call Drop Rate",
                "Handover Success Rate",
                "RRC Setup Success Rate",
                "E-RAB Setup Success Rate",
                "Throughput (DL/UL)",
            ]
            
            selected_kpis = st.multiselect(
                "Select KPIs to optimize",
                options=kpi_options,
                default=["Call Setup Success Rate", "Call Drop Rate"],
                key="target_kpis",
            )
        
        with col2:
            st.markdown(
                f"""
                <div class="card" style="
                    background: {COLORS['card_bg']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                    padding: 20px;
                ">
                    <h4 style="color: {COLORS['text_primary']}; margin-top: 0;">
                        ⚠️ Risk Settings
                    </h4>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            risk_tolerance = st.select_slider(
                "Risk Tolerance",
                options=["Low", "Medium", "High"],
                value="Medium",
                key="risk_tolerance",
            )
            
            auto_approve_low_risk = st.checkbox(
                "Auto-approve low-risk changes",
                value=False,
                key="auto_approve",
            )
            
            require_backup = st.checkbox(
                "Require configuration backup before changes",
                value=True,
                key="require_backup",
            )
    
    # Running State - Agent Progress
    elif st.session_state.optimization_state == "running":
        st.markdown("### 🤖 Agent Progress")
        
        # Agent progress display
        agents = [
            {
                "name": "Data Collector",
                "id": "data_collector",
                "description": "Collecting KPI data from Huawei iMaster MAE",
                "icon": "📥",
            },
            {
                "name": "Analyzer",
                "id": "analyzer",
                "description": "Analyzing KPI trends and identifying issues",
                "icon": "🔍",
            },
            {
                "name": "Strategy Planner",
                "id": "strategy_planner",
                "description": "Planning optimization strategy",
                "icon": "📋",
            },
            {
                "name": "Validator",
                "id": "validator",
                "description": "Validating proposed changes",
                "icon": "✅",
            },
            {
                "name": "Commander",
                "id": "commander",
                "description": "Generating MML commands",
                "icon": "⚡",
            },
            {
                "name": "Reviewer",
                "id": "reviewer",
                "description": "Reviewing execution results",
                "icon": "📊",
            },
        ]
        
        for agent in agents:
            status = st.session_state.agent_statuses.get(agent["id"], "pending")
            
            status_colors = {
                "pending": COLORS["text_secondary"],
                "running": CASSAVA_PURPLE,
                "complete": CASSAVA_GREEN,
                "error": COLORS["error"],
            }
            status_icons = {
                "pending": "⏳",
                "running": "🔄",
                "complete": "✅",
                "error": "❌",
            }
            
            color = status_colors.get(status, COLORS["text_secondary"])
            icon = status_icons.get(status, "⏳")
            
            st.markdown(
                f"""
                <div style="
                    display: flex;
                    align-items: center;
                    padding: 16px;
                    background: {COLORS['card_bg']};
                    border: 1px solid {color}40;
                    border-left: 4px solid {color};
                    border-radius: 8px;
                    margin-bottom: 12px;
                ">
                    <div style="font-size: 1.5rem; margin-right: 16px;">
                        {agent['icon']}
                    </div>
                    <div style="flex: 1;">
                        <div style="color: {COLORS['text_primary']}; font-weight: 600;">
                            {agent['name']}
                        </div>
                        <div style="color: {COLORS['text_secondary']}; font-size: 0.85rem;">
                            {agent['description']}
                        </div>
                    </div>
                    <div style="color: {color}; font-weight: 500;">
                        {icon} {status.title()}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        # Simulate progress (in real app, this would be driven by actual workflow)
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("⏸️ Cancel", type="secondary"):
                st.session_state.optimization_state = "idle"
                st.session_state.agent_statuses = {}
                st.rerun()
        
        # Info message - no demo button
        with col1:
            st.info("⏳ Waiting for optimization workflow to complete...")
    
    # Complete State - Recommendations
    elif st.session_state.optimization_state == "complete":
        st.markdown("### ✅ Optimization Complete")
        
        results = st.session_state.optimization_results or {}
        analysis = results.get("analysis_summary", {})
        recommendations = results.get("recommendations", [])
        
        # Check if we have actual results
        if not results or not recommendations:
            # Show empty state - no mock recommendations
            st.markdown(
                f"""
                <div style="
                    background: {COLORS['card_bg']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                    padding: 48px;
                    text-align: center;
                ">
                    <div style="font-size: 3rem; margin-bottom: 16px;">📋</div>
                    <div style="color: {COLORS['text_primary']}; font-size: 1.2rem; font-weight: 500;">
                        No Recommendations Generated
                    </div>
                    <div style="color: {COLORS['text_secondary']}; margin-top: 8px;">
                        The analysis did not produce any parameter recommendations.
                        This may indicate the network is already optimized for the selected KPIs.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            if st.button("🔄 Run Again", type="primary"):
                st.session_state.optimization_state = "idle"
                st.session_state.optimization_results = None
                st.session_state.approved_recommendations = []
                st.rerun()
        else:
            # Analysis Summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Issues Found",
                    value=analysis.get("issues_found", 0),
                )
            with col2:
                st.metric(
                    label="Optimization Potential",
                    value=analysis.get("optimization_potential", "N/A"),
                )
            with col3:
                st.metric(
                    label="Estimated Improvement",
                    value=analysis.get("estimated_improvement", "N/A"),
                )
            
            st.markdown("---")
            
            # Recommendations
            st.markdown("### 💡 Recommendations")
            
            approved = render_recommendations_list(
                recommendations=recommendations,
                show_approval=True,
                batch_approval=True,
            )
            
            if approved:
                st.session_state.approved_recommendations = approved
            
            st.markdown("---")
            
            # Execution Section
            if st.session_state.approved_recommendations:
                st.markdown("### ⚡ Execute Changes")
                
                render_approval_panel(
                    recommendations=st.session_state.approved_recommendations,
                    on_execute=lambda recs: st.success(f"Executing {len(recs)} changes..."),
                    on_cancel=lambda: st.session_state.approved_recommendations.clear(),
                )
            
            # Actions
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("🔄 Run Again", type="primary"):
                    st.session_state.optimization_state = "idle"
                    st.session_state.optimization_results = None
                    st.session_state.approved_recommendations = []
                    st.rerun()
            
            with col2:
                if st.button("📊 Export Report", type="secondary"):
                    st.info("Report export - connect to report service")
    
    # Error State
    elif st.session_state.optimization_state == "error":
        render_error_banner(
            message="Optimization workflow failed. Please check the logs and try again.",
            error_type="error",
            title="Optimization Error",
        )
        
        if st.button("🔄 Retry", type="primary"):
            st.session_state.optimization_state = "idle"
            st.rerun()
