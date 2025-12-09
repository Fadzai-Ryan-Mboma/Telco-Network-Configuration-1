"""
History page for the Cassava 4G Network Optimizer.

Displays optimization history, command logs, and KPI trends over time.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional

import streamlit as st
import plotly.graph_objects as go

from cassava_optimizer.ui.theme import (
    CASSAVA_GREEN,
    CASSAVA_NAVY,
    CASSAVA_PURPLE,
    COLORS,
    get_custom_css,
)
from cassava_optimizer.ui.components import (
    render_site_selector,
    render_command_list,
    render_error_banner,
)
from cassava_optimizer.ui.components.charts import (
    create_kpi_line_chart,
    create_comparison_bar_chart,
)


def render_history_page(
    history_service: Any = None,
    site_service: Any = None,
) -> None:
    """
    Render the history and logs page.
    
    Args:
        history_service: Service for retrieving historical data
        site_service: Service for site data operations
    """
    # Apply custom CSS (already includes <style> tags)
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Header
    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <h1 style="color: {COLORS['text_primary']}; margin: 0;">
                📜 Optimization History
            </h1>
            <p style="color: {COLORS['text_secondary']}; margin: 4px 0 0 0;">
                View past optimizations, command logs, and KPI trends
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Filters
    st.markdown("### 🔍 Filters")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        # Get sites from service - NO FALLBACK MOCK DATA
        sites = []
        if site_service:
            try:
                sites = asyncio.run(site_service.list_sites())
            except Exception as e:
                st.warning(f"⚠️ Failed to load sites: {e}")
        
        if sites:
            site_names = ["All Sites"] + [s.get("name", "") for s in sites]
        else:
            site_names = ["All Sites"]
        
        selected_site = st.selectbox(
            "Site",
            options=site_names,
            index=0,
            key="history_site_filter",
        )
    
    with col2:
        date_range = st.selectbox(
            "Time Range",
            options=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Custom"],
            index=1,
            key="history_date_range",
        )
    
    with col3:
        status_filter = st.multiselect(
            "Status",
            options=["Success", "Failed", "Rolled Back"],
            default=["Success", "Failed"],
            key="history_status_filter",
        )
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", type="secondary"):
            st.rerun()
    
    st.markdown("---")
    
    # Tabs for different history views
    tab1, tab2, tab3 = st.tabs(["📊 Optimization Runs", "⚡ Command Log", "📈 KPI History"])
    
    # Tab 1: Optimization Runs
    with tab1:
        st.markdown("### Recent Optimization Runs")
        
        # Load optimization history from database - NO MOCK DATA
        optimization_history = []
        try:
            from cassava_optimizer.services import get_optimization_service
            opt_service = get_optimization_service()
            
            # Apply filters
            site_filter = None if selected_site == "All Sites" else selected_site
            optimization_history = asyncio.run(opt_service.get_optimization_history(
                site_name=site_filter,
                limit=20
            ))
        except Exception as e:
            st.warning(f"⚠️ Failed to load optimization history: {e}")
        
        if not optimization_history:
            # Show empty state instead of mock data
            st.markdown(
                f"""
                <div style="
                    background: {COLORS['card_bg']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                    padding: 48px;
                    text-align: center;
                ">
                    <div style="font-size: 3rem; margin-bottom: 16px;">📭</div>
                    <div style="color: {COLORS['text_primary']}; font-size: 1.2rem; font-weight: 500;">
                        No Optimization History
                    </div>
                    <div style="color: {COLORS['text_secondary']}; margin-top: 8px;">
                        Run an optimization from the Optimization page to see history here
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # Summary metrics from real data
            col1, col2, col3, col4 = st.columns(4)
            
            total_runs = len(optimization_history)
            successful = sum(1 for o in optimization_history if o.get("status") == "completed")
            failed = sum(1 for o in optimization_history if o.get("status") == "failed")
            rolled_back = sum(1 for o in optimization_history if o.get("status") == "rolled_back")
            
            with col1:
                st.metric("Total Runs", total_runs)
            with col2:
                success_rate = f"{(successful/total_runs*100):.0f}%" if total_runs > 0 else "N/A"
                st.metric("Successful", successful, delta=success_rate)
            with col3:
                st.metric("Failed", failed)
            with col4:
                st.metric("Rolled Back", rolled_back)
            
            st.markdown("---")
            
            # History table from real data
            for opt in optimization_history:
                status = opt.get("status", "unknown")
                status_colors = {
                    "completed": CASSAVA_GREEN,
                    "success": CASSAVA_GREEN,
                    "failed": COLORS["error"],
                    "rolled_back": COLORS["warning"],
                    "running": CASSAVA_PURPLE,
                }
                status_icons = {
                    "completed": "✅",
                    "success": "✅",
                    "failed": "❌",
                    "rolled_back": "↩️",
                    "running": "🔄",
                }
                
                color = status_colors.get(status, COLORS["text_secondary"])
                icon = status_icons.get(status, "❓")
                
                # Format timestamp
                timestamp = opt.get("started_at", opt.get("timestamp", ""))
                if hasattr(timestamp, "strftime"):
                    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M')
                else:
                    timestamp_str = str(timestamp)[:16]
                
                # Get other fields with defaults
                opt_id = opt.get("id", opt.get("run_id", "N/A"))
                site_name = opt.get("site_name", opt.get("site", "Unknown"))
                changes = opt.get("changes_count", opt.get("changes", 0))
                improvement = opt.get("improvement", "N/A")
                duration = opt.get("duration", "N/A")
                
                st.markdown(
                    f"""
                    <div style="
                        display: flex;
                        align-items: center;
                        padding: 16px;
                        background: {COLORS['card_bg']};
                        border: 1px solid {COLORS['border']};
                        border-left: 4px solid {color};
                        border-radius: 8px;
                        margin-bottom: 12px;
                    ">
                        <div style="width: 100px; color: {COLORS['text_secondary']}; font-family: monospace;">
                            {opt_id}
                        </div>
                        <div style="width: 120px; color: {COLORS['text_primary']};">
                            📡 {site_name}
                        </div>
                        <div style="width: 180px; color: {COLORS['text_secondary']}; font-size: 0.9rem;">
                            {timestamp_str}
                        </div>
                        <div style="flex: 1; display: flex; gap: 24px;">
                            <span style="color: {COLORS['text_secondary']};">
                                📝 {changes} changes
                            </span>
                            <span style="color: {CASSAVA_GREEN if '+' in str(improvement) else COLORS['text_secondary']};">
                                {improvement}
                            </span>
                            <span style="color: {COLORS['text_secondary']};">
                                ⏱️ {duration}
                        </span>
                    </div>
                    <div style="color: {color}; font-weight: 500;">
                        {icon} {opt['status'].replace('_', ' ').title()}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        # Pagination
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.button("← Previous", disabled=True)
        with col2:
            st.markdown(
                f"<div style='text-align: center; color: {COLORS['text_secondary']};'>Page 1 of 1</div>",
                unsafe_allow_html=True,
            )
        with col3:
            st.button("Next →", disabled=True)
    
    # Tab 2: Command Log
    with tab2:
        st.markdown("### MML Command History")
        
        # Load command log from database - NO MOCK DATA
        command_log = []
        try:
            from cassava_optimizer.services import get_command_service
            cmd_service = get_command_service()
            
            # Apply filters
            site_filter = None if selected_site == "All Sites" else selected_site
            command_log = asyncio.run(cmd_service.get_command_history(
                site_name=site_filter,
                limit=20
            ))
        except Exception as e:
            st.warning(f"⚠️ Failed to load command history: {e}")
        
        if command_log:
            render_command_list(commands=command_log, show_timeline=True)
        else:
            # Show empty state instead of mock data
            st.markdown(
                f"""
                <div style="
                    background: {COLORS['card_bg']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                    padding: 48px;
                    text-align: center;
                ">
                    <div style="font-size: 3rem; margin-bottom: 16px;">⚡</div>
                    <div style="color: {COLORS['text_primary']}; font-size: 1.2rem; font-weight: 500;">
                        No Command History
                    </div>
                    <div style="color: {COLORS['text_secondary']}; margin-top: 8px;">
                        MML commands will appear here after optimization runs
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    # Tab 3: KPI History
    with tab3:
        st.markdown("### KPI Trends Over Time")
        
        # KPI selector
        kpi_options = [
            "Call Setup Success Rate",
            "Call Drop Rate",
            "Handover Success Rate",
            "RRC Setup Success Rate",
            "E-RAB Setup Success Rate",
            "DL Throughput",
        ]
        
        # Map display names to DB field names
        kpi_field_map = {
            "Call Setup Success Rate": "call_setup_success_rate",
            "Call Drop Rate": "call_drop_rate",
            "Handover Success Rate": "handover_success_rate",
            "RRC Setup Success Rate": "rrc_setup_success_rate",
            "E-RAB Setup Success Rate": "erab_setup_success_rate",
            "DL Throughput": "throughput_downlink",
        }
        
        selected_kpi = st.selectbox(
            "Select KPI",
            options=kpi_options,
            index=0,
            key="history_kpi_selector",
        )
        
        # Load real KPI trend data from database - NO MOCK DATA
        trend_data = []
        try:
            from cassava_optimizer.services import get_kpi_service
            kpi_service = get_kpi_service()
            
            # Get site for query
            site_for_query = None if selected_site == "All Sites" else selected_site
            if site_for_query:
                kpi_field = kpi_field_map.get(selected_kpi, "call_setup_success_rate")
                trend_data = asyncio.run(kpi_service.get_kpi_history(
                    site_name=site_for_query,
                    kpi_name=kpi_field,
                    hours=168  # 7 days
                ))
        except Exception as e:
            st.warning(f"⚠️ Failed to load KPI history: {e}")
        
        # Create chart
        target_values = {
            "Call Setup Success Rate": 99.0,
            "Call Drop Rate": 1.0,
            "Handover Success Rate": 98.0,
            "RRC Setup Success Rate": 99.5,
            "E-RAB Setup Success Rate": 99.0,
            "DL Throughput": 50.0,
        }
        
        if trend_data:
            fig = create_kpi_line_chart(
                data=trend_data,
                x_field="timestamp",
                y_field="value",
                kpi_name=selected_kpi,
                target_value=target_values.get(selected_kpi),
                height=400,
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistics from real data
            st.markdown("### 📊 Statistics")
            
            values = [d["value"] for d in trend_data if d.get("value") is not None]
            
            if values:
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Current", f"{values[-1]:.2f}")
                with col2:
                    st.metric("Average", f"{sum(values)/len(values):.2f}")
                with col3:
                    st.metric("Min", f"{min(values):.2f}")
                with col4:
                    st.metric("Max", f"{max(values):.2f}")
                with col5:
                    change = values[-1] - values[0]
                    st.metric(
                        "Change",
                        f"{change:+.2f}",
                        delta=f"{(change/values[0]*100):+.1f}%" if values[0] != 0 else "N/A",
                    )
        else:
            # Show empty state instead of mock data
            st.markdown(
                f"""
                <div style="
                    background: {COLORS['card_bg']};
                    border: 1px solid {COLORS['warning']}40;
                    border-radius: 12px;
                    padding: 48px;
                    text-align: center;
                ">
                    <div style="font-size: 3rem; margin-bottom: 16px;">📈</div>
                    <div style="color: {COLORS['text_primary']}; font-size: 1.2rem; font-weight: 500;">
                        No KPI History Available
                    </div>
                    <div style="color: {COLORS['text_secondary']}; margin-top: 8px;">
                        {f'Select a specific site to view KPI trends' if selected_site == 'All Sites' else 'No historical data available for this site'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        # Optimization markers - load from DB
        st.markdown("---")
        st.markdown("### 🎯 Optimization Events")
        
        # Get recent optimization events from database
        opt_events = []
        try:
            from cassava_optimizer.services import get_optimization_service
            opt_service = get_optimization_service()
            site_for_query = None if selected_site == "All Sites" else selected_site
            opt_events = asyncio.run(opt_service.get_recent_optimization_runs(
                site_name=site_for_query,
                limit=5
            ))
        except Exception as e:
            pass  # Silently fail, will show empty state
        
        if opt_events:
            events_html = ""
            for event in opt_events:
                opt_id = event.get("id", event.get("run_id", "N/A"))
                timestamp = event.get("started_at", event.get("timestamp", ""))
                
                # Format time ago
                if hasattr(timestamp, "strftime"):
                    delta = datetime.now() - timestamp
                    if delta.days > 0:
                        time_ago = f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
                    elif delta.seconds // 3600 > 0:
                        hours = delta.seconds // 3600
                        time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
                    else:
                        mins = delta.seconds // 60
                        time_ago = f"{mins} minute{'s' if mins > 1 else ''} ago"
                else:
                    time_ago = str(timestamp)[:16]
                
                events_html += f"""
                <div style="
                    background: {CASSAVA_GREEN}20;
                    border: 1px solid {CASSAVA_GREEN};
                    border-radius: 8px;
                    padding: 12px 16px;
                ">
                    <span style="color: {CASSAVA_GREEN};">🎯</span>
                    <span style="color: {COLORS['text_primary']};">Optimization {opt_id}</span>
                    <span style="color: {COLORS['text_secondary']};">• {time_ago}</span>
                </div>
                """
            
            st.markdown(
                f"""
                <div style="
                    display: flex;
                    gap: 16px;
                    flex-wrap: wrap;
                ">
                    {events_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="
                    color: {COLORS['text_secondary']};
                    text-align: center;
                    padding: 16px;
                ">
                    No optimization events in the selected period
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        # Export options
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            if st.button("📥 Export CSV", type="secondary"):
                st.info("Export to CSV - connect to export service")
        
        with col2:
            if st.button("📊 Export Chart", type="secondary"):
                st.info("Export chart as image - connect to export service")
