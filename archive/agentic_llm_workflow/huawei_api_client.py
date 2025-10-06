"""
Huawei iMaster MAE API Client
Provides authentication and network management capabilities for live Huawei network elements.
"""

import requests
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
import urllib3

# Disable SSL warnings for internal network usage
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def retry_on_failure(max_retries=3, delay=1.0, backoff=2.0):
    """Decorator to retry failed API calls with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    retries += 1
                    if retries >= max_retries:
                        raise e
                    
                    # Log retry attempt
                    if hasattr(args[0], 'logger'):
                        args[0].logger.warning(f"Attempt {retries} failed: {e}. Retrying in {current_delay}s...")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
            return func(*args, **kwargs)
        return wrapper
    return decorator

@dataclass
class NetworkElement:
    """Represents a network element in the Huawei network"""
    name: str
    site_id: str
    cell_ids: List[int]
    location: str

@dataclass
class ParameterConfig:
    """Configuration for network parameters"""
    parameter_name: str
    query_command: str
    modify_command: str
    value_range: str
    description: str

class HuaweiAPIClient:
    """Client for interacting with Huawei iMaster MAE API"""
    
    def __init__(self, base_url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL for the iMaster MAE API (or from env var HUAWEI_API_URL)
            username: Authentication username (or from env var HUAWEI_USERNAME)  
            password: Authentication password (or from env var HUAWEI_PASSWORD)
        """
        # Use environment variables if parameters not provided
        self.base_url = (base_url or os.getenv('HUAWEI_API_URL', 'https://41.174.191.214:31127')).rstrip('/')
        self.username = username or os.getenv('HUAWEI_USERNAME', 'cassava.ai')
        self.password = password or os.getenv('HUAWEI_PASSWORD', '#Pass123#')
        
        self.auth_token = None
        self.token_expires_at = None
        self.session = requests.Session()
        self.session.verify = False  # For internal networks
        
        # Configure session with connection pooling and timeouts
        from requests.adapters import HTTPAdapter
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Load network elements and parameter configurations
        self.network_elements = self._load_network_elements()
        self.parameter_configs = self._load_parameter_configs()
    
    def _load_network_elements(self) -> List[NetworkElement]:
        """Load network elements from configuration"""
        # Based on your NE Names.txt file
        return [
            NetworkElement(
                name="MSH-0013-Bindura-Zaoga",
                site_id="MSH-0013",
                cell_ids=[1, 2, 3, 4, 5, 6],
                location="Bindura Zaoga"
            ),
            NetworkElement(
                name="MSH-0331-Chiwaridzo 2",
                site_id="MSH-0331",
                cell_ids=[1, 2, 3, 4, 5, 6],
                location="Chiwaridzo 2"
            ),
            NetworkElement(
                name="MSH-0112-Bindura Hospital",
                site_id="MSH-0112",
                cell_ids=[1, 2, 3, 4, 5, 6],
                location="Bindura Hospital"
            ),
            NetworkElement(
                name="MSH-0014-Chipadze",
                site_id="MSH-0014",
                cell_ids=[1, 2, 3, 4, 5, 6],
                location="Chipadze"
            )
        ]
    
    def _load_parameter_configs(self) -> Dict[str, ParameterConfig]:
        """Load parameter configurations from your Configurations.txt"""
        return {
            "reference_signal_power": ParameterConfig(
                parameter_name="Reference Signal Power (RS Power)",
                query_command="LST PDSCHCFG",
                modify_command="MOD PDSCHCFG:LOCALCELLID={cell_id},REFERENCESIGNALPWR={value}; {{{ne_name}}}",
                value_range="-600 to 500",
                description="Reference signal power configuration for downlink"
            ),
            "a3_event_offset": ParameterConfig(
                parameter_name="A3 Event Offset (Intra-freq HO threshold)",
                query_command="LST UECOOPERATIONPARA",
                modify_command="MOD UECOOPERATIONPARA:LOCALCELLID={cell_id},A3OFFSET=dB{value}; {{{ne_name}}}",
                value_range="dB0 to dB15",
                description="Intra-frequency handover threshold"
            ),
            "t310_timer": ParameterConfig(
                parameter_name="T310 Timer (RLF detection)",
                query_command="LST UETIMERCONST",
                modify_command="MOD UETIMERCONST:LOCALCELLID={cell_id},T310={value}; {{{ne_name}}}",
                value_range="MS100_T310 to MS6000_T310",
                description="Radio Link Failure detection timer"
            ),
            "p0_nominal_pusch": ParameterConfig(
                parameter_name="P0_NominalPUSCH (UL nominal power offset)",
                query_command="LST CELLULPCCOMM",
                modify_command="MOD CELLULPCCOMM:LOCALCELLID={cell_id},P0NOMINALPUSCH={value}; {{{ne_name}}}",
                value_range="-126 to 24",
                description="Uplink nominal power control configuration"
            )
        }
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
    def authenticate(self) -> bool:
        """
        Authenticate with the iMaster MAE API
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            url = f"{self.base_url}/api/rest/securityManagement/v1/oauth/token"
            
            payload = {
                "grantType": "password",
                "userName": self.username,
                "value": self.password
            }
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(url, headers=headers, data=json.dumps(payload), timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'accessSession' in result:
                self.auth_token = result['accessSession']
                # Set token expiry with some buffer (23 hours instead of 24)
                self.token_expires_at = datetime.now() + timedelta(hours=23)
                self.logger.info("Authentication successful")
                return True
            else:
                self.logger.error(f"Authentication failed: {result}")
                return False
                
        except requests.RequestException as e:
            self.logger.error(f"Authentication request failed: {e}")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid authentication token with automatic renewal"""
        # Check if token is expired or about to expire (5 minute buffer)
        if (not self.auth_token or 
            (self.token_expires_at and datetime.now() >= (self.token_expires_at - timedelta(minutes=5)))):
            self.logger.info("Token expired or about to expire, re-authenticating...")
            return self.authenticate()
        return True
    
    @retry_on_failure(max_retries=2, delay=0.5, backoff=2.0)
    def execute_mml_command(self, command: str, ne_names: List[str]) -> Dict[str, Any]:
        """
        Execute an MML command on specified network elements with retry logic
        
        Args:
            command: MML command to execute
            ne_names: List of network element names
            
        Returns:
            Dict containing the command response
        """
        if not self._ensure_authenticated():
            raise Exception("Authentication failed")
        
        # Validate network elements exist
        valid_ne_names = []
        for ne_name in ne_names:
            if any(ne.name == ne_name for ne in self.network_elements):
                valid_ne_names.append(ne_name)
            else:
                self.logger.warning(f"Unknown network element: {ne_name}")
        
        if not valid_ne_names:
            raise ValueError(f"No valid network elements found in: {ne_names}")
        
        try:
            url = f"{self.base_url}/api/rest/mmlManagement/v1/command"
            
            payload = {
                "command": command,
                "neNames": valid_ne_names
            }
            
            headers = {
                'X-Auth-Token': self.auth_token,
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            
            # Log response details for troubleshooting
            self.logger.debug(f"Response status: {response.status_code}")
            self.logger.debug(f"Response text: {response.text}")
            
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            self.logger.error(f"MML command execution failed: {e}")
            # Log more details if response is available
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response status: {e.response.status_code}")
                self.logger.error(f"Response text: {e.response.text}")
            raise
    
    def query_parameter(self, parameter_name: str, ne_names: List[str]) -> Dict[str, Any]:
        """
        Query a specific parameter from network elements
        
        Args:
            parameter_name: Parameter to query (from parameter_configs)
            ne_names: List of network element names
            
        Returns:
            Dict containing the query results
        """
        if parameter_name not in self.parameter_configs:
            raise ValueError(f"Unknown parameter: {parameter_name}")
        
        config = self.parameter_configs[parameter_name]
        return self.execute_mml_command(config.query_command, ne_names)
    
    def modify_parameter(self, parameter_name: str, ne_name: str, cell_id: int, value: Any) -> Dict[str, Any]:
        """
        Modify a parameter on a specific network element and cell
        
        Args:
            parameter_name: Parameter to modify
            ne_name: Network element name
            cell_id: Cell ID
            value: New parameter value
            
        Returns:
            Dict containing the modification result
        """
        if parameter_name not in self.parameter_configs:
            raise ValueError(f"Unknown parameter: {parameter_name}")
        
        config = self.parameter_configs[parameter_name]
        command = config.modify_command.format(
            cell_id=cell_id,
            value=value,
            ne_name=ne_name
        )
        
        return self.execute_mml_command(command, [ne_name])
    
    def get_network_elements(self) -> List[NetworkElement]:
        """Get list of available network elements"""
        return self.network_elements
    
    def get_parameter_configs(self) -> Dict[str, ParameterConfig]:
        """Get available parameter configurations"""
        return self.parameter_configs
    
    def get_kpi_data(self, ne_names: List[str], start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """
        Retrieve KPI data for specified network elements and time range
        This would need to be implemented based on specific KPI APIs available
        
        Args:
            ne_names: Network element names
            start_time: Start time for KPI data
            end_time: End time for KPI data
            
        Returns:
            Dict containing KPI data
        """
        # This is a placeholder - actual implementation depends on available KPI APIs
        # You may need to use different endpoints for performance data
        self.logger.info(f"Retrieving KPI data for {ne_names} from {start_time} to {end_time}")
        return {"message": "KPI data retrieval not yet implemented"}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the API connection and authentication
        
        Returns:
            Dict containing health check results
        """
        try:
            # Test authentication
            auth_ok = self._ensure_authenticated()
            
            # Test basic API call with correct syntax
            if auth_ok:
                test_result = self.execute_mml_command("LST UECOOPERATIONPARA:;", ["MSH-0112-Bindura Hospital"])
                api_ok = test_result.get('results', [{}])[0].get('retCode') == 0
            else:
                api_ok = False
            
            return {
                "status": "healthy" if (auth_ok and api_ok) else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "authentication": "ok" if auth_ok else "failed",
                "api_calls": "ok" if api_ok else "failed",
                "token_expires": self.token_expires_at.isoformat() if self.token_expires_at else None
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def bulk_execute_commands(self, commands: List[Dict[str, Any]], delay_between_commands: float = 0.1) -> List[Dict[str, Any]]:
        """
        Execute multiple MML commands with rate limiting
        
        Args:
            commands: List of command dictionaries with 'command' and 'ne_names' keys
            delay_between_commands: Delay in seconds between commands
            
        Returns:
            List of command results
        """
        results = []
        
        for i, cmd_info in enumerate(commands):
            try:
                if i > 0:  # Add delay between commands to avoid overwhelming the API
                    time.sleep(delay_between_commands)
                
                result = self.execute_mml_command(
                    cmd_info['command'], 
                    cmd_info['ne_names']
                )
                results.append({
                    "command": cmd_info['command'],
                    "ne_names": cmd_info['ne_names'],
                    "success": True,
                    "result": result
                })
                
            except Exception as e:
                self.logger.error(f"Bulk command failed: {cmd_info['command']} - {e}")
                results.append({
                    "command": cmd_info['command'],
                    "ne_names": cmd_info['ne_names'],
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    # ========================================
    # ADAPTER METHODS FOR LEGACY AGENT COMPATIBILITY
    # ========================================
    
    def is_connected(self) -> bool:
        """
        Adapter method: Check if API is connected
        Used by legacy agent files for backward compatibility
        """
        return self.auth_token is not None
    
    def connect(self) -> bool:
        """
        Adapter method: Connect to API (maps to authenticate)
        Used by legacy agent files for backward compatibility
        """
        try:
            return self.authenticate()
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def get_cell_status(self, cell_id: str = "1") -> Dict[str, Any]:
        """
        Adapter method: Get cell status information
        Used by legacy agent files for backward compatibility
        """
        try:
            # Get network elements and return status for the specified cell
            elements = self.get_network_elements()
            is_connected = self.auth_token is not None
            if elements:
                # Return basic status information
                return {
                    "cell_id": cell_id,
                    "status": "active",
                    "connected": is_connected,
                    "network_elements": len(elements),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "cell_id": cell_id,
                    "status": "unknown",
                    "connected": is_connected,
                    "network_elements": 0,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Get cell status failed: {e}")
            return {
                "cell_id": cell_id,
                "status": "error",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }