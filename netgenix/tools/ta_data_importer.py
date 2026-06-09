"""
Timing Advance (TA) Data Importer for LZ Network Optimizer.

Purpose: Import TA distribution data from Huawei PM exports into timing_advance_data table.
Created: 2026-01-12

This module imports Timing Advance distribution data which provides insights into:
- UE distance distribution across 12 distance bins
- Coverage overshoot issues (Index 0, 10, 11)
- Cell edge loading (Index 9, 10, 11)
- Average user equipment distance from base station
"""

import csv
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# TA Index Distance Ranges (meters) - LTE Standard
TA_DISTANCE_RANGES = {
    0: (0, 78),           # Very close / overshoot indicator
    1: (78, 156),
    2: (156, 312),
    3: (312, 547),
    4: (547, 781),
    5: (781, 1172),       # Optimal coverage zone
    6: (1172, 1563),      # Optimal coverage zone
    7: (1563, 2344),
    8: (2344, 3906),
    9: (3906, 7813),      # Cell edge
    10: (7813, 15625),    # Overshoot (far)
    11: (15625, 31250)    # Excessive overshoot
}


class TADataImporter:
    """Import TA distribution data from CSV into SQLite database."""

    def __init__(self, db_path: str = None):
        """
        Initialize TA data importer.

        Args:
            db_path: Path to SQLite database (default: data/lz_network.db)
        """
        if db_path is None:
            # Default to data/lz_network.db relative to project root
            import os
            self.db_path = os.path.join(
                os.path.dirname(__file__), "..", "data", "lz_network.db"
            )
        else:
            self.db_path = db_path

        logger.info(f"TA Data Importer initialized with database: {self.db_path}")

    def import_ta_csv(self, csv_path: Path) -> Dict[str, int]:
        """
        Import TA data from CSV file.

        Expected CSV columns:
        - Date
        - eNodeB Name
        - Cell FDD TDD Indication
        - Cell Name
        - LocalCell Id
        - eNodeB Function Name
        - Integrity
        - L.RA.TA.UE.Index0 through L.RA.TA.UE.Index11
        - RACH Setup Success Rate(%)

        Args:
            csv_path: Path to TA CSV file

        Returns:
            Summary dict: {"records_imported": N, "sites": N, "cells": N}
        """
        logger.info(f"Importing TA data from {csv_path}")

        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Parse CSV
        rows = self._parse_csv(csv_path)
        logger.info(f"Parsed {len(rows)} TA records from CSV")

        # Process and insert into database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        records_imported = 0
        records_skipped = 0
        sites_seen = set()
        cells_seen = set()

        for row_num, row in enumerate(rows, start=2):  # Start at 2 (header is row 1)
            try:
                # Extract and validate required fields
                date_str = row.get("Date", "").strip()
                site_name = row.get("eNodeB Name", "").strip()
                cell_id_str = row.get("LocalCell Id", "").strip()

                if not date_str or not site_name or not cell_id_str:
                    logger.debug(f"Row {row_num}: Missing required fields, skipping")
                    records_skipped += 1
                    continue

                # Parse date
                timestamp = self._parse_date(date_str)
                if not timestamp:
                    logger.warning(f"Row {row_num}: Invalid date format '{date_str}', skipping")
                    records_skipped += 1
                    continue

                # Parse cell ID
                try:
                    cell_id = int(cell_id_str)
                except ValueError:
                    logger.warning(f"Row {row_num}: Invalid cell ID '{cell_id_str}', skipping")
                    records_skipped += 1
                    continue

                # Parse integrity (e.g., "95%" -> 95.0 or "95.5" -> 95.5)
                integrity_str = row.get("Integrity", "100").strip()
                try:
                    integrity = float(integrity_str.replace("%", ""))
                except (ValueError, AttributeError):
                    integrity = 100.0

                # Parse RACH (decimal format: 0.4281 -> 42.81%)
                rach_str = row.get("RACH Setup Success Rate(%)", "").strip()
                try:
                    rach_decimal = float(rach_str)
                    # If value is < 1, assume it's decimal format (0.85 = 85%)
                    # If value is > 1, assume it's already percentage (95.5 = 95.5%)
                    rach = rach_decimal * 100 if rach_decimal < 1 else rach_decimal
                except (ValueError, TypeError):
                    rach = None

                # Extract TA indices (UE counts per distance bin)
                ta_values = []
                for i in range(12):
                    col_name = f"L.RA.TA.UE.Index{i}"
                    val_str = row.get(col_name, "0").strip()
                    try:
                        ta_values.append(int(val_str) if val_str else 0)
                    except ValueError:
                        logger.warning(f"Row {row_num}: Invalid TA value for {col_name}: '{val_str}', using 0")
                        ta_values.append(0)

                # Calculate total UEs
                total_ues = sum(ta_values)
                if total_ues == 0:
                    # Skip records with no UEs (empty data)
                    logger.debug(f"Row {row_num}: No UEs detected (all TA indices are 0), skipping")
                    records_skipped += 1
                    continue

                # Calculate weighted average TA index
                avg_ta = sum(i * count for i, count in enumerate(ta_values)) / total_ues

                # Calculate overshoot percentage (Index 0, 10, 11)
                overshoot = (ta_values[0] + ta_values[10] + ta_values[11]) / total_ues * 100

                # Calculate cell edge percentage (Index 9, 10, 11)
                cell_edge = (ta_values[9] + ta_values[10] + ta_values[11]) / total_ues * 100

                # Insert into database
                cursor.execute("""
                    INSERT INTO timing_advance_data (
                        timestamp, site_name, cell_id,
                        ta_index_0, ta_index_1, ta_index_2, ta_index_3,
                        ta_index_4, ta_index_5, ta_index_6, ta_index_7,
                        ta_index_8, ta_index_9, ta_index_10, ta_index_11,
                        total_ues, avg_ta_index, overshoot_percentage, cell_edge_percentage,
                        integrity, rach_success_rate, data_source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, site_name, cell_id,
                    ta_values[0], ta_values[1], ta_values[2], ta_values[3],
                    ta_values[4], ta_values[5], ta_values[6], ta_values[7],
                    ta_values[8], ta_values[9], ta_values[10], ta_values[11],
                    total_ues, avg_ta, overshoot, cell_edge,
                    integrity, rach, "csv_import"
                ))

                records_imported += 1
                sites_seen.add(site_name)
                cells_seen.add(f"{site_name}_cell_{cell_id}")

            except Exception as e:
                logger.error(f"Row {row_num}: Error processing row: {e}")
                records_skipped += 1
                continue

        conn.commit()
        conn.close()

        logger.info(f"✅ TA import complete:")
        logger.info(f"   Records imported: {records_imported}")
        logger.info(f"   Records skipped: {records_skipped}")
        logger.info(f"   Sites: {len(sites_seen)}")
        logger.info(f"   Cells: {len(cells_seen)}")

        return {
            "records_imported": records_imported,
            "records_skipped": records_skipped,
            "sites": len(sites_seen),
            "cells": len(cells_seen),
            "site_names": list(sites_seen)
        }

    def _parse_csv(self, csv_path: Path) -> List[Dict[str, str]]:
        """
        Parse CSV with UTF-8-sig encoding (handles BOM).

        Args:
            csv_path: Path to CSV file

        Returns:
            List of dictionaries (one per row)
        """
        rows = []
        try:
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
        except UnicodeDecodeError:
            # Fallback to latin-1 encoding if UTF-8 fails
            logger.warning("UTF-8 decoding failed, trying latin-1 encoding")
            with open(csv_path, "r", encoding="latin-1") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)

        return rows

    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse date string to ISO format (YYYY-MM-DD HH:MM:SS).

        Supports multiple formats:
        - YYYY-MM-DD
        - DD/MM/YYYY
        - MM/DD/YYYY
        - YYYY/MM/DD

        Args:
            date_str: Date string from CSV

        Returns:
            ISO formatted datetime string or None if parsing fails
        """
        # Try multiple date formats
        date_formats = [
            "%Y-%m-%d",      # 2025-09-01
            "%d/%m/%Y",      # 01/09/2025
            "%m/%d/%Y",      # 09/01/2025
            "%Y/%m/%d",      # 2025/09/01
            "%Y-%m-%d %H:%M:%S",  # With time
            "%d/%m/%Y %H:%M:%S"
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue

        # If all formats fail, return None
        return None

    def validate_import(self) -> Dict[str, Any]:
        """
        Validate the imported TA data.

        Checks:
        - Total records in database
        - Number of unique sites
        - Date range coverage
        - Data quality issues

        Returns:
            Validation summary dictionary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total records
        cursor.execute("SELECT COUNT(*) FROM timing_advance_data")
        total_records = cursor.fetchone()[0]

        # Unique sites
        cursor.execute("SELECT COUNT(DISTINCT site_name) FROM timing_advance_data")
        unique_sites = cursor.fetchone()[0]

        # Date range
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp)
            FROM timing_advance_data
        """)
        min_date, max_date = cursor.fetchone()

        # Sites list
        cursor.execute("SELECT DISTINCT site_name FROM timing_advance_data ORDER BY site_name")
        sites = [row[0] for row in cursor.fetchall()]

        # Check for data quality issues
        cursor.execute("""
            SELECT COUNT(*) FROM timing_advance_data
            WHERE overshoot_percentage > 15
        """)
        high_overshoot_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM timing_advance_data
            WHERE cell_edge_percentage > 25
        """)
        high_cell_edge_count = cursor.fetchone()[0]

        conn.close()

        return {
            "total_records": total_records,
            "unique_sites": unique_sites,
            "sites": sites,
            "date_range": {
                "min": min_date,
                "max": max_date
            },
            "data_quality": {
                "high_overshoot_records": high_overshoot_count,
                "high_cell_edge_records": high_cell_edge_count
            }
        }


def run_ta_import():
    """
    Standalone script to import TA data.

    Usage:
        python -m tools.ta_data_importer

    Or from Python:
        from tools.ta_data_importer import run_ta_import
        run_ta_import()
    """
    import os
    from tools.sql_tools import create_ta_data_table

    print("=" * 80)
    print("LZ Network Optimizer - TA Data Importer")
    print("=" * 80)
    print()

    # Step 1: Create table if it doesn't exist
    print("Step 1: Creating timing_advance_data table...")
    try:
        create_ta_data_table()
        print("✅ Table created/verified successfully")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return

    # Step 2: Locate CSV file
    print("\nStep 2: Locating TA CSV file...")
    csv_path = Path("lz-network-optimizer/data/Timing Advance (L.RA.TA)_Query_Result_Sep-Nov2025_Bindura Cluster.csv")

    # Try alternative path if first doesn't exist
    if not csv_path.exists():
        csv_path = Path("data/Timing Advance (L.RA.TA)_Query_Result_Sep-Nov2025_Bindura Cluster.csv")

    if not csv_path.exists():
        print(f"❌ CSV file not found at: {csv_path}")
        print("   Please ensure the TA CSV file is in the data/ directory")
        return

    print(f"✅ Found CSV file: {csv_path}")
    print(f"   File size: {csv_path.stat().st_size:,} bytes")

    # Step 3: Import data
    print("\nStep 3: Importing TA data...")
    importer = TADataImporter()

    try:
        result = importer.import_ta_csv(csv_path)

        print("\n" + "=" * 80)
        print("✅ TA Data Import Complete!")
        print("=" * 80)
        print(f"  Records imported: {result['records_imported']}")
        print(f"  Records skipped:  {result['records_skipped']}")
        print(f"  Sites discovered: {result['sites']}")
        print(f"  Cells discovered: {result['cells']}")
        print(f"\n  Sites:")
        for site in result['site_names']:
            print(f"    - {site}")

        # Step 4: Validate import
        print("\nStep 4: Validating imported data...")
        validation = importer.validate_import()

        print(f"\n  Total records in DB: {validation['total_records']}")
        print(f"  Date range: {validation['date_range']['min']} to {validation['date_range']['max']}")
        print(f"\n  Data Quality:")
        print(f"    High overshoot records: {validation['data_quality']['high_overshoot_records']}")
        print(f"    High cell edge records: {validation['data_quality']['high_cell_edge_records']}")

        print("\n" + "=" * 80)
        print("✅ Import and validation successful!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    run_ta_import()
