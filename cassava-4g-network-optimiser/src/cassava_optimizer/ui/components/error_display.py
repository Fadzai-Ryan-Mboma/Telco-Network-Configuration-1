"""
Error display components for the Streamlit UI.

Implements fail-fast error presentation with detailed diagnostics,
stack traces, and recovery suggestions.
"""

from typing import Any, Optional
import traceback

import streamlit as st

from cassava_optimizer.ui.theme import COLORS, CASSAVA_GREEN, CASSAVA_NAVY


def render_error_banner(
    message: str,
    error_type: str = "error",
    title: Optional[str] = None,
    dismissible: bool = True,
) -> None:
    """
    Render a prominent error banner.
    
    Args:
        message: Error message to display
        error_type: Type of error (error, warning, info)
        title: Optional title for the banner
        dismissible: Whether the banner can be dismissed
    """
    colors = {
        "error": (COLORS["error"], "❌", "Error"),
        "warning": (COLORS["warning"], "⚠️", "Warning"),
        "info": (COLORS["info"], "ℹ️", "Info"),
        "critical": ("#dc2626", "🚨", "Critical Error"),
    }
    
    color, icon, default_title = colors.get(
        error_type, (COLORS["error"], "❌", "Error")
    )
    display_title = title or default_title
    
    st.markdown(
        f"""
        <div class="error-banner" style="
            background: {color}15;
            border: 1px solid {color};
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
        ">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 1.5rem;">{icon}</span>
                <span style="font-size: 1.1rem; font-weight: 600; color: {color};">
                    {display_title}
                </span>
            </div>
            <div style="color: {COLORS['text_primary']}; line-height: 1.5;">
                {message}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_exception(
    exception: Exception,
    show_traceback: bool = True,
    context: Optional[str] = None,
) -> None:
    """
    Render a Python exception with optional traceback.
    
    Args:
        exception: The exception to display
        show_traceback: Whether to show the full traceback
        context: Additional context about when/where the error occurred
    """
    error_type = type(exception).__name__
    error_message = str(exception)
    
    # Main error display
    render_error_banner(
        message=error_message,
        error_type="error",
        title=error_type,
    )
    
    # Context
    if context:
        st.markdown(
            f"""
            <div style="
                background: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 10px;
                margin: 10px 0;
            ">
                <span style="color: {COLORS['text_secondary']};">Context:</span>
                <span style="color: {COLORS['text_primary']};">{context}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # Traceback
    if show_traceback:
        with st.expander("🔍 Stack Trace", expanded=False):
            tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
            st.code(tb, language="python")


def render_api_error(
    status_code: int,
    response_body: Optional[str] = None,
    endpoint: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """
    Render an API error with details.
    
    Args:
        status_code: HTTP status code
        response_body: Response body if available
        endpoint: API endpoint that was called
        request_id: Request ID for tracking
    """
    # Determine error severity based on status code
    if status_code >= 500:
        error_type = "critical"
        title = "Server Error"
        description = "The server encountered an error. This is not your fault."
    elif status_code == 401 or status_code == 403:
        error_type = "error"
        title = "Authentication Error"
        description = "Authentication failed. Please check your credentials."
    elif status_code == 404:
        error_type = "warning"
        title = "Not Found"
        description = "The requested resource was not found."
    elif status_code == 429:
        error_type = "warning"
        title = "Rate Limited"
        description = "Too many requests. Please wait before trying again."
    else:
        error_type = "error"
        title = f"HTTP {status_code}"
        description = "The API request failed."
    
    render_error_banner(
        message=description,
        error_type=error_type,
        title=title,
    )
    
    # Details
    st.markdown(
        f"""
        <div class="card" style="background: {COLORS['card_bg']};">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">
                {f"<p><strong>Endpoint:</strong> <code>{endpoint}</code></p>" if endpoint else ""}
                {f"<p><strong>Request ID:</strong> <code>{request_id}</code></p>" if request_id else ""}
                <p><strong>Status Code:</strong> <code>{status_code}</code></p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Response body
    if response_body:
        with st.expander("📤 Response Body", expanded=False):
            st.code(response_body, language="json")


def render_database_error(
    error: Exception,
    operation: Optional[str] = None,
    table: Optional[str] = None,
    suggestion: Optional[str] = None,
) -> None:
    """
    Render a database error with recovery suggestions.
    
    Args:
        error: The database exception
        operation: The operation that failed (SELECT, INSERT, etc.)
        table: The table involved
        suggestion: Recovery suggestion
    """
    render_error_banner(
        message=str(error),
        error_type="error",
        title="Database Error",
    )
    
    # Operation details
    details = []
    if operation:
        details.append(f"**Operation:** {operation}")
    if table:
        details.append(f"**Table:** {table}")
    
    if details:
        st.markdown(" • ".join(details))
    
    # Suggestion
    if suggestion:
        st.info(f"💡 **Suggestion:** {suggestion}")
    else:
        # Default suggestions based on error type
        error_str = str(error).lower()
        if "connection" in error_str:
            st.info("💡 **Suggestion:** Check if the database server is running and accessible.")
        elif "timeout" in error_str:
            st.info("💡 **Suggestion:** The database may be overloaded. Try again in a moment.")
        elif "constraint" in error_str:
            st.info("💡 **Suggestion:** This operation violates a database constraint. Check your data.")
        elif "not found" in error_str or "does not exist" in error_str:
            st.info("💡 **Suggestion:** The requested record or table doesn't exist. Run database migrations.")


def render_validation_errors(
    errors: list[dict[str, Any]],
    field_names: Optional[dict[str, str]] = None,
) -> None:
    """
    Render validation errors for form fields.
    
    Args:
        errors: List of error dictionaries with 'field' and 'message' keys
        field_names: Optional mapping of field keys to display names
    """
    if not errors:
        return
    
    st.markdown(
        f"""
        <div class="validation-errors" style="
            background: {COLORS['error']}10;
            border: 1px solid {COLORS['error']};
            border-radius: 8px;
            padding: 16px;
            margin: 10px 0;
        ">
            <div style="color: {COLORS['error']}; font-weight: 600; margin-bottom: 10px;">
                ❌ Please fix the following errors:
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    for error in errors:
        field = error.get("field", "Unknown")
        message = error.get("message", "Invalid value")
        display_field = field_names.get(field, field) if field_names else field
        
        st.markdown(
            f"""
            <div style="
                padding: 8px 12px;
                margin: 4px 0;
                background: {COLORS['card_bg']};
                border-left: 3px solid {COLORS['error']};
                border-radius: 0 4px 4px 0;
            ">
                <strong style="color: {COLORS['text_primary']};">{display_field}:</strong>
                <span style="color: {COLORS['text_secondary']};">{message}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_connection_error(
    service: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    retry_available: bool = True,
    on_retry: Optional[callable] = None,
) -> None:
    """
    Render a connection error with retry option.
    
    Args:
        service: Name of the service that couldn't be reached
        host: Host that was being connected to
        port: Port that was being connected to
        retry_available: Whether retry is available
        on_retry: Callback when retry is clicked
    """
    render_error_banner(
        message=f"Unable to connect to {service}. Please check your network connection and service availability.",
        error_type="error",
        title="Connection Failed",
    )
    
    # Connection details
    if host or port:
        connection_str = ""
        if host:
            connection_str = host
        if port:
            connection_str += f":{port}"
        
        st.markdown(f"**Target:** `{connection_str}`")
    
    # Troubleshooting steps
    with st.expander("🔧 Troubleshooting Steps", expanded=True):
        st.markdown(f"""
        1. **Check if {service} is running** - Verify the service is operational
        2. **Verify network connectivity** - Ensure you can reach the host
        3. **Check firewall settings** - The port may be blocked
        4. **Verify credentials** - Authentication may have expired
        5. **Check service logs** - Look for errors in the {service} logs
        """)
    
    # Retry button
    if retry_available:
        if st.button("🔄 Retry Connection", type="primary"):
            if on_retry:
                on_retry()
            else:
                st.rerun()


def render_fail_fast_notice() -> None:
    """
    Render a notice explaining the fail-fast behavior.
    """
    st.markdown(
        f"""
        <div style="
            background: {COLORS['info']}15;
            border: 1px solid {COLORS['info']};
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
        ">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 1.2rem;">ℹ️</span>
                <span style="font-size: 1rem; font-weight: 600; color: {COLORS['info']};">
                    Fail-Fast Mode Active
                </span>
            </div>
            <div style="color: {COLORS['text_secondary']}; font-size: 0.9rem; line-height: 1.5;">
                This application operates in fail-fast mode. When errors occur, operations 
                stop immediately rather than using fallback data. This ensures you always 
                work with real, accurate data from your network infrastructure.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_error_summary(
    errors: list[dict[str, Any]],
    show_details: bool = True,
) -> None:
    """
    Render a summary of multiple errors.
    
    Args:
        errors: List of error dictionaries
        show_details: Whether to show individual error details
    """
    if not errors:
        return
    
    # Group by type
    by_type: dict[str, list] = {}
    for error in errors:
        error_type = error.get("type", "Unknown")
        if error_type not in by_type:
            by_type[error_type] = []
        by_type[error_type].append(error)
    
    # Summary header
    st.markdown(
        f"""
        <div class="card" style="border: 2px solid {COLORS['error']};">
            <div class="card-header" style="color: {COLORS['error']};">
                <span>❌</span>
                <span>Error Summary: {len(errors)} errors occurred</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Group summaries
    for error_type, error_list in by_type.items():
        with st.expander(f"{error_type} ({len(error_list)})", expanded=show_details):
            for err in error_list:
                st.markdown(f"- {err.get('message', 'Unknown error')}")
