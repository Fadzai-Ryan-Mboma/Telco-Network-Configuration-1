"""
Main Streamlit Application Entry Point.

Cassava 4G Network Optimizer - AI-Powered Network Optimization Dashboard
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

import streamlit as st

from cassava_optimizer.ui.theme import (
    CASSAVA_GREEN,
    CASSAVA_NAVY,
    CASSAVA_PURPLE,
    COLORS,
    get_custom_css,
)
from cassava_optimizer.ui.pages import (
    render_dashboard_page,
    render_optimization_page,
    render_history_page,
    render_settings_page,
)


# Page configuration
st.set_page_config(
    page_title="Cassava 4G Network Optimizer",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/cassava/network-optimizer",
        "Report a bug": "https://github.com/cassava/network-optimizer/issues",
        "About": "# Cassava 4G Network Optimizer\nAI-Powered Network Optimization Platform",
    },
)


async def _check_api_connection() -> tuple[bool, str]:
    """
    Check if the Huawei API is reachable.
    
    Returns:
        Tuple of (is_connected, message)
    """
    try:
        from cassava_optimizer.infrastructure.huawei_client import HuaweiMAEClient
        
        host = os.environ.get("MAE_HOST", os.environ.get("HUAWEI_API_HOST", "41.174.191.214"))
        port = int(os.environ.get("MAE_PORT", os.environ.get("HUAWEI_API_PORT", "31127")))
        username = os.environ.get("MAE_USERNAME", os.environ.get("HUAWEI_API_USERNAME", "cassava.ai"))
        password = os.environ.get("MAE_PASSWORD", os.environ.get("HUAWEI_API_PASSWORD", "#Pass123#"))
        
        async with HuaweiMAEClient(
            host=host,
            port=port,
            username=username,
            password=password,
            timeout=10.0,
        ) as client:
            await client.authenticate()
            return True, "Connected"
    except Exception as e:
        return False, str(e)[:50]


async def _check_database_connection() -> tuple[bool, str]:
    """
    Check if the database is accessible.
    
    Returns:
        Tuple of (is_connected, db_name)
    """
    try:
        from cassava_optimizer.services import get_site_service
        service = get_site_service()
        # Try to list sites to verify DB is working
        sites = await service.list_sites()
        return True, f"{len(sites)} sites"
    except Exception as e:
        return False, str(e)[:30]


def _get_cached_status() -> dict:
    """Get cached connection status or check fresh."""
    import time
    
    cache_key = "_connection_status_cache"
    cache_time_key = "_connection_status_time"
    cache_ttl = 30  # Cache for 30 seconds
    
    current_time = time.time()
    
    # Check if cache is valid
    if (cache_key in st.session_state and 
        cache_time_key in st.session_state and
        current_time - st.session_state[cache_time_key] < cache_ttl):
        return st.session_state[cache_key]
    
    # Refresh status
    try:
        api_connected, api_msg = asyncio.run(_check_api_connection())
    except Exception:
        api_connected, api_msg = False, "Error"
    
    try:
        db_connected, db_msg = asyncio.run(_check_database_connection())
    except Exception:
        db_connected, db_msg = False, "Error"
    
    status = {
        "api_connected": api_connected,
        "api_message": api_msg,
        "db_connected": db_connected,
        "db_message": db_msg,
    }
    
    # Cache the result
    st.session_state[cache_key] = status
    st.session_state[cache_time_key] = current_time
    
    return status


def init_session_state() -> None:
    """Initialize session state variables."""
    defaults = {
        "selected_site": None,
        "current_page": "Dashboard",
        "optimization_state": "idle",
        "optimization_results": None,
        "agent_statuses": {},
        "approved_recommendations": [],
        "dark_mode": True,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar() -> str:
    """
    Render the sidebar navigation.
    
    Returns:
        Selected page name
    """
    with st.sidebar:
        # Logo and branding - using Cassava icon SVG
        st.markdown(
            f"""
            <div style="
                text-align: center;
                padding: 20px 0;
                border-bottom: 1px solid {COLORS['border']};
                margin-bottom: 20px;
            ">
                <div style="margin-bottom: 8px;">
                    <svg width="60" height="60" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                        <path fill="#00f19c" d="M0,0h31.01C31.55,0,32,.45,32,.99v31.01H.99c-.55,0-.99-.45-.99-.99V0h0Z"/>
                        <path fill="#001c5c" d="M9.32,27.09c-1.19,0-2.2-.2-3.05-.61-.85-.4-1.5-.95-1.95-1.65-.45-.7-.68-1.48-.68-2.34s.22-1.69.66-2.37c.44-.68,1.14-1.21,2.1-1.59.96-.39,2.21-.58,3.75-.58h4.03v2.57h-3.56c-1.03,0-1.74.17-2.13.51-.39.34-.58.76-.58,1.27,0,.56.22,1.01.66,1.34.44.33,1.05.49,1.82.49s1.39-.17,1.98-.52c.58-.35,1.01-.86,1.27-1.54l.68,2.03c-.32.98-.9,1.72-1.75,2.23-.85.51-1.94.76-3.27.76ZM13.95,26.86v-2.96l-.28-.65v-5.3c0-.94-.29-1.67-.86-2.2-.57-.53-1.45-.79-2.64-.79-.81,0-1.6.13-2.38.38-.78.25-1.44.6-1.99,1.03l-1.58-3.08c.83-.58,1.82-1.03,2.99-1.35,1.17-.32,2.35-.48,3.56-.48,2.31,0,4.11.55,5.39,1.64,1.28,1.09,1.92,2.79,1.92,5.11v8.66h-4.12Z"/>
                        <path fill="#001c5c" d="M24.24,9.56c-.81,0-1.47-.23-1.98-.71-.51-.47-.76-1.05-.76-1.75s.25-1.28.76-1.75c.51-.47,1.17-.71,1.98-.71s1.47.22,1.98.66c.51.44.76,1.01.76,1.71,0,.73-.25,1.34-.75,1.82-.5.48-1.16.72-1.99.72ZM22.04,26.86v-15.18h4.4v15.18h-4.4Z"/>
                    </svg>
                </div>
                <div style="
                    font-size: 1.2rem;
                    font-weight: 700;
                    color: {COLORS['text_primary']};
                ">Cassava Network</div>
                <div style="
                    font-size: 0.9rem;
                    color: {CASSAVA_GREEN};
                ">4G Optimizer</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Navigation
        st.markdown(
            f"<div style='color: {COLORS['text_secondary']}; font-size: 0.8rem; margin-bottom: 8px;'>NAVIGATION</div>",
            unsafe_allow_html=True,
        )
        
        pages = {
            "📊 Dashboard": "Dashboard",
            "🚀 Optimization": "Optimization",
            "📜 History": "History",
            "⚙️ Settings": "Settings",
        }
        
        # Check for navigation from other pages
        if "navigate_to" in st.session_state:
            target = st.session_state.pop("navigate_to")
            st.session_state["current_page"] = target.title()
        
        selected = st.radio(
            "Navigation",
            options=list(pages.keys()),
            index=list(pages.values()).index(st.session_state.get("current_page", "Dashboard")),
            label_visibility="collapsed",
            key="nav_radio",
        )
        
        selected_page = pages[selected]
        st.session_state["current_page"] = selected_page
        
        st.markdown("---")
        
        # Quick status - REAL connection checks
        st.markdown(
            f"<div style='color: {COLORS['text_secondary']}; font-size: 0.8rem; margin-bottom: 8px;'>STATUS</div>",
            unsafe_allow_html=True,
        )
        
        # Get real connection status (cached for 30s)
        status = _get_cached_status()
        
        api_color = CASSAVA_GREEN if status["api_connected"] else COLORS["error"]
        api_status_text = "API Connected" if status["api_connected"] else "API Offline"
        api_detail = "iMaster MAE" if status["api_connected"] else status["api_message"]
        
        # Connection status indicator
        st.markdown(
            f"""
            <div style="
                display: flex;
                align-items: center;
                padding: 12px;
                background: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-bottom: 12px;
            ">
                <div style="
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    background: {api_color};
                    margin-right: 10px;
                "></div>
                <div>
                    <div style="color: {COLORS['text_primary']}; font-size: 0.9rem;">{api_status_text}</div>
                    <div style="color: {COLORS['text_secondary']}; font-size: 0.75rem;">{api_detail}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        db_color = CASSAVA_GREEN if status["db_connected"] else COLORS["error"]
        db_status_text = "Database Online" if status["db_connected"] else "Database Offline"
        db_detail = status["db_message"] if status["db_connected"] else status["db_message"]
        
        # Database status
        st.markdown(
            f"""
            <div style="
                display: flex;
                align-items: center;
                padding: 12px;
                background: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-bottom: 12px;
            ">
                <div style="
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    background: {db_color};
                    margin-right: 10px;
                "></div>
                <div>
                    <div style="color: {COLORS['text_primary']}; font-size: 0.9rem;">{db_status_text}</div>
                    <div style="color: {COLORS['text_secondary']}; font-size: 0.75rem;">{db_detail}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Selected site
        if st.session_state.get("selected_site"):
            st.markdown(
                f"""
                <div style="
                    padding: 12px;
                    background: {CASSAVA_GREEN}15;
                    border: 1px solid {CASSAVA_GREEN}40;
                    border-radius: 8px;
                    margin-bottom: 12px;
                ">
                    <div style="color: {COLORS['text_secondary']}; font-size: 0.75rem;">SELECTED SITE</div>
                    <div style="color: {CASSAVA_GREEN}; font-size: 1rem; font-weight: 600;">
                        📡 {st.session_state['selected_site']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        st.markdown("---")
        
        # Footer
        st.markdown(
            f"""
            <div style="
                text-align: center;
                padding: 16px 0;
                color: {COLORS['text_secondary']};
                font-size: 0.75rem;
            ">
                <div>Cassava Network Optimizer</div>
                <div>v1.0.0</div>
                <div style="margin-top: 8px;">
                    <span style="color: {CASSAVA_GREEN};">●</span> Powered by NVIDIA NIM
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        return selected_page


def main() -> None:
    """Main application entry point."""
    # Initialize session state
    init_session_state()
    
    # Apply global CSS (already includes <style> tags)
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Render sidebar and get selected page
    selected_page = render_sidebar()
    
    # Route to appropriate page
    if selected_page == "Dashboard":
        render_dashboard_page()
    elif selected_page == "Optimization":
        render_optimization_page()
    elif selected_page == "History":
        render_history_page()
    elif selected_page == "Settings":
        render_settings_page()
    else:
        st.error(f"Unknown page: {selected_page}")


if __name__ == "__main__":
    main()
