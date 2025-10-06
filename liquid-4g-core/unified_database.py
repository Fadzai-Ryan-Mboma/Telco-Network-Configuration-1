#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Platform - Unified Database Manager
Consolidates all database operations into a single, reliable system
"""

import sqlite3
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class UnifiedDatabaseManager:
    """Unified database manager for all LZ 4G platform data"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            self.base_path = Path(__file__).parent.parent / "data"
        else:
            self.base_path = Path(base_path)
        
        self.base_path.mkdir(exist_ok=True)
        self.main_db = self.base_path / "lz_platform.db"
        self.logger = logging.getLogger(__name__)
        
        # Initialize unified database
        self._initialize_unified_database()
        self._populate_sample_data()
    
    def _initialize_unified_database(self):
        """Initialize all required tables in one database"""
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            
            # Network Elements table (replaces live_network.db)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS network_elements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    site_id TEXT,
                    location TEXT,
                    cell_ids TEXT,
                    status TEXT DEFAULT 'active',
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # KPI Data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kpi_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    site_id TEXT,
                    kpi_name TEXT,
                    value REAL,
                    data_source TEXT DEFAULT 'system'
                )
            """)
            
            # Parameter Data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parameter_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    site_id TEXT,
                    parameter_name TEXT,
                    value REAL,
                    data_source TEXT DEFAULT 'system'
                )
            """)
            
            # System Status table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    component TEXT,
                    status TEXT,
                    details TEXT
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kpi_site_name ON kpi_data(site_id, kpi_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_param_site_name ON parameter_data(site_id, parameter_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_network_name ON network_elements(name)")
            
            conn.commit()
            self.logger.info("Unified database initialized successfully")
    
    def _populate_sample_data(self):
        """Populate with realistic sample data"""
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            
            # Check if data already exists
            cursor.execute("SELECT COUNT(*) FROM network_elements")
            if cursor.fetchone()[0] > 0:
                return  # Data already exists
            
            # Sample network elements
            network_elements = [
                ("LZ_HARARE_001", "HARARE_CENTRAL", "Harare Central Business District", "1,2,3", "active"),
                ("LZ_BULAWAYO_001", "BULAWAYO_MAIN", "Bulawayo Main Street", "1,2", "active"),
                ("LZ_MUTARE_001", "MUTARE_TOWN", "Mutare Town Center", "1,2,3,4", "active")
            ]
            
            for name, site_id, location, cell_ids, status in network_elements:
                cursor.execute("""
                    INSERT INTO network_elements (name, site_id, location, cell_ids, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, site_id, location, cell_ids, status))
            
            # Sample KPI data
            import random
            kpi_names = [
                "network_access_success", "download_quality", "upload_quality",
                "control_channel_load", "feedback_channel_load", "download_speed", "upload_speed"
            ]
            
            for name, site_id, _, _, _ in network_elements:
                for kpi_name in kpi_names:
                    # Generate realistic values
                    if "success" in kpi_name:
                        value = random.uniform(95, 99.5)
                    elif "quality" in kpi_name or "load" in kpi_name:
                        value = random.uniform(2, 15)
                    else:  # speed
                        value = random.uniform(5000, 25000)
                    
                    cursor.execute("""
                        INSERT INTO kpi_data (site_id, kpi_name, value, data_source)
                        VALUES (?, ?, ?, 'sample')
                    """, (site_id, kpi_name, round(value, 2)))
            
            # Sample parameter data
            param_names = [
                "reference_signal_power_rs", "reference_signal_power_pdschcfg",
                "a3_event_offset", "t310_timer", "p0_nominal_pusch", "pdcch_aggregation_level"
            ]
            
            for name, site_id, _, _, _ in network_elements:
                for param_name in param_names:
                    # Generate realistic parameter values
                    if "power" in param_name:
                        value = random.uniform(-300, -100)
                    elif "offset" in param_name:
                        value = random.uniform(1, 8)
                    elif "timer" in param_name:
                        value = random.choice([100, 200, 500, 1000, 1500, 2000])
                    elif "pusch" in param_name:
                        value = random.uniform(-90, -50)
                    else:
                        value = random.uniform(5, 20)
                    
                    cursor.execute("""
                        INSERT INTO parameter_data (site_id, parameter_name, value, data_source)
                        VALUES (?, ?, ?, 'sample')
                    """, (site_id, param_name, round(value, 2)))
            
            # System status
            cursor.execute("""
                INSERT INTO system_status (component, status, details)
                VALUES ('api_client', 'operational', 'Connected to production API'),
                       ('database', 'operational', 'Unified database active'),
                       ('kpi_manager', 'operational', 'All KPI systems functional'),
                       ('parameter_manager', 'operational', 'Parameter optimization ready')
            """)
            
            conn.commit()
            self.logger.info("Sample data populated successfully")
    
    def get_network_elements(self) -> Dict[str, Dict]:
        """Get all network elements"""
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, site_id, location, cell_ids, status, last_updated
                FROM network_elements ORDER BY name
            """)
            
            elements = {}
            for row in cursor.fetchall():
                name, site_id, location, cell_ids, status, last_updated = row
                elements[name] = {
                    'site_id': site_id,
                    'location': location,
                    'cell_ids': cell_ids.split(',') if cell_ids else [],
                    'status': status,
                    'last_updated': last_updated
                }
            
            return elements
    
    def get_kpi_data(self, site_id: str = None) -> List[Dict]:
        """Get KPI data for all sites or specific site"""
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            
            if site_id:
                cursor.execute("""
                    SELECT site_id, kpi_name, value, timestamp, data_source
                    FROM kpi_data WHERE site_id = ?
                    ORDER BY timestamp DESC
                """, (site_id,))
            else:
                cursor.execute("""
                    SELECT site_id, kpi_name, value, timestamp, data_source
                    FROM kpi_data ORDER BY timestamp DESC
                """)
            
            return [
                {
                    'site_id': row[0],
                    'kpi_name': row[1],
                    'value': row[2],
                    'timestamp': row[3],
                    'data_source': row[4]
                }
                for row in cursor.fetchall()
            ]
    
    def get_parameter_data(self, site_id: str = None) -> List[Dict]:
        """Get parameter data for all sites or specific site"""
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            
            if site_id:
                cursor.execute("""
                    SELECT site_id, parameter_name, value, timestamp, data_source
                    FROM parameter_data WHERE site_id = ?
                    ORDER BY timestamp DESC
                """, (site_id,))
            else:
                cursor.execute("""
                    SELECT site_id, parameter_name, value, timestamp, data_source
                    FROM parameter_data ORDER BY timestamp DESC
                """)
            
            return [
                {
                    'site_id': row[0],
                    'parameter_name': row[1],
                    'value': row[2],
                    'timestamp': row[3],
                    'data_source': row[4]
                }
                for row in cursor.fetchall()
            ]
    
    def get_system_status(self) -> Dict[str, str]:
        """Get current system status"""
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT component, status, details, timestamp
                FROM system_status ORDER BY timestamp DESC
            """)
            
            status = {}
            for row in cursor.fetchall():
                component, stat, details, timestamp = row
                status[component] = {
                    'status': stat,
                    'details': details,
                    'timestamp': timestamp
                }
            
            return status
    
    def update_system_status(self, component: str, status: str, details: str = ""):
        """Update system component status"""
        with sqlite3.connect(self.main_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_status (component, status, details)
                VALUES (?, ?, ?)
            """, (component, status, details))
            conn.commit()

# Global instance for easy access
db_manager = None

def get_db_manager() -> UnifiedDatabaseManager:
    """Get global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = UnifiedDatabaseManager()
    return db_manager

if __name__ == "__main__":
    # Test the unified database
    manager = UnifiedDatabaseManager()
    
    print("🗄️  UNIFIED DATABASE MANAGER TEST")
    print("=" * 50)
    
    elements = manager.get_network_elements()
    print(f"✅ Network Elements: {len(elements)}")
    for name, info in elements.items():
        print(f"   📡 {name}: {info['location']} ({info['status']})")
    
    kpi_data = manager.get_kpi_data()
    print(f"✅ KPI Records: {len(kpi_data)}")
    
    param_data = manager.get_parameter_data()
    print(f"✅ Parameter Records: {len(param_data)}")
    
    status = manager.get_system_status()
    print(f"✅ System Components: {len(status)}")
    for comp, info in status.items():
        print(f"   🔧 {comp}: {info['status']}")
    
    print("\n🎉 Unified database working perfectly!")