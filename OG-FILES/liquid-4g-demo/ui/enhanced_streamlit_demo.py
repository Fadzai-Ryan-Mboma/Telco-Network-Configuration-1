#!/usr/bin/env python3
"""
Enhanced Liquid Zimbabwe 4G Demo - Comprehensive Streamlit UI
Interactive demonstration of 6-stage agentic workflow with full prompt architecture
"""

import streamlit as st
import asyncio
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import time
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure page
st.set_page_config(
    page_title="LZ 4G Network Optimizer - Enhanced Demo",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LZ-Enhanced-Demo')

# Add paths for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent / 'agents'))
sys.path.append(str(current_dir.parent / 'prompts'))
sys.path.append(str(current_dir.parent / 'utils'))

# Import enhanced modules
try:
    from enhanced_workflow_engine import EnhancedWorkflowEngine, WorkflowContext, AgentResponse
    from enhanced_prompt_templates import PromptTemplates, DemoPromptGenerator, PromptValidator
    from bindura_data_loader import BinduraDataLoader
    MODULES_AVAILABLE = True
except ImportError as e:
    st.error(f"Required modules not found: {str(e)}")
    MODULES_AVAILABLE = False

# Theme and styling
def get_theme_colors():
    """Get Liquid Zimbabwe brand colors"""
    return {
        'primary_color': '#001d58',      # Dark blue
        'secondary_bg': '#00f19c',       # Bright green
        'background_color': '#ffffff',   # White
        'text_color': '#00082f',         # Very dark blue
        'accent_color': '#f63366',       # Red accent
        'success_color': '#00f19c',      # Green
        'warning_color': '#ff8c00',      # Orange
        'error_color': '#ff4444'         # Red
    }

def load_custom_css():
    """Load custom CSS for enhanced styling"""
    colors = get_theme_colors()
    
    css = f"""
    <style>
    .main .block-container {{
        padding-top: 1rem;
        padding-bottom: 1rem;
    }}
    
    .stage-container {{
        border: 2px solid {colors['primary_color']};
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: {colors['background_color']};
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    .stage-header {{
        color: {colors['primary_color']};
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
    }}
    
    .stage-status {{
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-left: 1rem;
    }}
    
    .status-pending {{ background-color: #f0f0f0; color: #666; }}
    .status-running {{ background-color: {colors['warning_color']}; color: white; }}
    .status-success {{ background-color: {colors['success_color']}; color: white; }}
    .status-error {{ background-color: {colors['error_color']}; color: white; }}
    
    .kpi-card {{
        background: linear-gradient(135deg, {colors['primary_color']}, {colors['accent_color']});
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        text-align: center;
    }}
    
    .approval-interface {{
        border: 3px solid {colors['warning_color']};
        border-radius: 10px;
        padding: 1.5rem;
        background-color: #fff8e1;
        margin: 1rem 0;
    }}
    
    .demo-header {{
        background: linear-gradient(90deg, {colors['primary_color']}, {colors['secondary_bg']});
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }}
    
    .workflow-progress {{
        background-color: {colors['background_color']};
        border: 1px solid {colors['primary_color']};
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }}
    
    .agent-response {{
        background-color: #f8f9fa;
        border-left: 4px solid {colors['primary_color']};
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }}
    
    .prompt-display {{
        background-color: #2d3748;
        color: #e2e8f0;
        padding: 1rem;
        border-radius: 8px;
        font-family: monospace;
        font-size: 0.85rem;
        white-space: pre-wrap;
        max-height: 400px;
        overflow-y: auto;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def display_header():
    """Display enhanced header with logo and branding"""
    st.markdown("""
    <div class="demo-header">
        <h1>🏢 Liquid Zimbabwe 4G Network Optimizer</h1>
        <h2>Enhanced Agentic Workflow Demonstration</h2>
        <p>Comprehensive 6-Stage AI Agent System with Real Bindura Network Data</p>
    </div>
    """, unsafe_allow_html=True)

def display_workflow_progress(current_stage: str, stage_results: Dict[str, Any]):
    """Display workflow progress with visual indicators"""
    stages = [
        ("network_connector", "🔌 Network Discovery"),
        ("monitoring_analysis", "📊 Performance Analysis"), 
        ("kpi_analytics", "🧠 AI Analytics"),
        ("configuration", "⚙️ Configuration"),
        ("validation", "✅ Safety Validation"),
        ("execution", "🚀 Execution")
    ]
    
    st.markdown('<div class="workflow-progress">', unsafe_allow_html=True)
    st.subheader("Workflow Progress")
    
    cols = st.columns(len(stages))
    
    for i, (stage_id, stage_name) in enumerate(stages):
        with cols[i]:
            if stage_id in stage_results:
                if stage_results[stage_id].get('success', False):
                    status_class = "status-success"
                    status_text = "✅ Complete"
                else:
                    status_class = "status-error"
                    status_text = "❌ Failed"
            elif stage_id == current_stage:
                status_class = "status-running"
                status_text = "⏳ Running"
            else:
                status_class = "status-pending"
                status_text = "⏸️ Pending"
            
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-weight: bold; margin-bottom: 0.5rem;">{stage_name}</div>
                <div class="stage-status {status_class}">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_network_overview():
    """Display network overview with real data"""
    st.subheader("🗺️ Bindura Network Overview")
    
    # Network stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <h3>4</h3>
            <p>Total Sites</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="kpi-card">
            <h3>11</h3>
            <p>Total Cells</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="kpi-card">
            <h3>0.536%</h3>
            <p>RACH Success</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="kpi-card">
            <h3>15.94%</h3>
            <p>DL IBLER</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Site details
    sites_data = {
        "Site Name": [
            "MSH0013-Bindura-Zaoga",
            "MSH-0331-Chiwaridzo 2", 
            "MSH-0112-Bindura Hospital",
            "MSH-0014-Chipadze"
        ],
        "Status": ["🔴 Critical", "🟡 Warning", "🟢 Normal", "🟡 Warning"],
        "Cells": [3, 3, 2, 3],
        "RACH (%)": [0.536, 0.721, 1.245, 0.892],
        "DL IBLER (%)": [15.94, 14.82, 12.45, 16.78]
    }
    
    st.dataframe(pd.DataFrame(sites_data), use_container_width=True)

def display_stage_detail(stage_name: str, stage_result: AgentResponse, show_prompt: bool = False):
    """Display detailed stage information"""
    st.markdown(f'<div class="stage-container">', unsafe_allow_html=True)
    
    # Stage header
    status_icon = "✅" if stage_result.success else "❌"
    st.markdown(f"""
    <div class="stage-header">
        {status_icon} {stage_name.replace('_', ' ').title()}
        <span class="stage-status {'status-success' if stage_result.success else 'status-error'}">
            {f"Success ({stage_result.execution_time:.1f}s)" if stage_result.success else f"Failed ({stage_result.execution_time:.1f}s)"}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Stage content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="agent-response">', unsafe_allow_html=True)
        
        if stage_result.success and stage_result.data:
            # Display key results based on stage type
            if stage_name == "network_connector":
                st.write("**🔌 Network Discovery Results:**")
                data = stage_result.data
                st.write(f"- Connection Status: {data.get('connection_status', 'Unknown')}")
                st.write(f"- Discovered Sites: {len(data.get('discovered_sites', []))}")
                st.write(f"- Data Source: {data.get('data_source', 'Unknown')}")
                
            elif stage_name == "monitoring_analysis":
                st.write("**📊 Performance Analysis Results:**")
                data = stage_result.data
                kpi_status = data.get('kpi_status', {})
                for kpi, info in kpi_status.items():
                    if isinstance(info, dict):
                        st.write(f"- {kpi.replace('_', ' ').title()}: {info.get('value', 'N/A')}% ({info.get('status', 'Unknown')})")
                
            elif stage_name == "kpi_analytics":
                st.write("**🧠 AI Analytics Results:**")
                data = stage_result.data
                st.write(f"- Analysis: {data.get('analytics_summary', 'No summary available')}")
                strategy = data.get('optimization_strategy', {})
                if 'parameter_recommendations' in strategy:
                    st.write("- Key Recommendations:")
                    for rec in strategy['parameter_recommendations'][:3]:
                        st.write(f"  • {rec.get('parameter', 'Parameter')}: {rec.get('current_value', 'N/A')} → {rec.get('recommended_value', 'N/A')}")
                
            elif stage_name == "configuration":
                st.write("**⚙️ Configuration Results:**")
                data = stage_result.data
                commands = data.get('mml_commands', [])
                st.write(f"- Generated Commands: {len(commands)}")
                st.write(f"- Risk Level: {data.get('change_summary', {}).get('risk_level', 'Unknown')}")
                if commands:
                    st.write("- Sample Command:")
                    st.code(commands[0].get('command', 'No command available'), language='text')
                
            elif stage_name == "validation":
                st.write("**✅ Safety Validation Results:**")
                data = stage_result.data
                validation = data.get('validation_summary', {})
                st.write(f"- Recommendation: {validation.get('overall_recommendation', 'Unknown')}")
                st.write(f"- Safety Score: {validation.get('safety_score', 'N/A')}")
                st.write(f"- Risk Level: {validation.get('risk_level', 'Unknown')}")
                
            elif stage_name == "execution":
                st.write("**🚀 Execution Results:**")
                data = stage_result.data
                execution = data.get('execution_summary', {})
                st.write(f"- Status: {execution.get('execution_status', 'Unknown')}")
                st.write(f"- Sites Completed: {execution.get('sites_completed', 'N/A')}")
                results = data.get('crisis_optimization_results', {})
                if 'rach_improvement' in results:
                    rach = results['rach_improvement']
                    st.write(f"- RACH Improvement: {rach.get('before', 'N/A')} → {rach.get('after', 'N/A')}")
        else:
            st.error(f"Stage failed: {stage_result.error}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.write(f"**Confidence:** {stage_result.confidence:.1%}")
        st.write(f"**Execution Time:** {stage_result.execution_time:.1f}s")
        st.write(f"**Next Stage Ready:** {'Yes' if stage_result.next_stage_ready else 'No'}")
        
        if show_prompt and st.button(f"Show {stage_name} Prompt", key=f"prompt_{stage_name}"):
            st.session_state[f"show_prompt_{stage_name}"] = True
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_approval_interface(validation_result: Dict[str, Any]):
    """Display human approval interface for validation stage"""
    st.markdown('<div class="approval-interface">', unsafe_allow_html=True)
    st.subheader("🚨 Human Approval Required")
    
    approval_request = validation_result.get('approval_request', {})
    
    st.write("**Change Description:**")
    st.write(approval_request.get('change_description', 'No description available'))
    
    st.write("**Business Justification:**")
    st.write(approval_request.get('business_justification', 'No justification available'))
    
    st.write("**Expected Benefits:**")
    benefits = approval_request.get('expected_benefits', [])
    for benefit in benefits:
        st.write(f"• {benefit}")
    
    st.write("**Risk Assessment:**")
    st.write(f"Risk Level: {approval_request.get('implementation_risk', 'Unknown')}")
    
    st.write("**Rollback Plan:**")
    st.write(approval_request.get('rollback_plan', 'No rollback plan available'))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ APPROVE", type="primary", use_container_width=True):
            st.session_state.approval_decision = "approved"
            st.success("Changes approved! Proceeding to execution...")
            return "approved"
    
    with col2:
        if st.button("⚠️ CONDITIONAL APPROVE", type="secondary", use_container_width=True):
            st.session_state.approval_decision = "conditional"
            st.warning("Conditional approval granted with enhanced monitoring...")
            return "conditional"
    
    with col3:
        if st.button("❌ REJECT", type="secondary", use_container_width=True):
            st.session_state.approval_decision = "rejected"
            st.error("Changes rejected. Review required before proceeding.")
            return "rejected"
    
    st.markdown('</div>', unsafe_allow_html=True)
    return None

def display_real_time_monitoring(execution_results: Dict[str, Any]):
    """Display real-time monitoring dashboard"""
    st.subheader("📈 Real-Time Network Monitoring")
    
    # KPI improvement charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**RACH Success Rate Improvement**")
        rach_data = execution_results.get('crisis_optimization_results', {}).get('rach_improvement', {})
        before = float(rach_data.get('before', '0.536').replace('%', ''))
        after = float(rach_data.get('after', '18.2').replace('%', ''))
        
        fig_rach = go.Figure()
        fig_rach.add_trace(go.Bar(
            x=['Before', 'After'],
            y=[before, after],
            marker_color=['red', 'green'],
            text=[f'{before}%', f'{after}%'],
            textposition='auto'
        ))
        fig_rach.update_layout(
            title="RACH Success Rate",
            yaxis_title="Success Rate (%)",
            showlegend=False,
            height=300
        )
        st.plotly_chart(fig_rach, use_container_width=True)
    
    with col2:
        st.write("**DL IBLER Improvement**")
        ibler_data = execution_results.get('crisis_optimization_results', {}).get('ibler_improvement', {})
        before = float(ibler_data.get('before', '15.94').replace('%', ''))
        after = float(ibler_data.get('after', '12.1').replace('%', ''))
        
        fig_ibler = go.Figure()
        fig_ibler.add_trace(go.Bar(
            x=['Before', 'After'],
            y=[before, after],
            marker_color=['orange', 'green'],
            text=[f'{before}%', f'{after}%'],
            textposition='auto'
        ))
        fig_ibler.update_layout(
            title="DL IBLER",
            yaxis_title="Error Rate (%)",
            showlegend=False,
            height=300
        )
        st.plotly_chart(fig_ibler, use_container_width=True)
    
    # Monitoring timeline
    st.write("**Monitoring Timeline**")
    timeline_data = {
        'Time': ['0 min', '5 min', '10 min', '15 min', '20 min', '25 min', '30 min'],
        'RACH (%)': [0.536, 2.1, 8.5, 15.2, 17.8, 18.1, 18.2],
        'DL IBLER (%)': [15.94, 15.1, 14.2, 13.5, 12.8, 12.3, 12.1]
    }
    
    fig_timeline = go.Figure()
    fig_timeline.add_trace(go.Scatter(
        x=timeline_data['Time'],
        y=timeline_data['RACH (%)'],
        mode='lines+markers',
        name='RACH Success Rate',
        line=dict(color='green', width=3)
    ))
    fig_timeline.add_trace(go.Scatter(
        x=timeline_data['Time'],
        y=timeline_data['DL IBLER (%)'],
        mode='lines+markers',
        name='DL IBLER',
        yaxis='y2',
        line=dict(color='orange', width=3)
    ))
    
    fig_timeline.update_layout(
        title="Real-Time KPI Monitoring",
        xaxis_title="Time Since Execution",
        yaxis=dict(title="RACH Success Rate (%)", side="left"),
        yaxis2=dict(title="DL IBLER (%)", side="right", overlaying="y"),
        legend=dict(x=0.02, y=0.98),
        height=400
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)

async def run_workflow_demo(workflow_engine: EnhancedWorkflowEngine, user_query: str):
    """Run the complete workflow demonstration"""
    
    # Start workflow
    workflow_id = await workflow_engine.start_workflow(user_query, "Bindura")
    st.session_state.workflow_id = workflow_id
    st.session_state.workflow_results = {}
    
    # Progress container
    progress_container = st.container()
    results_container = st.container()
    
    stages = [
        ("network_connector", "Network Discovery"),
        ("monitoring_analysis", "Performance Analysis"),
        ("kpi_analytics", "AI Analytics"), 
        ("configuration", "Configuration Generation"),
        ("validation", "Safety Validation"),
        ("execution", "Execution & Monitoring")
    ]
    
    for i, (stage_id, stage_name) in enumerate(stages):
        with progress_container:
            display_workflow_progress(stage_id, st.session_state.workflow_results)
        
        with results_container:
            st.write(f"### 🔄 Executing: {stage_name}")
            
            # Show stage execution with progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text(f"Initializing {stage_name}...")
            progress_bar.progress(0.2)
            
            status_text.text(f"Processing {stage_name}...")
            progress_bar.progress(0.5)
            
            # Execute stage
            result = await workflow_engine.execute_workflow_stage(workflow_id, stage_id)
            st.session_state.workflow_results[stage_id] = result
            
            progress_bar.progress(1.0)
            status_text.text(f"✅ {stage_name} completed!")
            
            # Display stage results
            display_stage_detail(stage_id, result, show_prompt=True)
            
            # Special handling for validation stage
            if stage_id == "validation" and result.success:
                approval_decision = display_approval_interface(result.data)
                if approval_decision == "rejected":
                    st.error("Workflow terminated by user rejection.")
                    return
                elif approval_decision in ["approved", "conditional"]:
                    st.success(f"Proceeding with {approval_decision} approval...")
                    time.sleep(2)  # Brief pause for UX
            
            # Special handling for execution stage
            if stage_id == "execution" and result.success:
                display_real_time_monitoring(result.data)
            
            st.markdown("---")
    
    # Final summary
    st.success("🎉 Workflow completed successfully!")
    st.balloons()

def main():
    """Main application function"""
    
    # Load custom styling
    load_custom_css()
    
    # Display header
    display_header()
    
    if not MODULES_AVAILABLE:
        st.error("Required modules not available. Please check installation.")
        return
    
    # Initialize session state
    if 'workflow_engine' not in st.session_state:
        st.session_state.workflow_engine = EnhancedWorkflowEngine()
    
    if 'workflow_results' not in st.session_state:
        st.session_state.workflow_results = {}
    
    # Sidebar configuration
    with st.sidebar:
        st.title("🎛️ Demo Controls")
        
        # Demo scenario selection
        st.subheader("Demo Scenarios")
        scenarios = DemoPromptGenerator.get_demo_scenarios()
        
        scenario_names = [s['name'] for s in scenarios]
        selected_scenario = st.selectbox("Choose a scenario:", scenario_names, index=0)
        
        selected_scenario_data = next(s for s in scenarios if s['name'] == selected_scenario)
        st.write("**Description:**")
        st.write(selected_scenario_data['description'])
        
        # Custom query option
        st.subheader("Custom Query")
        custom_query = st.text_area(
            "Or enter custom optimization request:",
            value=selected_scenario_data['query'],
            height=100
        )
        
        # Demo options
        st.subheader("Demo Options")
        show_prompts = st.checkbox("Show AI Agent Prompts", value=False)
        show_json_responses = st.checkbox("Show Raw JSON Responses", value=False)
        simulation_speed = st.select_slider(
            "Simulation Speed:",
            options=["Slow", "Normal", "Fast"],
            value="Normal"
        )
        
        # Network overview
        st.subheader("Current Network Status")
        st.error("🔴 CRITICAL: RACH 0.536%")
        st.warning("🟡 WARNING: DL IBLER 15.94%")
        st.info("ℹ️ 4 sites, 11 cells monitored")
        
        # Start demo button
        start_demo = st.button("🚀 Start Demo", type="primary", use_container_width=True)
    
    # Main content area
    display_network_overview()
    
    # Demo execution
    if start_demo:
        st.header("🔄 Running 6-Stage Agentic Workflow")
        
        # Run the workflow
        try:
            asyncio.run(run_workflow_demo(st.session_state.workflow_engine, custom_query))
        except Exception as e:
            st.error(f"Demo execution failed: {str(e)}")
            logger.error(f"Demo execution error: {str(e)}")
    
    elif st.session_state.workflow_results:
        # Display existing results if available
        st.header("📋 Previous Workflow Results")
        display_workflow_progress("completed", st.session_state.workflow_results)
        
        for stage_id, result in st.session_state.workflow_results.items():
            if hasattr(result, 'success'):  # Check if it's an AgentResponse object
                display_stage_detail(stage_id, result, show_prompt=show_prompts)
    
    else:
        # Welcome message
        st.info("""
        👋 **Welcome to the Enhanced Liquid Zimbabwe 4G Network Optimizer Demo!**
        
        This demonstration showcases a sophisticated 6-stage agentic workflow system that uses AI agents 
        to optimize network performance. The system analyzes real Bindura network data showing critical 
        performance issues (RACH success rate of only 0.536%) and demonstrates how AI agents can 
        collaborate to diagnose, plan, and execute network optimizations.
        
        **Key Features:**
        - 🤖 6 AI agents with specialized prompt architectures
        - 📊 Real Bindura network data integration  
        - 🔐 Human approval workflow for safety
        - 📈 Real-time monitoring and rollback capabilities
        - ⚡ Complete MML command generation and execution
        
        Select a demo scenario from the sidebar and click "Start Demo" to begin!
        """)

if __name__ == "__main__":
    main()