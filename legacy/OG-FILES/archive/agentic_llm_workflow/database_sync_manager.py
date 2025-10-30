"""
Liquid Zimbabwe Database Sync Manager

This module handles automatic synchronization between historical_data.csv 
and the liquid_zimbabwe.db database, ensuring data consistency on startup.
"""

import os
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
from typing import Dict, Tuple, Optional
import logging
from liquid_zimbabwe_kpi import LiquidZimbabweKPIManager

class DatabaseSyncManager:
    """
    Manages synchronization between CSV historical data and SQLite database
    """
    
    def __init__(self, csv_path: str = "../data/historical_data.csv", 
                 db_path: str = "../data/liquid_zimbabwe.db"):
        self.csv_path = csv_path
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Initialize KPI manager
        self.kpi_manager = LiquidZimbabweKPIManager(db_path)
    
    def check_data_sync(self) -> Dict:
        """
        Check if CSV data matches database data
        
        Returns:
            Dictionary with sync status and recommendations
        """
        print("🔍 Checking data synchronization...")
        
        # Check if files exist
        csv_exists = os.path.exists(self.csv_path)
        db_exists = os.path.exists(self.db_path)
        
        if not csv_exists:
            return {
                "status": "error",
                "message": "❌ historical_data.csv not found",
                "action": "none"
            }
        
        if not db_exists:
            return {
                "status": "db_missing",
                "message": "📄 Database not found - will create and import CSV data",
                "action": "import_all"
            }
        
        # Get CSV data info
        csv_info = self._analyze_csv()
        if csv_info["status"] == "error":
            return csv_info
        
        # Get database data info
        db_info = self._analyze_database()
        
        # Compare the two
        sync_result = self._compare_data(csv_info, db_info)
        
        return sync_result
    
    def _analyze_csv(self) -> Dict:
        """Analyze CSV file content"""
        try:
            df = pd.read_csv(self.csv_path)
            
            # Calculate content hash
            content_hash = self._calculate_dataframe_hash(df)
            
            # Get unique sites and date range
            sites = sorted(df['eNodeB Name'].unique()) if 'eNodeB Name' in df.columns else []
            
            date_col = 'Date' if 'Date' in df.columns else df.columns[0]
            date_range = {
                'start': df[date_col].min(),
                'end': df[date_col].max()
            }
            
            return {
                "status": "success",
                "row_count": len(df),
                "sites": sites,
                "site_count": len(sites),
                "date_range": date_range,
                "content_hash": content_hash,
                "columns": list(df.columns)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"❌ Error reading CSV: {str(e)}"
            }
    
    def _analyze_database(self) -> Dict:
        """Analyze database content"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if kpi_data table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kpi_data'")
                table_exists = cursor.fetchone()
                
                if not table_exists:
                    return {
                        "status": "empty",
                        "row_count": 0,
                        "sites": [],
                        "site_count": 0
                    }
                
                # Get row count
                cursor.execute("SELECT COUNT(*) FROM kpi_data")
                row_count = cursor.fetchone()[0]
                
                if row_count == 0:
                    return {
                        "status": "empty",
                        "row_count": 0,
                        "sites": [],
                        "site_count": 0
                    }
                
                # Get unique sites
                cursor.execute("SELECT DISTINCT site_name FROM kpi_data ORDER BY site_name")
                sites = [row[0] for row in cursor.fetchall()]
                
                # Get date range
                cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM kpi_data")
                date_range_result = cursor.fetchone()
                date_range = {
                    'start': date_range_result[0],
                    'end': date_range_result[1]
                }
                
                # Get sample data for hash comparison
                df = pd.read_sql_query("SELECT * FROM kpi_data ORDER BY timestamp, site_name", conn)
                content_hash = self._calculate_dataframe_hash(df)
                
                return {
                    "status": "has_data",
                    "row_count": row_count,
                    "sites": sites,
                    "site_count": len(sites),
                    "date_range": date_range,
                    "content_hash": content_hash
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"❌ Error reading database: {str(e)}"
            }
    
    def _calculate_dataframe_hash(self, df: pd.DataFrame) -> str:
        """Calculate hash of dataframe content for comparison"""
        try:
            # Create a string representation of the data
            content_str = df.to_string()
            return hashlib.md5(content_str.encode()).hexdigest()[:8]
        except:
            return "unknown"
    
    def _compare_data(self, csv_info: Dict, db_info: Dict) -> Dict:
        """Compare CSV and database data"""
        
        if db_info["status"] == "empty":
            return {
                "status": "sync_needed",
                "message": f"📊 Database is empty. CSV has {csv_info['row_count']} records from {csv_info['site_count']} sites",
                "action": "import_all",
                "details": {
                    "csv_sites": csv_info['sites'],
                    "csv_rows": csv_info['row_count'],
                    "db_rows": 0
                }
            }
        
        if db_info["status"] == "error":
            return db_info
        
        # Compare row counts
        if csv_info["row_count"] != db_info["row_count"]:
            return {
                "status": "sync_needed",
                "message": f"📊 Row count mismatch: CSV has {csv_info['row_count']}, DB has {db_info['row_count']}",
                "action": "update_db",
                "details": {
                    "csv_sites": csv_info['sites'],
                    "db_sites": db_info['sites'],
                    "csv_rows": csv_info['row_count'],
                    "db_rows": db_info['row_count']
                }
            }
        
        # Compare site counts
        if csv_info["site_count"] != db_info["site_count"]:
            return {
                "status": "sync_needed", 
                "message": f"🏢 Site count mismatch: CSV has {csv_info['site_count']}, DB has {db_info['site_count']}",
                "action": "update_db",
                "details": {
                    "csv_sites": csv_info['sites'],
                    "db_sites": db_info['sites'],
                    "csv_rows": csv_info['row_count'],
                    "db_rows": db_info['row_count']
                }
            }
        
        # Compare sites
        csv_sites_set = set(csv_info['sites'])
        db_sites_set = set(db_info['sites'])
        
        if csv_sites_set != db_sites_set:
            missing_in_db = csv_sites_set - db_sites_set
            extra_in_db = db_sites_set - csv_sites_set
            
            message = "🏢 Site mismatch detected:"
            if missing_in_db:
                message += f" Missing in DB: {list(missing_in_db)}"
            if extra_in_db:
                message += f" Extra in DB: {list(extra_in_db)}"
            
            return {
                "status": "sync_needed",
                "message": message,
                "action": "update_db",
                "details": {
                    "csv_sites": csv_info['sites'],
                    "db_sites": db_info['sites'],
                    "missing_in_db": list(missing_in_db),
                    "extra_in_db": list(extra_in_db)
                }
            }
        
        # If we get here, basic counts match - check content hash
        if csv_info.get("content_hash") != db_info.get("content_hash"):
            return {
                "status": "sync_needed",
                "message": "📊 Data content has changed - database update recommended",
                "action": "update_db",
                "details": {
                    "csv_hash": csv_info.get("content_hash"),
                    "db_hash": db_info.get("content_hash")
                }
            }
        
        # Everything matches
        return {
            "status": "synchronized",
            "message": f"✅ Data is synchronized: {csv_info['row_count']} records from {csv_info['site_count']} sites",
            "action": "none",
            "details": {
                "sites": csv_info['sites'],
                "rows": csv_info['row_count']
            }
        }
    
    def sync_database(self, force: bool = False) -> Dict:
        """
        Synchronize database with CSV data
        
        Args:
            force: If True, update without prompting
            
        Returns:
            Dictionary with sync results
        """
        
        # Check current sync status
        sync_status = self.check_data_sync()
        
        if sync_status["status"] == "synchronized" and not force:
            return sync_status
        
        if sync_status["status"] == "error":
            return sync_status
        
        # Prompt user if not forced
        if not force and sync_status["action"] in ["import_all", "update_db"]:
            print(f"\n{sync_status['message']}")
            print("\nOptions:")
            print("1. Update database with CSV data")
            print("2. Keep current database")
            print("3. View detailed comparison")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "3":
                self._show_detailed_comparison(sync_status)
                choice = input("\nUpdate database with CSV data? (y/n): ").strip().lower()
                if choice not in ['y', 'yes']:
                    return {"status": "skipped", "message": "Database update skipped by user"}
            elif choice == "2":
                return {"status": "skipped", "message": "Database update skipped by user"}
            elif choice != "1":
                return {"status": "cancelled", "message": "Operation cancelled"}
        
        # Perform the sync
        try:
            print("🔄 Updating database with CSV data...")
            
            # Clear existing data
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM kpi_data")
                conn.commit()
                print("🗑️ Cleared existing database records")
            
            # Import new data
            success = self.kpi_manager.import_historical_data(self.csv_path)
            
            if success:
                # Verify the import
                new_status = self.check_data_sync()
                if new_status["status"] == "synchronized":
                    return {
                        "status": "success",
                        "message": f"✅ Database updated successfully: {new_status['details']['rows']} records imported",
                        "details": new_status["details"]
                    }
                else:
                    return {
                        "status": "success",
                        "message": "✅ Database updated successfully",
                        "details": {"records_imported": "Unknown"}
                    }
            else:
                return {
                    "status": "error",
                    "message": "❌ Failed to import CSV data to database"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"❌ Error during database sync: {str(e)}"
            }
    
    def _show_detailed_comparison(self, sync_status: Dict):
        """Show detailed comparison between CSV and database"""
        details = sync_status.get("details", {})
        
        print("\n📊 DETAILED COMPARISON")
        print("=" * 50)
        
        if "csv_rows" in details:
            print(f"CSV Records: {details['csv_rows']}")
            print(f"DB Records:  {details['db_rows']}")
        
        if "csv_sites" in details:
            print(f"\nCSV Sites ({len(details['csv_sites'])}):")
            for site in details['csv_sites']:
                print(f"  • {site}")
        
        if "db_sites" in details:
            print(f"\nDB Sites ({len(details['db_sites'])}):")
            for site in details['db_sites']:
                print(f"  • {site}")
        
        if "missing_in_db" in details:
            print(f"\nMissing in DB:")
            for site in details['missing_in_db']:
                print(f"  ❌ {site}")
        
        if "extra_in_db" in details:
            print(f"\nExtra in DB:")
            for site in details['extra_in_db']:
                print(f"  ➕ {site}")


def run_startup_sync_check(interactive: bool = True) -> Dict:
    """
    Run startup synchronization check
    
    Args:
        interactive: If True, prompt user for decisions
        
    Returns:
        Sync status results
    """
    print("🚀 Starting Liquid Zimbabwe Data Sync Check...")
    print("=" * 50)
    
    sync_manager = DatabaseSyncManager()
    
    # Check sync status
    status = sync_manager.check_data_sync()
    print(status["message"])
    
    # Handle sync if needed
    if status["action"] in ["import_all", "update_db"]:
        if interactive:
            return sync_manager.sync_database(force=False)
        else:
            # Auto-sync in non-interactive mode
            return sync_manager.sync_database(force=True)
    
    return status


if __name__ == "__main__":
    # Run interactive sync check
    result = run_startup_sync_check(interactive=True)
    print(f"\n🎯 Final Status: {result['message']}")