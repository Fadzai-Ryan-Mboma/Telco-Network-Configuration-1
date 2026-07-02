"""
Liquid Zimbabwe 4G Network Optimizer - UI Database Helper
Purpose: Database query functions for Streamlit UI
"""

import sqlite3
import logging
import os
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

        # Anchor the history window to the newest KPI record we actually have
        # so archived demo datasets still produce charts.
        cursor.execute("""
            SELECT MAX(timestamp) as latest_timestamp
            FROM kpi_data
            WHERE site_name = ?
        """, (site_name,))

        latest_row = cursor.fetchone()
        if not latest_row or not latest_row["latest_timestamp"]:
            conn.close()
            return []

        end_date = datetime.fromisoformat(str(latest_row["latest_timestamp"]))
        start_date = end_date - timedelta(days=days)

        # Aggregate across all cells per day
        query = f"""
            SELECT DATE(timestamp) as date, AVG({kpi_name}) as value
            FROM kpi_data
            WHERE site_name = ? AND timestamp >= ? AND timestamp <= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        """

        cursor.execute(query, (
            site_name,
            start_date.isoformat(sep=" "),
            end_date.isoformat(sep=" "),
        ))

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
    Get operating average value for a KPI based on actual network data.

    Args:
        kpi_name: Name of the KPI

    Returns:
        Operating average value
    """
    # Operating averages based on actual Bindura Cluster network data (Sept-Nov 2025)
    thresholds = {
        "network_access_success": 90.0,   # Avg: 92%, target slightly below
        "download_speed": 5.0,            # Avg: 6.56 Mbps
        "upload_speed": 3.0,              # Avg: 3.93 Mbps
        "download_quality": 80.0,         # Avg: 83.72%
        "upload_quality": 92.0,           # Avg: 93.54%
        "control_channel_load": 70.0,     # Avg: 32.46%, max: 61%
        "feedback_channel_load": 20.0     # Avg: 5%, max: 23%
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

        # Also get optimization queries (approved, rejected, incomplete)
        cursor.execute("""
            SELECT
                site_name,
                timestamp,
                user_query,
                status,
                recommendation_summary
            FROM optimization_queries
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        for row in cursor.fetchall():
            status_map = {
                "approved": "success",
                "rejected": "rejected",
                "incomplete": "detected"
            }
            activities.append({
                "site_name": row["site_name"],
                "timestamp": row["timestamp"],
                "action_type": "query",
                "description": f"Query: {row['user_query']}",
                "changes": row["recommendation_summary"] or "No recommendation",
                "result": row["status"].title(),
                "status": status_map.get(row["status"], "info")
            })
        
        # Sort all activities by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        conn.close()
        return activities[:limit]

    except Exception as e:
        logger.error(f"Error getting activity log: {e}")
        return []


def check_api_status(site_name: str = None) -> Dict[str, str]:
    """
    Check status of APIs, Network Elements, and database.

    Args:
        site_name: Optional site name to check NE connectivity
        
    Returns:
        Dict with status of each component:
        - api: API Connected / API Unreachable
        - ne: NEs Connected / NEs Unreachable  
        - db: DB Connected / DB Unreachable
    """
    import os
    import socket

    status = {}

    # 1. Check Huawei API connectivity
    huawei_url = os.getenv("HUAWEI_API_URL")
    huawei_user = os.getenv("HUAWEI_USERNAME")
    api_reachable = False

    if huawei_url and huawei_user:
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(huawei_url)
            hostname = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((hostname, port))
            sock.close()

            if result == 0:
                api_reachable = True
                status["api"] = "✅ API Connected"
            else:
                status["api"] = "❌ API Unreachable"
        except Exception as e:
            status["api"] = "❌ API Unreachable"
    else:
        status["api"] = "❌ API Unreachable"

    # 2. Check Network Element (NE) connectivity - if API is connected, NEs are connected
    if api_reachable:
        status["ne"] = "✅ NEs Connected"
    else:
        status["ne"] = "⚠️ NEs Unknown"

    # 3. Check database connectivity
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM kpi_data")
        row = cursor.fetchone()
        conn.close()
        status["db"] = "✅ DB Connected"
    except:
        status["db"] = "❌ DB Unreachable"

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


