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
    Get list of all unique sites from database (Option B: Site-level aggregation).

    Returns 4 unique sites without cell duplication.

    Returns:
        List of dicts with site information
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT site_name
            FROM kpi_data
            ORDER BY site_name
        """)

        sites = []
        for row in cursor.fetchall():
            sites.append({
                "site_name": row["site_name"]
            })

        conn.close()
        return sites

    except Exception as e:
        logger.error(f"Error getting sites: {e}")
        return []


def get_site_cell_count(site_name: str) -> int:
    """
    Get number of cells for a site.

    Args:
        site_name: Name of the site

    Returns:
        Number of cells (typically 6)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(DISTINCT cell_id) as count
            FROM kpi_data
            WHERE site_name = ?
        """, (site_name,))

        row = cursor.fetchone()
        conn.close()

        return row["count"] if row else 0

    except Exception as e:
        logger.error(f"Error getting cell count for {site_name}: {e}")
        return 0


def get_site_info(site_name: str) -> Optional[Dict[str, any]]:
    """
    Get detailed information for a specific site (aggregated across all cells).

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
            SELECT site_name, timestamp
            FROM kpi_data
            WHERE site_name = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (site_name,))

        row = cursor.fetchone()

        if row:
            # Get cell count
            cell_count = get_site_cell_count(site_name)

            conn.close()

            # Parse location from site name (e.g., "MSH0013-Bindura-Zaoga" -> "Bindura")
            location = site_name.split("-")[1] if "-" in site_name else "Unknown"

            return {
                "site_name": row["site_name"],
                "location": location,
                "cell_count": cell_count,
                "cell_id": 1,  # Use cell 1 as representative for workflow
                "status": "🟢 Live",  # Could be enhanced with actual status check
                "last_updated": row["timestamp"]
            }

        conn.close()
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
        Dict with parameter values or None (returns defaults if no parameter_changes exist)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if parameter_changes table has data for this site
        cursor.execute("""
            SELECT
                parameter_name,
                new_value,
                timestamp
            FROM parameter_changes
            WHERE site_name = ?
            ORDER BY timestamp DESC
            LIMIT 5
        """, (site_name,))

        rows = cursor.fetchall()
        conn.close()

        if rows:
            # Build parameter dict from parameter_changes
            params = {
                "reference_signal_power_pdschcfg": -180,
                "a3_event_offset": 3,
                "t310_timer": 1000,
                "p0_nominal_pusch": -96,
                "pdcch_aggregation_level": 4,
                "last_modified": None
            }

            for row in rows:
                param_name = row["parameter_name"]
                if param_name in params:
                    params[param_name] = float(row["new_value"]) if row["new_value"] else params[param_name]
                    if not params["last_modified"]:
                        params["last_modified"] = row["timestamp"]

            return params

        # No parameter changes found - return defaults
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
        # Return defaults on error
        return {
            "reference_signal_power_pdschcfg": -180,
            "a3_event_offset": 3,
            "t310_timer": 1000,
            "p0_nominal_pusch": -96,
            "pdcch_aggregation_level": 4,
            "last_modified": None
        }


def get_site_kpis(site_name: str) -> Optional[Dict[str, float]]:
    """
    Get latest aggregated KPI values for a site (averaged across all cells).

    Args:
        site_name: Name of the site

    Returns:
        Dict with aggregated KPI values or None
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the latest timestamp for this site
        cursor.execute("""
            SELECT MAX(timestamp) as latest_timestamp
            FROM kpi_data
            WHERE site_name = ?
        """, (site_name,))

        timestamp_row = cursor.fetchone()
        if not timestamp_row or not timestamp_row["latest_timestamp"]:
            conn.close()
            return None

        latest_timestamp = timestamp_row["latest_timestamp"]

        # Get aggregated KPIs across all cells for the latest timestamp
        cursor.execute("""
            SELECT
                AVG(network_access_success) as network_access_success,
                AVG(download_speed) as download_speed,
                AVG(download_quality) as download_quality,
                AVG(upload_speed) as upload_speed,
                AVG(upload_quality) as upload_quality,
                AVG(control_channel_load) as control_channel_load,
                AVG(feedback_channel_load) as feedback_channel_load,
                MAX(timestamp) as timestamp
            FROM kpi_data
            WHERE site_name = ? AND timestamp = ?
            GROUP BY site_name
        """, (site_name, latest_timestamp))

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
    Get historical KPI data for charting (aggregated across all cells).

    Args:
        site_name: Name of the site
        kpi_name: Name of the KPI column
        days: Number of days of history

    Returns:
        List of (date, value) tuples with averaged values across all cells
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Aggregate across all cells per day
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
    Get recent optimization activity log (from optimization_history table).

    Args:
        limit: Number of recent activities to return

    Returns:
        List of activity records mapped to UI format
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query optimization_history table with actual schema
        cursor.execute("""
            SELECT
                site_name,
                cell_id,
                timestamp,
                kpi_issue,
                trigger_reason,
                parameters_changed,
                success,
                weighted_improvement
            FROM optimization_history
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        activities = []
        for row in cursor.fetchall():
            # Map actual schema to UI expected format
            status = "success" if row["success"] else "rejected"
            changes = row["parameters_changed"] if row["parameters_changed"] else "No changes"
            result = f"+{row['weighted_improvement']:.1f}% improvement" if row["weighted_improvement"] else "N/A"

            activities.append({
                "site_name": row["site_name"],
                "timestamp": row["timestamp"],
                "action_type": "optimization",
                "description": row["kpi_issue"] or row["trigger_reason"] or "Network optimization",
                "changes": changes,
                "result": result,
                "status": status
            })

        conn.close()
        return activities

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
    import socket

    status = {}

    # Check NVIDIA API key
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    status["nvidia_api"] = "✅ Connected" if nvidia_key else "❌ Not configured"

    # Check Huawei API (test actual connection)
    huawei_url = os.getenv("HUAWEI_API_URL")
    huawei_user = os.getenv("HUAWEI_USERNAME")

    if huawei_url and huawei_user:
        try:
            # Try to test API client initialization
            from network.huawei_api_client import HuaweiAPIClient

            config = {
                'base_url': huawei_url,
                'username': huawei_user,
                'password': os.getenv("HUAWEI_PASSWORD"),
                'timeout': 5,  # Quick timeout for UI
                'retry_attempts': 1,
                'retry_delay': 1,
                'ssl_verify': False
            }

            # Test TCP connection to API endpoint
            from urllib.parse import urlparse
            parsed_url = urlparse(huawei_url)
            hostname = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((hostname, port))
            sock.close()

            if result == 0:
                # Connection successful - API is reachable
                status["huawei_api"] = "✅ Connected"
            else:
                # Cannot connect - fallback to DB
                status["huawei_api"] = "⚠️ Fallback to DB"
        except Exception as e:
            # Error testing connection - fallback to DB
            status["huawei_api"] = "⚠️ Fallback to DB"
    else:
        status["huawei_api"] = "❌ Not configured"

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
