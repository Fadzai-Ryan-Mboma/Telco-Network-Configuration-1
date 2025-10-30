#!/usr/bin/env python3
"""
Agentic Operator UI Components for Liquid Zimbabwe 4G Network Optimizer
Provides intelligent automation interface for network management operations
Enhanced with persistent database integration
"""

import streamlit as st
import os
import json
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger('LZ-Agentic-UI')

# Import database integration
try:
    from agentic_database import AgenticDatabase
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    AgenticDatabase = None
    logger.warning("Database integration not available")

def render_agentic_operator_interface():
    """Main agentic operator interface with database integration and query system"""
    st.header("🤖 Agentic Network Operator")
    st.markdown("Intelligent automation and orchestration for network management operations")
    
    # Initialize database connection
    if DB_AVAILABLE and AgenticDatabase:
        try:
            db = AgenticDatabase()
            st.session_state.agentic_db = db
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            st.session_state.agentic_db = None
    else:
        st.session_state.agentic_db = None
    
    # Quick status overview
    render_agent_status_overview()
    
    # Stage 1.3: Natural Language Query Interface
    st.markdown("---")
    render_query_interface()
    
    # Stage 1.3: 4-Tab Output System
    render_query_results_tabs()
    
    # Main operation areas
    st.markdown("---")
    st.subheader("🎛️ Advanced Operations Dashboard")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_operation_center()
    
    with col2:
        render_agent_controls()
    
    # Operation history and logs
    st.markdown("---")
    render_operation_history()

def render_agent_status_overview():
    """Display current agent status and capabilities with database integration"""
    st.subheader("🔍 Agent Status Overview")
    
    # Get real metrics from database
    db = st.session_state.get('agentic_db')
    if db:
        try:
            metrics = db.get_current_metrics()
            
            # Agent status metrics
            status_col1, status_col2, status_col3, status_col4 = st.columns(4)
            
            with status_col1:
                st.metric("Active Agents", metrics.get("active_agents", 3), delta="+1")
            
            with status_col2:
                st.metric("Operations Today", metrics.get("operations_today", 12), delta="+2")
            
            with status_col3:
                st.metric("Success Rate", f"{metrics.get('success_rate', 95.8):.1f}%", delta="+2.1%")
            
            with status_col4:
                st.metric("Auto-Optimizations", metrics.get("auto_optimizations", 7), delta="+1")
                
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")
            # Fallback to default metrics
            render_default_metrics()
    else:
        render_default_metrics()
    
    # Agent capabilities overview
    st.markdown("**Available Agent Capabilities:**")
    capabilities = [
        "🔍 Parameter Monitoring & Analysis",
        "⚙️ Automated Configuration Optimization", 
        "📊 Performance Trend Analysis",
        "🚨 Anomaly Detection & Alerting",
        "🔄 Automated Parameter Tuning"
    ]
    
    cap_col1, cap_col2 = st.columns(2)
    for i, cap in enumerate(capabilities):
        if i % 2 == 0:
            cap_col1.markdown(f"✅ {cap}")
        else:
            cap_col2.markdown(f"✅ {cap}")

def render_default_metrics():
    """Render default metrics when database is unavailable"""
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    
    with status_col1:
        st.metric("Active Agents", "3", delta="+1")
    
    with status_col2:
        st.metric("Operations Today", "12", delta="+2")
    
    with status_col3:
        st.metric("Success Rate", "95.8%", delta="+2.1%")
    
    with status_col4:
        st.metric("Auto-Optimizations", "7", delta="+1")

def render_operation_center():
    """Main operation center for agentic tasks"""
    st.subheader("🎯 Operation Center")
    
    # Operation type selection
    operation_type = st.selectbox(
        "Select Operation Type:",
        [
            "Parameter Optimization",
            "Network Analysis", 
            "Automated Monitoring",
            "Performance Tuning",
            "Anomaly Investigation"
        ]
    )
    
    # Dynamic operation interface based on selection
    if operation_type == "Parameter Optimization":
        render_parameter_optimization_interface()
    elif operation_type == "Network Analysis":
        render_network_analysis_interface()
    elif operation_type == "Automated Monitoring":
        render_monitoring_interface()
    elif operation_type == "Performance Tuning":
        render_performance_tuning_interface()
    elif operation_type == "Anomaly Investigation":
        render_anomaly_investigation_interface()

