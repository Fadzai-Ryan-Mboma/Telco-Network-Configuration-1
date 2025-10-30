"""
Streamlit Web UI

Web interface for the network optimization system.
"""

import streamlit as st
import requests
from datetime import datetime
import pandas as pd

# Configuration
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Liquid 4G Network Optimizer",
    page_icon="📡",
    layout="wide"
)

# Title
st.title("📡 Liquid 4G Network Optimizer")
st.markdown("AI-Powered Network Optimization System")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Sites & Cells", "KPIs", "Operations", "Agents", "Optimize"])

# === Dashboard ===
if page == "Dashboard":
    st.header("Dashboard")

    col1, col2, col3 = st.columns(3)

    # Statistics
    try:
        stats = requests.get(f"{API_URL}/api/v1/statistics/operations").json()
        kpi_stats = requests.get(f"{API_URL}/api/v1/statistics/kpis").json()

        with col1:
            st.metric("Total Operations", stats.get("total_operations", 0))

        with col2:
            st.metric("Active Alerts", kpi_stats.get("active_alerts", 0))

        with col3:
            st.metric("Total KPIs", kpi_stats.get("total_kpi_measurements", 0))

    except Exception as e:
        st.error(f"Error loading statistics: {e}")

    # Recent operations
    st.subheader("Recent Operations")
    try:
        operations = requests.get(f"{API_URL}/api/v1/operations?limit=10").json()
        if operations["total"] > 0:
            df = pd.DataFrame(operations["operations"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No operations yet")
    except Exception as e:
        st.error(f"Error loading operations: {e}")

# === Sites & Cells ===
elif page == "Sites & Cells":
    st.header("Sites & Cells")

    # List sites
    try:
        sites = requests.get(f"{API_URL}/api/v1/sites").json()

        if sites["total"] > 0:
            site_ids = [s["site_id"] for s in sites["sites"]]
            selected_site = st.selectbox("Select Site", site_ids)

            if selected_site:
                site_data = requests.get(f"{API_URL}/api/v1/sites/{selected_site}").json()

                st.subheader(f"Site: {site_data['site']['site_name']}")
                st.write(f"**Location:** {site_data['site']['location']}")
                st.write(f"**Status:** {site_data['site']['status']}")
                st.write(f"**Region:** {site_data['site']['region']}")

                st.subheader("Cells")
                if site_data["cells"]:
                    df = pd.DataFrame(site_data["cells"])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No cells in this site")
        else:
            st.warning("No sites found. Initialize the database first.")

    except Exception as e:
        st.error(f"Error loading sites: {e}")

# === KPIs ===
elif page == "KPIs":
    st.header("KPI Monitoring")

    cell_id = st.text_input("Enter Cell ID", "HAR_001_1")

    if st.button("Load KPIs"):
        try:
            kpis = requests.get(f"{API_URL}/api/v1/cells/{cell_id}/kpis").json()

            if "kpis" in kpis and kpis["kpis"]:
                st.success(f"Loaded {len(kpis['kpis'])} KPIs for {cell_id}")

                for kpi in kpis["kpis"]:
                    st.metric(
                        label=kpi["kpi_key"],
                        value=f"{kpi['value']:.2f}",
                        delta=None
                    )
            else:
                st.warning(f"No KPIs found for cell {cell_id}")

        except Exception as e:
            st.error(f"Error loading KPIs: {e}")

# === Operations ===
elif page == "Operations":
    st.header("Operations")

    status_filter = st.selectbox("Filter by Status", ["All", "pending", "running", "completed", "failed"])

    try:
        if status_filter == "All":
            operations = requests.get(f"{API_URL}/api/v1/operations").json()
        else:
            operations = requests.get(f"{API_URL}/api/v1/operations?status={status_filter}").json()

        if operations["total"] > 0:
            st.write(f"Found {operations['total']} operations")
            df = pd.DataFrame(operations["operations"])
            st.dataframe(df, use_container_width=True)

            # Operation details
            selected_op = st.selectbox("View Details", [op["operation_id"] for op in operations["operations"]])

            if selected_op and st.button("Load Details"):
                op_data = requests.get(f"{API_URL}/api/v1/operations/{selected_op}").json()
                st.json(op_data)
        else:
            st.info("No operations found")

    except Exception as e:
        st.error(f"Error loading operations: {e}")

# === Agents ===
elif page == "Agents":
    st.header("Agent Status")

    try:
        agents = requests.get(f"{API_URL}/api/v1/agents").json()

        if "agents" in agents:
            for agent in agents["agents"]:
                with st.expander(f"{agent['display_name']} ({agent['agent_id']})"):
                    st.write(f"**Type:** {agent['agent_type']}")
                    st.write(f"**Status:** {agent['status']}")
                    st.write("**Metrics:**")
                    st.json(agent["metrics"])
        else:
            st.info("No agents found")

    except Exception as e:
        st.error(f"Error loading agents: {e}")

# === Optimize ===
elif page == "Optimize":
    st.header("Run Optimization")

    optimization_type = st.radio("Optimization Type", ["Single Cell", "Entire Site"])

    if optimization_type == "Single Cell":
        cell_id = st.text_input("Cell ID", "HAR_001_1")
        auto_execute = st.checkbox("Auto-execute approved changes", value=False)

        if st.button("Start Optimization"):
            try:
                response = requests.post(
                    f"{API_URL}/api/v1/optimize/cell",
                    json={"cell_id": cell_id, "auto_execute": auto_execute}
                )
                if response.status_code == 200:
                    st.success(f"Optimization started for cell {cell_id}")
                    st.json(response.json())
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Error starting optimization: {e}")

    else:
        site_id = st.text_input("Site ID", "HAR_001")
        auto_execute = st.checkbox("Auto-execute approved changes", value=False)

        if st.button("Start Site Optimization"):
            try:
                response = requests.post(
                    f"{API_URL}/api/v1/optimize/site",
                    json={"site_id": site_id, "auto_execute": auto_execute}
                )
                if response.status_code == 200:
                    st.success(f"Site optimization started for {site_id}")
                    st.json(response.json())
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Error starting optimization: {e}")

    st.markdown("---")
    st.info("**Note:** Optimizations run in the background. Check the Operations page for status.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Liquid Zimbabwe 4G Network Optimizer v2.0**")
st.sidebar.markdown("Powered by AI and LangChain")
