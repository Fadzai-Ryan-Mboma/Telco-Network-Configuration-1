"""
Liquid Zimbabwe Parameter Management System
Handles the 5 core network parameters for optimization with MML command integration
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import sqlite3

class LiquidZimbabweParameterManager:
    """Manages the 5 core network parameters for Liquid Zimbabwe"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Parameter configuration based on Configurations.txt
        self.parameter_config = {
            "reference_signal_power_pdschcfg": {
                "technical_name": "Reference Signal Power (PDSCHCFG(0.1 dBm))",
                "user_friendly_name": "Download Signal Strength",
                "description": "Power level for download reference signals (affects coverage area)",
                "unit": "0.1 dBm",
                "range": (-600, 500),
                "query_command": "LST PDSCHCFG",
                "modify_command": "MOD PDSCHCFG:LOCALCELLID={cell_id},REFERENCESIGNALPWR={value}; {{{ne_name}}}",
                "impact": "Higher values increase coverage but may cause interference"
            },
            "reference_signal_power_rs": {
                "technical_name": "Reference Signal Power (RS Power)",
                "user_friendly_name": "Cell Coverage Power", 
                "description": "Primary reference signal power (main coverage control)",
                "unit": "0.1 dBm",
                "range": (-600, 500),
                "query_command": "LST PDSCHCFG",
                "modify_command": "MOD PDSCHCFG:LOCALCELLID={cell_id},REFERENCESIGNALPWR={value}; {{{ne_name}}}",
                "impact": "Main parameter controlling cell footprint and interference"
            },
            "a3_event_offset": {
                "technical_name": "A3 Event Offset (Intra-freq HO threshold)",
                "user_friendly_name": "Handover Sensitivity",
                "description": "When devices switch between cells (lower = switch earlier)",
                "unit": "dB",
                "range": (0, 15),
                "query_command": "LST UECOOPERATIONPARA", 
                "modify_command": "MOD UECOOPERATIONPARA:LOCALCELLID={cell_id},A3OFFSET=dB{value}; {{{ne_name}}}",
                "impact": "Lower values reduce call drops but increase ping-pong handovers"
            },
            "t310_timer": {
                "technical_name": "T310 Timer (RLF detection)",
                "user_friendly_name": "Connection Recovery Time",
                "description": "How long to wait before declaring connection failure",
                "unit": "ms",
                "range": (100, 6000),
                "valid_values": ["MS100_T310", "MS200_T310", "MS500_T310", "MS1000_T310", 
                               "MS1500_T310", "MS2000_T310", "MS2500_T310", "MS6000_T310"],
                "query_command": "LST UETIMERCONST",
                "modify_command": "MOD UETIMERCONST:LOCALCELLID={cell_id},T310={value}; {{{ne_name}}}",
                "impact": "Longer timers reduce false alarms but delay real failure detection"
            },
            "p0_nominal_pusch": {
                "technical_name": "P0_NominalPUSCH (UL nominal power offset)",
                "user_friendly_name": "Upload Power Control",
                "description": "Base power level for device uploads (affects battery and interference)",
                "unit": "dBm", 
                "range": (-126, 24),
                "query_command": "LST CELLULPCCOMM",
                "modify_command": "MOD CELLULPCCOMM:LOCALCELLID={cell_id},P0NOMINALPUSCH={value}; {{{ne_name}}}",
                "impact": "Higher values improve upload quality but increase interference"
            },
            "pdcch_aggregation_level": {
                "technical_name": "PDCCH Aggregation Level", 
                "user_friendly_name": "Control Channel Robustness",
                "description": "How much redundancy to use in control messages",
                "unit": "level",
                "range": (0, 30),
                "query_command": "LST CELLUSPARACFG",
                "modify_command": "MOD CELLUSPARACFG:LOCALCELLID={cell_id},USDATAPDCCHSINROFFSET={value}; {{{ne_name}}}",
                "impact": "Higher levels improve reliability but use more resources"
            }
        }
        
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the parameter tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create parameter values table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parameter_values (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    site_name TEXT,
                    cell_id INTEGER,
                    parameter_name TEXT,
                    current_value TEXT,
                    previous_value TEXT,
                    change_reason TEXT,
                    changed_by TEXT
                )
            """)
            
            # Create indexes for parameter values table
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_parameter_values_site_param ON parameter_values(site_name, parameter_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_parameter_values_timestamp ON parameter_values(timestamp)")
            
            # Create parameter change history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parameter_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    site_name TEXT,
                    cell_id INTEGER,
                    parameter_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    change_type TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    rollback_available BOOLEAN DEFAULT TRUE,
                    kpi_before TEXT,
                    kpi_after TEXT
                )
            """)
            
            conn.commit()
    
    def get_parameter_info(self, parameter_name: str) -> Dict:
        """Get detailed information about a parameter"""
        if parameter_name not in self.parameter_config:
            raise ValueError(f"Unknown parameter: {parameter_name}")
        
        return self.parameter_config[parameter_name].copy()
    
    def get_all_parameters(self) -> Dict[str, Dict]:
        """Get information about all parameters"""
        return {name: config.copy() for name, config in self.parameter_config.items()}
    
    def validate_parameter_value(self, parameter_name: str, value: Any) -> Tuple[bool, str]:
        """Validate a parameter value against its constraints"""
        if parameter_name not in self.parameter_config:
            return False, f"Unknown parameter: {parameter_name}"
        
        config = self.parameter_config[parameter_name]
        
        # Handle T310 timer special case with valid values
        if parameter_name == "t310_timer":
            if str(value) not in config["valid_values"]:
                return False, f"Value must be one of: {', '.join(config['valid_values'])}"
            return True, "Valid"
        
        # Handle A3 offset special formatting
        if parameter_name == "a3_event_offset":
            try:
                # Remove 'dB' prefix if present
                clean_value = str(value).replace('dB', '').replace('db', '')
                numeric_value = float(clean_value)
                min_val, max_val = config["range"]
                if not (min_val <= numeric_value <= max_val):
                    return False, f"Value must be between {min_val} and {max_val} dB"
                return True, "Valid"
            except ValueError:
                return False, "Value must be a number (with or without dB suffix)"
        
        # Standard numeric range validation
        try:
            numeric_value = float(value)
            min_val, max_val = config["range"]
            if not (min_val <= numeric_value <= max_val):
                return False, f"Value must be between {min_val} and {max_val}"
            return True, "Valid"
        except ValueError:
            return False, "Value must be a number"
    
    def format_mml_command(self, parameter_name: str, cell_id: int, value: Any, ne_name: str) -> str:
        """Format the MML command for parameter modification"""
        if parameter_name not in self.parameter_config:
            raise ValueError(f"Unknown parameter: {parameter_name}")
        
        config = self.parameter_config[parameter_name]
        
        # Special formatting for A3 offset
        if parameter_name == "a3_event_offset":
            # Ensure dB prefix
            if not str(value).startswith('dB'):
                value = f"dB{value}"
        
        # Format the command
        command = config["modify_command"].format(
            cell_id=cell_id,
            value=value,
            ne_name=ne_name
        )
        
        return command
    
    def record_parameter_change(self, site_name: str, cell_id: int, parameter_name: str, 
                              old_value: Any, new_value: Any, change_type: str = "manual",
                              success: bool = True, error_message: Optional[str] = None) -> int:
        """Record a parameter change in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO parameter_changes (
                    site_name, cell_id, parameter_name, old_value, new_value,
                    change_type, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (site_name, cell_id, parameter_name, str(old_value), str(new_value),
                  change_type, success, error_message))
            
            change_id = cursor.lastrowid or 0
            
            # Update current parameter value if change was successful
            if success:
                cursor.execute("""
                    INSERT OR REPLACE INTO parameter_values (
                        site_name, cell_id, parameter_name, current_value, previous_value
                    ) VALUES (?, ?, ?, ?, ?)
                """, (site_name, cell_id, parameter_name, str(new_value), str(old_value)))
            
            conn.commit()
            return change_id
    
    def get_current_parameters(self, site_name: str, cell_id: Optional[int] = None) -> Dict:
        """Get current parameter values for a site/cell"""
        with sqlite3.connect(self.db_path) as conn:
            if cell_id is not None:
                query = """
                    SELECT parameter_name, current_value, timestamp
                    FROM parameter_values 
                    WHERE site_name = ? AND cell_id = ?
                    ORDER BY timestamp DESC
                """
                params = (site_name, str(cell_id))
            else:
                query = """
                    SELECT parameter_name, current_value, cell_id, timestamp
                    FROM parameter_values 
                    WHERE site_name = ?
                    ORDER BY cell_id, timestamp DESC
                """
                params = (site_name,)
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if cell_id is not None:
                # Single cell result
                parameters = {}
                for param_name, current_value, timestamp in results:
                    if param_name not in parameters:  # Get most recent only
                        config = self.parameter_config.get(param_name, {})
                        parameters[param_name] = {
                            "current_value": current_value,
                            "user_friendly_name": config.get("user_friendly_name", param_name),
                            "description": config.get("description", ""),
                            "unit": config.get("unit", ""),
                            "last_updated": timestamp
                        }
                return parameters
            else:
                # Multi-cell result
                cells = {}
                for param_name, current_value, cell_id_result, timestamp in results:
                    if cell_id_result not in cells:
                        cells[cell_id_result] = {}
                    if param_name not in cells[cell_id_result]:
                        config = self.parameter_config.get(param_name, {})
                        cells[cell_id_result][param_name] = {
                            "current_value": current_value,
                            "user_friendly_name": config.get("user_friendly_name", param_name),
                            "description": config.get("description", ""),
                            "unit": config.get("unit", ""),
                            "last_updated": timestamp
                        }
                return cells
    
    def get_change_history(self, site_name: str, cell_id: Optional[int] = None, 
                          parameter_name: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get parameter change history"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT timestamp, site_name, cell_id, parameter_name, 
                       old_value, new_value, change_type, success, error_message
                FROM parameter_changes 
                WHERE site_name = ?
            """
            params = [site_name]
            
            if cell_id is not None:
                query += " AND cell_id = ?"
                params.append(str(cell_id))
            
            if parameter_name is not None:
                query += " AND parameter_name = ?"
                params.append(parameter_name)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(str(limit))
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            history = []
            for row in results:
                config = self.parameter_config.get(row[3], {})
                history.append({
                    "timestamp": row[0],
                    "site_name": row[1], 
                    "cell_id": row[2],
                    "parameter_name": row[3],
                    "user_friendly_name": config.get("user_friendly_name", row[3]),
                    "old_value": row[4],
                    "new_value": row[5],
                    "change_type": row[6],
                    "success": bool(row[7]),
                    "error_message": row[8]
                })
            
            return history
    
    def get_rollback_candidates(self, site_name: str, cell_id: Optional[int] = None) -> List[Dict]:
        """Get parameters that can be rolled back due to performance degradation"""
        with sqlite3.connect(self.db_path) as conn:
            # Get recent changes that were successful
            query = """
                SELECT id, timestamp, parameter_name, old_value, new_value
                FROM parameter_changes 
                WHERE site_name = ? AND success = 1 AND rollback_available = 1
                AND timestamp >= datetime('now', '-24 hours')
            """
            params = [site_name]
            
            if cell_id is not None:
                query += " AND cell_id = ?"
                params.append(str(cell_id))
            
            query += " ORDER BY timestamp DESC"
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            rollback_candidates = []
            for row in results:
                config = self.parameter_config.get(row[2], {})
                rollback_candidates.append({
                    "change_id": row[0],
                    "timestamp": row[1],
                    "parameter_name": row[2],
                    "user_friendly_name": config.get("user_friendly_name", row[2]),
                    "current_value": row[4],
                    "rollback_value": row[3],
                    "description": config.get("description", "")
                })
            
            return rollback_candidates
    
    def suggest_parameter_optimization(self, kpi_issues: List[str]) -> List[Dict]:
        """Suggest parameter changes based on KPI issues"""
        suggestions = []
        
        # Knowledge base of parameter impacts based on training data
        optimization_rules = {
            "low_network_access_success": [
                ("reference_signal_power_rs", "increase", "Higher RS power improves access success"),
                ("a3_event_offset", "decrease", "Lower A3 offset reduces handover failures")
            ],
            "high_download_quality_issues": [
                ("reference_signal_power_pdschcfg", "increase", "Higher PDSCH power improves download quality"),
                ("pdcch_aggregation_level", "increase", "Higher aggregation improves control reliability")
            ],
            "high_upload_quality_issues": [
                ("p0_nominal_pusch", "increase", "Higher P0 improves upload quality for edge users"),
                ("t310_timer", "increase", "Longer timer reduces unnecessary failures")
            ],
            "high_control_channel_load": [
                ("pdcch_aggregation_level", "decrease", "Lower aggregation reduces resource usage")
            ],
            "low_download_speed": [
                ("reference_signal_power_pdschcfg", "increase", "Higher power improves coverage and speed"),
                ("pdcch_aggregation_level", "optimize", "Balance between reliability and efficiency")
            ],
            "low_upload_speed": [
                ("p0_nominal_pusch", "increase", "Higher power improves upload performance")
            ]
        }
        
        for issue in kpi_issues:
            if issue in optimization_rules:
                for param_name, direction, reason in optimization_rules[issue]:
                    if param_name in self.parameter_config:
                        config = self.parameter_config[param_name]
                        suggestions.append({
                            "parameter_name": param_name,
                            "user_friendly_name": config["user_friendly_name"],
                            "direction": direction,
                            "reason": reason,
                            "impact": config["impact"],
                            "current_range": config["range"]
                        })
        
        return suggestions
    
    # ========================================
    # ADAPTER METHODS FOR LEGACY AGENT COMPATIBILITY
    # ========================================
    
    def get_parameter_value(self, param_name: str, cell_id: str = "1") -> Optional[float]:
        """
        Adapter method: Get current parameter value
        Used by legacy agent files for backward compatibility
        """
        # In a real implementation, this would query the actual network
        # For now, return a default value based on parameter config
        if param_name in self.parameter_config:
            config = self.parameter_config[param_name]
            min_val, max_val = config["range"]
            return (min_val + max_val) / 2  # Return midpoint as default
        return None
    
    def execute_mml_command(self, command: str, cell_id: str = "1") -> Dict[str, Any]:
        """
        Adapter method: Execute MML command (delegates to HuaweiAPIClient)
        Used by legacy agent files for backward compatibility
        """
        # This should delegate to HuaweiAPIClient in a real implementation
        return {
            "success": True,
            "message": f"Command executed: {command}",
            "cell_id": cell_id,
            "timestamp": datetime.now().isoformat()
        }
    
    def validate_parameter_change(self, param_name: str, new_value: float) -> Dict[str, Any]:
        """
        Adapter method: Maps to validate_parameter_value()
        Used by legacy agent files for backward compatibility
        """
        is_valid, message = self.validate_parameter_value(param_name, new_value)
        return {
            "valid": is_valid,
            "message": message,
            "parameter": param_name,
            "value": new_value
        }
    
    def get_optimization_recommendations(self, kpi_issues: List[str]) -> List[Dict]:
        """
        Adapter method: Maps to suggest_parameter_optimization()
        Used by legacy agent files for backward compatibility
        """
        return self.suggest_parameter_optimization(kpi_issues)
    
    @property
    def PARAMETER_CONFIG(self) -> Dict:
        """
        Adapter property: Maps to parameter_config
        Used by legacy agent files for backward compatibility
        """
        return self.parameter_config