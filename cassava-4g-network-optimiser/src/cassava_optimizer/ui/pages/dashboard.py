"""
Dashboard page for the Cassava 4G Network Optimizer.

Main overview page showing network health, KPIs, and quick actions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import streamlit as st
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

from cassava_optimizer.ui.theme import (
    CASSAVA_GREEN,
    CASSAVA_NAVY,
    CASSAVA_PURPLE,
    COLORS,
    get_custom_css,
    get_plotly_template,
)
from cassava_optimizer.ui.components import (
    render_kpi_card,
    render_kpi_grid,
    render_site_selector,
    render_error_banner,
)
from cassava_optimizer.ui.components.charts import (
    create_kpi_line_chart,
    create_health_radar_chart,
    create_gauge_chart,
)
from cassava_optimizer.services import get_site_service, get_kpi_service
from cassava_optimizer.services.data_importer import CSVDataImporter

logger = logging.getLogger(__name__)

# Auto-refresh interval in milliseconds (60 seconds for active site)
AUTO_REFRESH_INTERVAL_MS = 60000


async def _ensure_data_imported() -> None:
    """Ensure CSV data is imported on first load."""
    if "data_imported" not in st.session_state:
        try:
            importer = CSVDataImporter()
            result = await importer.import_all_csv_files()
            st.session_state["data_imported"] = True
            if result["sites"] > 0:
                logger.info(f"Imported {result['sites']} sites, {result['cells']} cells, {result['kpi_records']} KPIs")
        except Exception as e:
            logger.warning(f"CSV import failed (may already exist): {e}")
            st.session_state["data_imported"] = True


def render_dashboard_page(
    site_service: Any = None,
    kpi_service: Any = None,
) -> None:
    """
    Render the main dashboard page.
    
    Args:
        site_service: Service for site data operations (uses default if None)
        kpi_service: Service for KPI data operations (uses default if None)
    """
    # Use default services if not provided
    if site_service is None:
        site_service = get_site_service()
    if kpi_service is None:
        kpi_service = get_kpi_service()
    
    # Auto-refresh every 60 seconds
    st_autorefresh(interval=AUTO_REFRESH_INTERVAL_MS, key="dashboard_autorefresh")
    
    # Ensure data is imported
    asyncio.run(_ensure_data_imported())
    
    # Apply custom CSS (already includes <style> tags)
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Header
    st.markdown(
        f"""
        <div class="dashboard-header" style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        ">
            <div>
                <h1 style="color: {COLORS['text_primary']}; margin: 0;">
                    📊 Network Dashboard
                </h1>
                <p style="color: {COLORS['text_secondary']}; margin: 4px 0 0 0;">
                    Real-time network health and KPI overview
                </p>
            </div>
            <div style="
                background: {CASSAVA_GREEN}20;
                color: {CASSAVA_GREEN};
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 0.9rem;
            ">
                Last updated: {datetime.now().strftime('%H:%M:%S')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Site selector
    st.markdown("### 🏢 Select Site")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Get sites from service
        try:
            sites = asyncio.run(site_service.list_sites())
            if not sites:
                # No sites in database yet, show info
                st.info("📥 No sites found. Import CSV data or connect to Huawei API.")
                sites = []
        except Exception as e:
            render_error_banner(
                message=f"Failed to load sites: {str(e)}",
                error_type="error",
                title="Data Load Error",
            )
            sites = []
        
        selected_site = render_site_selector(
            sites=sites,
            selected_site=st.session_state.get("selected_site"),
            key="dashboard_site_selector",
        )
        
        if selected_site:
            st.session_state["selected_site"] = selected_site
    
    with col2:
        if st.button("🔄 Refresh", type="secondary", use_container_width=True):
            with st.spinner("Refreshing..."):
                # Clear any cached data
                st.session_state.pop("_kpi_cache", None)
                st.rerun()
    
    st.markdown("---")
    
    # Quick Stats Row
    st.markdown("### 📈 Network Overview")
    
    # Get KPI data - Try live API first, then database
    kpi_data = {}
    kpi_load_error = None
    kpi_source = None
    
    if not selected_site:
        st.warning("⚠️ Select a site to view KPI data")
    else:
        # First try to get live KPI data from Huawei API
        try:
            with st.spinner("Fetching live data from network..."):
                kpi_data = asyncio.run(kpi_service.get_live_kpis_from_api(selected_site))
                if kpi_data:
                    kpi_source = "live"
                    st.success("✅ Connected to live network")
        except Exception as e:
            logger.warning(f"Live API fetch failed: {e}")
        
        # If no live data, try database
        if not kpi_data:
            try:
                kpi_data = asyncio.run(kpi_service.get_site_kpis(selected_site))
                if kpi_data:
                    kpi_source = "database"
            except Exception as e:
                logger.warning(f"Database fetch failed: {e}")
        
        if not kpi_data:
            kpi_load_error = "No KPI data available for this site"
    
    # Show inline warning if no KPI data (not demo data)
    if kpi_load_error:
        st.warning(f"⚠️ {kpi_load_error}")
    
    # KPI targets (used for display even without data)
    kpi_targets = {
        "call_setup_success_rate": 99.0,
        "call_drop_rate": 1.0,
        "handover_success_rate": 98.0,
        "rrc_setup_success_rate": 99.5,
        "erab_setup_success_rate": 99.0,
        "throughput_downlink": 50.0,
    }
    
    # KPI Cards
    col1, col2, col3 = st.columns(3)
    
    kpi_definitions = [
        ("Call Setup Success Rate", "call_setup_success_rate", "%", "📞"),
        ("Call Drop Rate", "call_drop_rate", "%", "📉"),
        ("Handover Success Rate", "handover_success_rate", "%", "🔄"),
        ("RRC Setup Success", "rrc_setup_success_rate", "%", "📶"),
        ("E-RAB Setup Success", "erab_setup_success_rate", "%", "🔗"),
        ("DL Throughput", "throughput_downlink", "Mbps", "⬇️"),
    ]
    
    for i, (name, key, unit, icon) in enumerate(kpi_definitions):
        with [col1, col2, col3][i % 3]:
            data = kpi_data.get(key, {})
            value = data.get("value")
            target = kpi_targets.get(key, 0)
            trend = data.get("trend", "")
            
            # If no value available, show warning card instead
            if value is None:
                st.markdown(
                    f"""
                    <div class="kpi-card" style="
                        background: {COLORS['card_bg']};
                        border: 1px solid {COLORS['warning']}40;
                        border-radius: 12px;
                        padding: 20px;
                        margin-bottom: 16px;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <div style="color: {COLORS['text_secondary']}; font-size: 0.85rem;">
                                    {icon} {name}
                                </div>
                                <div style="color: {COLORS['warning']}; font-size: 1.2rem; font-weight: 500; margin: 8px 0;">
                                    ⚠️ No data
                                </div>
                                <div style="font-size: 0.75rem; color: {COLORS['text_secondary']};">
                                    Check API connection
                                </div>
                            </div>
                        </div>
                        <div style="
                            margin-top: 12px;
                            padding-top: 12px;
                            border-top: 1px solid {COLORS['border']};
                            font-size: 0.75rem;
                            color: {COLORS['text_secondary']};
                        ">
                            Target: {target}{unit}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                continue
            
            # Determine if this is a "lower is better" KPI
            inverse = key in ["call_drop_rate"]
            
            # Calculate status
            if inverse:
                status = "good" if value <= target else "warning"
            else:
                status = "good" if value >= target else "warning"
            
            st.markdown(
                f"""
                <div class="kpi-card" style="
                    background: {COLORS['card_bg']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                    padding: 20px;
                    margin-bottom: 16px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <div style="color: {COLORS['text_secondary']}; font-size: 0.85rem;">
                                {icon} {name}
                            </div>
                            <div style="color: {COLORS['text_primary']}; font-size: 2rem; font-weight: 700; margin: 8px 0;">
                                {value:.1f}<span style="font-size: 1rem; color: {COLORS['text_secondary']};">{unit}</span>
                            </div>
                            <div style="font-size: 0.8rem; color: {CASSAVA_GREEN if '+' in str(trend) else COLORS['error']};">
                                {trend}
                            </div>
                        </div>
                        <div style="
                            width: 12px;
                            height: 12px;
                            border-radius: 50%;
                            background: {CASSAVA_GREEN if status == 'good' else COLORS['warning']};
                        "></div>
                    </div>
                    <div style="
                        margin-top: 12px;
                        padding-top: 12px;
                        border-top: 1px solid {COLORS['border']};
                        font-size: 0.75rem;
                        color: {COLORS['text_secondary']};
                    ">
                        Target: {target}{unit}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    st.markdown("---")
    
    # Charts Row
    st.markdown("### 📊 Trends & Health")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # KPI Trend Chart
        st.markdown(
            f"<div class='card-header'><span>📈</span><span>KPI Trend (24h)</span></div>",
            unsafe_allow_html=True,
        )
        
        # Get real trend data from database
        trend_data = []
        if selected_site:
            try:
                # Get KPI history from service
                trend_data = asyncio.run(kpi_service.get_kpi_history(
                    site_name=selected_site,
                    kpi_name="call_setup_success_rate",
                    hours=24
                ))
            except Exception as e:
                logger.warning(f"Failed to load KPI trend: {e}")
        
        if trend_data:
            fig = create_kpi_line_chart(
                data=trend_data,
                x_field="timestamp",
                y_field="value",
                kpi_name="CSSR (%)",
                target_value=99.0,
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Show warning instead of mock data
            st.markdown(
                f"""
                <div style="
                    background: {COLORS['card_bg']};
                    border: 1px solid {COLORS['warning']}40;
                    border-radius: 12px;
                    padding: 40px;
                    text-align: center;
                    height: 260px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                ">
                    <div style="font-size: 2rem; margin-bottom: 8px;">⚠️</div>
                    <div style="color: {COLORS['warning']}; font-weight: 500;">No Trend Data Available</div>
                    <div style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin-top: 8px;">
                        Select a site and ensure KPI data is being collected
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    with col2:
        # Health Radar Chart
        st.markdown(
            f"<div class='card-header'><span>🎯</span><span>Health Score</span></div>",
            unsafe_allow_html=True,
        )
        
        # Calculate health scores from real KPI data
        health_scores = {}
        if kpi_data:
            # Map KPIs to health categories
            if kpi_data.get("call_setup_success_rate", {}).get("value"):
                health_scores["Accessibility"] = kpi_data["call_setup_success_rate"]["value"]
            if kpi_data.get("call_drop_rate", {}).get("value"):
                # Invert call drop rate (lower is better, so 100 - rate)
                health_scores["Retainability"] = 100 - kpi_data["call_drop_rate"]["value"]
            if kpi_data.get("handover_success_rate", {}).get("value"):
                health_scores["Mobility"] = kpi_data["handover_success_rate"]["value"]
            if kpi_data.get("throughput_downlink", {}).get("value"):
                # Normalize throughput to percentage of target
                target = kpi_targets.get("throughput_downlink", 50.0)
                throughput = kpi_data["throughput_downlink"]["value"]
                health_scores["Throughput"] = min(100, (throughput / target) * 100)
            if kpi_data.get("erab_setup_success_rate", {}).get("value"):
                health_scores["Availability"] = kpi_data["erab_setup_success_rate"]["value"]
        
        if health_scores:
            fig = create_health_radar_chart(
                kpi_values=health_scores,
                kpi_targets={k: 95 for k in health_scores},
                title="",
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Show warning instead of hardcoded scores
            st.markdown(
                f"""
                <div style="
                    background: {COLORS['card_bg']};
                    border: 1px solid {COLORS['warning']}40;
                    border-radius: 12px;
                    padding: 40px;
                    text-align: center;
                    height: 260px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                ">
                    <div style="font-size: 2rem; margin-bottom: 8px;">⚠️</div>
                    <div style="color: {COLORS['warning']}; font-weight: 500;">No Health Data Available</div>
                    <div style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin-top: 8px;">
                        KPI data required to calculate health scores
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Run Analysis", type="primary", use_container_width=True):
            st.session_state["navigate_to"] = "optimization"
            st.rerun()
    
    with col2:
        if st.button("📜 View History", type="secondary", use_container_width=True):
            st.session_state["navigate_to"] = "history"
            st.rerun()
    
    with col3:
        if st.button("📊 Export Report", type="secondary", use_container_width=True):
            with st.spinner("Generating report..."):
                st.toast("📊 Report export coming soon!", icon="ℹ️")
    
    with col4:
        if st.button("⚙️ Settings", type="secondary", use_container_width=True):
            st.session_state["navigate_to"] = "settings"
            st.rerun()
    
    # Recent Activity - load from database
    st.markdown("---")
    st.markdown("### 📋 Recent Activity")
    
    # Get recent activities from optimization history
    activities = []
    try:
        from cassava_optimizer.services import get_optimization_service
        opt_service = get_optimization_service()
        recent_runs = asyncio.run(opt_service.get_recent_optimization_runs(limit=5))
        
        for run in recent_runs:
            activities.append({
                "time": run.get("completed_at", run.get("started_at", "")).strftime("%H:%M") if hasattr(run.get("completed_at", run.get("started_at", "")), "strftime") else str(run.get("completed_at", run.get("started_at", ""))),
                "action": f"Optimization {run.get('status', 'completed')}",
                "site": run.get("site_name", "Unknown"),
                "status": "success" if run.get("status") == "completed" else "warning",
            })
    except Exception as e:
        logger.debug(f"No recent activities: {e}")
    
    if activities:
        for activity in activities:
            status_color = CASSAVA_GREEN if activity["status"] == "success" else COLORS["warning"]
            st.markdown(
                f"""
                <div style="
                    display: flex;
                    align-items: center;
                    padding: 12px;
                    background: {COLORS['card_bg']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 8px;
                    margin-bottom: 8px;
                ">
                    <div style="
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background: {status_color};
                        margin-right: 12px;
                    "></div>
                    <div style="flex: 1;">
                        <span style="color: {COLORS['text_primary']};">{activity['action']}</span>
                        <span style="color: {COLORS['text_secondary']}; margin-left: 8px;">• {activity['site']}</span>
                    </div>
                    <div style="color: {COLORS['text_secondary']}; font-size: 0.85rem;">
                        {activity['time']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        # Show info message instead of mock data
        st.markdown(
            f"""
            <div style="
                background: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 24px;
                text-align: center;
            ">
                <div style="color: {COLORS['text_secondary']};">
                    📭 No recent activity
                </div>
                <div style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin-top: 8px;">
                    Run an optimization to see activity here
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