def render_parameter_optimization_interface():
    """Interface for automated parameter optimization with database integration"""
    st.markdown("**🔧 Automated Parameter Optimization**")
    
    # Target selection
    target_col1, target_col2 = st.columns(2)
    
    with target_col1:
        optimization_target = st.selectbox(
            "Optimization Target:",
            ["All Sites", "Specific Site", "Site Group", "Problem Areas"]
        )
    
    with target_col2:
        optimization_goal = st.selectbox(
            "Optimization Goal:",
            ["Maximize Throughput", "Improve Coverage", "Reduce Interference", "Balance Load"]
        )
    
    # Parameters to optimize
    st.markdown("**Parameters to Include:**")
    param_col1, param_col2 = st.columns(2)
    
    with param_col1:
        ref_signal = st.checkbox("📡 Reference Signal Power", value=True)
        a3_offset = st.checkbox("⚡ A3 Event Offset", value=True)
        t310_timer = st.checkbox("⏱️ T310 Timer", value=False)
    
    with param_col2:
        p0_nominal = st.checkbox("📶 P0 Nominal PUSCH", value=True)
        pdcch_agg = st.checkbox("🔄 PDCCH Aggregation", value=False)
        custom_params = st.checkbox("🎯 Custom Parameters", value=False)
    
    # Execution controls
    exec_col1, exec_col2 = st.columns(2)
    
    with exec_col1:
        if st.button("🚀 Start Optimization", type="primary"):
            # Create database operation
            db = st.session_state.get('agentic_db')
            if db:
                try:
                    # Build parameters dict
                    parameters = {
                        "target": optimization_target,
                        "goal": optimization_goal,
                        "parameters": {
                            "reference_signal_power": ref_signal,
                            "a3_event_offset": a3_offset,
                            "t310_timer": t310_timer,
                            "p0_nominal_pusch": p0_nominal,
                            "pdcch_aggregation": pdcch_agg,
                            "custom_parameters": custom_params
                        }
                    }
                    
                    # Create operation in database
                    operation_id = db.create_operation(
                        operation_type="Parameter Optimization",
                        target_site=optimization_target if optimization_target != "All Sites" else None,
                        parameters=parameters,
                        agent_name="Optimizer Agent"
                    )
                    
                    if operation_id:
                        st.success(f"✅ Optimization operation created: {operation_id}")
                        
                        # Simulate operation progress
                        with st.spinner("Starting optimization analysis..."):
                            db.add_operation_log(operation_id, "Analysis phase: Collecting baseline metrics")
                            
                            # Update to in progress
                            db.update_operation_status(operation_id, "in_progress")
                            db.add_operation_log(operation_id, "Optimization parameters calculated")
                            
                            # Simulate completion
                            results = {
                                "baseline_throughput": "87.2 Mbps",
                                "optimized_throughput": "92.1 Mbps",
                                "improvement": "5.6%",
                                "parameters_changed": 3
                            }
                            
                            db.update_operation_status(operation_id, "completed", results)
                            db.add_operation_log(operation_id, "Optimization completed successfully", details=results)
                            
                        st.info("🔄 Check Operation History for detailed progress")
                    else:
                        st.error("❌ Failed to create optimization operation")
                        
                except Exception as e:
                    st.error(f"❌ Operation failed: {e}")
            else:
                # Fallback to simple success message
                st.success("✅ Optimization agent activated!")
                st.info("🔄 Analysis phase: Collecting baseline metrics...")
    
    with exec_col2:
        simulation_mode = st.checkbox("🧪 Simulation Mode", value=True)
        if simulation_mode:
            st.caption("Changes will be simulated first")

