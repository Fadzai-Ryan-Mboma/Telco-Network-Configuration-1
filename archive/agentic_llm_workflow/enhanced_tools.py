"""
Enhanced Tools for Live Network Integration
Extends existing BubbleRAN tools with Liquid Zimbabwe capabilities

These tools integrate with existing agents without modifying core agent logic.
They provide hybrid simulation + live network functionality.
"""

import os
import yaml
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime

from langchain_core.tools import tool
from huawei_api_client import HuaweiAPIClient
from liquid_zimbabwe_kpi import LiquidZimbabweKPIManager as LiquidZimbabweKPI
from liquid_zimbabwe_parameters import LiquidZimbabweParameterManager as LiquidZimbabweParameters

# Initialize managers (cached)
_api_client = None
_kpi_manager = None
_param_manager = None

def get_live_network_managers():
    """Get cached live network managers"""
    global _api_client, _kpi_manager, _param_manager
    
    if _api_client is None:
        try:
            _api_client = HuaweiAPIClient(
                base_url="https://41.174.191.214:31127",
                username="cassava.ai", 
                password="#Pass123#"
            )
            # Initialize KPI manager with database path
            db_path = os.path.join("data", "liquid_zimbabwe.db")
            os.makedirs("data", exist_ok=True)
            _kpi_manager = LiquidZimbabweKPI(db_path)
            # Initialize parameter manager with database path
            db_path = os.path.join("data", "liquid_zimbabwe.db")
            os.makedirs("data", exist_ok=True)
            _param_manager = LiquidZimbabweParameters(db_path)
        except Exception as e:
            print(f"Warning: Live network managers not available: {e}")
            return None, None, None
    
    return _api_client, _kpi_manager, _param_manager

# ============================================================================
# ENHANCED EXISTING TOOLS (Backward Compatible)
# ============================================================================

@tool
def find_value_in_gnb_enhanced(parameter_name: str) -> str:
    """
    Enhanced version of find_value_in_gnb that checks live network first,
    then falls back to simulation/config if needed.
    
    Args:
        parameter_name: The parameter to find (p0_nominal, dl_carrierBandwidth, etc.)
    
    Returns:
        String representation of the parameter value
    """
    api_client, kpi_manager, param_manager = get_live_network_managers()
    
    # Try live network first
    if api_client and param_manager:
        try:
            if api_client.test_connectivity():
                # Map old parameter names to new system
                param_mapping = {
                    "p0_nominal": "P0_NominalPUSCH",
                    "dl_carrierBandwidth": "ReferenceSignalPower_PDSCH", 
                    "ul_carrierBandwidth": "ReferenceSignalPower_PUSCH",
                    "att_tx": "A3EventOffset",
                    "att_rx": "T310Timer"
                }
                
                mapped_param = param_mapping.get(parameter_name, parameter_name)
                live_value = param_manager.get_parameter_value(mapped_param)
                
                if live_value is not None:
                    print(f"✅ Found {parameter_name} = {live_value} from live network")
                    return str(live_value)
        except Exception as e:
            print(f"⚠️ Live network failed, falling back to simulation: {e}")
    
    # Fallback to original simulation logic
    from agentic_llm_workflow.tools import find_value_in_gnb as original_find_value_in_gnb
    return original_find_value_in_gnb(parameter_name)

@tool 
def execute_historical_sql_enhanced(sql_query: str) -> str:
    """
    Enhanced historical SQL that can query both original BubbleRAN data
    and new Liquid Zimbabwe KPI data.
    
    Args:
        sql_query: SQL query to execute
    
    Returns:
        Query results as formatted string
    """
    api_client, kpi_manager, param_manager = get_live_network_managers()
    
    # Try Liquid Zimbabwe KPI database first for relevant queries
    if kpi_manager and ("P0 Nominal" in sql_query or "RACH" in sql_query or "IBLER" in sql_query):
        try:
            # Convert old query format to new KPI system
            lz_results = kpi_manager.execute_enhanced_query(sql_query)
            if lz_results is not None:
                print("✅ Using Liquid Zimbabwe KPI database")
                return lz_results
        except Exception as e:
            print(f"⚠️ Liquid Zimbabwe KPI query failed: {e}")
    
    # Fallback to original historical database
    from agentic_llm_workflow.tools import execute_historical_sql as original_execute_historical_sql
    print("ℹ️ Using original historical database")
    return original_execute_historical_sql(sql_query)

# ============================================================================
# NEW LIVE NETWORK TOOLS (Additive)
# ============================================================================

@tool
def get_live_network_kpis(site_name: Optional[str] = None) -> str:
    """
    Get current KPI values from live Huawei network.
    
    Args:
        site_name: Specific site to query, or None for all sites
    
    Returns:
        Formatted string with current KPI values and status
    """
    api_client, kpi_manager, param_manager = get_live_network_managers()
    
    if not (api_client and kpi_manager):
        return "❌ Live network not available. Using simulation mode."
    
    try:
        if not api_client.test_connectivity():
            return "❌ Cannot connect to live network. Check credentials."
        
        if site_name:
            kpi_data = kpi_manager.get_site_kpis(site_name)
        else:
            kpi_data = kpi_manager.get_all_kpis()
        
        # Format results for agent consumption
        result_lines = ["📊 Live Network KPI Status:"]
        for kpi_id, data in kpi_data.items():
            config = kpi_manager.KPI_CONFIG.get(kpi_id, {})
            user_name = config.get('user_friendly_name', kpi_id)
            status = data.get('status', 'unknown')
            value = data.get('value', 'N/A')
            unit = config.get('unit', '')
            
            status_icon = {"good": "✅", "warning": "⚠️", "critical": "🔴"}.get(status, "➖")
            result_lines.append(f"{status_icon} {user_name}: {value}{unit} ({status})")
        
        return "\n".join(result_lines)
    
    except Exception as e:
        return f"❌ Error retrieving live KPIs: {str(e)}"

