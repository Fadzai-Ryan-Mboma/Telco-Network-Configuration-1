"""
Chart components for the Streamlit UI.

Provides Plotly chart generation with Cassava branding
for KPI visualization and network analytics.
"""

from typing import Any, Optional

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from cassava_optimizer.ui.theme import (
    CASSAVA_GREEN,
    CASSAVA_NAVY,
    CASSAVA_PURPLE,
    COLORS,
    get_plotly_template,
)


def create_kpi_line_chart(
    data: list[dict[str, Any]],
    x_field: str = "timestamp",
    y_field: str = "value",
    title: str = "",
    kpi_name: Optional[str] = None,
    target_value: Optional[float] = None,
    threshold_low: Optional[float] = None,
    threshold_high: Optional[float] = None,
    height: int = 400,
) -> go.Figure:
    """
    Create a line chart for KPI trends over time.
    
    Args:
        data: List of data points with timestamp and value
        x_field: Field name for x-axis (timestamp)
        y_field: Field name for y-axis (value)
        title: Chart title
        kpi_name: Name of the KPI for labeling
        target_value: Target value to show as reference line
        threshold_low: Lower threshold for coloring
        threshold_high: Upper threshold for coloring
        height: Chart height in pixels
        
    Returns:
        Plotly figure object
    """
    if not data:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color=COLORS["text_secondary"]),
        )
        fig.update_layout(
            template=get_plotly_template(),
            height=height,
        )
        return fig
    
    x_values = [d.get(x_field) for d in data]
    y_values = [d.get(y_field) for d in data]
    
    fig = go.Figure()
    
    # Main line
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines+markers",
            name=kpi_name or "Value",
            line=dict(color=CASSAVA_GREEN, width=2),
            marker=dict(size=6, color=CASSAVA_GREEN),
            fill="tozeroy",
            fillcolor=f"rgba(0, 241, 156, 0.1)",
        )
    )
    
    # Target line
    if target_value is not None:
        fig.add_hline(
            y=target_value,
            line=dict(color=CASSAVA_PURPLE, width=2, dash="dash"),
            annotation_text=f"Target: {target_value}",
            annotation_position="right",
        )
    
    # Threshold regions
    if threshold_low is not None:
        fig.add_hrect(
            y0=0,
            y1=threshold_low,
            fillcolor=f"rgba(239, 68, 68, 0.1)",
            line=dict(width=0),
            annotation_text="Below threshold",
            annotation_position="bottom left",
        )
    
    if threshold_high is not None:
        max_y = max(y_values) * 1.1 if y_values else 100
        fig.add_hrect(
            y0=threshold_high,
            y1=max_y,
            fillcolor=f"rgba(239, 68, 68, 0.1)",
            line=dict(width=0),
            annotation_text="Above threshold",
            annotation_position="top left",
        )
    
    fig.update_layout(
        template=get_plotly_template(),
        title=dict(
            text=title,
            font=dict(size=16, color=COLORS["text_primary"]),
        ),
        xaxis_title="Time",
        yaxis_title=kpi_name or "Value",
        height=height,
        showlegend=False,
        hovermode="x unified",
    )
    
    return fig


