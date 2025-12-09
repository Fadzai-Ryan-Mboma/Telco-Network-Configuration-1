#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network - Live Huawei iMaster MAE API Client
Phase 2 Implementation: Live Network Connection Testing
"""

import os
import time
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Suppress SSL warnings if SSL verification is disabled
urllib3.disable_warnings(InsecureRequestWarning)

# Setup logging
logger = logging.getLogger('LZ-Huawei-API')

class HuaweiAPIError(Exception):
    """Custom exception for Huawei API errors"""
    pass

class HuaweiAuthenticationError(HuaweiAPIError):
    """Authentication-specific errors"""
    pass

class HuaweiAPIClient:
    """
    Production Huawei iMaster MAE API Client for Liquid Zimbabwe 4G Network
    
    Features:
    - Token-based authentication with auto-refresh
    - Retry logic with exponential backoff
    - SSL certificate validation
    - Connection pooling
    - Rate limiting
    - Comprehensive error handling
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get('base_url', '').rstrip('/')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.timeout = config.get('timeout', 30)
        self.retry_attempts = config.get('retry_attempts', 3)
        self.retry_delay = config.get('retry_delay', 5)
        self.ssl_verify = config.get('ssl_verify', True)
        
        # Authentication state
        self.access_token = None
        self.token_expires_at = None
        self.session_id = None
        
        # Session configuration
        self.session = requests.Session()
        self.session.verify = self.ssl_verify
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Minimum 100ms between requests
        
        logger.info("🔌 Huawei API Client initialized")
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate API configuration"""
        required_fields = ['base_url', 'username', 'password']
        missing_fields = [field for field in required_fields if not getattr(self, field)]
        
        if missing_fields:
            raise HuaweiAPIError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        if not self.base_url.startswith(('http://', 'https://')):
            raise HuaweiAPIError("Base URL must start with http:// or https://")
        
        logger.info("✅ API configuration validated")
    
    def connect(self) -> bool:
        """
        Establish connection and authenticate with Huawei iMaster MAE
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info("🔐 Attempting authentication with Huawei iMaster MAE...")

            # Prepare authentication request (corrected endpoint from Postman testing)
            auth_url = f"{self.base_url}/api/rest/securityManagement/v1/oauth/token"
            auth_payload = {
                "grantType": "password",
                "userName": self.username,
                "value": self.password
            }

            # Make authentication request (PUT method as per Huawei OAuth API)
            response = self._make_request('PUT', auth_url, json=auth_payload, authenticated=False)
            
            if response.status_code == 200:
                auth_data = response.json()

                # Extract authentication tokens (Huawei uses 'accessSession' not 'access_token')
                if 'accessSession' in auth_data:
                    self.access_token = auth_data['accessSession']

                    # Calculate token expiration (Huawei provides 'expires' in seconds)
                    expires_in = auth_data.get('expires', 1800)  # Default 30 minutes
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

                    # Store ROA random if available (used for some Huawei API calls)
                    self.session_id = auth_data.get('roaRand')

                    # Update session headers with Huawei's X-Auth-Token header
                    self.session.headers.update({
                        'X-Auth-Token': self.access_token,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    })

                    logger.info(f"✅ Successfully authenticated with Huawei iMaster MAE (token expires in {expires_in}s)")
                    return True
                else:
                    logger.error("❌ Authentication failed: No accessSession in response")
                    return False
            else:
                logger.error(f"❌ Authentication failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection error: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from the API and cleanup resources"""
        try:
            if self.access_token:
                logout_url = f"{self.base_url}/rest-oss/rest/plat/smapp/v1/logout"
                self._make_request('POST', logout_url)
                
            self.access_token = None
            self.token_expires_at = None
            self.session_id = None
            self.session.close()
            
            logger.info("🔌 Disconnected from Huawei iMaster MAE")
            
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {str(e)}")
    
    def _is_token_valid(self) -> bool:
        """Check if current token is valid"""
        if not self.access_token or not self.token_expires_at:
            return False
        
        # Add 5-minute buffer for token refresh
        return datetime.now() < (self.token_expires_at - timedelta(minutes=5))
    
    def _refresh_token(self) -> bool:
        """Refresh the authentication token"""
        logger.info("🔄 Refreshing authentication token...")
        return self.connect()
    
    def _make_request(self, method: str, url: str, authenticated: bool = True, **kwargs) -> requests.Response:
        """
        Make HTTP request with retry logic and error handling
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Request URL
            authenticated: Whether request requires authentication
            **kwargs: Additional request parameters
            
        Returns:
            requests.Response: HTTP response object
            
        Raises:
            HuaweiAPIError: On request failure
        """
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_request_time < self.min_request_interval:
            time.sleep(self.min_request_interval - (current_time - self.last_request_time))
        
        # Validate authentication if required
        if authenticated and not self._is_token_valid():
            if not self._refresh_token():
                raise HuaweiAuthenticationError("Failed to refresh authentication token")
        
        # Set default timeout
        kwargs.setdefault('timeout', self.timeout)
        
        # Retry logic
        last_exception = None
        for attempt in range(self.retry_attempts + 1):
            try:
                logger.debug(f"📡 {method} {url} (attempt {attempt + 1})")
                
                response = self.session.request(method, url, **kwargs)
                self.last_request_time = time.time()
                
                # Check for successful response
                if response.status_code < 400:
                    return response
                elif response.status_code == 401 and authenticated:
                    # Authentication failed, try to refresh token
                    logger.warning("🔐 Authentication expired, refreshing token...")
                    if self._refresh_token():
                        continue
                    else:
                        raise HuaweiAuthenticationError("Authentication refresh failed")
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.retry_attempts:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"⚠️ Request failed (attempt {attempt + 1}), retrying in {delay}s: {str(e)}")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ Request failed after {self.retry_attempts + 1} attempts: {str(e)}")
        
        raise HuaweiAPIError(f"Request failed: {str(last_exception)}")
    
    def get_kpi_data(self, cell_ids: List[str] = None, time_range: int = 15) -> Dict[str, Any]:
        """
        Retrieve KPI data from network elements
        
        Args:
            cell_ids: List of cell IDs to query (None for all cells)
            time_range: Time range in minutes for historical data
            
        Returns:
            Dict containing KPI data
        """
        try:
            logger.info(f"📊 Retrieving KPI data for {len(cell_ids) if cell_ids else 'all'} cells")
            
            # Build KPI query parameters
            params = {
                'timeRange': time_range,
                'granularity': 'PT15M',  # 15-minute granularity
                'kpiType': 'LTE_CELL_KPI'
            }
            
            if cell_ids:
                params['cellIds'] = ','.join(cell_ids)
            
            # Make KPI data request
            kpi_url = f"{self.base_url}/rest-oss/rest/kpi/v1/cells/kpi"
            response = self._make_request('GET', kpi_url, params=params)
            
            kpi_data = response.json()
            
            # Process and validate KPI data
            processed_data = self._process_kpi_data(kpi_data)
            
            logger.info(f"✅ Retrieved KPI data for {len(processed_data)} cells")
            return processed_data
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve KPI data: {str(e)}")
            raise HuaweiAPIError(f"KPI data retrieval failed: {str(e)}")
    
    def get_parameter_values(self, cell_ids: List[str], parameter_names: List[str]) -> Dict[str, Any]:
        """
        Retrieve current parameter values from network elements
        
        Args:
            cell_ids: List of cell IDs to query
            parameter_names: List of parameter names to retrieve
            
        Returns:
            Dict containing parameter values by cell
        """
        try:
            logger.info(f"⚙️ Retrieving parameters {parameter_names} for {len(cell_ids)} cells")
            
            # Build parameter query
            query_payload = {
                'cellIds': cell_ids,
                'parameters': parameter_names
            }
            
            # Make parameter request
            param_url = f"{self.base_url}/rest-oss/rest/config/v1/cells/parameters"
            response = self._make_request('POST', param_url, json=query_payload)
            
            param_data = response.json()
            
            # Process parameter data
            processed_params = self._process_parameter_data(param_data)
            
            logger.info(f"✅ Retrieved parameters for {len(processed_params)} cells")
            return processed_params
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve parameters: {str(e)}")
            raise HuaweiAPIError(f"Parameter retrieval failed: {str(e)}")
    
    def update_parameters(self, cell_id: str, parameter_updates: Dict[str, Any]) -> bool:
        """
        Update network parameters for a specific cell
        
        Args:
            cell_id: Target cell ID
            parameter_updates: Dict of parameter names and new values
            
        Returns:
            bool: True if update successful
        """
        try:
            logger.info(f"🔧 Updating parameters for cell {cell_id}: {list(parameter_updates.keys())}")
            
            # Build parameter update payload
            update_payload = {
                'cellId': cell_id,
                'parameters': parameter_updates,
                'validateOnly': False  # Set to True for dry-run validation
            }
            
            # Make parameter update request
            update_url = f"{self.base_url}/rest-oss/rest/config/v1/cells/{cell_id}/parameters"
            response = self._make_request('PUT', update_url, json=update_payload)
            
            if response.status_code in [200, 202]:
                update_result = response.json()
                
                # Check if update was successful
                if update_result.get('status') == 'success':
                    logger.info(f"✅ Successfully updated parameters for cell {cell_id}")
                    return True
                else:
                    logger.error(f"❌ Parameter update failed: {update_result.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"❌ Parameter update request failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to update parameters: {str(e)}")
            return False
    
    def execute_mml_command(self, mml_command: str, site_names: List[str]) -> Dict[str, Any]:
        """
        Execute single MML command on network elements (sites)

        IMPORTANT:
        - QUERY commands (LST) work site-wide and return data for all cells
        - MODIFY commands (MOD) must include LOCALCELLID and are cell-specific

        Args:
            mml_command: MML command string
                Query example: "LST UECOOPERATIONPARA:;"
                Modify example: "MOD PDSCHCFG:LOCALCELLID=1,REFERENCESIGNALPWR=-180;"
            site_names: List of site names (e.g., ["MSH-0112-Bindura Hospital"])

        Returns:
            Dict containing command execution result

        Example (Query - site-wide):
            >>> client.execute_mml_command(
            ...     "LST UECOOPERATIONPARA:;",
            ...     ["MSH-0112-Bindura Hospital"]
            ... )

        Example (Modify - cell-specific):
            >>> client.execute_mml_command(
            ...     "MOD PDSCHCFG:LOCALCELLID=1,REFERENCESIGNALPWR=-180;",
            ...     ["MSH-0112-Bindura Hospital"]
            ... )
        """
        try:
            logger.info(f"📝 Executing MML command: {mml_command}")
            logger.info(f"   Target sites: {', '.join(site_names)}")

            # Build MML command payload (corrected format from API documentation)
            command_payload = {
                'command': mml_command,
                'neNames': site_names
            }

            # Make MML command request (corrected endpoint from API documentation)
            mml_url = f"{self.base_url}/api/rest/mmlManagement/v1/command"
            response = self._make_request('POST', mml_url, json=command_payload)

            command_result = response.json()

            logger.info(f"✅ MML command executed successfully")
            return command_result

        except Exception as e:
            logger.error(f"❌ MML command execution failed: {str(e)}")
            raise HuaweiAPIError(f"MML command failed: {str(e)}")

    def execute_mml_command_batch(self, command_template: str, site_name: str,
                                   cell_ids: List[int] = None) -> List[Dict[str, Any]]:
        """
        Execute MML modification command for multiple cells at a site

        CRITICAL: Parameter modifications MUST be done cell-by-cell.
        This method executes the same parameter change across all cells.

        Args:
            command_template: MML command with {cell_id} placeholder
                Example: "MOD PDSCHCFG:LOCALCELLID={cell_id},REFERENCESIGNALPWR=-180;"
            site_name: Target site name (e.g., "MSH-0112-Bindura Hospital")
            cell_ids: List of cell IDs (default: [1,2,3,4,5,6] for standard 6-cell site)

        Returns:
            List of command execution results (one per cell)

        Example:
            >>> client.execute_mml_command_batch(
            ...     "MOD PDSCHCFG:LOCALCELLID={cell_id},REFERENCESIGNALPWR=-180;",
            ...     "MSH-0112-Bindura Hospital"
            ... )
            Returns: [
                {'cell_id': 1, 'command': '...', 'result': {...}, 'success': True},
                {'cell_id': 2, 'command': '...', 'result': {...}, 'success': True},
                ...
            ]
        """
        if cell_ids is None:
            cell_ids = [1, 2, 3, 4, 5, 6]  # Default 6-cell site configuration

        logger.info(f"📝 Executing batch MML command for {len(cell_ids)} cells at {site_name}")

        results = []
        for cell_id in cell_ids:
            try:
                # Format command with cell ID
                command = command_template.format(cell_id=cell_id)

                logger.info(f"   Cell {cell_id}: {command}")

                # Execute command for this cell
                result = self.execute_mml_command(command, [site_name])

                results.append({
                    'cell_id': cell_id,
                    'command': command,
                    'result': result,
                    'success': True
                })

                logger.info(f"   ✅ Cell {cell_id}: SUCCESS")

            except Exception as e:
                logger.error(f"   ❌ Cell {cell_id}: FAILED - {str(e)}")

                results.append({
                    'cell_id': cell_id,
                    'command': command if 'command' in locals() else 'N/A',
                    'result': None,
                    'success': False,
                    'error': str(e)
                })

        # Summary
        successful = sum(1 for r in results if r['success'])
        logger.info(f"✅ Batch execution complete: {successful}/{len(cell_ids)} cells successful")

        return results
    
    def get_cell_list(self) -> List[Dict[str, Any]]:
        """
        Retrieve list of all cells in the network
        
        Returns:
            List of cell information dictionaries
        """
        try:
            logger.info("📡 Retrieving cell inventory...")
            
            # Make cell list request
            cells_url = f"{self.base_url}/rest-oss/rest/inventory/v1/cells"
            response = self._make_request('GET', cells_url)
            
            cells_data = response.json()
            
            # Process cell list
            cell_list = cells_data.get('cells', [])
            
            logger.info(f"✅ Retrieved {len(cell_list)} cells from inventory")
            return cell_list
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve cell list: {str(e)}")
            raise HuaweiAPIError(f"Cell list retrieval failed: {str(e)}")
    
    def _process_kpi_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate raw KPI data"""
        processed = {}
        
        for cell_data in raw_data.get('data', []):
            cell_id = cell_data.get('cellId')
            if not cell_id:
                continue
                
            # Extract KPI values with validation
            kpis = {}
            for kpi in cell_data.get('kpis', []):
                kpi_name = kpi.get('name')
                kpi_value = kpi.get('value')
                
                if kpi_name and kpi_value is not None:
                    # Validate KPI value ranges
                    if self._validate_kpi_value(kpi_name, kpi_value):
                        kpis[kpi_name] = float(kpi_value)
                    else:
                        logger.warning(f"⚠️ Invalid KPI value for {kpi_name}: {kpi_value}")
            
            if kpis:
                processed[cell_id] = {
                    'timestamp': cell_data.get('timestamp', datetime.now().isoformat()),
                    'kpis': kpis
                }
        
        return processed
    
    def _process_parameter_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate raw parameter data"""
        processed = {}
        
        for cell_data in raw_data.get('data', []):
            cell_id = cell_data.get('cellId')
            if not cell_id:
                continue
                
            # Extract parameter values
            parameters = {}
            for param in cell_data.get('parameters', []):
                param_name = param.get('name')
                param_value = param.get('value')
                
                if param_name and param_value is not None:
                    parameters[param_name] = param_value
            
            if parameters:
                processed[cell_id] = parameters
        
        return processed
    
    def _validate_kpi_value(self, kpi_name: str, value: float) -> bool:
        """Validate KPI value is within reasonable ranges"""
        kpi_ranges = {
            'rsrp': (-150, -30),      # RSRP in dBm
            'rsrq': (-30, 0),         # RSRQ in dB
            'sinr': (-10, 40),        # SINR in dB
            'throughput_dl': (0, 1000), # DL Throughput in Mbps
            'throughput_ul': (0, 100),   # UL Throughput in Mbps
            'csr': (0, 100),           # Call Success Rate in %
            'hsr': (0, 100),           # Handover Success Rate in %
            'rru': (0, 100)            # Resource Block Utilization in %
        }
        
        if kpi_name.lower() in kpi_ranges:
            min_val, max_val = kpi_ranges[kpi_name.lower()]
            return min_val <= value <= max_val
        
        # If no validation rule defined, accept the value
        return True
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of API connection
        
        Returns:
            Dict containing health status information
        """
        health_status = {
            'status': 'unknown',
            'timestamp': datetime.now().isoformat(),
            'details': {}
        }
        
        try:
            # Check authentication status
            if self._is_token_valid():
                health_status['details']['authentication'] = 'valid'
            else:
                health_status['details']['authentication'] = 'expired'
            
            # Perform a simple API call to test connectivity
            start_time = time.time()
            response = self._make_request('GET', f"{self.base_url}/rest-oss/rest/system/v1/health")
            response_time = time.time() - start_time
            
            health_status['details']['response_time'] = f"{response_time:.3f}s"
            health_status['details']['api_status'] = response.status_code
            
            if response.status_code == 200:
                health_status['status'] = 'healthy'
                logger.info("✅ API health check passed")
            else:
                health_status['status'] = 'degraded'
                logger.warning(f"⚠️ API health check degraded: HTTP {response.status_code}")
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['details']['error'] = str(e)
            logger.error(f"❌ API health check failed: {str(e)}")
        
        return health_status

# Example usage for testing
if __name__ == "__main__":
    # Test configuration (use environment variables in production)
    test_config = {
        'base_url': os.getenv('LZ_API_URL', 'https://api.example.com'),
        'username': os.getenv('LZ_API_USERNAME', 'test_user'),
        'password': os.getenv('LZ_API_PASSWORD', 'test_password'),
        'timeout': 30,
        'retry_attempts': 3,
        'retry_delay': 5,
        'ssl_verify': False  # Set to True in production
    }
    
    # Initialize and test API client
    api_client = HuaweiAPIClient(test_config)
    
    try:
        # Test connection
        if api_client.connect():
            print("✅ API connection successful")
            
            # Test health check
            health = api_client.health_check()
            print(f"🏥 Health status: {health['status']}")
            
            # Test cell list retrieval
            cells = api_client.get_cell_list()
            print(f"📡 Found {len(cells)} cells")
            
        else:
            print("❌ API connection failed")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        
    finally:
        api_client.disconnect()