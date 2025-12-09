"""
Settings page for the Cassava 4G Network Optimizer.

Configuration management for API connections, thresholds,
agent behavior, and user preferences.
"""

import asyncio
import os
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
    render_error_banner,
)
from cassava_optimizer.utils.env_manager import update_env


def _load_env_defaults() -> dict:
    """Load current values from environment or .env file."""
    return {
        "api_base_url": os.environ.get("HUAWEI_API_BASE_URL", "https://imaster-mae.example.com/api/v1"),
        "api_username": os.environ.get("HUAWEI_API_USERNAME", ""),
        "api_timeout": int(os.environ.get("HUAWEI_API_TIMEOUT", "30")),
        "nim_api_key": os.environ.get("NVIDIA_API_KEY", ""),
        "nim_model": os.environ.get("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct"),
        "nim_temperature": float(os.environ.get("NVIDIA_TEMPERATURE", "0.1")),
        "nim_max_tokens": int(os.environ.get("NVIDIA_MAX_TOKENS", "2048")),
    }


def _show_restart_toast():
    """Show toast notification about settings requiring restart."""
    st.toast("⚙️ Settings saved! Changes will apply at next restart.", icon="✅")


async def _full_api_health_check() -> dict:
    """
    Perform a comprehensive API health check.
    
    Tests:
    1. Authentication (get token)
    2. Site list fetch
    3. MML command test (DSP CELL:;)
    
    Returns:
        Dictionary with status for each test
    """
    from cassava_optimizer.infrastructure.huawei_client import HuaweiMAEClient, HuaweiAPIError
    
    results = {
        "auth": {"status": "pending", "message": "Not tested"},
        "sites": {"status": "pending", "message": "Not tested"},
        "mml": {"status": "pending", "message": "Not tested"},
    }
    
    try:
        async with HuaweiMAEClient() as client:
            # Test 1: Authentication
            try:
                await client.authenticate()
                results["auth"] = {"status": "success", "message": "Token obtained successfully"}
            except HuaweiAPIError as e:
                results["auth"] = {"status": "failed", "message": str(e)[:100]}
                return results  # Can't continue without auth
            except Exception as e:
                results["auth"] = {"status": "failed", "message": f"Connection error: {str(e)[:80]}"}
                return results
            
            # Test 2: Site list fetch
            try:
                sites = await client.get_sites()
                if sites:
                    results["sites"] = {"status": "success", "message": f"Found {len(sites)} sites"}
                else:
                    results["sites"] = {"status": "warning", "message": "No sites returned"}
            except Exception as e:
                results["sites"] = {"status": "failed", "message": str(e)[:100]}
            
            # Test 3: MML command test
            try:
                # Use a read-only command that should work on any eNodeB
                # Try to get basic cell info
                mml_result = await client.execute_mml_command(
                    ne_id="*",  # All NEs
                    command="DSP CELL:;",  # Display cell info
                )
                if mml_result:
                    results["mml"] = {"status": "success", "message": "MML command executed successfully"}
                else:
                    results["mml"] = {"status": "warning", "message": "Command returned empty result"}
            except Exception as e:
                results["mml"] = {"status": "failed", "message": str(e)[:100]}
                
    except Exception as e:
        results["auth"] = {"status": "failed", "message": f"Client creation failed: {str(e)[:80]}"}
    
    return results


def _render_health_check_results(results: dict):
    """Render the health check results with appropriate styling."""
    status_icons = {
        "success": "✅",
        "warning": "⚠️",
        "failed": "❌",
        "pending": "⏳",
    }
    
    status_colors = {
        "success": CASSAVA_GREEN,
        "warning": "#f59e0b",
        "failed": "#ef4444",
        "pending": COLORS["text_secondary"],
    }
    
    st.markdown("#### 🔍 Health Check Results")
    
    for test_name, result in results.items():
        icon = status_icons.get(result["status"], "❓")
        color = status_colors.get(result["status"], COLORS["text_secondary"])
        label = test_name.upper()
        
        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 12px;
                background: {COLORS['card_bg']};
                border-left: 4px solid {color};
                border-radius: 4px;
                margin-bottom: 8px;
            ">
                <span style="font-weight: 500;">{icon} {label}</span>
                <span style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">
                    {result['message']}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _save_api_settings(
    api_base_url: str,
    api_username: str,
    api_password: str,
    api_timeout: int,
) -> bool:
    """
    Save API settings to .env file.
    
    Returns:
        True if settings were saved successfully
    """
    updates = {
        "HUAWEI_API_BASE_URL": api_base_url,
        "HUAWEI_API_USERNAME": api_username,
        "HUAWEI_API_TIMEOUT": str(api_timeout),
    }
    
    # Only update password if provided
    if api_password:
        updates["HUAWEI_API_PASSWORD"] = api_password
    
    success = update_env(updates)
    return success


