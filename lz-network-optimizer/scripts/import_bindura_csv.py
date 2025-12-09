#!/usr/bin/env python3
"""
Import Bindura Cluster KPI CSV data into the lz_network.db database.
CSV: LTZIM LTE Main KPIs Report_2_Query_Result_Sept-Oct2025_Bindura Cluster.csv
"""

import csv
import sqlite3
from datetime import datetime
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CSV_FILE = DATA_DIR / "LTZIM LTE Main KPIs Report_2_Query_Result_Sept-Oct2025_Bindura Cluster.csv"
DB_FILE = DATA_DIR / "lz_network.db"

# Column mapping: CSV column name -> processing function
def safe_float(value, default=0.0):
    """Convert string to float, handling empty or invalid values."""
    if value is None or value == '' or value == 'NIL':
        return default
    try:
        # Remove % sign if present
        return float(str(value).replace('%', '').strip())
    except (ValueError, TypeError):
        return default

def parse_date(date_str):
    """Parse D/M/YYYY format to YYYY-MM-DD HH:MM:SS."""
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d 00:00:00")
    except ValueError:
        return None

def map_row(row):
    """Map CSV row to database columns."""
    # CSV columns (from header):
    # Date, eNodeB Name, Cell FDD TDD Indication, Cell Name, LocalCell Id,
    # eNodeB Function Name, Integrity, Radio Net Availability Rate(%), 
    # RRC Setup Success Rate(all), RRC Setup Success Rate(Service)[%],
    # RRC Setup Success Rate(Signal)[%], E-RAB Setup Success Rate (ALL)(%),
    # Call Drop Rate (All)(%), HO Success Rate(Intra Freqency), HO Success Rate(S1)[%],
    # Paging Transfer Success Rate, Total Traffic (Gbit), DL Traffic Volume(Gbit),
    # UL Traffic Volume(Gbit), L.Traffic.User.Avg, L.Traffic.User.Max,
    # User DL PDCP Average Throughput, User UL PDCP Average Throughput,
    # DL IBLER[%], UL IBLER[%], DL ReTrans Rate[%], DL Packet Loss Rate(all),
    # UL Packet Loss Rate(all), DL PRB Usage Rate(%), UL PRB Usage Rate(%),
    # PUCCHUsage Rate[%], PDCCH CCE Usage Rate[%], Average CQI, Average PDSCH MCS
    
    timestamp = parse_date(row.get('Date', ''))
    if not timestamp:
        return None
    
    # Extract values with safe conversion
    network_access = safe_float(row.get('RRC Setup Success Rate(all)', ''))
    dl_throughput = safe_float(row.get('User DL PDCP Average Throughput', ''))
    ul_throughput = safe_float(row.get('User UL PDCP Average Throughput', ''))
    
    # IBLER is error rate, so quality = 100 - IBLER
    dl_ibler = safe_float(row.get('DL IBLER[%]', ''))
    ul_ibler = safe_float(row.get('UL IBLER[%]', ''))
    dl_quality = 100.0 - dl_ibler if dl_ibler else 0.0
    ul_quality = 100.0 - ul_ibler if ul_ibler else 0.0
    
    # Channel usage rates
    pdcch_usage = safe_float(row.get('PDCCH CCE Usage Rate[%]', ''))
    pucch_usage = safe_float(row.get('PUCCHUsage Rate[%]', ''))
    
    return {
        'timestamp': timestamp,
        'site_name': row.get('eNodeB Name', '').strip(),
        'cell_id': int(safe_float(row.get('LocalCell Id', 0))),
        'network_access_success': network_access,
        'download_speed': dl_throughput,
        'download_quality': dl_quality,
        'upload_speed': ul_throughput,
        'upload_quality': ul_quality,
        'control_channel_load': pdcch_usage,
        'feedback_channel_load': pucch_usage,
        'data_source': 'csv_import_bindura',
        'notes': f"Imported from Bindura Cluster CSV - {row.get('Cell Name', '')}"
    }

def import_csv():
    """Import CSV data into database."""
    print(f"📂 CSV File: {CSV_FILE}")
    print(f"📂 Database: {DB_FILE}")
    
    if not CSV_FILE.exists():
        print(f"❌ CSV file not found: {CSV_FILE}")
        return
    
    if not DB_FILE.exists():
        print(f"❌ Database not found: {DB_FILE}")
        return
    
    # Read CSV
    rows_to_import = []
    skipped = 0
    
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        for row in reader:
            mapped = map_row(row)
            if mapped:
                rows_to_import.append(mapped)
            else:
                skipped += 1
    
    print(f"📊 Rows to import: {len(rows_to_import)}")
    print(f"⚠️  Rows skipped (invalid date): {skipped}")
    
    if not rows_to_import:
        print("❌ No rows to import!")
        return
    
    # Show sample
    print("\n📋 Sample row (first):")
    for k, v in rows_to_import[0].items():
        print(f"   {k}: {v}")
    
    # Connect to database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check existing records
    cursor.execute("SELECT COUNT(*) FROM kpi_data")
    existing_count = cursor.fetchone()[0]
    print(f"\n📊 Existing records in kpi_data: {existing_count}")
    
    # Delete existing records to avoid duplicates (optional - comment out to append)
    # cursor.execute("DELETE FROM kpi_data WHERE data_source = 'csv_import_bindura'")
    # print(f"🗑️  Deleted previous import records")
    
    # Insert new records
    insert_sql = """
        INSERT INTO kpi_data (
            timestamp, site_name, cell_id,
            network_access_success, download_speed, download_quality,
            upload_speed, upload_quality, control_channel_load,
            feedback_channel_load, data_source, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    inserted = 0
    for row in rows_to_import:
        try:
            cursor.execute(insert_sql, (
                row['timestamp'],
                row['site_name'],
                row['cell_id'],
                row['network_access_success'],
                row['download_speed'],
                row['download_quality'],
                row['upload_speed'],
                row['upload_quality'],
                row['control_channel_load'],
                row['feedback_channel_load'],
                row['data_source'],
                row['notes']
            ))
            inserted += 1
        except Exception as e:
            print(f"❌ Error inserting row: {e}")
            skipped += 1
    
    conn.commit()
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM kpi_data")
    final_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM kpi_data")
    date_range = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(DISTINCT site_name) FROM kpi_data")
    site_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT cell_id) FROM kpi_data")
    cell_count = cursor.fetchone()[0]
    
    print(f"\n✅ Import complete!")
    print(f"   Inserted: {inserted} records")
    print(f"   Total records now: {final_count}")
    print(f"   Date range: {date_range[0]} to {date_range[1]}")
    print(f"   Unique sites: {site_count}")
    print(f"   Unique cell IDs: {cell_count}")
    
    conn.close()

if __name__ == "__main__":
    import_csv()
