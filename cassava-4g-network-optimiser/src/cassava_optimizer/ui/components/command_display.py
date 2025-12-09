"""
Command display components for the Streamlit UI.

Displays MML commands and their execution status.
"""

import html
from typing import Any, Dict, List, Optional

import streamlit as st

from cassava_optimizer.ui.theme import COLORS, CASSAVA_GREEN, CASSAVA_NAVY


def _escape_html(text: str) -> str:
    """Escape HTML characters for safe display."""
    return html.escape(str(text)) if text else ""


def render_command_card(
    command: Dict[str, Any],
    show_status: bool = True,
) -> None:
    """
    Render a single command card.
    
    Args:
        command: Command dictionary with command_id, command, status, etc.
        show_status: Whether to show execution status
    """
    command_id = command.get("command_id", command.get("id", "N/A"))
    command_text = _escape_html(command.get("command", command.get("mml_command", "")))
    status = command.get("status", "pending")
    description = _escape_html(command.get("description", ""))
    result = _escape_html(command.get("result", ""))
    
    # Status colors and icons
    status_config = {
        "pending": (COLORS["text_muted"], "⏳", "Pending"),
        "executing": (COLORS["warning"], "⚡", "Executing"),
        "success": (CASSAVA_GREEN, "✅", "Success"),
        "failed": (COLORS["error"], "❌", "Failed"),
        "skipped": (COLORS["text_muted"], "⏭️", "Skipped"),
        "rolled_back": (COLORS["warning"], "↩️", "Rolled Back"),
    }
    
    color, icon, status_text = status_config.get(
        status, (COLORS["text_muted"], "❓", status)
    )
    
    st.markdown(
        f"""
        <div class="command-card" style="
            background: {COLORS['card']};
            border: 1px solid {COLORS['border']};
            border-left: 3px solid {color};
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-family: monospace; color: {COLORS['text_secondary']}; font-size: 0.85rem;">
                    {_escape_html(command_id)}
                </span>
                {f'<span style="color: {color}; font-size: 0.85rem;">{icon} {status_text}</span>' if show_status else ''}
            </div>
            <div style="
                background: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 0.9rem;
                color: {CASSAVA_GREEN};
                overflow-x: auto;
                white-space: pre-wrap;
                word-break: break-all;
            ">
                {command_text}
            </div>
            {f'<div style="color: {COLORS["text_secondary"]}; font-size: 0.85rem; margin-top: 8px;">{description}</div>' if description else ''}
            {f'<div style="color: {color}; font-size: 0.85rem; margin-top: 8px; font-style: italic;">{result}</div>' if result else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_command_list(
    commands: List[Dict[str, Any]],
    title: str = "MML Commands",
    show_status: bool = True,
    collapsible: bool = True,
    show_timeline: bool = False,
) -> None:
    """
    Render a list of commands.
    
    Args:
        commands: List of command dictionaries
        title: Section title
        show_status: Whether to show execution status
        collapsible: Whether to use an expander
        show_timeline: Whether to show as a timeline (for compatibility)
    """
    if not commands:
        st.info("No commands to display.")
        return
    
    # Summary statistics
    total = len(commands)
    success = sum(1 for c in commands if c.get("status") == "success")
    failed = sum(1 for c in commands if c.get("status") == "failed")
    pending = sum(1 for c in commands if c.get("status") == "pending")
    
    # Header
    st.markdown(
        f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        ">
            <h3 style="color: {COLORS['text_primary']}; margin: 0;">{title}</h3>
            <div style="display: flex; gap: 16px; font-size: 0.85rem;">
                <span style="color: {COLORS['text_secondary']};">Total: {total}</span>
                <span style="color: {CASSAVA_GREEN};">✅ {success}</span>
                <span style="color: {COLORS['error']};">❌ {failed}</span>
                <span style="color: {COLORS['text_muted']};">⏳ {pending}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Render commands
    if collapsible and len(commands) > 3:
        with st.expander(f"View all {total} commands", expanded=False):
            for command in commands:
                render_command_card(command, show_status=show_status)
    else:
        for command in commands:
            render_command_card(command, show_status=show_status)


def render_command_preview(
    commands: List[str],
    title: str = "Commands to Execute",
) -> None:
    """
    Render a preview of commands before execution.
    
    Args:
        commands: List of command strings
        title: Section title
    """
    st.markdown(
        f"""
        <div style="margin-bottom: 16px;">
            <h4 style="color: {COLORS['text_primary']}; margin-bottom: 8px;">{title}</h4>
            <p style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">
                The following {len(commands)} command(s) will be executed:
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    for i, cmd in enumerate(commands, 1):
        st.markdown(
            f"""
            <div style="
                background: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 10px;
                margin: 4px 0;
                display: flex;
                gap: 12px;
            ">
                <span style="color: {COLORS['text_muted']}; min-width: 24px;">{i}.</span>
                <code style="color: {CASSAVA_GREEN}; font-family: monospace;">{cmd}</code>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_command_execution_log(
    log_entries: List[Dict[str, Any]],
) -> None:
    """
    Render real-time command execution log.
    
    Args:
        log_entries: List of log entries with timestamp, command, status, etc.
    """
    st.markdown(
        f"""
        <div style="
            background: {COLORS['background']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 16px;
            max-height: 400px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.85rem;
        ">
        """,
        unsafe_allow_html=True,
    )
    
    for entry in log_entries:
        timestamp = entry.get("timestamp", "")
        message = entry.get("message", "")
        level = entry.get("level", "info")
        
        level_colors = {
            "info": COLORS["text_secondary"],
            "success": CASSAVA_GREEN,
            "warning": COLORS["warning"],
            "error": COLORS["error"],
        }
        color = level_colors.get(level, COLORS["text_secondary"])
        
        st.markdown(
            f"""
            <div style="margin: 4px 0;">
                <span style="color: {COLORS['text_muted']};">[{timestamp}]</span>
                <span style="color: {color};">{message}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
