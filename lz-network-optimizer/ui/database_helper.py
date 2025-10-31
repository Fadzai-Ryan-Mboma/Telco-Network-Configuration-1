"""
Liquid Zimbabwe 4G Network Optimizer - UI Database Helper
Purpose: Database query functions for Streamlit UI
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Database paths
DB_PATH = Path(__file__).parent.parent / "data" / "lz_network.db"
HISTORICAL_DB_PATH = Path(__file__).parent.parent / "data" / "liquid_zimbabwe.db"


def get_db_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Get database connection."""
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise


def get_all_sites() -> List[Dict[str, str]]:
    """
    Get list of all sites from database.

    Returns:
        List of dicts with site information
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT site_name, cell_id
            FROM kpi_data
            ORDER BY site_name
        """)

        sites = []
        for row in cursor.fetchall():
            sites.append({
                "site_name": row["site_name"],
                "cell_id": row["cell_id"]
            })

        conn.close()
        return sites

    except Exception as e:
        logger.error(f"Error getting sites: {e}")
        return []


def get_site_info(site_name: str) -> Optional[Dict[str, any]]:
    """
    Get detailed information for a specific site.

    Args:
        site_name: Name of the site

    Returns:
        Dict with site information or None
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get latest KPI record for this site
        cursor.execute("""
            SELECT site_name, cell_id, timestamp
            FROM kpi_data
            WHERE site_name = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (site_name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            # Parse location from site name (e.g., "MSH0013-Bindura-Zaoga" -> "Bindura")
            location = site_name.split("-")[1] if "-" in site_name else "Unknown"

            return {
                "site_name": row["site_name"],
                "location": location,
                "cell_id": row["cell_id"],
                "status": "🟢 Live",  # Could be enhanced with actual status check
                "last_updated": row["timestamp"]
            }
        return None

    except Exception as e:
        logger.error(f"Error getting site info for {site_name}: {e}")
        return None


def get_site_parameters(site_name: str) -> Optional[Dict[str, any]]:
    """
    Get current parameter values for a site.

    Args:
        site_name: Name of the site

    Returns:
        Dict with parameter values or None
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get latest parameters from parameter_history table
        cursor.execute("""
            SELECT
                reference_signal_power_pdschcfg,
                a3_event_offset,
                t310_timer,
                p0_nominal_pusch,
                pdcch_aggregation_level,
                timestamp
            FROM parameter_history
            WHERE site_name = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (site_name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "reference_signal_power_pdschcfg": row["reference_signal_power_pdschcfg"],
                "a3_event_offset": row["a3_event_offset"],
                "t310_timer": row["t310_timer"],
                "p0_nominal_pusch": row["p0_nominal_pusch"],
                "pdcch_aggregation_level": row["pdcch_aggregation_level"],
                "last_modified": row["timestamp"]
            }

        # If no parameters found, return defaults
        return {
            "reference_signal_power_pdschcfg": -180,
            "a3_event_offset": 3,
            "t310_timer": 1000,
            "p0_nominal_pusch": -96,
            "pdcch_aggregation_level": 4,
            "last_modified": None
        }

    except Exception as e:
        logger.error(f"Error getting parameters for {site_name}: {e}")
        return None


def get_site_kpis(site_name: str) -> Optional[Dict[str, float]]:
    """
    Get latest KPI values for a site.

    Args:
        site_name: Name of the site

    Returns:
        Dict with KPI values or None
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                network_access_success,
                download_speed,
                download_quality,
                upload_speed,
                upload_quality,
                control_channel_load,
                feedback_channel_load,
                timestamp
            FROM kpi_data
            WHERE site_name = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (site_name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "network_access_success": row["network_access_success"],
                "download_speed": row["download_speed"],
                "download_quality": row["download_quality"],
                "upload_speed": row["upload_speed"],
                "upload_quality": row["upload_quality"],
                "control_channel_load": row["control_channel_load"],
                "feedback_channel_load": row["feedback_channel_load"],
                "timestamp": row["timestamp"]
            }
        return None

    except Exception as e:
        logger.error(f"Error getting KPIs for {site_name}: {e}")
        return None


def get_kpi_history(site_name: str, kpi_name: str, days: int = 7) -> List[Tuple[str, float]]:
    """
    Get historical KPI data for charting.

    Args:
        site_name: Name of the site
        kpi_name: Name of the KPI column
        days: Number of days of history

    Returns:
        List of (date, value) tuples
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query = f"""
            SELECT DATE(timestamp) as date, AVG({kpi_name}) as value
            FROM kpi_data
            WHERE site_name = ? AND timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        """

        cursor.execute(query, (site_name, start_date.isoformat()))

        history = []
        for row in cursor.fetchall():
            history.append((row["date"], row["value"]))

        conn.close()
        return history

    except Exception as e:
        logger.error(f"Error getting KPI history for {site_name}, {kpi_name}: {e}")
        return []


def get_kpi_threshold(kpi_name: str) -> float:
    """
    Get threshold value for a KPI.

    Args:
        kpi_name: Name of the KPI

    Returns:
        Threshold value
    """
    thresholds = {
        "network_access_success": 95.0,
        "download_speed": 50.0,
        "upload_speed": 20.0,
        "download_quality": 95.0,
        "upload_quality": 95.0,
        "control_channel_load": 80.0,
        "feedback_channel_load": 80.0
    }
    return thresholds.get(kpi_name, 0.0)


def get_recent_activity(limit: int = 10) -> List[Dict[str, any]]:
    """
    Get recent optimization activity log.

    Args:
        limit: Number of recent activities to return

    Returns:
        List of activity records
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query optimization_history table (if it exists)
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='optimization_history'
        """)

        if cursor.fetchone():
            cursor.execute("""
                SELECT
                    site_name,
                    timestamp,
                    action_type,
                    description,
                    changes,
                    result,
                    status
                FROM optimization_history
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            activities = []
            for row in cursor.fetchall():
                activities.append({
                    "site_name": row["site_name"],
                    "timestamp": row["timestamp"],
                    "action_type": row["action_type"],
                    "description": row["description"],
                    "changes": row["changes"],
                    "result": row["result"],
                    "status": row["status"]
                })

            conn.close()
            return activities

        # If table doesn't exist, return empty list
        conn.close()
        return []

    except Exception as e:
        logger.error(f"Error getting activity log: {e}")
        return []


def check_api_status() -> Dict[str, str]:
    """
    Check status of APIs and database.

    Returns:
        Dict with status of each component
    """
    import os

    status = {}

    # Check NVIDIA API key
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    status["nvidia_api"] = "✅ Connected" if nvidia_key else "❌ Not configured"

    # Check Huawei API (would need actual ping, for now check env vars)
    huawei_url = os.getenv("HUAWEI_API_URL")
    huawei_user = os.getenv("HUAWEI_USERNAME")
    if huawei_url and huawei_user:
        status["huawei_api"] = "⚠️ Fallback to DB"  # Conservative default
    else:
        status["huawei_api"] = "⚠️ Fallback to DB"

    # Check database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM kpi_data")
        row = cursor.fetchone()
        record_count = row["count"] if row else 0
        conn.close()
        status["database"] = f"✅ Online ({record_count} records)"
    except:
        status["database"] = "❌ Error"

    return status


def get_database_stats() -> Dict[str, int]:
    """
    Get database statistics.

    Returns:
        Dict with counts of sites, records, etc.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Count total sites
        cursor.execute("SELECT COUNT(DISTINCT site_name) as count FROM kpi_data")
        site_count = cursor.fetchone()["count"]

        # Count total records
        cursor.execute("SELECT COUNT(*) as count FROM kpi_data")
        record_count = cursor.fetchone()["count"]

        # Get latest timestamp
        cursor.execute("SELECT MAX(timestamp) as latest FROM kpi_data")
        latest = cursor.fetchone()["latest"]

        conn.close()

        return {
            "total_sites": site_count,
            "total_records": record_count,
            "latest_update": latest
        }

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {
            "total_sites": 0,
            "total_records": 0,
            "latest_update": None
        }
