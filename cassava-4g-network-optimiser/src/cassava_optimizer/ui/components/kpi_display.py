"""
KPI display components for the Streamlit UI.

Renders KPI cards, grids, and charts with appropriate formatting
and color coding based on thresholds.
"""

from typing import Any, Optional

import streamlit as st
import plotly.graph_objects as go

from cassava_optimizer.domain.kpi_definitions import get_kpi_definition
from cassava_optimizer.ui.theme import COLORS, CASSAVA_GREEN, CASSAVA_NAVY
from cassava_optimizer.utils.helpers import format_kpi_value


def get_kpi_status_color(value: float, kpi_name: str) -> str:
    """Determine the color for a KPI value based on thresholds."""
    kpi_def = get_kpi_definition(kpi_name)
    
    if not kpi_def:
        return CASSAVA_GREEN
    
    if kpi_def.higher_is_better:
        if value >= kpi_def.target:
            return COLORS["success"]
        elif value >= kpi_def.warning_threshold:
            return COLORS["warning"]
        else:
            return COLORS["error"]
    else:
        if value <= kpi_def.target:
            return COLORS["success"]
        elif value <= kpi_def.warning_threshold:
            return COLORS["warning"]
        else:
            return COLORS["error"]


def render_kpi_card(
    kpi_name: str,
    value: float,
    trend_value: Optional[float] = None,
    compact: bool = False,
) -> None:
    """
    Render a single KPI card.
    
    Args:
        kpi_name: Name of the KPI
        value: Current KPI value
        trend_value: Optional trend percentage
        compact: Use compact layout
    """
    kpi_def = get_kpi_definition(kpi_name)
    display_name = kpi_def.display_name if kpi_def else kpi_name.replace("_", " ").title()
    color = get_kpi_status_color(value, kpi_name)
    formatted_value = format_kpi_value(value, kpi_name)
    
    # Determine trend indicator
    trend_html = ""
    if trend_value is not None:
        if trend_value > 0:
            trend_class = "up" if (kpi_def and kpi_def.higher_is_better) else "down"
            trend_icon = "↑"
        elif trend_value < 0:
            trend_class = "down" if (kpi_def and kpi_def.higher_is_better) else "up"
            trend_icon = "↓"
        else:
            trend_class = ""
            trend_icon = "→"
        trend_html = f'<div class="kpi-trend {trend_class}">{trend_icon} {abs(trend_value):.1f}%</div>'
    
    padding = "0.75rem" if compact else "1rem"
    
    st.markdown(
        f"""
        <div class="kpi-card" style="padding: {padding};">
            <div class="kpi-value" style="color: {color};">{formatted_value}</div>
            <div class="kpi-label">{display_name}</div>
            {trend_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_grid(
    kpis: dict[str, float],
    trends: Optional[dict[str, float]] = None,
    columns: int = 4,
) -> None:
    """
    Render a grid of KPI cards.
    
    Args:
        kpis: Dictionary of KPI name -> value
        trends: Optional dictionary of KPI name -> trend percentage
        columns: Number of columns in the grid
    """
    trends = trends or {}
    kpi_list = list(kpis.items())
    
    # Create rows
    for i in range(0, len(kpi_list), columns):
        cols = st.columns(columns)
        for j, col in enumerate(cols):
            if i + j < len(kpi_list):
                kpi_name, value = kpi_list[i + j]
                with col:
                    render_kpi_card(
                        kpi_name=kpi_name,
                        value=value,
                        trend_value=trends.get(kpi_name),
                    )


def render_kpi_trend_chart(
    historical_data: dict[str, list[dict[str, Any]]],
    selected_kpis: Optional[list[str]] = None,
    height: int = 400,
) -> None:
    """
    Render a line chart showing KPI trends over time.
    
    Args:
        historical_data: Dictionary of KPI name -> list of {timestamp, value}
        selected_kpis: Optional list of KPIs to display
        height: Chart height in pixels
    """
    if not historical_data:
        st.info("No historical data available")
        return
    
    fig = go.Figure()
    
    # Color palette for lines
    colors = [
        CASSAVA_GREEN,
        "#3B82F6",
        "#EC4899",
        "#F59E0B",
        "#8B5CF6",
        "#6366F1",
    ]
    
    for i, (kpi_name, data_points) in enumerate(historical_data.items()):
        if selected_kpis and kpi_name not in selected_kpis:
            continue
        
        if not data_points:
            continue
        
        timestamps = [p.get("timestamp") for p in data_points]
        values = [p.get("value") for p in data_points]
        
        kpi_def = get_kpi_definition(kpi_name)
        display_name = kpi_def.display_name if kpi_def else kpi_name.replace("_", " ").title()
        
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=values,
                name=display_name,
                mode="lines+markers",
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=4),
                hovertemplate=f"<b>{display_name}</b><br>Value: %{{y:.2f}}<br>Time: %{{x}}<extra></extra>",
            )
        )
    
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_primary"]),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor=COLORS["border"],
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLORS["border"],
            tickfont=dict(size=10),
        ),
        hovermode="x unified",
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_health_gauge(
    score: float,
    title: str = "Network Health Score",
    height: int = 250,
) -> None:
    """
    Render a gauge chart showing overall health score.
    
    Args:
        score: Health score (0-100)
        title: Chart title
        height: Chart height in pixels
    """
    # Determine color based on score
    if score >= 90:
        color = COLORS["success"]
        status = "Excellent"
    elif score >= 75:
        color = CASSAVA_GREEN
        status = "Good"
    elif score >= 50:
        color = COLORS["warning"]
        status = "Fair"
    elif score >= 25:
        color = "#F97316"
        status = "Poor"
    else:
        color = COLORS["error"]
        status = "Critical"
    
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=score,
            title=dict(
                text=f"<b>{title}</b><br><span style='font-size:0.9em;color:{COLORS['text_secondary']}'>{status}</span>",
                font=dict(size=16, color=COLORS["text_primary"]),
            ),
            number=dict(
                font=dict(size=40, color=color),
                suffix="%",
            ),
            gauge=dict(
                axis=dict(
                    range=[0, 100],
                    tickwidth=1,
                    tickcolor=COLORS["border"],
                    tickfont=dict(color=COLORS["text_secondary"]),
                ),
                bar=dict(color=color, thickness=0.7),
                bgcolor=COLORS["surface"],
                borderwidth=2,
                bordercolor=COLORS["border"],
                steps=[
                    dict(range=[0, 25], color="rgba(239, 68, 68, 0.2)"),
                    dict(range=[25, 50], color="rgba(249, 115, 22, 0.2)"),
                    dict(range=[50, 75], color="rgba(245, 158, 11, 0.2)"),
                    dict(range=[75, 90], color="rgba(0, 241, 156, 0.15)"),
                    dict(range=[90, 100], color="rgba(0, 241, 156, 0.3)"),
                ],
                threshold=dict(
                    line=dict(color=COLORS["text_primary"], width=2),
                    thickness=0.75,
                    value=score,
                ),
            ),
        )
    )
    
    fig.update_layout(
        height=height,
        margin=dict(l=30, r=30, t=60, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_primary"]),
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_kpi_summary_table(
    kpis: dict[str, float],
    show_thresholds: bool = True,
) -> None:
    """
    Render a summary table of KPIs with status indicators.
    
    Args:
        kpis: Dictionary of KPI name -> value
        show_thresholds: Whether to show threshold columns
    """
    import pandas as pd
    
    rows = []
    for kpi_name, value in kpis.items():
        kpi_def = get_kpi_definition(kpi_name)
        display_name = kpi_def.display_name if kpi_def else kpi_name.replace("_", " ").title()
        
        # Determine status
        color = get_kpi_status_color(value, kpi_name)
        if color == COLORS["success"]:
            status = "✅ Good"
        elif color == COLORS["warning"]:
            status = "⚠️ Warning"
        else:
            status = "❌ Critical"
        
        row = {
            "KPI": display_name,
            "Value": format_kpi_value(value, kpi_name),
            "Status": status,
        }
        
        if show_thresholds and kpi_def:
            row["Target"] = format_kpi_value(kpi_def.target, kpi_name)
            row["Critical"] = format_kpi_value(kpi_def.critical_threshold, kpi_name)
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