def render_network_analysis_interface():
    """Interface for intelligent network analysis"""
    st.markdown("**📊 Intelligent Network Analysis**")
    
    analysis_type = st.radio(
        "Analysis Type:",
        ["Full Network Health Check", "Performance Bottleneck Analysis", "Coverage Gap Detection", "Interference Analysis"]
    )
    
    # Analysis configuration
    config_col1, config_col2 = st.columns(2)
    
    with config_col1:
        time_range = st.selectbox("Time Range:", ["Last Hour", "Last 24 Hours", "Last Week", "Custom Range"])
        include_predictions = st.checkbox("🔮 Include AI Predictions", value=True)
    
    with config_col2:
        detail_level = st.selectbox("Detail Level:", ["Summary", "Detailed", "Expert"])
        auto_recommendations = st.checkbox("💡 Auto-generate Recommendations", value=True)
    
    if st.button("🔍 Start Analysis", type="primary"):
        with st.spinner("Analyzing network data..."):
            st.success("✅ Analysis complete!")
            
            # Mock analysis results
            st.markdown("**🎯 Key Findings:**")
            st.markdown("- 📈 Average throughput: 89.2 Mbps (+5.3% vs baseline)")
            st.markdown("- 🎯 Coverage efficiency: 94.1% (Above target)")
            st.markdown("- ⚠️ 2 sites showing elevated interference")
            st.markdown("- 💡 3 optimization opportunities identified")

def render_monitoring_interface():
    """Interface for automated monitoring configuration"""
    st.markdown("**👁️ Automated Monitoring Setup**")
    
    monitor_col1, monitor_col2 = st.columns(2)
    
    with monitor_col1:
        st.markdown("**Monitoring Targets:**")
        st.checkbox("📊 KPI Thresholds", value=True)
        st.checkbox("🚨 Alarm Conditions", value=True)
        st.checkbox("📉 Performance Degradation", value=True)
        st.checkbox("🔄 Configuration Drift", value=False)
    
    with monitor_col2:
        st.markdown("**Alert Configuration:**")
        alert_method = st.selectbox("Alert Method:", ["Dashboard", "Email", "SMS", "Webhook"])
        alert_frequency = st.selectbox("Check Frequency:", ["Real-time", "5 minutes", "15 minutes", "Hourly"])
    
    if st.button("⚡ Activate Monitoring", type="primary"):
        st.success("✅ Automated monitoring activated!")
        st.info("🔄 Agent will monitor and alert on configured conditions")

def render_performance_tuning_interface():
    """Interface for automated performance tuning"""
    st.markdown("**⚡ Automated Performance Tuning**")
    
    tuning_col1, tuning_col2 = st.columns(2)
    
    with tuning_col1:
        st.markdown("**Tuning Focus:**")
        focus_area = st.radio("", ["Throughput Optimization", "Latency Reduction", "Capacity Enhancement", "Energy Efficiency"])
    
    with tuning_col2:
        st.markdown("**Constraints:**")
        st.slider("Max Change per Parameter (%)", 0, 20, 5)
        st.checkbox("Require Manual Approval", value=True)
    
    if st.button("🎯 Start Tuning", type="primary"):
        st.success("✅ Performance tuning initiated!")

def render_anomaly_investigation_interface():
    """Interface for anomaly investigation"""
    st.markdown("**🔍 Anomaly Investigation**")
    
    st.markdown("**Recent Anomalies Detected:**")
    
    # Mock anomaly data
    anomalies = [
        {"site": "HARARE_CENTRAL_01", "type": "Throughput Drop", "severity": "Medium", "time": "14:23"},
        {"site": "BULAWAYO_WEST_03", "type": "High Interference", "severity": "High", "time": "13:45"},
        {"site": "MUTARE_EAST_02", "type": "Coverage Gap", "severity": "Low", "time": "12:30"}
    ]
    
    for anomaly in anomalies:
        severity_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[anomaly["severity"]]
        with st.expander(f"{severity_color} {anomaly['site']} - {anomaly['type']} ({anomaly['time']})"):
            st.markdown(f"**Severity:** {anomaly['severity']}")
            st.markdown(f"**Detection Time:** {anomaly['time']}")
            st.markdown("**Suggested Actions:**")
            if st.button(f"🔍 Investigate {anomaly['site']}", key=f"investigate_{anomaly['site']}"):
                st.info("🤖 Agent dispatched for detailed investigation...")

