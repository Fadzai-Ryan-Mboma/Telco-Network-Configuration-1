"""
Updated Liquid Zimbabwe Monitoring Agent

This replaces the old BubbleRAN parameter monitoring with real network KPI monitoring
for Liquid Zimbabwe sites.
"""

import time
import pandas as pd
from typing import Dict, Generator
from liquid_zimbabwe_monitoring import LiquidZimbabweMonitor
from database_sync_manager import run_startup_sync_check


def liquid_zimbabwe_monitoring_agent(state) -> Dict:
    """
    New monitoring agent for Liquid Zimbabwe real network data
    
    This replaces the old BubbleRAN parameter monitoring (p0_nominal, 
    dl_carrierBandwidth, etc.) with real KPI monitoring from actual
    Bindura site data.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with monitoring results
    """
    
    def monitoring_generator():
        """Generator function for streaming monitoring messages"""
        
        # First, check data synchronization
        yield "🔄 Checking data synchronization..."
        try:
            sync_result = run_startup_sync_check(interactive=False)
            if sync_result["status"] == "success":
                yield f"✅ {sync_result['message']}"
            elif sync_result["status"] == "synchronized":
                yield f"✅ {sync_result['message']}"
            else:
                yield f"⚠️ Sync warning: {sync_result['message']}"
        except Exception as e:
            yield f"⚠️ Sync check failed: {str(e)} - proceeding with existing data"
        
        yield ""  # Blank line for readability
        
        # Initialize the Liquid Zimbabwe monitor
        try:
            monitor = LiquidZimbabweMonitor()
            yield "🔍 Initialized Liquid Zimbabwe Network Monitor"
        except Exception as e:
            yield f"❌ Failed to initialize monitor: {str(e)}"
            return
        
        # Run network monitoring
        yield "🚀 Starting real network monitoring..."
        yield "📍 Monitoring Bindura sites: Zaoga, Chiwaridzo 2, Hospital, Chipadze"
        yield ""
        
        monitoring_results = None
        message_count = 0
        
        try:
            for message in monitor.monitor_network_kpis():
                if isinstance(message, dict):
                    # This is the final result
                    monitoring_results = message
                    break
                else:
                    # This is a status message
                    yield message
                    message_count += 1
                    
                    # Add some delay to show progress
                    if message_count % 3 == 0:
                        time.sleep(0.5)
        
        except Exception as e:
            yield f"❌ Monitoring failed: {str(e)}"
            return
        
        # Process results
        if monitoring_results:
            yield ""
            if monitoring_results["status"] == "success":
                alerts = monitoring_results.get("alerts", [])
                recommendations = monitoring_results.get("recommendations", [])
                
                # Summary
                if not alerts:
                    yield "🎉 EXCELLENT: All network KPIs are performing within target ranges!"
                    yield "💚 No immediate action required - network is healthy"
                else:
                    critical_alerts = [a for a in alerts if a["status"] == "critical"]
                    warning_alerts = [a for a in alerts if a["status"] == "warning"]
                    
                    if critical_alerts:
                        yield f"🚨 CRITICAL ISSUES DETECTED: {len(critical_alerts)} KPIs need immediate attention"
                        for alert in critical_alerts[:3]:  # Show top 3
                            yield f"   • {alert['message']}"
                    
                    if warning_alerts:
                        yield f"⚠️ WARNINGS: {len(warning_alerts)} KPIs need monitoring"
                
                # Recommendations
                if recommendations:
                    yield ""
                    yield "💡 RECOMMENDATIONS:"
                    for rec in recommendations[:5]:  # Show top 5
                        yield f"   {rec}"
                
                yield ""
                yield "📊 Monitoring complete - detailed analysis available in system logs"
                
            else:
                yield f"❌ Monitoring failed: {monitoring_results.get('message', 'Unknown error')}"
        else:
            yield "❌ No monitoring results received"
    
    # Collect all monitoring messages
    messages = []
    final_message = ""
    
    try:
        for message in monitoring_generator():
            messages.append(('assistant', message))
            final_message = message
            
        # Determine next action based on results
        # For now, we don't trigger reconfiguration since we're monitoring real network data
        # rather than optimizing simulation parameters
        
        return {
            "next": None,  # Stay in monitoring mode (no automatic reconfiguration)
            "agent_id": "liquid_zimbabwe_monitoring", 
            "messages": messages,
            "average_kpis_df": None,  # Not used in real network monitoring
            "vars_current": state.get("vars_current", {}),  # Preserve existing vars
            "vars_new": None,  # No parameter changes from monitoring
            "weighted_average_gain": None  # Not applicable to real network monitoring
        }
        
    except Exception as e:
        error_message = f"❌ Liquid Zimbabwe monitoring agent failed: {str(e)}"
        return {
            "next": None,
            "agent_id": "liquid_zimbabwe_monitoring",
            "messages": [('assistant', error_message)],
            "average_kpis_df": None,
            "vars_current": state.get("vars_current", {}),
            "vars_new": None,
            "weighted_average_gain": None
        }


# Alias for integration with existing workflow
def monitoring_agent_liquid_zimbabwe(state) -> Dict:
    """Alias for the new monitoring agent"""
    return liquid_zimbabwe_monitoring_agent(state)