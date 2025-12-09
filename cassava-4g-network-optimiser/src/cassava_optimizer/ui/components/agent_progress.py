"""
Agent progress tracking components for the Streamlit UI.

Displays real-time agent status, progress, and workflow timeline
during optimization runs.
"""

from datetime import datetime
from typing import Any, Optional

import streamlit as st

from cassava_optimizer.ui.theme import COLORS, AGENT_COLORS, CASSAVA_GREEN


# Agent configuration with display names and icons
AGENTS = {
    "data_collector": {
        "name": "Data Collector",
        "icon": "📊",
        "description": "Gathering KPI data and cell configuration",
    },
    "analyzer": {
        "name": "Analyzer",
        "icon": "🔍",
        "description": "Analyzing network performance and identifying issues",
    },
    "strategy_planner": {
        "name": "Strategy Planner",
        "icon": "📋",
        "description": "Planning optimization strategies and parameter changes",
    },
    "validator": {
        "name": "Validator",
        "icon": "✓",
        "description": "Validating recommendations and risk assessment",
    },
    "commander": {
        "name": "Commander",
        "icon": "⚡",
        "description": "Executing MML commands on network elements",
    },
    "reviewer": {
        "name": "Reviewer",
        "icon": "📈",
        "description": "Reviewing results and measuring impact",
    },
}


