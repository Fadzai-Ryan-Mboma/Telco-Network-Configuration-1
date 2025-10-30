"""
Liquid Zimbabwe KPI Management System
Handles the 7 core KPIs for network opt            }
        }
        
        self._initialize_database()
    
    @property
    def KPI_CONFIG(self):
        """Provide access to KPI configuration for backward compatibility"""
        return self.kpi_configth user-friendly naming
"""

import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

class LiquidZimbabweKPIManager:
    """Manages the 7 core KPIs for Liquid Zimbabwe network optimization"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # KPI Configuration with user-friendly names and technical details
        self.kpi_config = {
            "network_access_success": {
                "technical_name": "RACH Setup Success Rate(%)",
                "user_friendly_name": "Network Access Success", 
                "description": "How often devices successfully connect to the network",
                "unit": "%",
                "higher_is_better": True,
                "normal_range": (95, 100),
                "critical_threshold": 90
            },
            "download_quality": {
                "technical_name": "DL IBLER[%]",
                "user_friendly_name": "Download Quality",
                "description": "Error rate in data received by devices (lower is better)", 
                "unit": "%",
                "higher_is_better": False,
                "normal_range": (0, 5),
                "critical_threshold": 10
            },
            "upload_quality": {
                "technical_name": "UL IBLER[%]", 
                "user_friendly_name": "Upload Quality",
                "description": "Error rate in data sent by devices (lower is better)",
                "unit": "%",
                "higher_is_better": False,
                "normal_range": (0, 8),
                "critical_threshold": 15
            },
            "control_channel_load": {
                "technical_name": "PDCCH CCE Usage Rate[%]",
                "user_friendly_name": "Control Channel Load",
                "description": "How busy the network's control channels are",
                "unit": "%", 
                "higher_is_better": False,
                "normal_range": (0, 70),
                "critical_threshold": 85
            },
            "feedback_channel_load": {
                "technical_name": "PUCCHUsage Rate[%]",
                "user_friendly_name": "Feedback Channel Load", 
                "description": "Usage of channels that send network feedback",
                "unit": "%",
                "higher_is_better": False,
                "normal_range": (0, 60),
                "critical_threshold": 80
            },
            "download_speed": {
                "technical_name": "DL Cell PDCP Layer Average Throughput(kbit/s)",
                "user_friendly_name": "Download Speed",
                "description": "Average data download speed (higher is better)",
                "unit": "kbit/s",
                "higher_is_better": True,
                "normal_range": (5000, 25000),
                "critical_threshold": 2000
            },
            "upload_speed": {
                "technical_name": "UL Cell PDCP Layer Average Throughput(kbit/s)", 
                "user_friendly_name": "Upload Speed",
                "description": "Average data upload speed (higher is better)",
                "unit": "kbit/s",
                "higher_is_better": True,
                "normal_range": (1000, 8000), 
                "critical_threshold": 500
            }
        }
        
        self._initialize_database()
    
    @property
    def KPI_CONFIG(self):
        """Provide access to KPI configuration for backward compatibility"""
        return self.kpi_config
    
    def _initialize_database(self):
        """Initialize the KPI database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create KPI data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kpi_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    site_name TEXT,
                    cell_id INTEGER,
                    network_access_success REAL,
                    download_quality REAL,
                    upload_quality REAL,
                    control_channel_load REAL,
                    feedback_channel_load REAL,
                    download_speed REAL,
                    upload_speed REAL
                )
            """)
            
            # Create indexes for kpi_data table
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kpi_data_site_timestamp ON kpi_data(site_name, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kpi_data_timestamp ON kpi_data(timestamp)")
            
            # Create KPI alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kpi_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    site_name TEXT,
                    cell_id INTEGER,
                    kpi_name TEXT,
                    current_value REAL,
                    threshold_value REAL,
                    alert_type TEXT,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            conn.commit()
    
    def import_historical_data(self, csv_path: str) -> bool:
        """Import historical data from Bindura CSV file"""
        try:
            df = pd.read_csv(csv_path)
            
            with sqlite3.connect(self.db_path) as conn:
                for _, row in df.iterrows():
                    # Map CSV columns to our KPI structure
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO kpi_data (
                            timestamp, site_name, cell_id,
                            network_access_success, download_quality, upload_quality,
                            control_channel_load, feedback_channel_load, 
                            download_speed, upload_speed
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('Date', datetime.now().strftime('%Y-%m-%d')),
                        row.get('eNodeB Name', 'Unknown'),
                        row.get('LocalCell Id', 0),
                        row.get('RACH Setup Success Rate(%)', 0),
                        row.get('DL IBLER[%]', 0),
                        row.get('UL IBLER[%]', 0), 
                        row.get('PDCCH CCE Usage Rate[%]', 0),
                        row.get('PUCCHUsage Rate[%]', 0),
                        row.get('DL Cell PDCP Layer Average Throughput(kbit/s)', 0),
                        row.get('UL Cell PDCP Layer Average Throughput(kbit/s)', 0)
                    ))
                
                conn.commit()
            
            self.logger.info(f"Successfully imported {len(df)} historical records")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import historical data: {e}")
            return False
    
    def get_historical_kpis(self, site_name: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Get historical KPI data as DataFrame for analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Build query with optional filters
                query = """
                    SELECT 
                        timestamp, site_name, cell_id,
                        network_access_success, download_quality, upload_quality,
                        control_channel_load, feedback_channel_load, 
                        download_speed, upload_speed
                    FROM kpi_data
                """
                
                conditions = []
                params = []
                
                if site_name:
                    conditions.append("site_name = ?")
                    params.append(site_name)
                
                if start_date:
                    conditions.append("timestamp >= ?")
                    params.append(start_date)
                
                if end_date:
                    conditions.append("timestamp <= ?") 
                    params.append(end_date)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY timestamp DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            self.logger.error(f"Failed to get historical KPIs: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error
    
    def get_kpi_summary(self, site_name: Optional[str] = None) -> Dict:
        """Get KPI summary for dashboard"""
        with sqlite3.connect(self.db_path) as conn:
            # Base query
            query = """
                SELECT 
                    AVG(network_access_success) as avg_network_access,
                    AVG(download_quality) as avg_download_quality,
                    AVG(upload_quality) as avg_upload_quality,
                    AVG(control_channel_load) as avg_control_load,
                    AVG(feedback_channel_load) as avg_feedback_load,
                    AVG(download_speed) as avg_download_speed,
                    AVG(upload_speed) as avg_upload_speed,
                    COUNT(DISTINCT site_name) as site_count,
                    COUNT(DISTINCT cell_id) as cell_count
                FROM kpi_data 
                WHERE timestamp >= datetime('now', '-24 hours')
            """
            
            if site_name:
                query += " AND site_name = ?"
                params = (site_name,)
            else:
                params = ()
            
            result = pd.read_sql_query(query, conn, params=params)
            
            if result.empty:
                return {}
            
            row = result.iloc[0]
            
            summary = {}
            kpi_keys = ["network_access_success", "download_quality", "upload_quality", 
                       "control_channel_load", "feedback_channel_load", "download_speed", "upload_speed"]
            
            for i, kpi_key in enumerate(kpi_keys):
                config = self.kpi_config[kpi_key]
                avg_col = f"avg_{kpi_key.replace('_', '_')}" if i < 2 else f"avg_{kpi_key.split('_')[0]}_{kpi_key.split('_')[1]}"
                if i == 0: avg_col = "avg_network_access"
                elif i == 1: avg_col = "avg_download_quality"
                elif i == 2: avg_col = "avg_upload_quality"  
                elif i == 3: avg_col = "avg_control_load"
                elif i == 4: avg_col = "avg_feedback_load"
                elif i == 5: avg_col = "avg_download_speed"
                elif i == 6: avg_col = "avg_upload_speed"
                
                value = row[avg_col] if pd.notna(row[avg_col]) else 0
                
                summary[kpi_key] = {
                    "value": round(value, 2),
                    "user_friendly_name": config["user_friendly_name"],
                    "technical_name": config["technical_name"],
                    "description": config["description"],
                    "unit": config["unit"],
                    "status": self._get_kpi_status(value, config)
                }
            
            summary["meta"] = {
                "site_count": int(row["site_count"]),
                "cell_count": int(row["cell_count"]),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return summary
    
    def _get_kpi_status(self, value: float, config: Dict) -> str:
        """Determine KPI status based on value and configuration"""
        if value == 0:
            return "no_data"
        
        normal_min, normal_max = config["normal_range"]
        critical_threshold = config["critical_threshold"]
        higher_is_better = config["higher_is_better"]
        
        if higher_is_better:
            if value >= normal_min:
                return "good"
            elif value >= critical_threshold:
                return "warning"
            else:
                return "critical"
        else:
            if value <= normal_max:
                return "good"
            elif value <= critical_threshold:
                return "warning" 
            else:
                return "critical"
    
    def get_site_drill_down(self, site_name: str) -> Dict:
        """Get cell-level details for a specific site"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT 
                    cell_id,
                    AVG(network_access_success) as network_access_success,
                    AVG(download_quality) as download_quality,
                    AVG(upload_quality) as upload_quality,
                    AVG(control_channel_load) as control_channel_load,
                    AVG(feedback_channel_load) as feedback_channel_load, 
                    AVG(download_speed) as download_speed,
                    AVG(upload_speed) as upload_speed
                FROM kpi_data 
                WHERE site_name = ? AND timestamp >= datetime('now', '-24 hours')
                GROUP BY cell_id
                ORDER BY cell_id
            """
            
            result = pd.read_sql_query(query, conn, params=(site_name,))
            
            cells = []
            for _, row in result.iterrows():
                cell_data = {"cell_id": int(row["cell_id"])}
                
                for kpi_key, config in self.kpi_config.items():
                    value = row[kpi_key] if pd.notna(row[kpi_key]) else 0
                    cell_data[kpi_key] = {
                        "value": round(value, 2),
                        "status": self._get_kpi_status(value, config)
                    }
                
                cells.append(cell_data)
            
            return {"site_name": site_name, "cells": cells}
    
    def record_real_time_kpi(self, site_name: str, cell_id: int, kpi_values: Dict) -> bool:
        """Record real-time KPI data from live network"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO kpi_data (
                        timestamp, site_name, cell_id,
                        network_access_success, download_quality, upload_quality,
                        control_channel_load, feedback_channel_load,
                        download_speed, upload_speed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(),
                    site_name,
                    cell_id,
                    kpi_values.get('network_access_success', 0),
                    kpi_values.get('download_quality', 0),
                    kpi_values.get('upload_quality', 0),
                    kpi_values.get('control_channel_load', 0),
                    kpi_values.get('feedback_channel_load', 0),
                    kpi_values.get('download_speed', 0),
                    kpi_values.get('upload_speed', 0)
                ))
                conn.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to record real-time KPI: {e}")
            return False
    
    def check_kpi_alerts(self) -> List[Dict]:
        """Check for KPI threshold breaches"""
        alerts = []
        
        with sqlite3.connect(self.db_path) as conn:
            # Get latest KPI values for all sites/cells
            query = """
                SELECT site_name, cell_id, 
                       network_access_success, download_quality, upload_quality,
                       control_channel_load, feedback_channel_load,
                       download_speed, upload_speed
                FROM kpi_data 
                WHERE timestamp >= datetime('now', '-10 minutes')
                ORDER BY timestamp DESC
            """
            
            result = pd.read_sql_query(query, conn)
            
            for _, row in result.iterrows():
                for kpi_key, config in self.kpi_config.items():
                    value = row[kpi_key]
                    if pd.isna(value) or value == 0:
                        continue
                    
                    status = self._get_kpi_status(value, config)
                    
                    if status in ["warning", "critical"]:
                        alerts.append({
                            "site_name": row["site_name"],
                            "cell_id": row["cell_id"], 
                            "kpi_name": config["user_friendly_name"],
                            "technical_name": config["technical_name"],
                            "current_value": value,
                            "status": status,
                            "description": config["description"],
                            "unit": config["unit"]
                        })
        
        return alerts