def render_agent_controls():
    """Agent control panel with database integration"""
    st.subheader("🎛️ Agent Controls")
    
    # Get real agent status from database
    db = st.session_state.get('agentic_db')
    if db:
        try:
            agents = db.get_agent_status()
            
            st.markdown("**🤖 Agent Status:**")
            for agent in agents:
                with st.container():
                    # Status emoji mapping
                    status_emoji = {
                        "active": "🟢",
                        "standby": "🟡", 
                        "error": "🔴",
                        "offline": "⚫"
                    }
                    
                    emoji = status_emoji.get(agent['status'], "❓")
                    st.markdown(f"**{agent['agent_name']}**")
                    st.markdown(f"Status: {emoji} {agent['status'].title()}")
                    st.markdown(f"Active Tasks: {agent['active_tasks']}")
                    
                    # Agent control buttons
                    control_col1, control_col2 = st.columns(2)
                    with control_col1:
                        if st.button(f"⏸️ Pause", key=f"pause_{agent['agent_name']}"):
                            db.update_agent_status(agent['agent_name'], "standby", 0)
                            st.rerun()
                    with control_col2:
                        if st.button(f"▶️ Resume", key=f"resume_{agent['agent_name']}"):
                            db.update_agent_status(agent['agent_name'], "active")
                            st.rerun()
                    
                    st.markdown("---")
                    
        except Exception as e:
            logger.error(f"Failed to load agent status: {e}")
            render_default_agent_status()
    else:
        render_default_agent_status()
    
    # Global controls
    st.markdown("**🎛️ Global Controls:**")
    
    global_col1, global_col2 = st.columns(2)
    
    with global_col1:
        if st.button("⏸️ Pause All"):
            if db:
                try:
                    agents = db.get_agent_status()
                    for agent in agents:
                        db.update_agent_status(agent['agent_name'], "standby", 0)
                    st.warning("All agents paused")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to pause agents: {e}")
            else:
                st.warning("All agents paused")
    
    with global_col2:
        if st.button("🔄 Restart All"):
            if db:
                try:
                    agents = db.get_agent_status()
                    for agent in agents:
                        db.update_agent_status(agent['agent_name'], "active")
                    st.success("All agents restarted")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to restart agents: {e}")
            else:
                st.info("Agents restarting...")

def render_default_agent_status():
    """Render default agent status when database is unavailable"""
    st.markdown("**🤖 Agent Status:**")
    agents = [
        {"name": "Monitor Agent", "status": "🟢 Active", "tasks": 3},
        {"name": "Optimizer Agent", "status": "🟡 Standby", "tasks": 0}, 
        {"name": "Analyzer Agent", "status": "🟢 Active", "tasks": 1}
    ]
    
    for agent in agents:
        with st.container():
            st.markdown(f"**{agent['name']}**")
            st.markdown(f"Status: {agent['status']}")
            st.markdown(f"Active Tasks: {agent['tasks']}")
            st.markdown("---")