def create_health_radar_chart(
    kpi_values: dict[str, float],
    kpi_targets: Optional[dict[str, float]] = None,
    title: str = "Network Health",
    height: int = 400,
) -> go.Figure:
    """
    Create a radar chart showing multiple KPI health scores.
    
    Args:
        kpi_values: Dictionary of KPI name -> current value (0-100 scale)
        kpi_targets: Optional dictionary of KPI name -> target value
        title: Chart title
        height: Chart height in pixels
        
    Returns:
        Plotly figure object
    """
    if not kpi_values:
        fig = go.Figure()
        fig.add_annotation(
            text="No KPI data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color=COLORS["text_secondary"]),
        )
        fig.update_layout(template=get_plotly_template(), height=height)
        return fig
    
    categories = list(kpi_values.keys())
    values = list(kpi_values.values())
    
    # Close the radar chart by repeating first value
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]
    
    fig = go.Figure()
    
    # Current values
    fig.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            fillcolor=f"rgba(0, 241, 156, 0.2)",
            line=dict(color=CASSAVA_GREEN, width=2),
            name="Current",
        )
    )
    
    # Target values
    if kpi_targets:
        target_values = [kpi_targets.get(k, 100) for k in categories]
        target_values_closed = target_values + [target_values[0]]
        
        fig.add_trace(
            go.Scatterpolar(
                r=target_values_closed,
                theta=categories_closed,
                fill="none",
                line=dict(color=CASSAVA_PURPLE, width=2, dash="dash"),
                name="Target",
            )
        )
    
    fig.update_layout(
        template=get_plotly_template(),
        title=dict(
            text=title,
            font=dict(size=16, color=COLORS["text_primary"]),
        ),
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor=COLORS["border"],
                linecolor=COLORS["border"],
            ),
            angularaxis=dict(
                gridcolor=COLORS["border"],
                linecolor=COLORS["border"],
            ),
            bgcolor=COLORS["card_bg"],
        ),
        height=height,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05,
        ),
    )
    
    return fig