# ============================================================================
# LIVE PARAMETER FETCHING FROM HUAWEI API
# ============================================================================

def get_live_parameters(site_name: str, cell_id: int = 1) -> Optional[Dict[str, any]]:
    """
    Get LIVE parameter values from Huawei iMaster MAE API.
    
    This queries the actual network equipment for current parameter values
    instead of using database defaults.
    
    Args:
        site_name: Name of the site (e.g., 'MSH-0014-Chipadze')
        cell_id: Cell ID to query (default: 1, or 0 for global params)
    
    Returns:
        Dict with parameter values and metadata, or None on error
    """
    try:
        # Import tools (delayed import to avoid circular imports)
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from tools.huawei_tools import query_huawei_parameter_site
        from domain.mml_commands import format_command_response
        
        params = {
            "reference_signal_power_pdschcfg": None,
            "a3_event_offset": None,
            "t310_timer": None,
            "p0_nominal_pusch": None,
            "pdcch_aggregation_level": None,
            "last_modified": datetime.now().isoformat(),
            "data_source": "live_api",
            "errors": [],
            "site_offline": False  # Flag to indicate if NE is not connected
        }
        
        param_names = [
            "reference_signal_power_pdschcfg",
            "a3_event_offset",
            "t310_timer",
            "p0_nominal_pusch",
            "pdcch_aggregation_level"
        ]
        
        for param_name in param_names:
            try:
                result = query_huawei_parameter_site.invoke({
                    "parameter_name": param_name,
                    "site_name": site_name
                })
                
                if result and "ERROR" not in result:
                    # Parse the value from the result string
                    value = _parse_parameter_value(result, param_name)
                    params[param_name] = value
                else:
                    params["errors"].append(f"{param_name}: {result}")
                    # Check if site/NE is not connected
                    if result and ("not connected" in result.lower() or "ne is not connected" in result.lower()):
                        params["site_offline"] = True
                    
            except Exception as e:
                logger.warning(f"Failed to query {param_name}: {e}")
                params["errors"].append(f"{param_name}: {str(e)}")
        
        return params
        
    except Exception as e:
        logger.error(f"Error getting live parameters for {site_name}: {e}")
        return None


def _parse_parameter_value(result_str: str, param_name: str) -> any:
    """
    Parse parameter value from query result string.
    
    Args:
        result_str: Raw result string from query_huawei_parameter_site
        param_name: Name of the parameter
    
    Returns:
        Parsed value (numeric or string)
    """
    try:
        # Handle global parameters (single value)
        if "global" in result_str.lower():
            # Extract value after the colon, e.g., "Parameter x for site: 3dB  (global)"
            match = re.search(r':\s*([^\s(]+)', result_str)
            if match:
                value = match.group(1).strip()
                # Try to convert to number if possible
                return _convert_value(value, param_name)
        
        # Handle cell-specific parameters - get Cell 1 value as representative
        cell_match = re.search(r'Cell 1:\s*([^\n,]+)', result_str)
        if cell_match:
            value = cell_match.group(1).strip()
            return _convert_value(value, param_name)
        
        # Fallback: find any numeric value
        num_match = re.search(r'[-+]?\d+\.?\d*', result_str)
        if num_match:
            return float(num_match.group())
        
        return result_str
        
    except Exception as e:
        logger.warning(f"Failed to parse value for {param_name}: {e}")
        return result_str


def _convert_value(value_str: str, param_name: str) -> any:
    """
    Convert value string to appropriate type based on parameter.
    
    Args:
        value_str: Value string (may include units like 'dB', 'ms')
        param_name: Parameter name for context
    
    Returns:
        Converted value
    """
    # Remove common units for numeric conversion
    clean_value = value_str.replace('dB', '').replace('ms', '').replace('dBm', '').strip()
    
    # Handle special cases
    if param_name == "a3_event_offset":
        # Keep as string with unit, or extract number
        try:
            return int(clean_value)
        except:
            return value_str
            
    elif param_name == "t310_timer":
        # Convert ms value to integer
        try:
            return int(clean_value)
        except:
            return value_str
            
    elif param_name == "pdcch_aggregation_level":
        # Keep as string (e.g., "CONGREG_LV4")
        return value_str
    
    # Default: try numeric conversion
    try:
        if '.' in clean_value:
            return float(clean_value)
        return int(clean_value)
    except:
        return value_str


