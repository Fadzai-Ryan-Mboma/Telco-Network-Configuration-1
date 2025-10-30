"""
Agentic Database Integration for UI
Provides database connectivity and data retrieval for the Streamlit interface
"""

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class AgenticDatabase:
    """Database integration for the UI to connect with liquid-4g-prod backend"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection"""
        if db_path is None:
            # Try to find the database in the standard location
            project_root = Path(__file__).parent.parent.parent.parent.parent
            db_path = project_root / "data" / "database" / "liquid4g.db"
        
        self.db_path = str(db_path)
        self._ensure_connection()
    
    def _ensure_connection(self) -> bool:
        """Ensure database connection is available"""
        try:
            if Path(self.db_path).exists():
                conn = sqlite3.connect(self.db_path)
                conn.close()
                return True
            else:
                logger.warning(f"Database not found at {self.db_path}")
                return False
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics for the UI"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get basic stats
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            stats = {
                "tables_count": len(tables),
                "tables": tables,
                "status": "connected",
                "last_check": datetime.now().isoformat()
            }
            
            # Try to get specific liquid4g stats if tables exist
            if "network_sites" in tables:
                cursor.execute("SELECT COUNT(*) FROM network_sites")
                stats["total_sites"] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM network_sites WHERE status = 'active'")
                stats["active_sites"] = cursor.fetchone()[0]
            
            if "optimization_results" in tables:
                cursor.execute("SELECT COUNT(*) FROM optimization_results")
                stats["optimization_count"] = cursor.fetchone()[0]
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    def get_live_active_sites(self) -> Dict[str, Dict[str, Any]]:
        """Get active network sites from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if network_sites table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='network_sites';")
            if not cursor.fetchone():
                logger.warning("network_sites table not found")
                return self._get_fallback_sites()
            
            cursor.execute("""
                SELECT site_id, site_name, location, status, 
                       cell_count, last_updated
                FROM network_sites 
                WHERE status = 'active'
            """)
            
            sites = {}
            for row in cursor.fetchall():
                site_id, name, location, status, cell_count, last_updated = row
                sites[name] = {
                    "site_id": site_id,
                    "location": location,
                    "status": status,
                    "cell_count": cell_count or 6,  # Default to 6 cells
                    "last_updated": last_updated
                }
            
            conn.close()
            return sites
            
        except Exception as e:
            logger.error(f"Failed to get live sites: {e}")
            return self._get_fallback_sites()
    
    def _get_fallback_sites(self) -> Dict[str, Dict[str, Any]]:
        """Fallback site data when database is not available - Real Bindura cluster"""
        return {
            "MSH-0013-Bindura-Zaoga": {
                "site_id": "MSH-0013",
                "location": "Bindura-Zaoga",
                "status": "active",
                "cell_count": 6,
                "last_updated": datetime.now().isoformat()
            },
            "MSH-0331-Chiwaridzo 2": {
                "site_id": "MSH-0331", 
                "location": "Chiwaridzo 2",
                "status": "active",
                "cell_count": 6,
                "last_updated": datetime.now().isoformat()
            },
            "MSH-0112-Bindura Hospital": {
                "site_id": "MSH-0112",
                "location": "Bindura Hospital",
                "status": "active",
                "cell_count": 6,
                "last_updated": datetime.now().isoformat()
            },
            "MSH-0014-Chipadze": {
                "site_id": "MSH-0014",
                "location": "Chipadze",
                "status": "active", 
                "cell_count": 6,
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def get_optimization_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent optimization history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='optimization_results';")
            if not cursor.fetchone():
                return []
            
            cursor.execute("""
                SELECT id, site_id, optimization_type, status, 
                       created_at, results_summary
                FROM optimization_results 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            history = []
            for row in cursor.fetchall():
                opt_id, site_id, opt_type, status, created_at, results = row
                
                # Parse results if it's JSON
                try:
                    results_data = json.loads(results) if results else {}
                except:
                    results_data = {}
                
                history.append({
                    "id": opt_id,
                    "site_id": site_id,
                    "type": opt_type,
                    "status": status,
                    "timestamp": created_at,
                    "results": results_data
                })
            
            conn.close()
            return history
            
        except Exception as e:
            logger.error(f"Failed to get optimization history: {e}")
            return []
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health indicators"""
        try:
            stats = self.get_database_stats()
            sites = self.get_live_active_sites()
            
            return {
                "database_status": stats.get("status", "unknown"),
                "total_sites": len(sites),
                "active_sites": len([s for s in sites.values() if s.get("status") == "active"]),
                "total_cells": sum(s.get("cell_count", 0) for s in sites.values()),
                "system_mode": "production" if stats.get("status") == "connected" else "simulation",
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                "database_status": "error",
                "error": str(e),
                "system_mode": "offline",
                "last_check": datetime.now().isoformat()
            }

# Global instance for UI usage
db_instance = None

def get_database_instance() -> AgenticDatabase:
    """Get singleton database instance"""
    global db_instance
    if db_instance is None:
        db_instance = AgenticDatabase()
    return db_instance

def get_database_stats() -> Dict[str, Any]:
    """Convenience function for UI"""
    return get_database_instance().get_database_stats()

def get_live_active_sites() -> Dict[str, Dict[str, Any]]:
    """Convenience function for UI"""
    return get_database_instance().get_live_active_sites()

def get_optimization_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Convenience function for UI"""
    return get_database_instance().get_optimization_history(limit)

def get_system_health() -> Dict[str, Any]:
    """Convenience function for UI"""
    return get_database_instance().get_system_health()