def render_agent_card(
    agent_id: str,
    status: str,
    message: Optional[str] = None,
    progress: float = 0,
    duration: Optional[float] = None,
) -> None:
    """
    Render a single agent status card.
    
    Args:
        agent_id: Agent identifier
        status: Agent status (pending, running, complete, error)
        message: Optional status message
        progress: Progress percentage (0-100)
        duration: Optional duration in seconds
    """
    agent_info = AGENTS.get(agent_id, {"name": agent_id, "icon": "🤖", "description": ""})
    color = AGENT_COLORS.get(agent_id, COLORS["text_secondary"])
    
    # Status badge styling
    status_map = {
        "pending": ("pending", COLORS["text_muted"]),
        "running": ("running", "#60A5FA"),
        "complete": ("complete", CASSAVA_GREEN),
        "completed": ("complete", CASSAVA_GREEN),
        "error": ("error", COLORS["error"]),
        "failed": ("error", COLORS["error"]),
    }
    status_class, status_color = status_map.get(status.lower(), ("pending", COLORS["text_muted"]))
    
    # Format duration
    duration_text = ""
    if duration is not None:
        if duration >= 60:
            duration_text = f"{duration / 60:.1f}m"
        else:
            duration_text = f"{duration:.1f}s"
    
    # Progress bar color
    progress_color = color if status_class == "running" else (
        CASSAVA_GREEN if status_class == "complete" else COLORS["border"]
    )
    
    st.markdown(
        f"""
        <div class="agent-progress">
            <div class="agent-header">
                <div class="agent-name">
                    <span>{agent_info['icon']}</span>
                    <span>{agent_info['name']}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    {f'<span style="font-size: 0.8rem; color: {COLORS["text_muted"]};">{duration_text}</span>' if duration_text else ''}
                    <span class="agent-status {status_class}">{status.title()}</span>
                </div>
            </div>
            <div class="agent-progress-bar">
                <div class="agent-progress-fill" style="width: {progress}%; background: {progress_color};"></div>
            </div>
            {f'<div class="agent-message">{message}</div>' if message else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_agent_progress(
    agent_statuses: dict[str, dict[str, Any]],
) -> None:
    """
    Render progress cards for all agents.
    
    Args:
        agent_statuses: Dictionary of agent_id -> {status, message, progress, duration}
    """
    st.markdown(
        f"""
        <div class="card">
            <div class="card-header">
                <span>🤖</span>
                <span>Agent Progress</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    for agent_id in AGENTS.keys():
        agent_status = agent_statuses.get(agent_id, {"status": "pending"})
        render_agent_card(
            agent_id=agent_id,
            status=agent_status.get("status", "pending"),
            message=agent_status.get("message"),
            progress=agent_status.get("progress", 0),
            duration=agent_status.get("duration"),
        )


def render_workflow_timeline(
    events: list[dict[str, Any]],
) -> None:
    """
    Render a timeline of workflow events.
    
    Args:
        events: List of {timestamp, agent, action, status} events
    """
    if not events:
        st.info("No workflow events yet")
        return
    
    st.markdown(
        f"""
        <div class="card">
            <div class="card-header">
                <span>⏱️</span>
                <span>Workflow Timeline</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    
    for i, event in enumerate(events):
        timestamp = event.get("timestamp", "")
        if isinstance(timestamp, datetime):
            timestamp = timestamp.strftime("%H:%M:%S")
        
        agent_id = event.get("agent", "")
        agent_info = AGENTS.get(agent_id, {"name": agent_id, "icon": "📌"})
        action = event.get("action", "")
        status = event.get("status", "info")
        
        # Status indicator
        status_colors = {
            "success": CASSAVA_GREEN,
            "error": COLORS["error"],
            "warning": COLORS["warning"],
            "info": COLORS["info"],
        }
        status_color = status_colors.get(status, COLORS["text_secondary"])
        
        # Is this the latest event?
        is_latest = i == len(events) - 1
        
        st.markdown(
            f"""
            <div style="display: flex; gap: 12px; padding: 0.75rem 0; border-bottom: 1px solid {COLORS['border']};">
                <div style="width: 70px; font-size: 0.8rem; color: {COLORS['text_muted']};">{timestamp}</div>
                <div style="width: 8px; height: 8px; border-radius: 50%; background: {status_color}; margin-top: 4px; {f'animation: pulse 2s infinite;' if is_latest else ''}"></div>
                <div style="flex: 1;">
                    <div style="font-size: 0.9rem; color: {COLORS['text_primary']};">
                        {agent_info['icon']} {agent_info['name']}
                    </div>
                    <div style="font-size: 0.85rem; color: {COLORS['text_secondary']};">{action}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_workflow_summary(
    status: str,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
    site_name: str = "",
    optimization_type: str = "",
) -> None:
    """
    Render a summary of the current workflow status.
    
    Args:
        status: Current workflow status
        started_at: When the workflow started
        completed_at: When the workflow completed
        site_name: Site being optimized
        optimization_type: Type of optimization
    """
    # Status indicator
    status_map = {
        "idle": ("Idle", COLORS["text_muted"], "⏸️"),
        "running": ("Running", COLORS["info"], "▶️"),
        "collecting_data": ("Collecting Data", COLORS["info"], "📊"),
        "analyzing": ("Analyzing", COLORS["info"], "🔍"),
        "planning": ("Planning Strategy", COLORS["info"], "📋"),
        "validating": ("Validating", COLORS["info"], "✓"),
        "awaiting_approval": ("Awaiting Approval", COLORS["warning"], "⏳"),
        "executing": ("Executing", COLORS["info"], "⚡"),
        "reviewing": ("Reviewing", COLORS["info"], "📈"),
        "completed": ("Completed", CASSAVA_GREEN, "✅"),
        "failed": ("Failed", COLORS["error"], "❌"),
        "rolled_back": ("Rolled Back", COLORS["warning"], "↩️"),
    }
    
    status_text, status_color, status_icon = status_map.get(
        status.lower(),
        (status.title(), COLORS["text_secondary"], "•"),
    )
    
    # Calculate duration
    duration_text = ""
    if started_at:
        end_time = completed_at or datetime.utcnow()
        duration = (end_time - started_at).total_seconds()
        if duration >= 60:
            duration_text = f"{duration / 60:.1f} minutes"
        else:
            duration_text = f"{duration:.0f} seconds"
    
    st.markdown(
        f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <span style="font-size: 1.5rem;">{status_icon}</span>
                        <span style="font-size: 1.25rem; font-weight: 600; color: {status_color};">{status_text}</span>
                    </div>
                    <div style="font-size: 0.9rem; color: {COLORS['text_secondary']};">
                        {f"Site: <b>{site_name}</b> | " if site_name else ""}
                        {f"Type: <b>{optimization_type.title()}</b> | " if optimization_type else ""}
                        {f"Duration: {duration_text}" if duration_text else ""}
                    </div>
                </div>
                <div style="text-align: right; font-size: 0.85rem; color: {COLORS['text_muted']};">
                    {f"Started: {started_at.strftime('%H:%M:%S')}" if started_at else ""}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def create_progress_placeholder() -> st.empty:
    """
    Create a placeholder for updating agent progress.
    
    Returns:
        Streamlit empty container for dynamic updates
    """
    return st.empty()


def update_progress_placeholder(
    placeholder: st.empty,
    agent_statuses: dict[str, dict[str, Any]],
) -> None:
    """
    Update the progress placeholder with new agent statuses.
    
    Args:
        placeholder: Streamlit empty container
        agent_statuses: Updated agent statuses
    """
    with placeholder.container():
        render_agent_progress(agent_statuses)