def render_operation_history():
    """Display operation history and logs with database integration"""
    st.subheader("📝 Operation History")
    
    db = st.session_state.get('agentic_db')
    
    # Recent operations
    with st.expander("Recent Operations", expanded=True):
        if db:
            try:
                operations = db.get_recent_operations(limit=10)
                
                if operations:
                    for op in operations:
                        # Status emoji mapping
                        status_emoji = {
                            "completed": "✅",
                            "in_progress": "🔄", 
                            "failed": "❌",
                            "initiated": "🆕"
                        }
                        
                        status_display = f"{status_emoji.get(op['status'], '❓')} {op['status'].title()}"
                        
                        # Format timestamp
                        try:
                            from datetime import datetime
                            if op['started_at']:
                                timestamp = datetime.fromisoformat(op['started_at'].replace('Z', '+00:00'))
                                time_str = timestamp.strftime("%H:%M")
                            else:
                                time_str = "Unknown"
                        except:
                            time_str = "Unknown"
                        
                        target = op['target_site'] or "All Sites"
                        st.markdown(f"**{time_str}** - {op['operation_type']} on {target} - {status_display}")
                        
                        # Show error if failed
                        if op['status'] == 'failed' and op['error_message']:
                            st.markdown(f"   ⚠️ Error: {op['error_message']}")
                else:
                    st.markdown("*No operations recorded yet*")
                    
            except Exception as e:
                logger.error(f"Failed to load operation history: {e}")
                render_default_operations()
        else:
            render_default_operations()
    
    # Detailed logs
    with st.expander("Detailed Logs"):
        if db:
            try:
                # Get recent operations and their logs
                operations = db.get_recent_operations(limit=3)
                
                log_text = ""
                for op in operations:
                    logs = db.get_operation_logs(op['operation_id'])
                    for log in logs:
                        timestamp = log['timestamp']
                        level = log['log_level']
                        message = log['message']
                        log_text += f"[{timestamp}] {level}: {message}\n"
                
                if log_text:
                    st.text_area(
                        "Agent Logs:",
                        value=log_text,
                        height=150,
                        disabled=True
                    )
                else:
                    st.text_area(
                        "Agent Logs:",
                        value="No detailed logs available yet",
                        height=150,
                        disabled=True
                    )
                    
            except Exception as e:
                logger.error(f"Failed to load detailed logs: {e}")
                render_default_logs()
        else:
            render_default_logs()

def render_default_operations():
    """Render default operations when database is unavailable"""
    operations = [
        {"time": "14:30", "operation": "Parameter Optimization", "site": "HARARE_NORTH_02", "status": "✅ Success"},
        {"time": "14:15", "operation": "Anomaly Investigation", "site": "BULAWAYO_CENTRAL", "status": "🔄 In Progress"},
        {"time": "13:45", "operation": "Performance Analysis", "site": "All Sites", "status": "✅ Success"},
        {"time": "13:20", "operation": "Monitoring Alert", "site": "MUTARE_SOUTH_01", "status": "⚠️ Resolved"}
    ]
    
    for op in operations:
        st.markdown(f"**{op['time']}** - {op['operation']} on {op['site']} - {op['status']}")

def render_default_logs():
    """Render default logs when database is unavailable"""
    st.text_area(
        "Agent Logs:",
        value="""[14:30:15] Monitor Agent: Baseline metrics collected for HARARE_NORTH_02
[14:30:22] Optimizer Agent: Parameter optimization started
[14:30:45] Optimizer Agent: Reference Signal Power adjusted: -2dB
[14:30:47] Optimizer Agent: A3 Event Offset optimized: +1dB
[14:30:52] Validator Agent: Changes validated successfully
[14:30:55] Monitor Agent: Post-optimization metrics show +3.2% improvement
[14:30:58] Optimizer Agent: Operation completed successfully""",
        height=150,
        disabled=True
    )

# ============================================================================
# STAGE 1.3: NATURAL LANGUAGE QUERY INTERFACE
# ============================================================================

def render_query_interface():
    """Render the natural language query interface"""
    st.subheader("💬 Natural Language Query Interface")
    st.markdown("Ask questions or give commands in natural language to interact with your network")
    
    # Query input area
    query_col1, query_col2 = st.columns([4, 1])
    
    with query_col1:
        user_query = st.text_area(
            "🎯 Enter your query:",
            placeholder="Example: 'Optimize throughput at Harare Central site' or 'Show me KPIs for all active sites'",
            height=100,
            key="agentic_query_input"
        )
    
    with query_col2:
        st.markdown("**Actions:**")
        if st.button("🚀 Send Query", type="primary", use_container_width=True):
            if user_query.strip():
                process_user_query(user_query)
            else:
                st.warning("Please enter a query")
        
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state.agentic_query_input = ""
            if 'query_results' in st.session_state:
                del st.session_state.query_results
            st.rerun()
    
    # Quick query buttons
    st.markdown("**🚀 Quick Queries:**")
    render_quick_query_buttons()