@tool
def check_live_network_status() -> str:
    """
    Check if live Huawei network is accessible and return status.
    
    Returns:
        Network connectivity status and available sites
    """
    api_client, kpi_manager, param_manager = get_live_network_managers()
    
    if not api_client:
        return "❌ Live network client not initialized"
    
    try:
        if api_client.test_connectivity():
            sites = api_client.get_network_elements()
            return f"✅ Live network connected. {len(sites)} sites available: {', '.join(sites[:5])}{'...' if len(sites) > 5 else ''}"
        else:
            return "❌ Live network not accessible. Using simulation mode."
    except Exception as e:
        return f"⚠️ Live network check failed: {str(e)}"

@tool
def get_parameter_recommendations(parameter_name: str, current_value: Any, site_name: Optional[str] = None) -> str:
    """
    Get AI-powered parameter optimization recommendations based on live network data.
    
    Args:
        parameter_name: Parameter to optimize
        current_value: Current parameter value  
        site_name: Target site for optimization
    
    Returns:
        Optimization recommendations with reasoning
    """
    api_client, kpi_manager, param_manager = get_live_network_managers()
    
    if not (api_client and param_manager):
        return "ℹ️ Live network recommendations not available. Using historical analysis."
    
    try:
        # Get current network performance
        current_kpis = kpi_manager.get_site_kpis(site_name) if site_name else kpi_manager.get_all_kpis()
        
        # Get optimization suggestions
        recommendations = param_manager.get_optimization_recommendations(
            parameter_name, current_value, current_kpis
        )
        
        if recommendations:
            return f"🎯 Live Network Recommendations for {parameter_name}:\n" + "\n".join(recommendations)
        else:
            return f"ℹ️ No specific recommendations for {parameter_name} at current performance levels."
    
    except Exception as e:
        return f"⚠️ Could not generate live recommendations: {str(e)}"

@tool
def validate_parameter_change_safety(parameter_name: str, old_value: Any, new_value: Any) -> str:
    """
    Validate if a parameter change is safe for live network deployment.
    
    Args:
        parameter_name: Parameter being changed
        old_value: Current parameter value
        new_value: Proposed new value
    
    Returns:
        Safety assessment with risk level and recommendations
    """
    api_client, kpi_manager, param_manager = get_live_network_managers()
    
    if not param_manager:
        return "⚠️ Live network safety validation not available"
    
    try:
        safety_check = param_manager.validate_parameter_change(
            parameter_name, old_value, new_value
        )
        
        risk_level = safety_check.get('risk_level', 'unknown')
        risk_icons = {"low": "✅", "medium": "⚠️", "high": "🔴"}
        icon = risk_icons.get(risk_level, "❓")
        
        result = [f"{icon} Parameter Change Safety Assessment:"]
        result.append(f"Parameter: {parameter_name}")
        result.append(f"Change: {old_value} → {new_value}")
        result.append(f"Risk Level: {risk_level.upper()}")
        
        if safety_check.get('warnings'):
            result.append("⚠️ Warnings:")
            for warning in safety_check['warnings']:
                result.append(f"  • {warning}")
        
        if safety_check.get('rollback_plan'):
            result.append(f"🔄 Rollback Plan: {safety_check['rollback_plan']}")
        
        return "\n".join(result)
    
    except Exception as e:
        return f"❌ Safety validation failed: {str(e)}"

# ============================================================================
# HYBRID DECISION TOOL
# ============================================================================

@tool
def get_network_mode_status() -> str:
    """
    Determine if system should use live network or simulation mode.
    
    Returns:
        Current operational mode and capabilities
    """
    api_client, kpi_manager, param_manager = get_live_network_managers()
    
    # Check simulation capability
    sim_available = os.path.exists('config.yaml')
    
    # Check live network capability  
    live_available = False
    live_sites = []
    
    if api_client:
        try:
            live_available = api_client.test_connectivity()
            if live_available:
                live_sites = api_client.get_network_elements()
        except:
            live_available = False
    
    # Determine best mode
    if live_available and live_sites:
        mode = "🌐 HYBRID MODE"
        details = f"Live network primary ({len(live_sites)} sites), simulation backup"
    elif live_available:
        mode = "🔗 LIVE MODE" 
        details = "Live network connected, limited sites"
    elif sim_available:
        mode = "🧪 SIMULATION MODE"
        details = "Live network unavailable, using simulation"
    else:
        mode = "❌ LIMITED MODE"
        details = "Neither live network nor simulation fully available"
    
    return f"{mode}\n{details}\nLive Network: {'✅' if live_available else '❌'}\nSimulation: {'✅' if sim_available else '❌'}"