def create_comparison_bar_chart(
    categories: list[str],
    current_values: list[float],
    target_values: Optional[list[float]] = None,
    previous_values: Optional[list[float]] = None,
    title: str = "KPI Comparison",
    orientation: str = "v",
    height: int = 400,
) -> go.Figure:
    """
    Create a bar chart comparing current vs target/previous values.
    
    Args:
        categories: List of category names
        current_values: List of current values
        target_values: Optional list of target values
        previous_values: Optional list of previous values
        title: Chart title
        orientation: 'v' for vertical, 'h' for horizontal
        height: Chart height in pixels
        
    Returns:
        Plotly figure object
    """
    if not categories or not current_values:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color=COLORS["text_secondary"]),
        )
        fig.update_layout(template=get_plotly_template(), height=height)
        return fig
    
    fig = go.Figure()
    
    # Determine x/y based on orientation
    if orientation == "h":
        x_curr, y_curr = current_values, categories
        x_targ, y_targ = target_values, categories
        x_prev, y_prev = previous_values, categories
    else:
        x_curr, y_curr = categories, current_values
        x_targ, y_targ = categories, target_values
        x_prev, y_prev = categories, previous_values
    
    # Previous values (if provided)
    if previous_values:
        fig.add_trace(
            go.Bar(
                x=x_prev,
                y=y_prev,
                name="Previous",
                marker_color=COLORS["text_secondary"],
                opacity=0.5,
                orientation=orientation,
            )
        )
    
    # Current values
    fig.add_trace(
        go.Bar(
            x=x_curr,
            y=y_curr,
            name="Current",
            marker_color=CASSAVA_GREEN,
            orientation=orientation,
        )
    )
    
    # Target values (if provided)
    if target_values:
        fig.add_trace(
            go.Bar(
                x=x_targ,
                y=y_targ,
                name="Target",
                marker_color=CASSAVA_PURPLE,
                opacity=0.7,
                orientation=orientation,
            )
        )
    
    fig.update_layout(
        template=get_plotly_template(),
        title=dict(
            text=title,
            font=dict(size=16, color=COLORS["text_primary"]),
        ),
        barmode="group",
        height=height,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    
    return fig


def create_gauge_chart(
    value: float,
    min_value: float = 0,
    max_value: float = 100,
    title: str = "",
    thresholds: Optional[dict[str, tuple[float, float, str]]] = None,
    height: int = 250,
) -> go.Figure:
    """
    Create a gauge chart for single KPI value.
    
    Args:
        value: Current value
        min_value: Minimum scale value
        max_value: Maximum scale value
        title: Chart title
        thresholds: Dictionary of threshold name -> (start, end, color)
        height: Chart height in pixels
        
    Returns:
        Plotly figure object
    """
    # Default thresholds (red, yellow, green)
    if thresholds is None:
        thresholds = {
            "Low": (0, 50, COLORS["error"]),
            "Medium": (50, 80, COLORS["warning"]),
            "High": (80, 100, CASSAVA_GREEN),
        }
    
    # Build steps for gauge
    steps = []
    for name, (start, end, color) in thresholds.items():
        steps.append({"range": [start, end], "color": f"{color}30"})
    
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            title={"text": title, "font": {"color": COLORS["text_primary"]}},
            number={"font": {"color": COLORS["text_primary"]}},
            gauge={
                "axis": {
                    "range": [min_value, max_value],
                    "tickcolor": COLORS["text_secondary"],
                },
                "bar": {"color": CASSAVA_GREEN},
                "steps": steps,
                "threshold": {
                    "line": {"color": CASSAVA_PURPLE, "width": 4},
                    "thickness": 0.75,
                    "value": value,
                },
            },
        )
    )
    
    fig.update_layout(
        template=get_plotly_template(),
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    
    return fig


def create_timeline_chart(
    events: list[dict[str, Any]],
    title: str = "Event Timeline",
    height: int = 300,
) -> go.Figure:
    """
    Create a timeline chart for events/activities.
    
    Args:
        events: List of event dictionaries with 'start', 'end', 'name', 'status'
        title: Chart title
        height: Chart height in pixels
        
    Returns:
        Plotly figure object
    """
    if not events:
        fig = go.Figure()
        fig.add_annotation(
            text="No events to display",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color=COLORS["text_secondary"]),
        )
        fig.update_layout(template=get_plotly_template(), height=height)
        return fig
    
    # Status colors
    status_colors = {
        "completed": CASSAVA_GREEN,
        "in_progress": CASSAVA_PURPLE,
        "pending": COLORS["text_secondary"],
        "failed": COLORS["error"],
    }
    
    fig = go.Figure()
    
    for i, event in enumerate(events):
        status = event.get("status", "pending")
        color = status_colors.get(status, COLORS["text_secondary"])
        
        fig.add_trace(
            go.Bar(
                x=[event.get("duration", 1)],
                y=[event.get("name", f"Event {i}")],
                orientation="h",
                marker_color=color,
                name=event.get("name", f"Event {i}"),
                showlegend=False,
                hovertemplate=f"<b>{event.get('name')}</b><br>Status: {status}<extra></extra>",
            )
        )
    
    fig.update_layout(
        template=get_plotly_template(),
        title=dict(
            text=title,
            font=dict(size=16, color=COLORS["text_primary"]),
        ),
        height=height,
        barmode="stack",
        showlegend=False,
    )
    
    return fig


def create_heatmap(
    data: list[list[float]],
    x_labels: list[str],
    y_labels: list[str],
    title: str = "Heatmap",
    colorscale: Optional[list] = None,
    height: int = 400,
) -> go.Figure:
    """
    Create a heatmap for correlation or intensity visualization.
    
    Args:
        data: 2D list of values
        x_labels: Labels for x-axis
        y_labels: Labels for y-axis
        title: Chart title
        colorscale: Custom color scale
        height: Chart height in pixels
        
    Returns:
        Plotly figure object
    """
    if colorscale is None:
        colorscale = [
            [0, CASSAVA_NAVY],
            [0.5, CASSAVA_PURPLE],
            [1, CASSAVA_GREEN],
        ]
    
    fig = go.Figure(
        go.Heatmap(
            z=data,
            x=x_labels,
            y=y_labels,
            colorscale=colorscale,
            hoverongaps=False,
        )
    )
    
    fig.update_layout(
        template=get_plotly_template(),
        title=dict(
            text=title,
            font=dict(size=16, color=COLORS["text_primary"]),
        ),
        height=height,
    )
    
    return fig
