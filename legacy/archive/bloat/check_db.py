#!/usr/bin/env python3
import sys
sys.path.append('/workspace')
import sqlite3

def check_database(db_path):
    print(f"Checking database: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables found: {tables}")
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} rows")
        
        conn.close()
        return tables
    except Exception as e:
        print(f"Error checking database {db_path}: {e}")
        return []

if __name__ == "__main__":
    print("Checking all databases...")
    check_database('/workspace/data/live_network.db')
    check_database('/workspace/data/liquid_zimbabwe.db')
    check_database('/workspace/data/historical_db')