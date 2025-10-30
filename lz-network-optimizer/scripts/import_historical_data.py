#!/usr/bin/env python3
"""
Liquid Zimbabwe 4G Network Optimizer - Historical Data Import Script
Purpose: Import historical_data.csv into SQLite database
Created: 2025-10-30
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CSV_FILE = DATA_DIR / "historical_data.csv"
DB_FILE = DATA_DIR / "lz_network.db"
SCHEMA_FILE = DATA_DIR / "schema.sql"


def create_database():
    """Create database with schema if it doesn't exist."""
    print(f"Creating database: {DB_FILE}")

    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Read schema
    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()

    # Create database and execute schema
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()

    print(f"✓ Database created successfully at {DB_FILE}")


def import_csv_data():
    """Import historical_data.csv into kpi_data table."""
    print(f"\nImporting data from: {CSV_FILE}")

    # Read CSV
    df = pd.read_csv(CSV_FILE)
    print(f"✓ Loaded {len(df)} rows from CSV")

    # Display CSV columns
    print(f"  Columns: {list(df.columns)}")

    # Map CSV columns to database schema
    # Actual CSV columns from Huawei eNodeB export:
    # Date, eNodeB Name, Cell Name, LocalCell Id, eNodeB Function Name,
    # RACH Setup Success Rate(%), DL IBLER[%], UL IBLER[%],
    # PDCCH CCE Usage Rate[%], PUCCHUsage Rate[%],
    # DL Cell PDCP Layer Average Throughput(kbit/s),
    # UL Cell PDCP Layer Average Throughput(kbit/s)

    column_mapping = {
        'Date': 'timestamp',
        'eNodeB Name': 'site_name',
        'LocalCell Id': 'cell_id',
        'RACH Setup Success Rate(%)': 'network_access_success',
        'DL Cell PDCP Layer Average Throughput(kbit/s)': 'download_speed',  # Convert kbit/s to Mbps
        'UL Cell PDCP Layer Average Throughput(kbit/s)': 'upload_speed',    # Convert kbit/s to Mbps
        'DL IBLER[%]': 'download_quality',  # Invert: 100 - IBLER = quality
        'UL IBLER[%]': 'upload_quality',    # Invert: 100 - IBLER = quality
        'PDCCH CCE Usage Rate[%]': 'control_channel_load',
        'PUCCHUsage Rate[%]': 'feedback_channel_load'
    }

    # Rename columns
    df_renamed = df.rename(columns=column_mapping)

    # Data conversions
    # Convert throughput from kbit/s to Mbps
    df_renamed['download_speed'] = df_renamed['download_speed'] / 1000  # kbit/s to Mbit/s
    df_renamed['upload_speed'] = df_renamed['upload_speed'] / 1000

    # Convert IBLER (error rate) to quality percentage: Quality = 100 - IBLER
    df_renamed['download_quality'] = 100 - df_renamed['download_quality']
    df_renamed['upload_quality'] = 100 - df_renamed['upload_quality']

    # Add required fields
    df_renamed['data_source'] = 'historical'
    df_renamed['notes'] = 'Imported from historical_data.csv - Huawei eNodeB export'

    # Convert timestamp to proper format if needed
    try:
        df_renamed['timestamp'] = pd.to_datetime(df_renamed['timestamp'])
    except Exception as e:
        print(f"  Warning: Could not parse timestamps: {e}")
        print(f"  Using current timestamp for all records")
        df_renamed['timestamp'] = datetime.now()

    # Select only columns that exist in database
    db_columns = [
        'timestamp', 'site_name', 'cell_id',
        'network_access_success', 'download_speed', 'download_quality',
        'upload_speed', 'upload_quality', 'control_channel_load',
        'feedback_channel_load', 'data_source', 'notes'
    ]

    df_final = df_renamed[db_columns]

    # Import to database
    conn = sqlite3.connect(DB_FILE)
    df_final.to_sql('kpi_data', conn, if_exists='append', index=False)
    conn.close()

    print(f"✓ Imported {len(df_final)} rows into kpi_data table")

    return len(df_final)


def verify_import():
    """Verify data was imported correctly."""
    print("\nVerifying import...")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Count rows
    cursor.execute("SELECT COUNT(*) FROM kpi_data")
    row_count = cursor.fetchone()[0]
    print(f"✓ Total rows in kpi_data: {row_count}")

    # Count unique sites
    cursor.execute("SELECT COUNT(DISTINCT site_name) FROM kpi_data")
    site_count = cursor.fetchone()[0]
    print(f"✓ Unique sites: {site_count}")

    # Show sample data
    print("\nSample data (first 3 rows):")
    cursor.execute("""
        SELECT
            timestamp,
            site_name,
            download_speed,
            upload_speed,
            network_access_success
        FROM kpi_data
        LIMIT 3
    """)

    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row[0]} | {row[1]} | DL: {row[2]} Mbps | UL: {row[3]} Mbps | Access: {row[4]}%")

    # Show date range
    cursor.execute("""
        SELECT
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest
        FROM kpi_data
    """)
    date_range = cursor.fetchone()
    print(f"\nDate range: {date_range[0]} to {date_range[1]}")

    # Show KPI averages
    cursor.execute("""
        SELECT
            ROUND(AVG(network_access_success), 2) as avg_access,
            ROUND(AVG(download_speed), 2) as avg_dl_speed,
            ROUND(AVG(upload_speed), 2) as avg_ul_speed
        FROM kpi_data
    """)
    averages = cursor.fetchone()
    print(f"\nKPI Averages:")
    print(f"  Network Access Success: {averages[0]}%")
    print(f"  Download Speed: {averages[1]} Mbps")
    print(f"  Upload Speed: {averages[2]} Mbps")

    conn.close()


def main():
    """Main import process."""
    print("=" * 70)
    print("Liquid Zimbabwe 4G Network Optimizer - Historical Data Import")
    print("=" * 70)

    # Check if CSV exists
    if not CSV_FILE.exists():
        print(f"ERROR: CSV file not found at {CSV_FILE}")
        return 1

    # Check if schema exists
    if not SCHEMA_FILE.exists():
        print(f"ERROR: Schema file not found at {SCHEMA_FILE}")
        return 1

    try:
        # Create database
        create_database()

        # Import data
        imported_count = import_csv_data()

        # Verify import
        verify_import()

        print("\n" + "=" * 70)
        print(f"✓ SUCCESS: Imported {imported_count} historical records")
        print(f"✓ Database ready at: {DB_FILE}")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