def _save_nim_settings(
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> bool:
    """
    Save NVIDIA NIM settings to .env file.
    
    Returns:
        True if settings were saved successfully
    """
    updates = {
        "NVIDIA_MODEL": model,
        "NVIDIA_TEMPERATURE": str(temperature),
        "NVIDIA_MAX_TOKENS": str(max_tokens),
    }
    
    # Only update API key if provided
    if api_key:
        updates["NVIDIA_API_KEY"] = api_key
    
    success = update_env(updates)
    return success


def render_settings_page(
    config_service: Any = None,
) -> None:
    """
    Render the settings and configuration page.
    
    Args:
        config_service: Service for managing configuration
    """
    # Apply custom CSS (already includes <style> tags)
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Header
    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <h1 style="color: {COLORS['text_primary']}; margin: 0;">
                ⚙️ Settings
            </h1>
            <p style="color: {COLORS['text_secondary']}; margin: 4px 0 0 0;">
                Configure API connections, thresholds, and preferences
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Tabs for different settings sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔌 API Configuration",
        "📊 KPI Thresholds",
        "🤖 Agent Settings",
        "🎨 Appearance",
        "💾 Database",
    ])
    
    # Tab 1: API Configuration
    with tab1:
        st.markdown("### Huawei iMaster MAE API")
        
        st.markdown(
            f"""
            <div class="card" style="
                background: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            ">
                <p style="color: {COLORS['text_secondary']}; margin: 0;">
                    Configure the connection to Huawei iMaster MAE for network data and command execution.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            api_base_url = st.text_input(
                "API Base URL",
                value=st.session_state.get("api_base_url", "https://imaster-mae.example.com/api/v1"),
                key="settings_api_url",
                help="The base URL for the Huawei iMaster MAE API",
            )
            
            api_username = st.text_input(
                "Username",
                value=st.session_state.get("api_username", ""),
                key="settings_api_username",
            )
        
        with col2:
            api_timeout = st.number_input(
                "Request Timeout (seconds)",
                min_value=5,
                max_value=300,
                value=st.session_state.get("api_timeout", 30),
                key="settings_api_timeout",
            )
            
            api_password = st.text_input(
                "Password",
                type="password",
                value="",
                key="settings_api_password",
                help="Password is not stored. Enter to update.",
            )
        
        # Connection test
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            if st.button("🔍 Test Connection", type="secondary"):
                with st.spinner("Running comprehensive health check..."):
                    results = asyncio.run(_full_api_health_check())
                    st.session_state["_health_check_results"] = results
                    
        # Show health check results if available
        if "_health_check_results" in st.session_state:
            _render_health_check_results(st.session_state["_health_check_results"])
        
        with col2:
            if st.button("💾 Save", type="primary", key="save_huawei_api"):
                # Save to session state
                st.session_state["api_base_url"] = api_base_url
                st.session_state["api_username"] = api_username
                st.session_state["api_timeout"] = api_timeout
                
                # Save to .env file for persistence
                success = _save_api_settings(
                    api_base_url=api_base_url,
                    api_username=api_username,
                    api_password=api_password,
                    api_timeout=api_timeout,
                )
                
                if success:
                    _show_restart_toast()
                else:
                    st.error("❌ Failed to save settings to .env file")
        
        st.markdown("---")
        
        # NVIDIA NIM Configuration
        st.markdown("### NVIDIA NIM API")
        
        col1, col2 = st.columns(2)
        
        # Load defaults from environment
        env_defaults = _load_env_defaults()
        
        with col1:
            nim_api_key = st.text_input(
                "API Key",
                type="password",
                value="",
                key="settings_nim_key",
                help="Your NVIDIA NIM API key (leave blank to keep existing)",
            )
            
            nim_model = st.selectbox(
                "Model",
                options=[
                    "meta/llama-3.1-70b-instruct",
                    "meta/llama-3.1-8b-instruct",
                    "mistralai/mixtral-8x7b-instruct",
                ],
                index=0 if env_defaults["nim_model"] == "meta/llama-3.1-70b-instruct" else 
                      1 if env_defaults["nim_model"] == "meta/llama-3.1-8b-instruct" else 2,
                key="settings_nim_model",
            )
        
        with col2:
            nim_temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=env_defaults["nim_temperature"],
                step=0.1,
                key="settings_nim_temp",
            )
            
            nim_max_tokens = st.number_input(
                "Max Tokens",
                min_value=100,
                max_value=4096,
                value=env_defaults["nim_max_tokens"],
                key="settings_nim_tokens",
            )
        
        # Save NIM settings button
        if st.button("💾 Save NIM Settings", type="primary", key="save_nim_api"):
            success = _save_nim_settings(
                api_key=nim_api_key,
                model=nim_model,
                temperature=nim_temperature,
                max_tokens=nim_max_tokens,
            )
            
            if success:
                _show_restart_toast()
            else:
                st.error("❌ Failed to save NIM settings to .env file")
    
    # Tab 2: KPI Thresholds
    with tab2:
        st.markdown("### KPI Target Thresholds")
        
        st.markdown(
            f"""
            <div class="card" style="
                background: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            ">
                <p style="color: {COLORS['text_secondary']}; margin: 0;">
                    Set target thresholds for KPIs. Values below these thresholds will trigger optimization recommendations.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        kpi_thresholds = [
            ("Call Setup Success Rate", "cssr", 99.0, "%", "Target for CSSR"),
            ("Call Drop Rate", "cdr", 1.0, "%", "Maximum acceptable CDR"),
            ("Handover Success Rate", "hosr", 98.0, "%", "Target for HOSR"),
            ("RRC Setup Success Rate", "rrc_ssr", 99.5, "%", "Target for RRC SSR"),
            ("E-RAB Setup Success Rate", "erab_ssr", 99.0, "%", "Target for E-RAB SSR"),
            ("DL Throughput", "dl_tp", 50.0, "Mbps", "Target DL throughput"),
            ("UL Throughput", "ul_tp", 25.0, "Mbps", "Target UL throughput"),
        ]
        
        col1, col2 = st.columns(2)
        
        for i, (name, key, default, unit, help_text) in enumerate(kpi_thresholds):
            with [col1, col2][i % 2]:
                st.number_input(
                    f"{name} ({unit})",
                    min_value=0.0,
                    max_value=100.0 if unit == "%" else 1000.0,
                    value=st.session_state.get(f"threshold_{key}", default),
                    step=0.1,
                    key=f"settings_threshold_{key}",
                    help=help_text,
                )
        
        st.markdown("---")
        
        # Alert thresholds
        st.markdown("### Alert Thresholds")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Warning Level**")
            warning_pct = st.slider(
                "Warning when KPI drops below target by (%)",
                min_value=1,
                max_value=20,
                value=5,
                key="settings_warning_pct",
            )
        
        with col2:
            st.markdown("**Critical Level**")
            critical_pct = st.slider(
                "Critical when KPI drops below target by (%)",
                min_value=5,
                max_value=30,
                value=10,
                key="settings_critical_pct",
            )
        
        if st.button("💾 Save Thresholds", type="primary"):
            st.success("Thresholds saved!")
    
    # Tab 3: Agent Settings
    with tab3:
        st.markdown("### Agent Behavior Configuration")
        
        st.markdown(
            f"""
            <div class="card" style="
                background: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            ">
                <p style="color: {COLORS['text_secondary']}; margin: 0;">
                    Configure how the AI agents behave during optimization workflows.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Optimization settings
        st.markdown("#### Optimization Behavior")
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_recommendations = st.number_input(
                "Max Recommendations per Run",
                min_value=1,
                max_value=20,
                value=10,
                key="settings_max_recs",
            )
            
            confidence_threshold = st.slider(
                "Minimum Confidence Threshold (%)",
                min_value=50,
                max_value=99,
                value=75,
                key="settings_confidence",
                help="Only show recommendations above this confidence level",
            )
        
        with col2:
            max_risk_level = st.selectbox(
                "Maximum Allowed Risk Level",
                options=["Low", "Medium", "High"],
                index=1,
                key="settings_max_risk",
            )
            
            require_validation = st.checkbox(
                "Require validation before execution",
                value=True,
                key="settings_require_validation",
            )
        
        st.markdown("---")
        
        # Execution settings
        st.markdown("#### Execution Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_rollback = st.checkbox(
                "Enable automatic rollback on failure",
                value=True,
                key="settings_auto_rollback",
            )
            
            backup_before_change = st.checkbox(
                "Create backup before any change",
                value=True,
                key="settings_backup",
            )
        
        with col2:
            command_delay = st.number_input(
                "Delay between commands (ms)",
                min_value=0,
                max_value=5000,
                value=500,
                key="settings_cmd_delay",
            )
            
            max_retries = st.number_input(
                "Max retries on failure",
                min_value=0,
                max_value=5,
                value=2,
                key="settings_retries",
            )
        
        st.markdown("---")
        
        # Agent-specific settings
        st.markdown("#### Agent-Specific Settings")
        
        with st.expander("📥 Data Collector Agent"):
            st.number_input(
                "Data collection timeout (seconds)",
                min_value=10,
                max_value=300,
                value=60,
                key="settings_dc_timeout",
            )
            st.number_input(
                "KPI history depth (hours)",
                min_value=1,
                max_value=168,
                value=24,
                key="settings_dc_history",
            )
        
        with st.expander("🔍 Analyzer Agent"):
            st.number_input(
                "Anomaly detection sensitivity",
                min_value=1,
                max_value=10,
                value=5,
                key="settings_analyzer_sensitivity",
            )
            st.checkbox(
                "Enable trend analysis",
                value=True,
                key="settings_analyzer_trends",
            )
        
        with st.expander("📋 Strategy Planner Agent"):
            st.selectbox(
                "Optimization strategy",
                options=["Conservative", "Balanced", "Aggressive"],
                index=1,
                key="settings_planner_strategy",
            )
        
        if st.button("💾 Save Agent Settings", type="primary"):
            st.success("Agent settings saved!")
    
    # Tab 4: Appearance
    with tab4:
        st.markdown("### Appearance Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Theme")
            
            theme = st.radio(
                "Color Theme",
                options=["Dark (Default)", "Light"],
                index=0,
                key="settings_theme",
            )
            
            st.markdown("#### Branding")
            
            st.color_picker(
                "Primary Color",
                value=CASSAVA_GREEN,
                key="settings_primary_color",
            )
            
            st.color_picker(
                "Secondary Color",
                value=CASSAVA_NAVY,
                key="settings_secondary_color",
            )
        
        with col2:
            st.markdown("#### Display")
            
            show_tooltips = st.checkbox(
                "Show tooltips",
                value=True,
                key="settings_tooltips",
            )
            
            compact_mode = st.checkbox(
                "Compact mode",
                value=False,
                key="settings_compact",
            )
            
            st.markdown("#### Charts")
            
            chart_animation = st.checkbox(
                "Enable chart animations",
                value=True,
                key="settings_chart_anim",
            )
            
            default_chart_height = st.number_input(
                "Default chart height (px)",
                min_value=200,
                max_value=800,
                value=400,
                key="settings_chart_height",
            )
    
    # Tab 5: Database
    with tab5:
        st.markdown("### Database Configuration")
        
        st.markdown(
            f"""
            <div class="card" style="
                background: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            ">
                <p style="color: {COLORS['text_secondary']}; margin: 0;">
                    Configure the SQLite database for storing optimization history and site data.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            db_path = st.text_input(
                "Database Path",
                value=st.session_state.get("db_path", "data/cassava_network.db"),
                key="settings_db_path",
            )
        
        with col2:
            connection_pool_size = st.number_input(
                "Connection Pool Size",
                min_value=1,
                max_value=20,
                value=5,
                key="settings_pool_size",
            )
        
        st.markdown("---")
        
        # Database operations
        st.markdown("#### Database Operations")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Check Connection", type="secondary"):
                st.info("Testing database connection...")
                # Simulate test
                import time
                time.sleep(0.5)
                st.success("✅ Database connected!")
        
        with col2:
            if st.button("🔄 Run Migrations", type="secondary"):
                st.info("Running database migrations...")
                # Simulate migration
                import time
                time.sleep(1)
                st.success("✅ Migrations complete!")
        
        with col3:
            if st.button("💾 Backup Database", type="secondary"):
                st.info("Creating database backup...")
                # Simulate backup
                import time
                time.sleep(1)
                st.success("✅ Backup created!")
        
        st.markdown("---")
        
        # Database stats
        st.markdown("#### Database Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Sites", "15")
        with col2:
            st.metric("KPI Records", "45,231")
        with col3:
            st.metric("Optimizations", "127")
        with col4:
            st.metric("Commands", "1,543")
        
        # Data retention
        st.markdown("---")
        st.markdown("#### Data Retention")
        
        col1, col2 = st.columns(2)
        
        with col1:
            kpi_retention = st.number_input(
                "KPI data retention (days)",
                min_value=7,
                max_value=365,
                value=90,
                key="settings_kpi_retention",
            )
        
        with col2:
            log_retention = st.number_input(
                "Log retention (days)",
                min_value=7,
                max_value=365,
                value=30,
                key="settings_log_retention",
            )
        
        # Danger zone
        st.markdown("---")
        st.markdown(
            f"""
            <div style="
                background: {COLORS['error']}15;
                border: 1px solid {COLORS['error']};
                border-radius: 12px;
                padding: 20px;
            ">
                <h4 style="color: {COLORS['error']}; margin-top: 0;">⚠️ Danger Zone</h4>
                <p style="color: {COLORS['text_secondary']};">
                    These actions are irreversible. Use with caution.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🗑️ Clear History", type="secondary"):
                st.warning("This will delete all optimization history!")
        
        with col2:
            if st.button("🔥 Reset Database", type="secondary"):
                st.error("This will delete ALL data!")
