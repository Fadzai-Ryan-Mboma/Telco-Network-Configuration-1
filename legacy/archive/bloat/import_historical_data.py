"""
Data Import Script for Liquid Zimbabwe Historical Data
Imports Bindura CSV data and sets up the baseline database
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime
from agentic_llm_workflow.liquid_zimbabwe_kpi import LiquidZimbabweKPIManager

def import_bindura_data():
    """Import historical Bindura data into the system"""
    
    # Setup paths
    project_root = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(project_root, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    db_path = os.path.join(data_dir, 'liquid_zimbabwe.db')
    csv_path = os.path.join(os.path.dirname(project_root), 'lit_historical_data_bindura.csv')
    
    print(f"📊 Importing Bindura historical data...")
    print(f"Database: {db_path}")
    print(f"CSV Source: {csv_path}")
    
    # Initialize KPI manager
    kpi_manager = LiquidZimbabweKPIManager(db_path)
    
    # Read the CSV
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} rows from CSV")
        
        # Show sample of data columns
        print(f"📋 Available columns: {list(df.columns[:10])}..." if len(df.columns) > 10 else f"📋 Available columns: {list(df.columns)}")
        
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}")
        return False
    
    # Process and import data
    imported_count = 0
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        for index, row in df.iterrows():
            try:
                # Map CSV columns to our KPI structure
                site_name = row.get('eNodeB Name', 'Unknown')
                cell_id = row.get('LocalCell Id', 0) 
                date_str = row.get('Date', datetime.now().strftime('%Y-%m-%d'))
                
                # Convert date string to proper timestamp
                try:
                    timestamp = datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    timestamp = datetime.now()
                
                # Extract KPI values with defaults
                network_access_success = row.get('RACH Setup Success Rate(%)', 0)
                download_quality = row.get('DL IBLER[%]', 0)
                upload_quality = row.get('UL IBLER[%]', 0)
                control_channel_load = row.get('PDCCH CCE Usage Rate[%]', 0)
                feedback_channel_load = row.get('PUCCHUsage Rate[%]', 0) 
                download_speed = row.get('DL Cell PDCP Layer Average Throughput(kbit/s)', 0)
                upload_speed = row.get('UL Cell PDCP Layer Average Throughput(kbit/s)', 0)
                
                # Insert into database
                cursor.execute("""
                    INSERT INTO kpi_data (
                        timestamp, site_name, cell_id,
                        network_access_success, download_quality, upload_quality,
                        control_channel_load, feedback_channel_load,
                        download_speed, upload_speed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, site_name, cell_id,
                    float(network_access_success) if pd.notna(network_access_success) else 0,
                    float(download_quality) if pd.notna(download_quality) else 0,
                    float(upload_quality) if pd.notna(upload_quality) else 0,
                    float(control_channel_load) if pd.notna(control_channel_load) else 0,
                    float(feedback_channel_load) if pd.notna(feedback_channel_load) else 0,
                    float(download_speed) if pd.notna(download_speed) else 0,
                    float(upload_speed) if pd.notna(upload_speed) else 0
                ))
                
                imported_count += 1
                
                # Progress indicator
                if imported_count % 50 == 0:
                    print(f"📈 Imported {imported_count} records...")
                
            except Exception as e:
                print(f"⚠️  Error importing row {index}: {e}")
                continue
        
        conn.commit()
    
    print(f"✅ Successfully imported {imported_count} records")
    
    # Generate summary
    summary = kpi_manager.get_kpi_summary()
    if summary:
        print("\n📊 BASELINE DATA SUMMARY:")
        print(f"Sites: {summary['meta']['site_count']}")
        print(f"Cells: {summary['meta']['cell_count']}")
        print("\n🎯 KPI Averages:")
        for kpi_key, kpi_data in summary.items():
            if kpi_key != 'meta':
                print(f"  {kpi_data['user_friendly_name']}: {kpi_data['value']}{kpi_data['unit']} ({kpi_data['status']})")
    
    return True

if __name__ == "__main__":
    success = import_bindura_data()
    if success:
        print("\n🎉 Historical data import completed successfully!")
    else:
        print("\n❌ Historical data import failed!")