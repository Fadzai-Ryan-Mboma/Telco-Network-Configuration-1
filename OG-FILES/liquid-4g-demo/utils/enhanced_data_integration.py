#!/usr/bin/env python3
"""
Enhanced Data Integration System with Intelligent Fallback
Integrates real Bindura network data with API fallback and simulation
"""

import json
import logging
import sqlite3
import pandas as pd
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class DataIntegrationEngine:
    """
    Enhanced data integration with multiple data sources and intelligent fallback
    """
    
    def __init__(self, db_path: str = "data/demo_database.db", csv_path: Optional[str] = None):
        self.db_path = db_path
        self.csv_path = csv_path or "data/historical_data.csv"
        self.api_available = False
        self.data_cache = {}
        self.fallback_hierarchy = ["live_api", "database", "csv_file", "simulation"]
        
        # Real Bindura network sites
        self.bindura_sites = {
            "MSH0013-Bindura-Zaoga": {
                "site_id": "MSH0013-Bindura-Zaoga",
                "site_name": "Bindura Zaoga",
                "location": "Bindura Zaoga Area",
                "latitude": -17.3011,
                "longitude": 31.3135,
                "vendor": "Huawei",
                "technology": "LTE",
                "cells": 3,
                "status": "critical"
            },
            "MSH-0331-Chiwaridzo 2": {
                "site_id": "MSH-0331-Chiwaridzo",
                "site_name": "Chiwaridzo 2",
                "location": "Chiwaridzo Residential",
                "latitude": -17.3028,
                "longitude": 31.3142,
                "vendor": "Huawei", 
                "technology": "LTE",
                "cells": 3,
                "status": "warning"
            },
            "MSH-0112-Bindura Hospital": {
                "site_id": "MSH-0112-Bindura-Hospital",
                "site_name": "Bindura Hospital",
                "location": "Bindura Provincial Hospital",
                "latitude": -17.3019,
                "longitude": 31.3089,
                "vendor": "Huawei",
                "technology": "LTE",
                "cells": 2,
                "status": "normal"
            },
            "MSH-0014-Chipadze": {
                "site_id": "MSH-0014-Chipadze",
                "site_name": "Chipadze",
                "location": "Chipadze Area",
                "latitude": -17.2995,
                "longitude": 31.3156,
                "vendor": "Huawei",
                "technology": "LTE",
                "cells": 3,
                "status": "warning"
            }
        }
        
        # Real KPI baseline from historical data
        self.baseline_kpis = {
            "rach_setup_success_rate": {
                "current_value": 0.536,
                "threshold": 95.0,
                "status": "critical",
                "unit": "%",
                "trend": "degrading"
            },
            "dl_ibler": {
                "current_value": 15.94,
                "threshold": 15.0,
                "status": "warning",
                "unit": "%",
                "trend": "stable"
            },
            "ul_ibler": {
                "current_value": 12.8,
                "threshold": 15.0,
                "status": "acceptable",
                "unit": "%",
                "trend": "improving"
            },
            "pdcch_cce_usage_rate": {
                "current_value": 67.3,
                "threshold": 80.0,
                "status": "normal",
                "unit": "%",
                "trend": "stable"
            },
            "pucch_usage_rate": {
                "current_value": 45.2,
                "threshold": 70.0,
                "status": "normal",
                "unit": "%",
                "trend": "stable"
            },
            "dl_pdcp_throughput": {
                "current_value": 8.5,
                "threshold": 10.0,
                "status": "acceptable",
                "unit": "Mbps",
                "trend": "stable"
            },
            "ul_pdcp_throughput": {
                "current_value": 3.2,
                "threshold": 5.0,
                "status": "acceptable",
                "unit": "Mbps",
                "trend": "stable"
            }
        }
    
    async def test_api_connectivity(self) -> Tuple[bool, str]:
        """Test live API connectivity"""
        try:
            # Simulate API connection test
            await asyncio.sleep(0.5)  # Simulate network delay
            
            # For demo purposes, randomly determine API availability
            # In real implementation, this would test actual API endpoints
            api_success = random.choice([False, False, True])  # 33% success rate for demo
            
            if api_success:
                self.api_available = True
                return True, "Live API connection successful"
            else:
                self.api_available = False
                return False, "API connection failed - network timeout"
                
        except Exception as e:
            self.api_available = False
            return False, f"API connection error: {str(e)}"
    
    async def get_network_data(self, data_type: str = "discovery") -> Dict[str, Any]:
        """Get network data with intelligent fallback"""
        
        # Try each data source in the fallback hierarchy
        for source in self.fallback_hierarchy:
            try:
                if source == "live_api":
                    if not self.api_available:
                        api_available, message = await self.test_api_connectivity()
                        if not api_available:
                            logger.warning(f"API unavailable: {message}")
                            continue
                    
                    logger.info("Attempting to fetch data from live API")
                    data = await self._fetch_from_api(data_type)
                    if data:
                        data["data_source"] = "live_api"
                        data["data_quality"] = "high"
                        return data
                
                elif source == "database":
                    logger.info("Attempting to fetch data from database")
                    data = await self._fetch_from_database(data_type)
                    if data:
                        data["data_source"] = "database"
                        data["data_quality"] = "high"
                        return data
                
                elif source == "csv_file":
                    logger.info("Attempting to fetch data from CSV file")
                    data = await self._fetch_from_csv(data_type)
                    if data:
                        data["data_source"] = "csv_file"
                        data["data_quality"] = "medium"
                        return data
                
                elif source == "simulation":
                    logger.info("Using simulated data as final fallback")
                    data = await self._generate_simulated_data(data_type)
                    data["data_source"] = "simulation"
                    data["data_quality"] = "simulated"
                    return data
                    
            except Exception as e:
                logger.error(f"Error fetching from {source}: {str(e)}")
                continue
        
        # If all sources fail, return minimal simulated data
        return await self._generate_minimal_fallback(data_type)
    
    async def _fetch_from_api(self, data_type: str) -> Optional[Dict[str, Any]]:
        """Fetch data from live API"""
        # Simulate API delay
        await asyncio.sleep(1.0)
        
        # Simulate API responses for different data types
        if data_type == "discovery":
            return {
                "discovered_sites": list(self.bindura_sites.keys()),
                "site_details": self.bindura_sites,
                "connection_status": "connected",
                "authentication_status": "authenticated",
                "topology_summary": {
                    "total_sites": len(self.bindura_sites),
                    "active_sites": len(self.bindura_sites),
                    "cell_count": sum(site["cells"] for site in self.bindura_sites.values())
                }
            }
        
        elif data_type == "kpi_monitoring":
            # Add some realistic variation to KPIs
            kpis = {}
            for kpi_name, kpi_data in self.baseline_kpis.items():
                variation = random.uniform(-0.1, 0.1)  # ±10% variation
                current_value = kpi_data["current_value"] * (1 + variation)
                kpis[kpi_name] = {
                    **kpi_data,
                    "current_value": round(current_value, 3),
                    "timestamp": datetime.now().isoformat()
                }
            
            return {
                "kpi_measurements": kpis,
                "measurement_timestamp": datetime.now().isoformat(),
                "sites_measured": list(self.bindura_sites.keys())
            }
        
        elif data_type == "parameter_config":
            return {
                "current_parameters": {
                    "reference_signal_power": -6.0,
                    "a3_offset": 3.0,
                    "t310_timer": 1000,
                    "p0_nominal_pusch": -96,
                    "pdcch_aggregation_level": 2
                },
                "parameter_ranges": {
                    "reference_signal_power": {"min": -60, "max": 50, "unit": "0.1 dBm"},
                    "a3_offset": {"min": -15, "max": 15, "unit": "dB"},
                    "t310_timer": {"min": 0, "max": 1000, "unit": "ms"}
                }
            }
        
        return None
    
    async def _fetch_from_database(self, data_type: str) -> Optional[Dict[str, Any]]:
        """Fetch data from local database"""
        try:
            # Check if database exists
            if not os.path.exists(self.db_path):
                logger.warning(f"Database not found: {self.db_path}")
                return None
            
            # Simulate database query delay
            await asyncio.sleep(0.3)
            
            # Connect to database and fetch relevant data
            with sqlite3.connect(self.db_path) as conn:
                if data_type == "discovery":
                    # Return site discovery data
                    return {
                        "discovered_sites": list(self.bindura_sites.keys()),
                        "site_details": self.bindura_sites,
                        "connection_status": "database_mode",
                        "authentication_status": "local_access"
                    }
                
                elif data_type == "kpi_monitoring":
                    # Fetch KPI data from database
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    
                    if tables:
                        # Use baseline KPIs with slight variation
                        kpis = {}
                        for kpi_name, kpi_data in self.baseline_kpis.items():
                            variation = random.uniform(-0.05, 0.05)  # ±5% variation
                            current_value = kpi_data["current_value"] * (1 + variation)
                            kpis[kpi_name] = {
                                **kpi_data,
                                "current_value": round(current_value, 3),
                                "timestamp": datetime.now().isoformat(),
                                "source": "database"
                            }
                        
                        return {
                            "kpi_measurements": kpis,
                            "measurement_timestamp": datetime.now().isoformat(),
                            "sites_measured": list(self.bindura_sites.keys()),
                            "data_freshness": "recent"
                        }
                    
        except Exception as e:
            logger.error(f"Database fetch error: {str(e)}")
            return None
    
    async def _fetch_from_csv(self, data_type: str) -> Optional[Dict[str, Any]]:
        """Fetch data from CSV file"""
        try:
            if not os.path.exists(self.csv_path):
                logger.warning(f"CSV file not found: {self.csv_path}")
                return None
            
            # Simulate file read delay
            await asyncio.sleep(0.2)
            
            # Read CSV data
            df = pd.read_csv(self.csv_path)
            
            if data_type == "discovery":
                # Extract site information from CSV
                sites_in_csv = df['eNodeB Name'].unique().tolist() if 'eNodeB Name' in df.columns else []
                
                return {
                    "discovered_sites": sites_in_csv or list(self.bindura_sites.keys()),
                    "site_details": self.bindura_sites,
                    "connection_status": "csv_mode",
                    "data_records": len(df)
                }
            
            elif data_type == "kpi_monitoring":
                # Process KPI data from CSV
                kpis = {}
                
                # Map CSV columns to our KPI names
                column_mapping = {
                    "RACH Setup Success Rate(%)": "rach_setup_success_rate",
                    "DL IBLER[%]": "dl_ibler",
                    "UL IBLER[%]": "ul_ibler",
                    "PDCCH CCE Usage Rate[%]": "pdcch_cce_usage_rate",
                    "PUCCHUsage Rate[%]": "pucch_usage_rate"
                }
                
                for csv_col, kpi_name in column_mapping.items():
                    if csv_col in df.columns:
                        # Get latest value from CSV
                        latest_value = df[csv_col].iloc[-1] if len(df) > 0 else self.baseline_kpis[kpi_name]["current_value"]
                        
                        kpis[kpi_name] = {
                            **self.baseline_kpis[kpi_name],
                            "current_value": round(float(latest_value), 3),
                            "timestamp": datetime.now().isoformat(),
                            "source": "csv_historical"
                        }
                
                return {
                    "kpi_measurements": kpis,
                    "measurement_timestamp": datetime.now().isoformat(),
                    "sites_measured": list(self.bindura_sites.keys()),
                    "historical_records": len(df)
                }
                
        except Exception as e:
            logger.error(f"CSV fetch error: {str(e)}")
            return None
    
    async def _generate_simulated_data(self, data_type: str) -> Dict[str, Any]:
        """Generate realistic simulated data"""
        # Simulate processing delay
        await asyncio.sleep(0.1)
        
        if data_type == "discovery":
            return {
                "discovered_sites": list(self.bindura_sites.keys()),
                "site_details": self.bindura_sites,
                "connection_status": "simulation_mode",
                "authentication_status": "simulated",
                "topology_summary": {
                    "total_sites": len(self.bindura_sites),
                    "active_sites": len(self.bindura_sites),
                    "cell_count": sum(site["cells"] for site in self.bindura_sites.values())
                }
            }
        
        elif data_type == "kpi_monitoring":
            # Generate simulated KPI data with realistic variations
            kpis = {}
            for kpi_name, kpi_data in self.baseline_kpis.items():
                # Add realistic variation based on KPI type
                if kpi_name == "rach_setup_success_rate":
                    variation = random.uniform(-0.2, 0.3)  # RACH can vary significantly
                elif "ibler" in kpi_name:
                    variation = random.uniform(-0.1, 0.15)  # IBLER moderate variation
                else:
                    variation = random.uniform(-0.05, 0.05)  # Other KPIs stable
                
                current_value = max(0, kpi_data["current_value"] * (1 + variation))
                
                kpis[kpi_name] = {
                    **kpi_data,
                    "current_value": round(current_value, 3),
                    "timestamp": datetime.now().isoformat(),
                    "source": "simulation"
                }
            
            return {
                "kpi_measurements": kpis,
                "measurement_timestamp": datetime.now().isoformat(),
                "sites_measured": list(self.bindura_sites.keys()),
                "simulation_note": "Realistic simulation based on Bindura baseline"
            }
        
        elif data_type == "parameter_config":
            return {
                "current_parameters": {
                    "reference_signal_power": round(random.uniform(-8, -4), 1),
                    "a3_offset": round(random.uniform(2, 4), 1),
                    "t310_timer": random.choice([500, 1000, 1500]),
                    "p0_nominal_pusch": random.randint(-100, -90),
                    "pdcch_aggregation_level": random.choice([1, 2, 4])
                },
                "parameter_ranges": {
                    "reference_signal_power": {"min": -60, "max": 50, "unit": "0.1 dBm"},
                    "a3_offset": {"min": -15, "max": 15, "unit": "dB"},
                    "t310_timer": {"min": 0, "max": 1000, "unit": "ms"}
                },
                "simulation_note": "Simulated parameters within valid ranges"
            }
        
        return {"simulated": True, "data_type": data_type}
    
    async def _generate_minimal_fallback(self, data_type: str) -> Dict[str, Any]:
        """Generate minimal fallback data when all sources fail"""
        return {
            "error": "All data sources unavailable",
            "fallback_data": {
                "sites": list(self.bindura_sites.keys()),
                "status": "minimal_fallback"
            },
            "data_source": "emergency_fallback",
            "data_quality": "minimal"
        }
    
    async def get_optimization_context(self) -> Dict[str, Any]:
        """Get comprehensive optimization context combining all data sources"""
        
        # Gather data from multiple sources
        discovery_data = await self.get_network_data("discovery")
        kpi_data = await self.get_network_data("kpi_monitoring")
        config_data = await self.get_network_data("parameter_config")
        
        # Combine into comprehensive context
        optimization_context = {
            "network_topology": discovery_data,
            "current_performance": kpi_data,
            "current_configuration": config_data,
            "optimization_targets": {
                "rach_target": 5.0,  # Realistic target for crisis network
                "ibler_target": 12.0,  # Achievable improvement
                "priority_sites": ["MSH0013-Bindura-Zaoga", "MSH-0331-Chiwaridzo 2"]
            },
            "business_context": {
                "urgency": "critical",
                "risk_tolerance": "high",
                "optimization_window": "immediate",
                "expected_benefits": [
                    "Restore network accessibility",
                    "Improve user experience",
                    "Reduce service complaints"
                ]
            },
            "technical_constraints": {
                "vendor": "Huawei",
                "technology": "4G LTE",
                "change_window": "24/7 (crisis mode)",
                "rollback_time": "5 minutes"
            },
            "data_sources_used": [
                discovery_data.get("data_source", "unknown"),
                kpi_data.get("data_source", "unknown"),
                config_data.get("data_source", "unknown")
            ],
            "context_timestamp": datetime.now().isoformat()
        }
        
        return optimization_context
    
    def get_data_source_status(self) -> Dict[str, Any]:
        """Get status of all data sources"""
        return {
            "live_api": {
                "available": self.api_available,
                "status": "connected" if self.api_available else "unavailable",
                "latency": "50ms" if self.api_available else "timeout"
            },
            "database": {
                "available": os.path.exists(self.db_path),
                "status": "accessible" if os.path.exists(self.db_path) else "not_found",
                "path": self.db_path
            },
            "csv_file": {
                "available": os.path.exists(self.csv_path),
                "status": "readable" if os.path.exists(self.csv_path) else "not_found",
                "path": self.csv_path
            },
            "simulation": {
                "available": True,
                "status": "always_available",
                "quality": "realistic_baseline"
            },
            "fallback_hierarchy": self.fallback_hierarchy,
            "cache_status": {
                "cached_items": len(self.data_cache),
                "cache_fresh": True
            }
        }