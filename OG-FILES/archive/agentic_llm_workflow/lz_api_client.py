"""
Hybrid API Client for Liquid Zimbabwe Integration
Provides seamless fallback between live API and simulation data
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any, Union
import logging

class LiquidZimbabweAPIClient:
    """
    Hybrid API client that tries live Liquid Zimbabwe API first,
    then gracefully falls back to simulation data
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize Liquid Zimbabwe API Client with optional config"""
        if config is None:
            # Use default configuration if none provided
            try:
                from agentic_llm_workflow.lz_config import LZ_CONFIG
                config = LZ_CONFIG
            except ImportError:
                # Fallback default configuration
                config = {
                    'liquid_zimbabwe': {
                        'api_endpoint': 'https://41.174.191.214:31127',
                        'username': 'admin',
                        'password': 'admin', 
                        'verify_ssl': False,
                        'timeout_seconds': 30,
                        'fallback_to_simulation': True
                    }
                }
        
        self.config = config.get('liquid_zimbabwe', {})
        self.base_url = self.config.get('api_endpoint', '')
        self.username = self.config.get('username', '')
        self.password = self.config.get('password', '')
        self.timeout = self.config.get('timeout_seconds', 10)
        self.verify_ssl = self.config.get('verify_ssl', False)
        self.fallback_enabled = self.config.get('fallback_to_simulation', True)
        
        self.session = None
        self.authenticated = False
        self._last_connection_attempt = 0
        self._connection_retry_interval = 60  # seconds
        
        # Initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self) -> bool:
        """Initialize API connection with authentication"""
        try:
            if not self.base_url:
                raise ValueError("No API endpoint configured")
                
            self.session = requests.Session()
            self.session.verify = self.verify_ssl
            
            # Attempt authentication
            auth_data = {
                "username": self.username,
                "password": self.password
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=auth_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.authenticated = True
                self._last_connection_attempt = time.time()
                print("✅ Liquid Zimbabwe API connected successfully")
                return True
            else:
                raise Exception(f"Authentication failed: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Live API connection failed: {e}")
            if self.fallback_enabled:
                print("🔄 Falling back to simulation mode")
            self.authenticated = False
            return False
    
    def is_connected(self) -> bool:
        """Check if API is connected and responsive"""
        if not self.authenticated:
            # Retry connection if enough time has passed
            if time.time() - self._last_connection_attempt > self._connection_retry_interval:
                return self._initialize_connection()
            return False
            
        try:
            # Quick health check
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            return response.status_code == 200
        except:
            self.authenticated = False
            return False
    
    def get_network_kpis(self, site_name: Optional[str] = None) -> Dict:
        """
        Get network KPIs from live API or simulation
        """
        if self.is_connected():
            return self._get_live_kpis(site_name)
        elif self.fallback_enabled:
            return self._get_simulation_kpis(site_name)
        else:
            raise Exception("API not connected and fallback disabled")
    
    def _get_live_kpis(self, site_name: Optional[str] = None) -> Dict:
        """Get KPIs from live Liquid Zimbabwe network"""
        try:
            endpoint = f"{self.base_url}/kpis"
            if site_name:
                endpoint += f"?site={site_name}"
                
            response = self.session.get(endpoint, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "source": "live_api",
                    "timestamp": time.time(),
                    "site": site_name or "all",
                    "kpis": self._normalize_kpi_data(data)
                }
            else:
                raise Exception(f"API error: {response.status_code}")
                
        except Exception as e:
            print(f"Live KPI fetch failed: {e}, falling back to simulation")
            if self.fallback_enabled:
                return self._get_simulation_kpis(site_name)
            raise e
    
    def _get_simulation_kpis(self, site_name: Optional[str] = None) -> Dict:
        """Get KPIs from simulation (original BubbleRAN behavior)"""
        # Simulate realistic KPI data for fallback
        import random
        
        simulation_kpis = {
            "RACH_Success_Rate": random.uniform(85, 95),
            "IBLER": random.uniform(5, 15),
            "Throughput_DL": random.uniform(50, 150),
            "Throughput_UL": random.uniform(20, 80),
            "SNR": random.uniform(10, 25),
            "bitrate_dl": random.uniform(100, 500),
            "bitrate_ul": random.uniform(50, 200)
        }
        
        return {
            "source": "simulation",
            "timestamp": time.time(),
            "site": site_name or "simulation",
            "kpis": simulation_kpis
        }
    
    def _normalize_kpi_data(self, raw_data: Dict) -> Dict:
        """Normalize KPI data from Liquid Zimbabwe API to standard format"""
        # This would map your specific API response format to standardized KPIs
        # Customize this based on your actual API response structure
        
        normalized = {}
        
        # Example mapping - adjust based on your actual API response
        if 'performance_metrics' in raw_data:
            metrics = raw_data['performance_metrics']
            
            normalized['RACH_Success_Rate'] = metrics.get('rach_success_rate', 90)
            normalized['IBLER'] = metrics.get('block_error_rate', 10)
            normalized['Throughput_DL'] = metrics.get('downlink_throughput', 100)
            normalized['Throughput_UL'] = metrics.get('uplink_throughput', 50)
            normalized['SNR'] = metrics.get('signal_noise_ratio', 15)
            
            # Map to original BubbleRAN KPI names for compatibility
            normalized['bitrate_dl'] = normalized['Throughput_DL']
            normalized['bitrate_ul'] = normalized['Throughput_UL']
            
        return normalized
    
    def get_parameter_value(self, parameter: str) -> Union[int, float]:
        """Get current parameter value from network"""
        if self.is_connected():
            return self._get_live_parameter(parameter)
        elif self.fallback_enabled:
            return self._get_simulation_parameter(parameter)
        else:
            raise Exception("Cannot get parameter: API not connected")
    
    def _get_live_parameter(self, parameter: str) -> Union[int, float]:
        """Get parameter from live API"""
        try:
            # Map original parameter to LZ parameter name
            from .lz_config import load_enhanced_config
            config = load_enhanced_config()
            
            lz_param = config['parameter_mapping'].get(parameter, parameter)
            
            response = self.session.get(
                f"{self.base_url}/parameters/{lz_param}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json().get('value', 0)
            else:
                raise Exception(f"Parameter fetch failed: {response.status_code}")
                
        except Exception as e:
            print(f"Live parameter fetch failed: {e}")
            if self.fallback_enabled:
                return self._get_simulation_parameter(parameter)
            raise e
    
    def _get_simulation_parameter(self, parameter: str) -> Union[int, float]:
        """Get parameter from simulation (use original tools)"""
        try:
            from .tools import find_value_in_gnb
            return find_value_in_gnb(parameter)
        except:
            # Default values as fallback
            defaults = {
                'p0_nominal': -90,
                'dl_carrierBandwidth': 51,
                'ul_carrierBandwidth': 51, 
                'att_tx': 10,
                'att_rx': 10
            }
            return defaults.get(parameter, 0)
    
    def get_connection_status(self) -> str:
        """Get human-readable connection status"""
        if self.is_connected():
            return "✅ Connected to Liquid Zimbabwe Live Network"
        elif self.fallback_enabled:
            return "🟡 Using Simulation Mode (Live API unavailable)"
        else:
            return "❌ Disconnected (No fallback enabled)"


# Global instance - lazy initialization
_api_client_instance = None

def get_api_client() -> LiquidZimbabweAPIClient:
    """Get global API client instance"""
    global _api_client_instance
    
    if _api_client_instance is None:
        try:
            from .lz_config import load_enhanced_config
            config = load_enhanced_config()
            _api_client_instance = LiquidZimbabweAPIClient(config)
        except Exception as e:
            print(f"Warning: Could not initialize LZ API client: {e}")
            # Return mock client that always uses simulation
            _api_client_instance = LiquidZimbabweAPIClient({
                'liquid_zimbabwe': {'fallback_to_simulation': True}
            })
    
    return _api_client_instance