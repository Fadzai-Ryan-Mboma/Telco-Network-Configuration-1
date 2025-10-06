#!/usr/bin/env python3
"""
CSV to Database Importer for Liquid Zimbabwe Network KPI Data

This script imports telco network KPI data from historical_data.csv into 
the liquid_zimbabwe.db SQLite database with proper column mapping.

Usage:
    python csv_to_db_importer.py [options]

Options:
    --csv-path: Path to CSV file (default: data/historical_data.csv)
    --db-path: Path to database file (default: data/liquid_zimbabwe.db)
    --clear-existing: Clear existing data before import
    --dry-run: Show what would be imported without actually importing
"""

import os
import sys
import sqlite3
import pandas as pd
import argparse
from datetime import datetime
from pathlib import Path

class KPIDataImporter:
    """Imports telco KPI data from CSV to SQLite database"""
    
    def __init__(self, csv_path: str, db_path: str):
        self.csv_path = Path(csv_path)
        self.db_path = Path(db_path)
        
        # Validate paths
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Create database directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _initialize_database(self):
        """Initialize database schema if it doesn't exist"""
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
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kpi_data_site_timestamp ON kpi_data(site_name, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kpi_data_timestamp ON kpi_data(timestamp)")
            
            conn.commit()
    
    def _clear_existing_data(self):
        """Clear existing KPI data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM kpi_data")
            conn.commit()
            print(f"🗑️ Cleared existing data from kpi_data table")
    
    def _load_csv_data(self):
        """Load and validate CSV data"""
        print(f"📖 Loading CSV data from {self.csv_path}")
        
        try:
            df = pd.read_csv(self.csv_path)
            print(f"✅ Loaded {len(df)} records from CSV")
            
            # Validate required columns
            required_columns = [
                'Date', 'eNodeB Name', 'LocalCell Id',
                'RACH Setup Success Rate(%)', 'DL IBLER[%]', 'UL IBLER[%]',
                'PDCCH CCE Usage Rate[%]', 'PUCCHUsage Rate[%]',
                'DL Cell PDCP Layer Average Throughput(kbit/s)',
                'UL Cell PDCP Layer Average Throughput(kbit/s)'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error loading CSV data: {e}")
            raise
    
    def _import_data(self, df: pd.DataFrame, dry_run: bool = False):
        """Import data from DataFrame to database"""
        
        if dry_run:
            print(f"🔍 DRY RUN: Would import {len(df)} records")
            print("\nSample mapping:")
            for i, (_, row) in enumerate(df.head(3).iterrows()):
                print(f"  Row {i + 1}:")
                print(f"    Date: {row['Date']} -> timestamp")
                print(f"    Site: {row['eNodeB Name']} -> site_name")
                print(f"    Cell: {row['LocalCell Id']} -> cell_id")
                print(f"    RACH: {row['RACH Setup Success Rate(%)']} -> network_access_success")
                print(f"    DL IBLER: {row['DL IBLER[%]']} -> download_quality")
                print(f"    UL IBLER: {row['UL IBLER[%]']} -> upload_quality")
                print(f"    PDCCH: {row['PDCCH CCE Usage Rate[%]']} -> control_channel_load")
                print(f"    PUCCH: {row['PUCCHUsage Rate[%]']} -> feedback_channel_load")
                print(f"    DL Throughput: {row['DL Cell PDCP Layer Average Throughput(kbit/s)']} -> download_speed")
                print(f"    UL Throughput: {row['UL Cell PDCP Layer Average Throughput(kbit/s)']} -> upload_speed")
                print()
            return
        
        print(f"💾 Importing {len(df)} records to database...")
        
        imported_count = 0
        failed_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for i, (idx, row) in enumerate(df.iterrows()):
                try:
                    # Map CSV columns to database schema
                    cursor.execute("""
                        INSERT INTO kpi_data (
                            timestamp, site_name, cell_id,
                            network_access_success, download_quality, upload_quality,
                            control_channel_load, feedback_channel_load, 
                            download_speed, upload_speed
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['Date'],
                        row['eNodeB Name'],
                        int(row['LocalCell Id']),
                        float(row['RACH Setup Success Rate(%)']),
                        float(row['DL IBLER[%]']),
                        float(row['UL IBLER[%]']),
                        float(row['PDCCH CCE Usage Rate[%]']),
                        float(row['PUCCHUsage Rate[%]']),
                        float(row['DL Cell PDCP Layer Average Throughput(kbit/s)']),
                        float(row['UL Cell PDCP Layer Average Throughput(kbit/s)'])
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Failed to import row {i + 1}: {e}")
                    failed_count += 1
                    continue
            
            conn.commit()
        
        print(f"✅ Import completed:")
        print(f"   - Successfully imported: {imported_count} records")
        if failed_count > 0:
            print(f"   - Failed imports: {failed_count} records")
    
    def get_database_stats(self):
        """Get current database statistics"""
        if not self.db_path.exists():
            return {"status": "Database does not exist"}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kpi_data'")
            if not cursor.fetchone():
                return {"status": "kpi_data table does not exist"}
            
            # Get record count
            cursor.execute("SELECT COUNT(*) FROM kpi_data")
            total_records = cursor.fetchone()[0]
            
            if total_records == 0:
                return {"status": "kpi_data table is empty", "records": 0}
            
            # Get date range
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM kpi_data")
            min_date, max_date = cursor.fetchone()
            
            # Get unique sites
            cursor.execute("SELECT COUNT(DISTINCT site_name) FROM kpi_data")
            unique_sites = cursor.fetchone()[0]
            
            # Get unique cells
            cursor.execute("SELECT COUNT(DISTINCT cell_id) FROM kpi_data")
            unique_cells = cursor.fetchone()[0]
            
            return {
                "status": "Database populated",
                "records": total_records,
                "date_range": f"{min_date} to {max_date}",
                "unique_sites": unique_sites,
                "unique_cells": unique_cells
            }
    
    def import_csv_to_database(self, clear_existing: bool = False, dry_run: bool = False):
        """Main import process"""
        try:
            print("🚀 Starting CSV to Database Import Process")
            print("=" * 50)
            
            # Show current database status
            stats = self.get_database_stats()
            print(f"📊 Current database status: {stats.get('status', 'Unknown')}")
            if 'records' in stats:
                print(f"   - Records: {stats['records']}")
                print(f"   - Date range: {stats.get('date_range', 'N/A')}")
                print(f"   - Sites: {stats.get('unique_sites', 'N/A')}")
                print(f"   - Cells: {stats.get('unique_cells', 'N/A')}")
            print()
            
            # Initialize database schema
            self._initialize_database()
            
            # Clear existing data if requested
            if clear_existing and not dry_run:
                self._clear_existing_data()
            
            # Load CSV data
            df = self._load_csv_data()
            
            # Import data
            self._import_data(df, dry_run)
            
            if not dry_run:
                print()
                # Show final statistics
                final_stats = self.get_database_stats()
                print(f"📊 Final database status: {final_stats.get('status', 'Unknown')}")
                if 'records' in final_stats:
                    print(f"   - Records: {final_stats['records']}")
                    print(f"   - Date range: {final_stats.get('date_range', 'N/A')}")
                    print(f"   - Sites: {final_stats.get('unique_sites', 'N/A')}")
                    print(f"   - Cells: {final_stats.get('unique_cells', 'N/A')}")
            
            print("\n🎉 Import process completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Import process failed: {e}")
            return False


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Import telco KPI data from CSV to SQLite database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python csv_to_db_importer.py
  python csv_to_db_importer.py --dry-run
  python csv_to_db_importer.py --clear-existing
  python csv_to_db_importer.py --csv-path custom_data.csv --db-path custom.db
        """
    )
    
    parser.add_argument(
        '--csv-path',
        default='data/historical_data.csv',
        help='Path to CSV file (default: data/historical_data.csv)'
    )
    
    parser.add_argument(
        '--db-path',
        default='data/liquid_zimbabwe.db',
        help='Path to database file (default: data/liquid_zimbabwe.db)'
    )
    
    parser.add_argument(
        '--clear-existing',
        action='store_true',
        help='Clear existing data before import'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be imported without actually importing'
    )
    
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Show database statistics only (no import)'
    )
    
    args = parser.parse_args()
    
    try:
        importer = KPIDataImporter(args.csv_path, args.db_path)
        
        if args.stats_only:
            print("📊 Database Statistics")
            print("=" * 30)
            stats = importer.get_database_stats()
            for key, value in stats.items():
                print(f"{key}: {value}")
            return
        
        success = importer.import_csv_to_database(
            clear_existing=args.clear_existing,
            dry_run=args.dry_run
        )
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()