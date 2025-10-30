#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Demo - Database and Data Setup
Initializes demo database with realistic network data for comprehensive demonstration
"""

import sqlite3
import json
import random
import pandas as pd
from datetime import datetime, timedelta
import os

class DemoDataGenerator:
    """Generate comprehensive demo data for Liquid Zimbabwe network demonstration"""
    
    def __init__(self):
        self.db_path = "data/demo_database.db"
        self.data_dir = "data"
        
        # Bindura network sites (real locations for authenticity)
        self.bindura_sites = [
            {
                "site_id": "BIND_001",
                "site_name": "Bindura Central",
                "location": {"lat": -17.3015, "lng": 31.3269},
                "technology": "4G",
                "cells": 3,
                "status": "active",
                "coverage_area": "urban",
                "capacity_mbps": 150
            },
            {
                "site_id": "BIND_002", 
                "site_name": "Bindura North",
                "location": {"lat": -17.2890, "lng": 31.3156},
                "technology": "4G",
                "cells": 2,
                "status": "active",
                "coverage_area": "suburban",
                "capacity_mbps": 100
            },
            {
                "site_id": "BIND_003",
                "site_name": "Bindura South Industrial",
                "location": {"lat": -17.3142, "lng": 31.3401},
                "technology": "4G", 
                "cells": 3,
                "status": "active",
                "coverage_area": "industrial",
                "capacity_mbps": 200
            },
            {
                "site_id": "BIND_004",
                "site_name": "Bindura East Residential",
                "location": {"lat": -17.3089, "lng": 31.3445},
                "technology": "4G",
                "cells": 2,
                "status": "active", 
                "coverage_area": "residential",
                "capacity_mbps": 120
            },
            {
                "site_id": "BIND_005",
                "site_name": "Bindura West Rural",
                "location": {"lat": -17.3203, "lng": 31.2987},
                "technology": "4G",
                "cells": 1,
                "status": "active",
                "coverage_area": "rural",
                "capacity_mbps": 75
            }
        ]
        
        # KPI definitions with realistic ranges
        self.kpi_definitions = {
            "rach_setup_success_rate": {"min": 85, "max": 99, "target": 95, "unit": "%"},
            "rrc_connection_success_rate": {"min": 90, "max": 99.5, "target": 98, "unit": "%"},
            "erab_setup_success_rate": {"min": 88, "max": 99, "target": 97, "unit": "%"},
            "handover_success_rate": {"min": 85, "max": 98, "target": 95, "unit": "%"},
            "average_dl_throughput": {"min": 15, "max": 45, "target": 25, "unit": "Mbps"},
            "average_ul_throughput": {"min": 3, "max": 15, "target": 5, "unit": "Mbps"},
            "rsrp_coverage": {"min": -110, "max": -70, "target": -100, "unit": "dBm"},
            "rsrq_quality": {"min": -15, "max": -5, "target": -10, "unit": "dB"},
            "call_drop_rate": {"min": 0.5, "max": 5, "target": 2, "unit": "%"},
            "session_setup_time": {"min": 1.5, "max": 8, "target": 3, "unit": "s"}
        }
        
        # Network parameters with MML commands
        self.network_parameters = {
            "cell_individual_offset": {
                "current_value": 0,
                "min_value": -10,
                "max_value": 10,
                "unit": "dB",
                "mml_command": "MOD CELLINDIVIDUALOFFSET: LOCALCELLID=1, INDIVIDUALOFFSET={value};",
                "description": "Individual cell offset for handover optimization"
            },
            "reference_signal_power": {
                "current_value": 15,
                "min_value": 10,
                "max_value": 23,
                "unit": "dBm", 
                "mml_command": "MOD PDSCHCFG: LOCALCELLID=1, REFERENCEPOWER={value};",
                "description": "Reference signal power for coverage optimization"
            },
            "a3_event_offset": {
                "current_value": 3,
                "min_value": 0,
                "max_value": 6,
                "unit": "dB",
                "mml_command": "MOD UECOOPERATIONPARA: LOCALCELLID=1, A3OFFSET={value};",
                "description": "A3 event offset for mobility optimization"
            },
            "t310_timer": {
                "current_value": 2000,
                "min_value": 1000,
                "max_value": 6000,
                "unit": "ms",
                "mml_command": "MOD UETIMERCONST: LOCALCELLID=1, T310={value};",
                "description": "T310 timer for connection stability"
            },
            "p0_nominal_pusch": {
                "current_value": -70,
                "min_value": -126,
                "max_value": 24,
                "unit": "dBm",
                "mml_command": "MOD CELLULPCCOMM: LOCALCELLID=1, P0NOMINALPUSCH={value};",
                "description": "P0 nominal PUSCH power control"
            }
        }

    def setup_directories(self):
        """Create necessary directories"""
        os.makedirs(self.data_dir, exist_ok=True)
        print("✅ Created data directories")

    def create_demo_database(self):
        """Create SQLite database with all required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Sites table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sites (
                    site_id TEXT PRIMARY KEY,
                    site_name TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    technology TEXT,
                    cells INTEGER,
                    status TEXT,
                    coverage_area TEXT,
                    capacity_mbps INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # KPI data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kpi_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id TEXT,
                    kpi_name TEXT,
                    kpi_value REAL,
                    unit TEXT,
                    timestamp TIMESTAMP,
                    FOREIGN KEY (site_id) REFERENCES sites (site_id)
                )
            """)
            
            # Network parameters table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS network_parameters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id TEXT,
                    parameter_name TEXT,
                    current_value REAL,
                    min_value REAL,
                    max_value REAL,
                    unit TEXT,
                    mml_command TEXT,
                    description TEXT,
                    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (site_id) REFERENCES sites (site_id)
                )
            """)
            
            # Agent operations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT UNIQUE,
                    operation_type TEXT,
                    user_query TEXT,
                    target_sites TEXT,
                    stage_results TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            # Optimization history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimization_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT,
                    site_id TEXT,
                    parameter_name TEXT,
                    old_value REAL,
                    new_value REAL,
                    impact_prediction TEXT,
                    applied BOOLEAN DEFAULT FALSE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (operation_id) REFERENCES agent_operations (operation_id),
                    FOREIGN KEY (site_id) REFERENCES sites (site_id)
                )
            """)
            
            # Audit logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT,
                    agent_name TEXT,
                    action TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (operation_id) REFERENCES agent_operations (operation_id)
                )
            """)
            
            conn.commit()
            conn.close()
            print("✅ Created demo database with all tables")
            
        except Exception as e:
            print(f"❌ Database creation failed: {e}")

    def populate_sites_data(self):
        """Populate sites table with Bindura network data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for site in self.bindura_sites:
                cursor.execute("""
                    INSERT OR REPLACE INTO sites 
                    (site_id, site_name, latitude, longitude, technology, cells, status, coverage_area, capacity_mbps)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    site["site_id"],
                    site["site_name"], 
                    site["location"]["lat"],
                    site["location"]["lng"],
                    site["technology"],
                    site["cells"],
                    site["status"],
                    site["coverage_area"],
                    site["capacity_mbps"]
                ))
            
            conn.commit()
            conn.close()
            print(f"✅ Populated {len(self.bindura_sites)} Bindura network sites")
            
        except Exception as e:
            print(f"❌ Sites data population failed: {e}")

    def generate_historical_kpi_data(self, days=30):
        """Generate realistic historical KPI data for the last N days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=days)
            total_records = 0
            
            for site in self.bindura_sites:
                site_id = site["site_id"]
                coverage_area = site["coverage_area"]
                
                # Generate data for each day, every hour
                for day in range(days):
                    current_date = start_date + timedelta(days=day)
                    
                    for hour in range(24):
                        timestamp = current_date + timedelta(hours=hour)
                        
                        # Generate realistic KPI values based on site characteristics
                        for kpi_name, kpi_config in self.kpi_definitions.items():
                            base_value = self._get_base_kpi_value(kpi_name, coverage_area, hour)
                            
                            # Add realistic variation and occasional anomalies
                            variation = random.uniform(-0.1, 0.1) * base_value
                            
                            # Inject occasional anomalies (5% chance)
                            if random.random() < 0.05:
                                anomaly_factor = random.uniform(0.7, 1.3)
                                base_value *= anomaly_factor
                            
                            final_value = max(kpi_config["min"], 
                                            min(kpi_config["max"], base_value + variation))
                            
                            cursor.execute("""
                                INSERT INTO kpi_data (site_id, kpi_name, kpi_value, unit, timestamp)
                                VALUES (?, ?, ?, ?, ?)
                            """, (site_id, kpi_name, final_value, kpi_config["unit"], timestamp))
                            
                            total_records += 1
            
            conn.commit()
            conn.close()
            print(f"✅ Generated {total_records} historical KPI records")
            
        except Exception as e:
            print(f"❌ KPI data generation failed: {e}")

    def _get_base_kpi_value(self, kpi_name, coverage_area, hour):
        """Get base KPI value adjusted for coverage area and time of day"""
        kpi_config = self.kpi_definitions[kpi_name]
        base = kpi_config["target"]
        
        # Coverage area adjustments
        area_multipliers = {
            "urban": {"good": 1.05, "bad": 0.95},
            "suburban": {"good": 1.02, "bad": 0.98}, 
            "industrial": {"good": 1.03, "bad": 0.97},
            "residential": {"good": 1.04, "bad": 0.96},
            "rural": {"good": 0.95, "bad": 0.85}
        }
        
        # Time of day adjustments (traffic patterns)
        traffic_hours = [7, 8, 9, 17, 18, 19, 20, 21]  # Peak hours
        
        multiplier = area_multipliers[coverage_area]["good"]
        if hour in traffic_hours:
            multiplier *= 0.98  # Slight degradation during peak hours
        
        return base * multiplier

    def populate_network_parameters(self):
        """Populate network parameters for all sites"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for site in self.bindura_sites:
                site_id = site["site_id"]
                
                for param_name, param_config in self.network_parameters.items():
                    # Add slight variation per site
                    variation = random.uniform(-0.1, 0.1)
                    current_value = param_config["current_value"] * (1 + variation)
                    
                    # Ensure within bounds
                    current_value = max(param_config["min_value"],
                                      min(param_config["max_value"], current_value))
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO network_parameters
                        (site_id, parameter_name, current_value, min_value, max_value, 
                         unit, mml_command, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        site_id,
                        param_name,
                        current_value,
                        param_config["min_value"],
                        param_config["max_value"],
                        param_config["unit"],
                        param_config["mml_command"],
                        param_config["description"]
                    ))
            
            conn.commit()
            conn.close()
            print(f"✅ Populated network parameters for all sites")
            
        except Exception as e:
            print(f"❌ Network parameters population failed: {e}")

    def create_json_data_files(self):
        """Create JSON data files for easy access"""
        try:
            # Sites data
            with open(f"{self.data_dir}/bindura_sites.json", "w") as f:
                json.dump(self.bindura_sites, f, indent=2)
            
            # KPI definitions
            with open(f"{self.data_dir}/kpi_definitions.json", "w") as f:
                json.dump(self.kpi_definitions, f, indent=2)
            
            # Network parameters
            with open(f"{self.data_dir}/network_parameters.json", "w") as f:
                json.dump(self.network_parameters, f, indent=2)
            
            print("✅ Created JSON data files")
            
        except Exception as e:
            print(f"❌ JSON file creation failed: {e}")

    def create_sample_operations(self):
        """Create sample agent operations for demonstration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            sample_operations = [
                {
                    "operation_id": "LZ_OPT_20251021_001",
                    "operation_type": "performance_optimization",
                    "user_query": "Optimize RACH performance for Bindura Central site",
                    "target_sites": "BIND_001",
                    "status": "completed"
                },
                {
                    "operation_id": "LZ_OPT_20251021_002", 
                    "operation_type": "coverage_analysis",
                    "user_query": "Analyze coverage quality in rural areas",
                    "target_sites": "BIND_005",
                    "status": "completed"
                },
                {
                    "operation_id": "LZ_OPT_20251021_003",
                    "operation_type": "anomaly_detection",
                    "user_query": "Check for performance anomalies across all sites",
                    "target_sites": "ALL",
                    "status": "in_progress"
                }
            ]
            
            for operation in sample_operations:
                cursor.execute("""
                    INSERT OR REPLACE INTO agent_operations
                    (operation_id, operation_type, user_query, target_sites, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    operation["operation_id"],
                    operation["operation_type"], 
                    operation["user_query"],
                    operation["target_sites"],
                    operation["status"]
                ))
            
            conn.commit()
            conn.close()
            print("✅ Created sample agent operations")
            
        except Exception as e:
            print(f"❌ Sample operations creation failed: {e}")

def main():
    """Main setup function"""
    print("🚀 Liquid Zimbabwe 4G Demo - Database Setup")
    print("=" * 50)
    
    generator = DemoDataGenerator()
    
    # Setup process
    generator.setup_directories()
    generator.create_demo_database()
    generator.populate_sites_data()
    generator.generate_historical_kpi_data(days=30)
    generator.populate_network_parameters()
    generator.create_json_data_files()
    generator.create_sample_operations()
    
    print("\n" + "=" * 50)
    print("✅ Demo database setup completed successfully!")
    print("\nGenerated Data Summary:")
    print("- 5 Bindura network sites")
    print("- 30 days of historical KPI data")
    print("- Network parameters for all sites")
    print("- Sample agent operations")
    print("- JSON reference files")
    print("\n🎯 Ready to launch demo application!")

if __name__ == "__main__":
    main()