def render_quick_query_buttons():
    """Render quick query buttons for common operations"""
    
    # Row 1: Analysis and Status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Show All KPIs", use_container_width=True):
            process_user_query("Show me current KPIs for all active sites")
    
    with col2:
        if st.button("⚙️ Optimize Network", use_container_width=True):
            process_user_query("Optimize network performance for all sites")
    
    with col3:
        if st.button("🔍 Analyze Performance", use_container_width=True):
            process_user_query("Analyze network performance and identify issues")
    
    with col4:
        if st.button("🚨 Check Issues", use_container_width=True):
            process_user_query("Check for network issues and anomalies")
    
    # Row 2: Specific Operations
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        if st.button("📡 Cell Status", use_container_width=True):
            process_user_query("Show cell status for all sites")
    
    with col6:
        if st.button("🔧 Parameter Check", use_container_width=True):
            process_user_query("Check current parameters for optimization")
    
    with col7:
        if st.button("📈 Performance Trends", use_container_width=True):
            process_user_query("Show performance trends over time")
    
    with col8:
        if st.button("🎯 Auto-Tune", use_container_width=True):
            process_user_query("Automatically tune parameters for best performance")

def process_user_query(query: str):
    """Process user query and store results for display"""
    db = st.session_state.get('agentic_db')
    operation_id = None
    
    try:
        # Stage 1.3: Basic query processing (will be enhanced in Stage 2)
        
        # Create operation in database
        if db:
            operation_id = db.create_operation(
                operation_type="Natural Language Query",
                target_site="Auto-detected",
                parameters={"query": query, "timestamp": datetime.now().isoformat()},
                agent_name="Query Processor"
            )
            
            if operation_id:
                db.add_operation_log(operation_id, f"Processing query: {query}")
        
        # Basic query interpretation
        query_results = interpret_query(query)
        
        # Store results in session state
        st.session_state.query_results = query_results
        
        # Update operation status
        if db and operation_id:
            db.update_operation_status(operation_id, "completed", query_results)
            db.add_operation_log(operation_id, "Query processed successfully")
        
        st.success(f"✅ Query processed: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        
    except Exception as e:
        error_msg = f"Query processing failed: {e}"
        st.error(f"❌ {error_msg}")
        
        if db and operation_id:
            db.update_operation_status(operation_id, "failed", error_message=error_msg)

def interpret_query(query: str) -> dict:
    """Basic query interpretation (will be enhanced in Stage 2 with AI)"""
    query_lower = query.lower()
    
    # Simple keyword-based interpretation
    result = {
        "query": query,
        "intent": "unknown",
        "target_sites": [],
        "parameters": [],
        "actions": [],
        "analysis_type": "general"
    }
    
    # Intent detection
    if any(word in query_lower for word in ["optimize", "optimization", "improve"]):
        result["intent"] = "optimization"
        result["analysis_type"] = "optimization"
    elif any(word in query_lower for word in ["show", "display", "kpi", "status"]):
        result["intent"] = "information"
        result["analysis_type"] = "status"
    elif any(word in query_lower for word in ["analyze", "analysis", "performance"]):
        result["intent"] = "analysis"
        result["analysis_type"] = "performance"
    elif any(word in query_lower for word in ["issue", "problem", "error", "anomaly"]):
        result["intent"] = "troubleshooting"
        result["analysis_type"] = "issues"
    elif any(word in query_lower for word in ["reset", "configure", "set", "threshold", "parameter", "config"]):
        result["intent"] = "configuration"
        result["analysis_type"] = "configuration"
    
    # Site detection
    sites = ["harare", "bulawayo", "mutare", "gweru", "bindura", "marondera"]
    for site in sites:
        if site in query_lower:
            result["target_sites"].append(site.title())
    
    if not result["target_sites"]:
        result["target_sites"] = ["All Sites"]
    
    # Parameter detection
    parameters = ["throughput", "coverage", "interference", "power", "timer", "offset"]
    for param in parameters:
        if param in query_lower:
            result["parameters"].append(param)
    
    # Generate mock results based on intent
    if result["intent"] == "optimization":
        result["recommendations"] = [
            "Adjust Reference Signal Power by -2dB",
            "Optimize A3 Event Offset to +1dB",
            "Fine-tune PDCCH Aggregation Level"
        ]
        result["potential_improvement"] = "8.5% throughput increase"
    elif result["intent"] == "information":
        result["current_metrics"] = {
            "average_throughput": "89.2 Mbps",
            "network_availability": "99.1%",
            "active_sites": 3,
            "total_cells": 18
        }
    elif result["intent"] == "analysis":
        result["performance_summary"] = {
            "overall_health": "Good",
            "trending": "Improving",
            "bottlenecks": 2,
            "optimization_score": "87%"
        }
    elif result["intent"] == "troubleshooting":
        result["detected_issues"] = [
            {"site": "Harare Central", "issue": "Minor interference detected", "severity": "Low"},
            {"site": "Bulawayo West", "issue": "Coverage gap in sector 3", "severity": "Medium"}
        ]
    
    return result

# ============================================================================
# STAGE 1.3: 4-TAB OUTPUT SYSTEM
# ============================================================================

def render_query_results_tabs():
    """Render the 4-tab output system for query results"""
    if 'query_results' not in st.session_state:
        st.info("💡 **Tip:** Use the query interface above to ask questions or give commands. Results will appear here in organized tabs.")
        return
    
    st.subheader("📋 Query Results")
    
    # Create 4 tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analysis", "⚙️ Actions", "📋 Details", "🎯 Recommendations"])
    
    results = st.session_state.query_results
    
    with tab1:
        render_analysis_tab(results)
    
    with tab2:
        render_actions_tab(results)
    
    with tab3:
        render_details_tab(results)
    
    with tab4:
        render_recommendations_tab(results)

def render_analysis_tab(results: dict):
    """Render the Analysis tab content"""
    st.markdown("### 📊 Analysis Results")
    
    # Display query info
    st.markdown(f"**Query:** {results['query']}")
    st.markdown(f"**Intent:** {results['intent'].title()}")
    st.markdown(f"**Target Sites:** {', '.join(results['target_sites'])}")
    
    # Intent-specific analysis
    if results["intent"] == "information":
        if "current_metrics" in results:
            st.markdown("#### Current Network Metrics")
            metrics = results["current_metrics"]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Avg Throughput", metrics.get("average_throughput", "N/A"))
            with col2:
                st.metric("Availability", metrics.get("network_availability", "N/A"))
            with col3:
                st.metric("Active Sites", metrics.get("active_sites", "N/A"))
            with col4:
                st.metric("Total Cells", metrics.get("total_cells", "N/A"))
    
    elif results["intent"] == "analysis":
        if "performance_summary" in results:
            st.markdown("#### Performance Analysis")
            summary = results["performance_summary"]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Overall Health:** {summary.get('overall_health', 'Unknown')}")
                st.markdown(f"**Trending:** {summary.get('trending', 'Unknown')}")
            with col2:
                st.markdown(f"**Bottlenecks Detected:** {summary.get('bottlenecks', 0)}")
                st.markdown(f"**Optimization Score:** {summary.get('optimization_score', 'N/A')}")
    
    elif results["intent"] == "troubleshooting":
        if "detected_issues" in results:
            st.markdown("#### Detected Issues")
            for issue in results["detected_issues"]:
                severity_color = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(issue["severity"], "⚪")
                st.markdown(f"{severity_color} **{issue['site']}:** {issue['issue']} (Severity: {issue['severity']})")

def render_actions_tab(results: dict):
    """Render the Actions tab content"""
    st.markdown("### ⚙️ Suggested Actions")
    
    if results["intent"] == "optimization":
        st.markdown("#### Optimization Actions Available")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Execute Optimization", type="primary"):
                execute_optimization_action(results)
        
        with col2:
            if st.button("🧪 Simulate Changes"):
                st.info("🔄 Simulation mode activated - no actual changes will be made")
        
        st.markdown("#### Parameters to Modify")
        if results.get("recommendations"):
            for i, rec in enumerate(results["recommendations"]):
                st.markdown(f"{i+1}. {rec}")
    
    elif results["intent"] == "troubleshooting":
        st.markdown("#### Issue Resolution Actions")
        
        if results.get("detected_issues"):
            for issue in results["detected_issues"]:
                with st.expander(f"🔧 Resolve: {issue['site']} - {issue['issue']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"🛠️ Auto-Fix", key=f"autofix_{issue['site']}"):
                            st.success(f"✅ Auto-fix initiated for {issue['site']}")
                    with col2:
                        if st.button(f"📋 Manual Review", key=f"manual_{issue['site']}"):
                            st.info(f"📋 Manual review scheduled for {issue['site']}")
    
    else:
        st.markdown("#### Available Actions")
        action_col1, action_col2, action_col3 = st.columns(3)
        
        with action_col1:
            if st.button("🔄 Refresh Data"):
                st.success("✅ Data refresh initiated")
        
        with action_col2:
            if st.button("📊 Export Report"):
                st.success("✅ Report exported")
        
        with action_col3:
            if st.button("⚙️ Configure Alerts"):
                st.info("🔔 Alert configuration opened")

def render_details_tab(results: dict):
    """Render the Details tab content"""
    st.markdown("### 📋 Detailed Information")
    
    # Query processing details
    st.markdown("#### Query Processing Details")
    
    detail_col1, detail_col2 = st.columns(2)
    
    with detail_col1:
        st.markdown("**Parsed Parameters:**")
        if results.get("parameters"):
            for param in results["parameters"]:
                st.markdown(f"- {param.title()}")
        else:
            st.markdown("- No specific parameters detected")
    
    with detail_col2:
        st.markdown("**Processing Metadata:**")
        st.markdown(f"- Processing time: ~0.2s")
        st.markdown(f"- Confidence level: 85%")
        st.markdown(f"- Analysis type: {results.get('analysis_type', 'general')}")
    
    # Raw results
    with st.expander("🔧 Raw Processing Results (Technical Details)"):
        st.json(results)

def render_recommendations_tab(results: dict):
    """Render the Recommendations tab content"""
    st.markdown("### 🎯 Smart Recommendations")
    
    if results["intent"] == "optimization":
        st.markdown("#### Optimization Recommendations")
        
        if results.get("recommendations"):
            for i, rec in enumerate(results["recommendations"], 1):
                st.markdown(f"**{i}. {rec}**")
                st.markdown(f"   - Expected impact: Positive")
                st.markdown(f"   - Risk level: Low")
                st.markdown(f"   - Implementation time: ~2 minutes")
        
        if results.get("potential_improvement"):
            st.success(f"🎯 **Potential Improvement:** {results['potential_improvement']}")
    
    else:
        st.markdown("#### General Recommendations")
        
        recommendations = [
            "Consider implementing automated monitoring for proactive issue detection",
            "Schedule regular performance optimization reviews",
            "Set up alerting thresholds for key performance indicators",
            "Review parameter configurations monthly for optimal performance"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"**{i}.** {rec}")
    
    # Next steps
    st.markdown("#### 🚀 Next Steps")
    st.markdown("1. **Review** the analysis results above")
    st.markdown("2. **Execute** recommended actions from the Actions tab")
    st.markdown("3. **Monitor** the impact of changes")
    st.markdown("4. **Iterate** with additional queries as needed")

def execute_optimization_action(results: dict):
    """Execute optimization action with database logging"""
    db = st.session_state.get('agentic_db')
    
    if db:
        try:
            # Create optimization operation
            operation_id = db.create_operation(
                operation_type="Auto Optimization",
                target_site=', '.join(results.get('target_sites', ['All Sites'])),
                parameters=results.get('recommendations', {}),
                agent_name="Optimization Engine"
            )
            
            if operation_id:
                db.add_operation_log(operation_id, "Optimization execution started")
                db.update_operation_status(operation_id, "completed", 
                                         {"improvement": results.get("potential_improvement", "Unknown")})
                
                st.success(f"✅ Optimization executed successfully! Operation ID: {operation_id}")
            else:
                st.error("❌ Failed to create optimization operation")
                
        except Exception as e:
            st.error(f"❌ Optimization failed: {e}")
    else:
        st.success("✅ Optimization simulation completed (database not available)")