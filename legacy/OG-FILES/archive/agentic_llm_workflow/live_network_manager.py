"""
Live Network Manager - Replaces simulation-based network operations
Integrates with Huawei iMaster MAE API for real network management
"""

import os
import yaml
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Generator
import logging

try:
    from huawei_api_client import HuaweiAPIClient, NetworkElement
except ImportError:
    # Fallback for when running in different contexts
    try:
        from agentic_llm_workflow.huawei_api_client import HuaweiAPIClient, NetworkElement
    except ImportError:
        # Final fallback with dummy classes for testing
        class HuaweiAPIClient:
            def __init__(self, *args, **kwargs):
                pass
            def connect(self):
                return False
            def get_network_elements(self):
                return []
            def get_parameter_value(self, *args, **kwargs):
                return None
            def modify_parameter(self, *args, **kwargs):
                return False
                
        class NetworkElement:
            def __init__(self, *args, **kwargs):
                pass

class LiveNetworkManager:
    """Manages live network operations replacing the simulation approach"""
    
    def __init__(self, api_client=None):
        """Initialize the live network manager"""
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        project_root = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(project_root, 'config.yaml')
        
        try:
            with open(config_path, 'r') as config_file:
                self.config = yaml.safe_load(config_file)
        except FileNotFoundError:
            # Fallback configuration
            self.config = {
                'huawei_api': {
                    'base_url': 'https://41.174.191.214:31127',
                    'username': 'cassava.ai',
                    'password': '#Pass123#'
                }
            }
        
        # Initialize API client (use provided client or create new one)
        if api_client is not None:
            self.api_client = api_client
        else:
            self.api_client = HuaweiAPIClient(
                base_url="https://41.174.191.214:31127",  # From your API Use.txt
                username="cassava.ai",
                password="#Pass123#"
            )
        
        # Database setup
        self.db_path = os.path.join(project_root, 'data', 'live_network.db')
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the database for live network data"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create network elements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS network_elements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    site_id TEXT,
                    location TEXT,
                    cell_ids TEXT,
                    status TEXT DEFAULT 'active',
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create parameter configurations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parameter_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parameter_name TEXT UNIQUE,
                    current_value TEXT,
                    target_value TEXT,
                    ne_name TEXT,
                    cell_id INTEGER,
                    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modification_status TEXT DEFAULT 'pending'
                )
            """)
            
            # Create KPI data table (replaces historical_data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kpi_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ne_name TEXT,
                    cell_id INTEGER,
                    timestamp TIMESTAMP,
                    parameter_name TEXT,
                    parameter_value REAL,
                    throughput_dl REAL,
                    throughput_ul REAL,
                    latency REAL,
                    availability REAL,
                    handover_success_rate REAL,
                    call_drop_rate REAL
                )
            """)
            
            # Create index for kpi_data table
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kpi_data_ne_timestamp ON kpi_data(ne_name, timestamp)")
            
            # Populate network elements from API client
            for ne in self.api_client.get_network_elements():
                cursor.execute("""
                    INSERT OR REPLACE INTO network_elements 
                    (name, site_id, location, cell_ids) 
                    VALUES (?, ?, ?, ?)
                """, (ne.name, ne.site_id, ne.location, ','.join(map(str, ne.cell_ids))))
            
            conn.commit()
    
    def check_network_status(self, print_output=False) -> bool:
        """
        Check if the live network elements are accessible
        Replaces the Docker container status check
        """
        try:
            # Test authentication
            if not self.api_client.authenticate():
                if print_output:
                    print("Authentication failed with iMaster MAE")
                return False
            
            # Test connectivity to network elements
            ne_names = [ne.name for ne in self.api_client.get_network_elements()[:1]]  # Test with one NE
            
            try:
                result = self.api_client.query_parameter("reference_signal_power", ne_names)
                if print_output:
                    print("✓ Successfully connected to live network")
                    print(f"✓ Network elements accessible: {len(self.api_client.get_network_elements())}")
                return True
            except Exception as e:
                if print_output:
                    print(f"✗ Network element query failed: {e}")
                return False
                
        except Exception as e:
            if print_output:
                print(f"✗ Network connectivity check failed: {e}")
            return False
    
    def start_network(self) -> Generator[str, None, None]:
        """
        Connect to live network (replaces Docker container startup)
        """
        yield("(1/3) Connecting to iMaster MAE API...")
        
        try:
            if not self.api_client.authenticate():
                yield "Error: Failed to authenticate with iMaster MAE"
                return
            
            yield("(2/3) Verifying network element connectivity...")
            
            # Test connectivity to all network elements
            ne_names = [ne.name for ne in self.api_client.get_network_elements()]
            accessible_count = 0
            
            for ne_name in ne_names:
                try:
                    self.api_client.query_parameter("reference_signal_power", [ne_name])
                    accessible_count += 1
                except Exception as e:
                    self.logger.warning(f"Network element {ne_name} not accessible: {e}")
            
            yield(f"(3/3) Connected to {accessible_count}/{len(ne_names)} network elements")
            
            if accessible_count > 0:
                # Initialize KPI data collection
                self._collect_initial_kpi_data()
                yield "Successfully connected to live network"
            else:
                yield "Error: No network elements accessible"
            
        except Exception as e:
            yield(f"Error: Failed to connect to live network: {e}")
    
    def stop_network(self, reset_db=False) -> Generator[str, None, None]:
        """
        Disconnect from live network (replaces Docker container shutdown)
        """
        try:
            yield("Disconnecting from live network...")
            
            # Clear authentication token
            self.api_client.auth_token = None
            self.api_client.token_expires_at = None
            
            if reset_db:
                yield("Clearing local database...")
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                self._initialize_database()
            
            yield("Successfully disconnected from live network")
            
        except Exception as e:
            yield(f"Error during disconnection: {e}")
    
    def _collect_initial_kpi_data(self):
        """Collect initial KPI data from network elements"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current timestamp
                current_time = datetime.now()
                
                for ne in self.api_client.get_network_elements():
                    try:
                        # Query current parameter values
                        for param_name in self.api_client.get_parameter_configs().keys():
                            result = self.api_client.query_parameter(param_name, [ne.name])
                            
                            # Parse result and store in database
                            # This is a simplified example - actual parsing depends on response format
                            for cell_id in ne.cell_ids:
                                cursor.execute("""
                                    INSERT INTO kpi_data 
                                    (ne_name, cell_id, timestamp, parameter_name, parameter_value) 
                                    VALUES (?, ?, ?, ?, ?)
                                """, (ne.name, cell_id, current_time, param_name, 0))  # Placeholder value
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to collect data from {ne.name}: {e}")
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to collect initial KPI data: {e}")
    
    def modify_parameter(self, parameter_name: str, ne_name: str, cell_id: int, new_value: Any) -> Dict[str, Any]:
        """
        Modify a parameter on the live network
        """
        try:
            # Execute the modification
            result = self.api_client.modify_parameter(parameter_name, ne_name, cell_id, new_value)
            
            # Store the modification in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO parameter_configs 
                    (parameter_name, target_value, ne_name, cell_id, modification_status) 
                    VALUES (?, ?, ?, ?, ?)
                """, (parameter_name, str(new_value), ne_name, cell_id, 'completed'))
                conn.commit()
            
            return {
                "success": True,
                "message": f"Successfully modified {parameter_name} on {ne_name} cell {cell_id}",
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Failed to modify parameter: {e}")
            return {
                "success": False,
                "message": f"Failed to modify {parameter_name}: {e}",
                "result": None
            }
    
    def get_current_parameters(self, ne_name: str) -> Dict[str, Any]:
        """Get current parameter values for a network element"""
        try:
            current_params = {}
            
            for param_name in self.api_client.get_parameter_configs().keys():
                result = self.api_client.query_parameter(param_name, [ne_name])
                current_params[param_name] = result
            
            return current_params
            
        except Exception as e:
            self.logger.error(f"Failed to get current parameters for {ne_name}: {e}")
            return {}
    
    def get_kpi_data(self, ne_name: Optional[str] = None, hours_back: int = 24) -> pd.DataFrame:
        """
        Retrieve KPI data from database
        Replaces the historical data loading from CSV
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT * FROM kpi_data 
                    WHERE timestamp >= datetime('now', '-{} hours')
                """.format(hours_back)
                
                if ne_name:
                    query += " AND ne_name = ?"
                    params = (ne_name,)
                else:
                    params = ()
                
                query += " ORDER BY timestamp DESC"
                
                return pd.read_sql_query(query, conn, params=params)
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve KPI data: {e}")
            return pd.DataFrame()
    
    def get_network_elements(self) -> List[NetworkElement]:
        """Get list of network elements"""
        return self.api_client.get_network_elements()
    
    def sync_with_network(self):
        """
        Synchronize local database with current network state
        Should be called periodically to update KPI data
        """
        self._collect_initial_kpi_data()


# Global instance for backward compatibility
live_network_manager = LiveNetworkManager()