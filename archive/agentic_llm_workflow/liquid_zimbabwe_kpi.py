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
                "normal_range": (5, 15),
                "critical_threshold": 20
            },
            "upload_quality": {
                "technical_name": "UL IBLER[%]",
                "user_friendly_name": "Upload Quality", 
                "description": "Error rate in data sent by devices (lower is better)",
                "unit": "%",
                "higher_is_better": False,
                "normal_range": (2, 10),
                "critical_threshold": 15
            },
            "control_channel_load": {
                "technical_name": "PDCCH CCE Usage Rate[%]",
                "user_friendly_name": "Control Channel Load",
                "description": "How busy the network's control channels are",
                "unit": "%",
                "higher_is_better": False,
                "normal_range": (20, 70),
                "critical_threshold": 85
            },
            "feedback_channel_load": {
                "technical_name": "PUCCHUsage Rate[%]",
                "user_friendly_name": "Feedback Channel Load",
                "description": "Usage of channels that send network feedback",
                "unit": "%",
                "higher_is_better": False,
                "normal_range": (1, 10),
                "critical_threshold": 15
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
                    alert_level TEXT,
                    message TEXT
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
            """
            
            params = []
            if site_name:
                query += " WHERE site_name = ?"
                params.append(site_name)
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            # Build summary response
            summary = {}
            
            # Individual KPI summaries
            for kpi_key, config in self.kpi_config.items():
                avg_value = result[list(self.kpi_config.keys()).index(kpi_key)] if result[0] is not None else 0
                status = self._get_kpi_status(avg_value, config)
                
                summary[kpi_key] = {
                    "value": avg_value,
                    "user_friendly_name": config["user_friendly_name"],
                    "technical_name": config["technical_name"],
                    "description": config["description"],
                    "unit": config["unit"],
                    "status": status
                }
            
            # Meta information
            summary["meta"] = {
                "site_count": result[-2] if result[-2] is not None else 0,
                "cell_count": result[-1] if result[-1] is not None else 0,
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return summary
    
    def _get_kpi_status(self, value: float, config: Dict) -> str:
        """Determine KPI status based on thresholds"""
        if value == 0:
            return "no_data"
            
        critical_threshold = config.get("critical_threshold", 0)
        normal_range = config.get("normal_range", (0, 100))
        higher_is_better = config.get("higher_is_better", True)
        
        if higher_is_better:
            if value <= critical_threshold:
                return "critical"
            elif value < normal_range[0]:
                return "warning"
            else:
                return "good"
        else:  # Lower is better
            if value >= critical_threshold:
                return "critical"
            elif value > normal_range[1]:
                return "warning"
            else:
                return "good"
    
    def get_site_drill_down(self, site_name: str) -> Dict:
        """Get detailed KPI breakdown for a specific site"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT 
                    cell_id,
                    AVG(network_access_success) as avg_network_access,
                    AVG(download_quality) as avg_download_quality,
                    AVG(upload_quality) as avg_upload_quality,
                    AVG(control_channel_load) as avg_control_load,
                    AVG(feedback_channel_load) as avg_feedback_load,
                    AVG(download_speed) as avg_download_speed,
                    AVG(upload_speed) as avg_upload_speed,
                    COUNT(*) as data_points
                FROM kpi_data
                WHERE site_name = ?
                GROUP BY cell_id
                ORDER BY cell_id
            """
            
            cursor = conn.cursor()
            cursor.execute(query, (site_name,))
            results = cursor.fetchall()
            
            site_data = {
                "site_name": site_name,
                "cells": {},
                "summary": {}
            }
            
            # Process each cell
            for row in results:
                cell_id = row[0]
                cell_data = {}
                
                for i, kpi_key in enumerate(self.kpi_config.keys()):
                    config = self.kpi_config[kpi_key]
                    value = row[i + 1]  # Skip cell_id
                    status = self._get_kpi_status(value, config)
                    
                    cell_data[kpi_key] = {
                        "value": value,
                        "status": status,
                        "user_friendly_name": config["user_friendly_name"],
                        "unit": config["unit"]
                    }
                
                cell_data["data_points"] = row[-1]
                site_data["cells"][f"Cell_{cell_id}"] = cell_data
            
            return site_data
    
    def record_real_time_kpi(self, site_name: str, cell_id: int, kpi_values: Dict) -> bool:
        """Record real-time KPI measurements"""
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
            self.logger.error(f"Failed to record KPI: {e}")
            return False
    
    def check_kpi_alerts(self) -> List[Dict]:
        """Check for KPI threshold violations and generate alerts"""
        alerts = []
        
        # Get recent data (last hour)
        recent_data = self.get_historical_kpis()
        if recent_data.empty:
            return alerts
        
        # Check each site's recent performance
        for site in recent_data['site_name'].unique():
            site_data = recent_data[recent_data['site_name'] == site]
            
            for kpi_key, config in self.kpi_config.items():
                if kpi_key in site_data.columns:
                    avg_value = site_data[kpi_key].mean()
                    status = self._get_kpi_status(avg_value, config)
                    
                    if status in ['critical', 'warning']:
                        alerts.append({
                            'site_name': site,
                            'kpi_name': config['user_friendly_name'],
                            'kpi_key': kpi_key,
                            'current_value': avg_value,
                            'status': status,
                            'threshold': config.get('critical_threshold', 0),
                            'timestamp': datetime.now().isoformat()
                        })
        
        return alerts
    
    # ========================================
    # ADAPTER METHODS FOR LEGACY AGENT COMPATIBILITY
    # ========================================
    
    def get_all_kpis(self) -> Dict:
        """
        Adapter method: Maps to get_kpi_summary()
        Used by legacy agent files for backward compatibility
        """
        return self.get_kpi_summary()
    
    def get_site_kpis(self, site_id: str) -> Dict:
        """
        Adapter method: Maps to get_site_drill_down()
        Used by legacy agent files for backward compatibility
        """
        return self.get_site_drill_down(site_id)
    
    def execute_enhanced_query(self, query: str, params: tuple = ()) -> pd.DataFrame:
        """
        Adapter method: Custom SQL query wrapper
        Used by legacy agent files for backward compatibility
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            self.logger.error(f"Enhanced query failed: {e}")
            return pd.DataFrame()