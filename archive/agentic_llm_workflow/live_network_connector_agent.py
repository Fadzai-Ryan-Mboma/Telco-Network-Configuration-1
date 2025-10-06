"""
Live Network Connector Agent for Liquid Zimbabwe
Specialized agent for managing real-time Huawei iMaster MAE API connections

This agent handles:
- API authentication and session management
- Network element discovery and health monitoring
- Connection failover and resilience
- Real-time network status reporting
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from huawei_api_client import HuaweiAPIClient
from live_network_manager import LiveNetworkManager
from agents import init_agent

class LiveNetworkConnectorAgent:
    """
    Specialized agent for managing live network connectivity and API operations.
    Works as a supporting agent for the main 3 agents.
    """
    
    def __init__(self):
        self.api_client = None
        self.network_manager = None
        self.connection_status = "disconnected"
        self.last_health_check = None
        self.available_sites = []
        self.llm_agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the LLM agent with specialized tools"""
        llm = init_agent()
        system_prompt = """You are the Live Network Connector Agent for Liquid Zimbabwe's RAN optimization system.
        Your primary responsibility is managing real-time connections to Huawei iMaster MAE API.
        You provide connection services to the main Configuration, Monitoring, and Validation agents.
        Always prioritize network stability and provide clear status information.
        Respond professionally and concisely."""
        
        tools = [
            self._connect_to_network_tool,
            self._check_network_health_tool,
            self._discover_network_elements_tool,
            self._test_api_connectivity_tool,
            self._get_connection_metrics_tool
        ]
        
        self.llm_agent = create_react_agent(llm, tools=tools, prompt=system_prompt)
    
    @tool
    def _connect_to_network_tool(self, force_reconnect: bool = False) -> str:
        """Connect to Huawei iMaster MAE API with authentication"""
        try:
            if self.api_client and self.connection_status == "connected" and not force_reconnect:
                return "✅ Already connected to live network"
            
            # Initialize API client
            self.api_client = HuaweiAPIClient(
                base_url="https://41.174.191.214:31127",
                username="cassava.ai",
                password="#Pass123#"
            )
            
            # Initialize network manager
            self.network_manager = LiveNetworkManager(self.api_client)
            
            # Test connectivity
            if self.api_client.test_connectivity():
                self.connection_status = "connected"
                self.last_health_check = datetime.now()
                
                # Discover available sites
                sites = self.api_client.get_network_elements()
                self.available_sites = sites
                
                return f"✅ Connected to live network! Discovered {len(sites)} network elements: {', '.join(sites[:3])}{'...' if len(sites) > 3 else ''}"
            else:
                self.connection_status = "failed"
                return "❌ Failed to authenticate with Huawei iMaster MAE API"
                
        except Exception as e:
            self.connection_status = "error"
            return f"❌ Connection error: {str(e)}"
    
    @tool 
    def _check_network_health_tool(self) -> str:
        """Check health of live network connection"""
        if not self.api_client:
            return "❌ No network connection established"
        
        try:
            # Test API responsiveness
            start_time = time.time()
            is_healthy = self.api_client.test_connectivity()
            response_time = (time.time() - start_time) * 1000  # ms
            
            if is_healthy:
                self.connection_status = "connected"
                self.last_health_check = datetime.now()
                
                health_info = {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "available_sites": len(self.available_sites),
                    "last_check": self.last_health_check.strftime("%H:%M:%S")
                }
                
                return f"✅ Network Health: {json.dumps(health_info, indent=2)}"
            else:
                self.connection_status = "unhealthy"
                return f"⚠️ Network connection unhealthy. Response time: {response_time:.2f}ms"
                
        except Exception as e:
            self.connection_status = "error"
            return f"❌ Health check failed: {str(e)}"
    
    @tool
    def _discover_network_elements_tool(self, site_filter: Optional[str] = None) -> str:
        """Discover and catalog network elements"""
        if not self.api_client:
            return "❌ No network connection. Use connect_to_network_tool first."
        
        try:
            all_sites = self.api_client.get_network_elements()
            
            if site_filter:
                filtered_sites = [site for site in all_sites if site_filter.lower() in site.lower()]
                return f"🔍 Filtered sites matching '{site_filter}': {filtered_sites}"
            
            # Categorize sites by type/location
            site_info = {}
            for site in all_sites:
                # Extract site type (if follows naming convention)
                if "bindura" in site.lower():
                    site_type = "Bindura_Cluster"
                elif "enb" in site.lower():
                    site_type = "4G_eNodeB"
                elif "gnb" in site.lower():
                    site_type = "5G_gNodeB"
                else:
                    site_type = "Other"
                
                if site_type not in site_info:
                    site_info[site_type] = []
                site_info[site_type].append(site)
            
            self.available_sites = all_sites
            
            result = ["📡 Network Element Discovery:"]
            for site_type, sites in site_info.items():
                result.append(f"  {site_type}: {len(sites)} elements")
                result.append(f"    Examples: {', '.join(sites[:2])}{'...' if len(sites) > 2 else ''}")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ Discovery failed: {str(e)}"
    
    @tool
    def _test_api_connectivity_tool(self, detailed: bool = False) -> str:
        """Test API connectivity with optional detailed diagnostics"""
        if not self.api_client:
            return "❌ No API client initialized"
        
        try:
            tests = [
                ("Authentication", lambda: self.api_client.authenticate()),
                ("Network Elements", lambda: len(self.api_client.get_network_elements()) > 0),
                ("API Response", lambda: self.api_client.test_connectivity())
            ]
            
            results = []
            all_passed = True
            
            for test_name, test_func in tests:
                try:
                    start_time = time.time()
                    result = test_func()
                    duration = (time.time() - start_time) * 1000
                    
                    if result:
                        results.append(f"✅ {test_name}: PASS ({duration:.1f}ms)")
                    else:
                        results.append(f"❌ {test_name}: FAIL ({duration:.1f}ms)")
                        all_passed = False
                except Exception as e:
                    results.append(f"❌ {test_name}: ERROR - {str(e)}")
                    all_passed = False
            
            summary = "✅ All connectivity tests passed" if all_passed else "⚠️ Some connectivity tests failed"
            
            if detailed:
                return f"{summary}\n" + "\n".join(results)
            else:
                return summary
                
        except Exception as e:
            return f"❌ Connectivity test failed: {str(e)}"
    
    @tool
    def _get_connection_metrics_tool(self) -> str:
        """Get detailed connection metrics and statistics"""
        if not self.api_client:
            return "❌ No connection to analyze"
        
        try:
            metrics = {
                "connection_status": self.connection_status,
                "api_endpoint": self.api_client.base_url,
                "last_health_check": self.last_health_check.strftime("%Y-%m-%d %H:%M:%S") if self.last_health_check else "Never",
                "available_sites_count": len(self.available_sites),
                "authentication_status": "Valid" if self.api_client.auth_token else "Invalid",
                "session_duration": str(datetime.now() - self.last_health_check) if self.last_health_check else "N/A"
            }
            
            return f"📊 Connection Metrics:\n{json.dumps(metrics, indent=2)}"
            
        except Exception as e:
            return f"❌ Failed to get metrics: {str(e)}"
    
    def handle_request(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests from main agents"""
        user_request = state.get("messages", [])[-1] if state.get("messages") else "Check network status"
        
        print("\n🌐 Live Network Connector Agent - Processing Request")
        
        try:
            # Use LLM agent to process the request
            response = self.llm_agent.invoke({"messages": [HumanMessage(content=user_request)]})
            
            result_message = response["messages"][-1].content if response.get("messages") else "Network connector ready"
            
            # Update state with network information
            enhanced_state = state.copy()
            enhanced_state.update({
                "live_network_status": self.connection_status,
                "available_sites": self.available_sites,
                "network_health": self.last_health_check,
                "api_client_ready": self.api_client is not None
            })
            
            enhanced_state["messages"] = state.get("messages", []) + [("assistant", result_message)]
            
            return enhanced_state
            
        except Exception as e:
            error_msg = f"❌ Live Network Connector Agent error: {str(e)}"
            print(error_msg)
            
            enhanced_state = state.copy()
            enhanced_state["messages"] = state.get("messages", []) + [("assistant", error_msg)]
            return enhanced_state
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get current network status for other agents"""
        return {
            "status": self.connection_status,
            "available_sites": self.available_sites,
            "api_ready": self.api_client is not None,
            "last_check": self.last_health_check,
            "site_count": len(self.available_sites)
        }

# Lazy initialization function for singleton instance
_live_network_connector = None

def get_live_network_connector():
    """Get the singleton live network connector agent instance"""
    global _live_network_connector
    if _live_network_connector is None:
        _live_network_connector = LiveNetworkConnectorAgent()
    return _live_network_connector

# For backward compatibility
def live_network_connector():
    """Backward compatibility function"""
    return get_live_network_connector()