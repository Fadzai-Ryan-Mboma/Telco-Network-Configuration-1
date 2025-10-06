#!/usr/bin/env python3
"""
Database Helper Utilities for Liquid Zimbabwe Network Management
Provides functions to load network elements from the database with various filters
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger('LZ-DB-Helper')

class LZDatabaseHelper:
    """Helper class for managing network elements database"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Detect if running in Docker/container by checking for /.dockerenv or environment variable
            import os
            if os.path.exists("/.dockerenv") or os.environ.get("LZ_DOCKER", "") == "1":
                self.db_path = "/app/data/live_network.db"
            else:
                project_root = Path(__file__).parent.parent.parent
                self.db_path = str(project_root / "data" / "live_network.db")
        else:
            self.db_path = db_path
    
    def get_network_elements(self, status_filter: Optional[str] = None) -> Dict[str, Dict]:
        """
        Load network elements from database with optional status filter
        
        Args:
            status_filter: Optional status to filter by ('live_active', 'active', 'error', 'db_only', etc.)
        
        Returns:
            Dictionary of network elements {ne_name: {site_id, location, cell_ids, status, ...}}
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status_filter:
                query = """
                    SELECT name, site_id, location, cell_ids, status, last_updated 
                    FROM network_elements 
                    WHERE status = ?
                    ORDER BY name
                """
                cursor.execute(query, (status_filter,))
            else:
                query = """
                    SELECT name, site_id, location, cell_ids, status, last_updated 
                    FROM network_elements 
                    ORDER BY name
                """
                cursor.execute(query)
            
            rows = cursor.fetchall()
            conn.close()
            
            network_elements = {}
            for row in rows:
                ne_name, site_id, location, cell_ids, status, last_updated = row
                network_elements[ne_name] = {
                    "site_id": site_id,
                    "location": location,
                    "cell_ids": cell_ids,
                    "status": status,
                    "last_updated": last_updated
                }
            
            return network_elements
            
        except Exception as e:
            logger.error(f"Failed to load network elements: {e}")
            return {}
    
    def get_live_active_sites(self) -> Dict[str, Dict]:
        """Get only the network elements that are confirmed to be live and active"""
        return self.get_network_elements(status_filter='live_active')
    
    def get_all_sites(self) -> Dict[str, Dict]:
        """Get all network elements regardless of status"""
        return self.get_network_elements()
    
    def get_sites_by_status(self, status: str) -> Dict[str, Dict]:
        """Get network elements by specific status"""
        return self.get_network_elements(status_filter=status)
    
    def get_site_names_list(self, status_filter: Optional[str] = None) -> List[str]:
        """Get a simple list of site names, optionally filtered by status"""
        sites = self.get_network_elements(status_filter=status_filter)
        return list(sites.keys())
    
    def get_live_active_site_names(self) -> List[str]:
        """Get list of only live active site names - useful for API calls"""
        return self.get_site_names_list(status_filter='live_active')
    
    def update_site_status(self, ne_name: str, new_status: str) -> bool:
        """Update the status of a specific network element"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE network_elements 
                SET status = ?, last_updated = datetime('now')
                WHERE name = ?
            """, (new_status, ne_name))
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_affected > 0:
                logger.info(f"Updated {ne_name} status to {new_status}")
                return True
            else:
                logger.warning(f"No network element found with name: {ne_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update site status: {e}")
            return False
    
    def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get status counts
            cursor.execute("""
                SELECT status, COUNT(*) 
                FROM network_elements 
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM network_elements")
            total_sites = cursor.fetchone()[0]
            
            # Get live active details
            cursor.execute("""
                SELECT name, location, cell_ids 
                FROM network_elements 
                WHERE status = 'live_active'
                ORDER BY name
            """)
            live_sites = cursor.fetchall()
            
            conn.close()
            
            # Calculate total cells for live sites
            total_live_cells = 0
            for _, _, cell_ids in live_sites:
                if cell_ids:
                    total_live_cells += len(str(cell_ids).split(','))
            
            return {
                'total_sites': total_sites,
                'status_counts': status_counts,
                'live_active_count': len(live_sites),
                'total_live_cells': total_live_cells,
                'live_sites': [{'name': name, 'location': loc, 'cells': cell_ids} 
                              for name, loc, cell_ids in live_sites]
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

# Convenience functions for easy importing
def get_live_active_sites() -> Dict[str, Dict]:
    """Quick function to get live active sites"""
    db = LZDatabaseHelper()
    return db.get_live_active_sites()

def get_live_active_site_names() -> List[str]:
    """Quick function to get list of live active site names"""
    db = LZDatabaseHelper()
    return db.get_live_active_site_names()

def get_all_sites() -> Dict[str, Dict]:
    """Quick function to get all sites"""
    db = LZDatabaseHelper()
    return db.get_all_sites()

def get_database_stats() -> Dict:
    """Quick function to get database statistics"""
    db = LZDatabaseHelper()
    return db.get_database_stats()

# Test function
def test_database_helper():
    """Test the database helper functions"""
    print("🔍 Testing Database Helper Functions")
    print("=" * 50)
    
    db = LZDatabaseHelper()
    
    # Test live active sites
    live_sites = db.get_live_active_sites()
    print(f"✅ Live Active Sites: {len(live_sites)}")
    for name, info in live_sites.items():
        print(f"   🟢 {name} ({info['location']})")
    
    # Test live active site names
    live_names = db.get_live_active_site_names()
    print(f"\n📋 Live Active Site Names List: {live_names}")
    
    # Test database stats
    stats = db.get_database_stats()
    print(f"\n📊 Database Statistics:")
    print(f"   Total Sites: {stats.get('total_sites', 0)}")
    print(f"   Live Active: {stats.get('live_active_count', 0)}")
    print(f"   Total Live Cells: {stats.get('total_live_cells', 0)}")
    print(f"   Status Breakdown: {stats.get('status_counts', {})}")

if __name__ == "__main__":
    test_database_helper()