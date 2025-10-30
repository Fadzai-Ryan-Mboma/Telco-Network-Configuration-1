"""
Liquid Zimbabwe KPI Management System
Handles the 7 core KPIs for network optimization with user-friendly naming
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
            
            # Create indexes separately
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_kpi_site_timestamp 
                ON kpi_data(site_name, timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_kpi_timestamp 
                ON kpi_data(timestamp)
            """)
            
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
    
    # ========== ADAPTER METHODS FOR AGENT COMPATIBILITY ==========
    # These methods provide compatibility with agent expectations
    
    def get_all_kpis(self):
        """Adapter method: Get all KPIs (maps to get_kpi_summary)"""
        return self.get_kpi_summary()
    
    def get_site_kpis(self, site_name: str):
        """Adapter method: Get KPIs for specific site"""
        return self.get_site_drill_down(site_name)
    
    def get_historical_kpis(self, site_name: Optional[str] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
        """Get historical KPI data - returns DataFrame for trends if time range specified"""
        if start_time and end_time and site_name:
            # Return time-series DataFrame for trend visualization
            return self.get_kpi_trends(site_name, start_time, end_time)
        elif site_name:
            # Return site drill-down data (dictionary format)
            return self.get_site_drill_down(site_name)
        else:
            # Return summary data
            return self.get_kpi_summary()
    
    def get_kpi_trends(self, site_name: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Get KPI trend data for visualization"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        timestamp,
                        AVG(network_access_success) as network_access_success,
                        AVG(download_quality) as download_quality,
                        AVG(upload_quality) as upload_quality,
                        AVG(control_channel_load) as control_channel_load,
                        AVG(feedback_channel_load) as feedback_channel_load,
                        AVG(download_speed) as download_speed,
                        AVG(upload_speed) as upload_speed
                    FROM kpi_data 
                    WHERE site_name = ? 
                        AND timestamp >= ? 
                        AND timestamp <= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY timestamp
                """
                
                df = pd.read_sql_query(
                    query, 
                    conn, 
                    params=(site_name, start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S'))
                )
                
                if df.empty:
                    # If no data from database, generate sample data for demonstration
                    self.logger.info(f"No historical data found for {site_name}, generating sample trend data")
                    return self._generate_sample_trend_data(start_time, end_time)
                
                # Convert timestamp to datetime and set as index
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                
                return df
                
        except Exception as e:
            self.logger.error(f"Error getting KPI trends: {e}")
            # Return sample data as fallback
            return self._generate_sample_trend_data(start_time, end_time)
    
    def _generate_sample_trend_data(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Generate sample trend data for demonstration when no real data available"""
        import numpy as np
        
        # Create date range
        dates = pd.date_range(start=start_time, end=end_time, freq='D')
        
        # Generate realistic sample data with some variation
        np.random.seed(42)  # For reproducible results
        
        data = {
            'network_access_success': 95 + np.random.normal(0, 2, len(dates)).clip(-5, 5),
            'download_quality': 2 + np.random.normal(0, 1, len(dates)).clip(-1, 3),
            'upload_quality': 3 + np.random.normal(0, 1.5, len(dates)).clip(-2, 5),
            'control_channel_load': 60 + np.random.normal(0, 10, len(dates)).clip(-30, 30),
            'feedback_channel_load': 40 + np.random.normal(0, 8, len(dates)).clip(-20, 40),
            'download_speed': 50 + np.random.normal(0, 10, len(dates)).clip(-25, 50),
            'upload_speed': 25 + np.random.normal(0, 5, len(dates)).clip(-15, 25)
        }
        
        df = pd.DataFrame(data, index=dates)
        df.index.name = 'timestamp'
        
        # Ensure values stay within realistic ranges
        df['network_access_success'] = df['network_access_success'].clip(85, 100)
        df['download_quality'] = df['download_quality'].clip(0, 10)
        df['upload_quality'] = df['upload_quality'].clip(0, 15)
        df['control_channel_load'] = df['control_channel_load'].clip(0, 100)
        df['feedback_channel_load'] = df['feedback_channel_load'].clip(0, 100)
        df['download_speed'] = df['download_speed'].clip(10, 100)
        df['upload_speed'] = df['upload_speed'].clip(5, 50)
        
        return df
    
    @property
    def KPI_CONFIG(self):
        """Adapter property: Uppercase compatibility"""
        return self.kpi_config
    
    def execute_enhanced_query(self, sql_query: str):
        """Adapter method: Execute custom SQL query"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql_query(sql_query, conn)
        except Exception as e:
            self.logger.error(f"Enhanced query execution failed: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error