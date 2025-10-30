"""
Huawei iMaster MAE API Client
Provides authentication and network management capabilities for live Huawei network elements.
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import urllib3

# Disable SSL warnings for internal network usage
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    
    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL for the iMaster MAE API
            username: Authentication username
            password: Authentication password
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth_token = None
        self.token_expires_at = None
        self.session = requests.Session()
        self.session.verify = False  # For internal networks
        
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
            response = self.session.put(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            # Accept 'accessToken' or fallback to 'accessSession' as token
            token = result.get('accessToken') or result.get('accessSession')
            if token:
                self.auth_token = token
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
        """Ensure we have a valid authentication token"""
        if not self.auth_token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            return self.authenticate()
        return True
    
    def test_connectivity(self) -> Dict[str, Any]:
        """
        Test connectivity to the Huawei iMaster MAE API
        
        Returns:
            Dict containing connectivity test results
        """
        try:
            # First test basic API endpoint availability
            url = f"{self.base_url}/api/rest/securityManagement/v1/oauth/token"
            
            # Simple GET request to check if the API endpoint is reachable
            response = self.session.get(url, timeout=10)
            
            # If we get any response (even error), the endpoint is reachable
            endpoint_reachable = True
            endpoint_status = response.status_code
            
        except requests.RequestException as e:
            endpoint_reachable = False
            endpoint_status = None
            self.logger.error(f"API endpoint unreachable: {e}")
        
        # Test authentication
        auth_successful = False
        auth_message = "Not tested"
        
        if endpoint_reachable:
            try:
                auth_successful = self.authenticate()
                auth_message = "Authentication successful" if auth_successful else "Authentication failed"
            except Exception as e:
                auth_message = f"Authentication error: {str(e)}"
        
        # Test network element discovery if authenticated
        elements_discovered = 0
        discovery_message = "Not tested"
        
        if auth_successful:
            try:
                # Try to get basic system information or network elements
                elements = self.get_network_elements()
                elements_discovered = len(elements)
                discovery_message = f"Found {elements_discovered} configured network elements"
            except Exception as e:
                discovery_message = f"Element discovery error: {str(e)}"
        
        return {
            "status": "success" if (endpoint_reachable and auth_successful) else "failed",
            "endpoint_reachable": endpoint_reachable,
            "endpoint_status_code": endpoint_status,
            "authentication_successful": auth_successful,
            "authentication_message": auth_message,
            "network_elements_count": elements_discovered,
            "discovery_message": discovery_message,
            "timestamp": datetime.now().isoformat(),
            "api_endpoint": self.base_url
        }
    
    def execute_mml_command(self, command: str, ne_names: List[str]) -> Dict[str, Any]:
        """
        Execute an MML command on specified network elements
        
        Args:
            command: MML command to execute
            ne_names: List of network element names
            
        Returns:
            Dict containing the command response
        """
        if not self._ensure_authenticated():
            raise Exception("Authentication failed")
        
        try:
            url = f"{self.base_url}/api/rest/mmlManagement/v1/command"
            payload = {
                "command": command,
                "neNames": ne_names
            }
            headers = {
                'X-Auth-Token': self.auth_token,
                'Content-Type': 'application/json'
            }
            response = self.session.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"MML command execution failed: {e}")
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
    
    # ========== ADAPTER METHODS FOR AGENT COMPATIBILITY ==========
    # These methods provide compatibility with agent expectations
    
    def is_connected(self) -> bool:
        """Check if currently connected to the API"""
        return self.auth_token is not None and (
            self.token_expires_at is None or datetime.now() < self.token_expires_at
        )
    
    def connect(self) -> Dict[str, Any]:
        """Connect to the API (wrapper for authenticate)"""
        success = self.authenticate()
        return {
            "status": "success" if success else "failed",
            "connected": success,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_cell_status(self, cell_id: int) -> Dict[str, Any]:
        """Get status information for a specific cell"""
        # This would require a specific API endpoint for cell status
        # For now, return a placeholder response
        return {
            "cell_id": cell_id,
            "status": "active",
            "message": "Cell status endpoint not yet implemented"
        }