def get_site_parameters_with_live(site_name: str, use_live: bool = False) -> Optional[Dict[str, any]]:
    """
    Get parameter values with option to use live API or database.
    
    Args:
        site_name: Name of the site
        use_live: If True, query live API; if False, use database/defaults
    
    Returns:
        Dict with parameter values
    """
    if use_live:
        live_params = get_live_parameters(site_name)
        if live_params and not live_params.get("errors"):
            return live_params
        
        # If live failed, log and fall back to database
        if live_params:
            logger.warning(f"Live query had errors: {live_params.get('errors')}")
    
    # Fall back to database/defaults
    return get_site_parameters(site_name)


# ============================================================================
# OPTIMIZATION QUERY LOGGING
# ============================================================================

def init_optimization_queries_table():
    """Create optimization_queries table if it doesn't exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                site_name TEXT NOT NULL,
                user_query TEXT NOT NULL,
                status TEXT DEFAULT 'incomplete',  -- 'incomplete', 'approved', 'rejected'
                recommendation_summary TEXT,
                kpi_issue TEXT,
                parameters_recommended TEXT,       -- JSON of recommended changes
                validation_status TEXT,
                execution_result TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queries_timestamp 
            ON optimization_queries(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queries_site 
            ON optimization_queries(site_name)
        """)
        
        conn.commit()
        conn.close()
        logger.info("optimization_queries table initialized")
        
    except Exception as e:
        logger.error(f"Error creating optimization_queries table: {e}")


def log_optimization_query(
    site_name: str,
    user_query: str,
    status: str = "incomplete",
    recommendation_summary: str = None,
    kpi_issue: str = None,
    parameters_recommended: str = None,
    validation_status: str = None,
    execution_result: str = None
) -> int:
    """
    Log an optimization query to the database.
    
    Args:
        site_name: Name of the site
        user_query: The user's optimization query
        status: 'incomplete', 'approved', or 'rejected'
        recommendation_summary: Summary of the recommendation
        kpi_issue: Detected KPI issue
        parameters_recommended: JSON string of recommended parameters
        validation_status: Validation result
        execution_result: Execution result
    
    Returns:
        ID of the inserted record, or -1 on error
    """
    try:
        # Ensure table exists
        init_optimization_queries_table()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO optimization_queries (
                site_name, user_query, status, recommendation_summary,
                kpi_issue, parameters_recommended, validation_status, execution_result
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            site_name, user_query, status, recommendation_summary,
            kpi_issue, parameters_recommended, validation_status, execution_result
        ))
        
        query_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Logged optimization query {query_id}: {site_name} - {status}")
        return query_id
        
    except Exception as e:
        logger.error(f"Error logging optimization query: {e}")
        return -1


def update_optimization_query_status(
    query_id: int,
    status: str,
    recommendation_summary: str = None,
    kpi_issue: str = None,
    parameters_recommended: str = None,
    validation_status: str = None,
    execution_result: str = None
):
    """
    Update the status of an existing optimization query.
    
    Args:
        query_id: ID of the query to update
        status: New status ('incomplete', 'approved', 'rejected')
        Other fields: Optional updates to other fields
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build dynamic update query
        updates = ["status = ?"]
        values = [status]
        
        if recommendation_summary is not None:
            updates.append("recommendation_summary = ?")
            values.append(recommendation_summary)
        if kpi_issue is not None:
            updates.append("kpi_issue = ?")
            values.append(kpi_issue)
        if parameters_recommended is not None:
            updates.append("parameters_recommended = ?")
            values.append(parameters_recommended)
        if validation_status is not None:
            updates.append("validation_status = ?")
            values.append(validation_status)
        if execution_result is not None:
            updates.append("execution_result = ?")
            values.append(execution_result)
        
        values.append(query_id)
        
        query = f"UPDATE optimization_queries SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated optimization query {query_id} to status: {status}")
        
    except Exception as e:
        logger.error(f"Error updating optimization query {query_id}: {e}")
