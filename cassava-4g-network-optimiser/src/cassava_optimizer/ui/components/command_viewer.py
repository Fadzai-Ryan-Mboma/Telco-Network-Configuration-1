"""
MML Command viewer components for the Streamlit UI.

Displays MML commands, their execution status, and results
with syntax highlighting and copy functionality.
"""

import html
from typing import Any, Optional

import streamlit as st

from cassava_optimizer.ui.theme import COLORS, CASSAVA_GREEN, CASSAVA_NAVY, CASSAVA_PURPLE


def _escape_html(text: str) -> str:
    """Escape HTML characters for safe display."""
    return html.escape(str(text)) if text else ""


def render_command_syntax(
    command: str,
    language: str = "bash",
) -> None:
    """
    Render a command with syntax highlighting.
    
    Args:
        command: The MML command string
        language: Language for syntax highlighting
    """
    st.code(command, language=language)


def render_command_card(
    command: dict[str, Any],
    index: int = 0,
    show_result: bool = True,
) -> None:
    """
    Render a single MML command as a card.
    
    Args:
        command: Command dictionary with keys like 'command', 'status', 'result'
        index: Index for unique key generation
        show_result: Whether to show execution result
    """
    cmd_text = command.get("command", "")
    status = command.get("status", "pending")
    result = command.get("result", "")
    error = command.get("error", "")
    executed_at = command.get("executed_at", "")
    execution_time = command.get("execution_time_ms", 0)
    
    # Status styling
    status_styles = {
        "pending": (COLORS["text_secondary"], "⏳", "Pending"),
        "executing": (CASSAVA_PURPLE, "⚡", "Executing"),
        "success": (CASSAVA_GREEN, "✅", "Success"),
        "failed": (COLORS["error"], "❌", "Failed"),
        "rolled_back": (COLORS["warning"], "↩️", "Rolled Back"),
    }
    
    status_color, status_icon, status_text = status_styles.get(
        status.lower(), (COLORS["text_secondary"], "❓", status)
    )
    
    st.markdown(
        f"""
        <div class="command-card" style="
            background: {COLORS['card_bg']};
            border: 1px solid {COLORS['border']};
            border-left: 4px solid {status_color};
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">
                    Command #{index + 1}
                </span>
                <span style="
                    background: {status_color}20;
                    color: {status_color};
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 0.8rem;
                    font-weight: 500;
                ">
                    {status_icon} {status_text}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Command code block
    st.code(cmd_text, language="bash")
    
    # Copy button
    if st.button(f"📋 Copy", key=f"copy_cmd_{index}"):
        st.toast("Command copied to clipboard!")
    
    # Execution details
    if executed_at or execution_time:
        details_parts = []
        if executed_at:
            details_parts.append(f"Executed: {executed_at}")
        if execution_time:
            details_parts.append(f"Duration: {execution_time}ms")
        
        st.caption(" • ".join(details_parts))
    
    # Result or error
    if show_result:
        if error:
            with st.expander("❌ Error Details", expanded=True):
                st.error(error)
        elif result:
            with st.expander("📤 Command Output", expanded=False):
                st.code(result, language="text")


def render_command_list(
    commands: list[dict[str, Any]],
    show_timeline: bool = True,
) -> None:
    """
    Render a list of MML commands with optional timeline view.
    
    Args:
        commands: List of command dictionaries
        show_timeline: Whether to show as a timeline
    """
    if not commands:
        st.info("No commands to display")
        return
    
    # Summary stats
    total = len(commands)
    successful = sum(1 for c in commands if c.get("status") == "success")
    failed = sum(1 for c in commands if c.get("status") == "failed")
    pending = sum(1 for c in commands if c.get("status") == "pending")
    
    # Stats bar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Successful", successful, delta=None)
    with col3:
        st.metric("Failed", failed, delta=f"-{failed}" if failed else None, delta_color="inverse")
    with col4:
        st.metric("Pending", pending)
    
    st.markdown("---")
    
    # Commands
    for i, cmd in enumerate(commands):
        render_command_card(cmd, index=i)


def render_command_builder(
    templates: Optional[dict[str, str]] = None,
    on_submit: Optional[callable] = None,
) -> Optional[str]:
    """
    Render an interactive command builder.
    
    Args:
        templates: Dictionary of template name -> template command
        on_submit: Callback when command is submitted
        
    Returns:
        The built command string
    """
    st.markdown(
        f"""
        <div class="card">
            <div class="card-header">
                <span>🔧</span>
                <span>MML Command Builder</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Template selector
    if templates:
        template_names = ["-- Custom Command --"] + list(templates.keys())
        selected_template = st.selectbox(
            "Select Template",
            options=template_names,
            key="cmd_template",
        )
        
        if selected_template != "-- Custom Command --":
            initial_command = templates[selected_template]
        else:
            initial_command = ""
    else:
        initial_command = ""
    
    # Command input
    command = st.text_area(
        "MML Command",
        value=initial_command,
        height=100,
        key="cmd_input",
        help="Enter the MML command to execute",
        placeholder="DSP CELLQCI:;",
    )
    
    # Parameter inputs for common substitutions
    with st.expander("📝 Parameters", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            site_param = st.text_input("Site Name", key="cmd_site")
            cell_param = st.text_input("Cell ID", key="cmd_cell")
        with col2:
            param1 = st.text_input("Parameter 1", key="cmd_param1")
            param2 = st.text_input("Parameter 2", key="cmd_param2")
        
        # Apply substitutions
        if site_param:
            command = command.replace("{site}", site_param)
            command = command.replace("$SITE", site_param)
        if cell_param:
            command = command.replace("{cell}", cell_param)
            command = command.replace("$CELL", cell_param)
        if param1:
            command = command.replace("{param1}", param1)
        if param2:
            command = command.replace("{param2}", param2)
    
    # Preview
    if command:
        st.markdown("**Preview:**")
        st.code(command, language="bash")
    
    # Submit
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("▶️ Execute", type="primary", disabled=not command):
            if on_submit:
                on_submit(command)
            return command
    
    return None


def render_command_history(
    history: list[dict[str, Any]],
    max_items: int = 20,
) -> None:
    """
    Render command execution history.
    
    Args:
        history: List of historical command executions
        max_items: Maximum number of items to display
    """
    if not history:
        st.info("No command history available")
        return
    
    st.markdown(
        f"""
        <div class="card">
            <div class="card-header">
                <span>📜</span>
                <span>Command History</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Search/filter
    search = st.text_input(
        "🔍 Search commands",
        placeholder="Filter by command text...",
        key="cmd_history_search",
    )
    
    # Filter
    filtered_history = history[:max_items]
    if search:
        filtered_history = [
            h for h in filtered_history
            if search.lower() in h.get("command", "").lower()
        ]
    
    # Display
    for i, item in enumerate(filtered_history):
        cmd = item.get("command", "")
        status = item.get("status", "unknown")
        executed_at = item.get("executed_at", "")
        site = item.get("site_name", "")
        
        status_emoji = "✅" if status == "success" else ("❌" if status == "failed" else "⏳")
        
        with st.container():
            cols = st.columns([1, 4, 2, 1])
            with cols[0]:
                st.markdown(f"**{status_emoji}**")
            with cols[1]:
                st.code(cmd[:50] + "..." if len(cmd) > 50 else cmd, language="bash")
            with cols[2]:
                st.caption(f"{site} • {executed_at}")
            with cols[3]:
                if st.button("🔄", key=f"rerun_{i}", help="Re-run command"):
                    st.session_state[f"rerun_cmd_{i}"] = cmd


def render_batch_commands(
    commands: list[str],
    on_execute: Optional[callable] = None,
) -> None:
    """
    Render batch command execution interface.
    
    Args:
        commands: List of command strings to execute
        on_execute: Callback when batch execution is triggered
    """
    if not commands:
        return
    
    st.markdown(
        f"""
        <div class="card" style="border: 2px solid {CASSAVA_PURPLE};">
            <div class="card-header" style="color: {CASSAVA_PURPLE};">
                <span>📦</span>
                <span>Batch Execution</span>
            </div>
            <p style="color: {COLORS['text_secondary']};">
                {len(commands)} commands ready for execution
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Preview commands
    with st.expander("📋 View Commands", expanded=True):
        for i, cmd in enumerate(commands):
            st.markdown(f"**{i + 1}.** `{cmd}`")
    
    # Execution options
    col1, col2 = st.columns(2)
    with col1:
        stop_on_error = st.checkbox(
            "Stop on first error",
            value=True,
            key="batch_stop_on_error",
        )
    with col2:
        delay = st.slider(
            "Delay between commands (ms)",
            min_value=0,
            max_value=5000,
            value=500,
            step=100,
            key="batch_delay",
        )
    
    # Execute button
    if st.button("⚡ Execute All", type="primary"):
        if on_execute:
            on_execute(commands, stop_on_error=stop_on_error, delay_ms=delay)
