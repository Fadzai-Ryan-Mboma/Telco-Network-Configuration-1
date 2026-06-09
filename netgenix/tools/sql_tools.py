"""
Liquid Zimbabwe 4G Network Optimizer - SQL Database Tools
Purpose: LangChain tools for querying historical and live KPI data from SQLite
Created: 2025-10-30

These tools allow agents to query the unified database for KPI analysis and optimization history.
Pattern follows Nvidia's execute_xapp_sql implementation.
"""

from langchain_core.tools import tool
from typing import Annotated, Optional, Dict, Any
import sqlite3
import pandas as pd
import os
import sys
import logging
import yaml

# Setup logging
logger = logging.getLogger(__name__)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "lz_network.db")


# ============================================================================
# TOOL 1: execute_historical_sql
# ============================================================================

@tool
def execute_historical_sql(
    sql_query: Annotated[str, "The SQL query to execute on historical KPI database"]
) -> str:
    """
    Execute SQL query on the historical KPI database.

    This tool allows querying the unified database containing:
    - kpi_data: Historical and live KPI measurements
    - parameter_changes: Log of all parameter modifications
    - optimization_history: Complete optimization cycle records

    Common queries:
    - Fetch KPIs for a site: SELECT * FROM kpi_data WHERE site_name='Site1' ORDER BY timestamp DESC LIMIT 10
    - Calculate KPI trends: SELECT AVG(download_speed) FROM kpi_data WHERE site_name='Site1' AND timestamp >= date('now', '-7 days')
    - Check recent changes: SELECT * FROM parameter_changes WHERE site_name='Site1' ORDER BY timestamp DESC LIMIT 5
    - View optimization history: SELECT * FROM optimization_history WHERE site_name='Site1' AND success=1

    Available views:
    - latest_kpi_per_site: Most recent KPI for each site
    - recent_parameter_changes: Parameter changes in last 30 days
    - optimization_success_rate: Success rate by site

    Args:
        sql_query: SQL SELECT statement to execute

    Returns:
        String containing formatted query results as table

    Example:
        execute_historical_sql("SELECT site_name, AVG(download_speed) as avg_dl FROM kpi_data GROUP BY site_name")
        Returns: Formatted table with results
    """
    try:
        # Validate query is a SELECT statement (safety check)
        query_upper = sql_query.strip().upper()
        if not query_upper.startswith('SELECT'):
            return "ERROR: Only SELECT queries are allowed. Use modify_huawei_parameter for parameter changes."

        # Prevent dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'INSERT', 'UPDATE']
        if any(keyword in query_upper for keyword in dangerous_keywords):
            return f"ERROR: Query contains dangerous keyword. Only SELECT queries allowed."

        logger.info(f"Executing SQL query: {sql_query}")

        # Check if database exists
        if not os.path.exists(DB_PATH):
            return f"ERROR: Database not found at {DB_PATH}. Run scripts/import_historical_data.py first."

        # Connect and execute query
        conn = sqlite3.connect(DB_PATH)

        try:
            # Execute query
            df = pd.read_sql_query(sql_query, conn)

            # Check if empty result
            if df.empty:
                return "Query returned no results."

            # Format result as string table
            result = df.to_string(index=False, max_rows=100)

            # Add row count
            row_count = len(df)
            result += f"\n\n[{row_count} row(s) returned]"

            return result

        except Exception as query_error:
            logger.error(f"SQL query error: {query_error}")
            return f"ERROR: SQL query failed: {str(query_error)}"

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error executing SQL: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# TOOL 2: execute_lz_kpi_sql
# ============================================================================

@tool
def execute_lz_kpi_sql(
    sql_query: Annotated[str, "The SQL query to execute on LZ KPI database"]
) -> str:
    """
    Execute SQL query specifically focused on KPI data analysis.

    This tool is optimized for querying KPI metrics and trends from the kpi_data table.
    Use this for KPI analytics and comparison queries.

    Table schema (kpi_data):
    - id, timestamp, site_name, cell_id
    - network_access_success (%)
    - download_speed (Mbps)
    - download_quality (%)
    - upload_speed (Mbps)
    - upload_quality (%)
    - control_channel_load (%)
    - feedback_channel_load (%)
    - data_source ('live' or 'historical')

    Common queries:
    - Latest KPIs: SELECT * FROM kpi_data WHERE site_name='MSH0013-Bindura-Zaoga' ORDER BY timestamp DESC LIMIT 1
    - KPI trends: SELECT DATE(timestamp) as date, AVG(download_speed) as avg_dl FROM kpi_data WHERE site_name='Site1' GROUP BY date
    - Compare sites: SELECT site_name, AVG(network_access_success) as avg_access FROM kpi_data GROUP BY site_name
    - Identify issues: SELECT * FROM kpi_data WHERE download_speed < 50 OR network_access_success < 95

    Args:
        sql_query: SQL SELECT statement focused on kpi_data table

    Returns:
        String containing formatted KPI query results

    Example:
        execute_lz_kpi_sql("SELECT site_name, AVG(download_speed), AVG(upload_speed) FROM kpi_data GROUP BY site_name")
        Returns: Average download/upload speeds by site
    """
    try:
        # Validate query is a SELECT statement
        query_upper = sql_query.strip().upper()
        if not query_upper.startswith('SELECT'):
            return "ERROR: Only SELECT queries are allowed for KPI analysis."

        # Prevent dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'INSERT', 'UPDATE']
        if any(keyword in query_upper for keyword in dangerous_keywords):
            return f"ERROR: Query contains dangerous keyword. Only SELECT queries allowed."

        logger.info(f"Executing KPI SQL query: {sql_query}")

        # Check if database exists
        if not os.path.exists(DB_PATH):
            return f"ERROR: Database not found at {DB_PATH}. Run scripts/import_historical_data.py first."

        # Connect and execute query
        conn = sqlite3.connect(DB_PATH)

        try:
            # Execute query
            df = pd.read_sql_query(sql_query, conn)

            # Check if empty result
            if df.empty:
                return "Query returned no KPI data. Check site name and date range."

            # Format result with better readability for KPIs
            result = "KPI Query Results:\n"
            result += "=" * 80 + "\n"
            result += df.to_string(index=False, max_rows=100)
            result += "\n" + "=" * 80

            # Add statistics if numeric columns exist
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_cols) > 0:
                result += "\n\nSummary Statistics:\n"
                for col in numeric_cols:
                    if col != 'id' and col != 'cell_id':  # Skip ID columns
                        avg_val = df[col].mean()
                        min_val = df[col].min()
                        max_val = df[col].max()
                        result += f"  {col}: avg={avg_val:.2f}, min={min_val:.2f}, max={max_val:.2f}\n"

            # Add row count
            row_count = len(df)
            result += f"\n[{row_count} row(s) returned]"

            return result

        except Exception as query_error:
            logger.error(f"KPI SQL query error: {query_error}")
            return f"ERROR: KPI SQL query failed: {str(query_error)}\n\nHint: Check table name is 'kpi_data' and column names are correct."

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error executing KPI SQL: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# Helper Function: Direct KPI Query (Fallback)
# ============================================================================

def get_latest_kpis_direct(site_name: str, cell_id: int = 1) -> Optional[Dict[str, Any]]:
    """
    Direct database query to get latest KPIs for a site.
    This bypasses LLM query generation and serves as a reliable fallback.

    Args:
        site_name: Site name to query
        cell_id: Cell ID (default 1)

    Returns:
        Dictionary with KPI values or None if not found
    """
    try:
        if not os.path.exists(DB_PATH):
            logger.error(f"Database not found at {DB_PATH}")
            return None

        conn = sqlite3.connect(DB_PATH)

        # Use parameterized query to prevent SQL injection
        query = """
        SELECT
            site_name,
            cell_id,
            network_access_success,
            download_speed,
            download_quality,
            upload_speed,
            upload_quality,
            control_channel_load,
            feedback_channel_load,
            data_source,
            timestamp
        FROM kpi_data
        WHERE site_name = ? AND cell_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
        """

        df = pd.read_sql_query(query, conn, params=(site_name, cell_id))
        conn.close()

        if df.empty:
            logger.warning(f"No KPI data found for site {site_name}, cell {cell_id}")
            return None

        # Convert to dictionary
        kpis = df.iloc[0].to_dict()
        logger.info(f"✅ Direct query successful for {site_name}: {len(kpis)} fields retrieved")
        return kpis

    except Exception as e:
        logger.error(f"Direct KPI query error: {e}")
        return None


# ============================================================================
# Helper Function: Get Database Schema
# ============================================================================

def get_database_schema() -> str:
    """
    Get complete database schema for reference.

    Returns:
        String containing table schemas
    """
    try:
        if not os.path.exists(DB_PATH):
            return f"ERROR: Database not found at {DB_PATH}"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()

        schema_info = "Database Schema:\n" + "=" * 80 + "\n\n"

        for table_name in tables:
            table = table_name[0]
            schema_info += f"Table: {table}\n"
            schema_info += "-" * 40 + "\n"

            # Get table schema
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()

            for col in columns:
                col_id, name, type_, notnull, default, pk = col
                schema_info += f"  {name:30} {type_:15}"
                if pk:
                    schema_info += " PRIMARY KEY"
                if notnull:
                    schema_info += " NOT NULL"
                if default:
                    schema_info += f" DEFAULT {default}"
                schema_info += "\n"

            schema_info += "\n"

        conn.close()
        return schema_info

    except Exception as e:
        return f"ERROR: {str(e)}"


# ============================================================================
# Helper Function: Get Sample Queries
# ============================================================================

def get_sample_queries() -> dict:
    """
    Get sample SQL queries for common use cases.

    Returns:
        Dictionary of query examples
    """
    return {
        "latest_kpis_by_site": """
            SELECT site_name, MAX(timestamp) as latest,
                   network_access_success, download_speed, upload_speed
            FROM kpi_data
            GROUP BY site_name
        """,

        "kpi_trends_last_7_days": """
            SELECT DATE(timestamp) as date,
                   AVG(download_speed) as avg_dl_speed,
                   AVG(upload_speed) as avg_ul_speed,
                   AVG(network_access_success) as avg_access
            FROM kpi_data
            WHERE site_name = '{site_name}'
              AND timestamp >= date('now', '-7 days')
            GROUP BY date
            ORDER BY date
        """,

        "sites_below_threshold": """
            SELECT DISTINCT site_name,
                   AVG(download_speed) as avg_dl_speed,
                   AVG(network_access_success) as avg_access
            FROM kpi_data
            WHERE timestamp >= date('now', '-1 day')
            GROUP BY site_name
            HAVING avg_dl_speed < 50 OR avg_access < 95
        """,

        "recent_optimizations": """
            SELECT timestamp, site_name, kpi_issue,
                   weighted_score_before, weighted_score_after,
                   weighted_improvement, success
            FROM optimization_history
            WHERE site_name = '{site_name}'
            ORDER BY timestamp DESC
            LIMIT 10
        """,

        "parameter_change_log": """
            SELECT timestamp, parameter_name,
                   old_value, new_value, reason, success
            FROM parameter_changes
            WHERE site_name = '{site_name}'
            ORDER BY timestamp DESC
            LIMIT 10
        """
    }


# ============================================================================
# TA Data Management Functions
# ============================================================================

def create_ta_data_table():
    """
    Create timing_advance_data table for TA distribution tracking.

    This function creates the database schema for storing Timing Advance (TA)
    distribution data from Huawei Performance Management exports.

    TA Index Distance Ranges (LTE):
        Index 0: 0-78m (overshoot/interference)
        Index 1: 78-156m
        Index 2: 156-312m
        Index 3: 312-547m
        Index 4: 547-781m
        Index 5: 781-1172m
        Index 6: 1172-1563m
        Index 7: 1563-2344m
        Index 8: 2344-3906m
        Index 9: 3906-7813m (cell edge)
        Index 10: 7813-15625m (overshoot)
        Index 11: 15625-31250m (excessive overshoot)

    Returns:
        True if successful, raises exception otherwise
    """
    try:
        if not os.path.exists(DB_PATH):
            # Create database file if it doesn't exist
            logger.warning(f"Database not found at {DB_PATH}, creating new database")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create timing_advance_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timing_advance_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                site_name TEXT NOT NULL,
                cell_id INTEGER NOT NULL,

                -- TA Distribution (UE counts per distance bin)
                ta_index_0 INTEGER DEFAULT 0,   -- 0-78m (overshoot)
                ta_index_1 INTEGER DEFAULT 0,   -- 78-156m
                ta_index_2 INTEGER DEFAULT 0,   -- 156-312m
                ta_index_3 INTEGER DEFAULT 0,   -- 312-547m
                ta_index_4 INTEGER DEFAULT 0,   -- 547-781m
                ta_index_5 INTEGER DEFAULT 0,   -- 781-1172m
                ta_index_6 INTEGER DEFAULT 0,   -- 1172-1563m
                ta_index_7 INTEGER DEFAULT 0,   -- 1563-2344m
                ta_index_8 INTEGER DEFAULT 0,   -- 2344-3906m
                ta_index_9 INTEGER DEFAULT 0,   -- 3906-7813m (cell edge)
                ta_index_10 INTEGER DEFAULT 0,  -- 7813-15625m (overshoot)
                ta_index_11 INTEGER DEFAULT 0,  -- 15625-31250m (excessive)

                -- Calculated Metrics
                total_ues INTEGER,               -- Sum of all TA indices
                avg_ta_index REAL,               -- Weighted average TA index
                overshoot_percentage REAL,       -- (Index0 + Index10 + Index11) / total
                cell_edge_percentage REAL,       -- (Index9 + Index10 + Index11) / total

                -- Additional Data
                integrity REAL,                  -- Data integrity percentage
                rach_success_rate REAL,          -- RACH from TA file

                -- Metadata
                data_source TEXT DEFAULT 'csv_import'
            )
        """)

        # Create indices for query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ta_site_timestamp
            ON timing_advance_data(site_name, timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ta_site_cell
            ON timing_advance_data(site_name, cell_id)
        """)

        conn.commit()
        conn.close()

        logger.info("✅ timing_advance_data table created successfully with indexes")
        return True

    except Exception as e:
        logger.error(f"Error creating timing_advance_data table: {e}")
        raise


@tool
def query_ta_metrics(
    site_name: Annotated[str, "Site identifier"],
    cell_id: Annotated[Optional[int], "Cell ID (None = aggregate all cells)"] = None,
    days: Annotated[int, "Days of history to retrieve"] = 7
) -> str:
    """
    Query TA distribution data for a site/cell.

    This tool retrieves Timing Advance (TA) distribution metrics including:
    - UE count per distance bin (Index 0-11)
    - Overshoot percentage (Index 0, 10, 11)
    - Cell edge percentage (Index 9, 10, 11)
    - Average TA index (typical UE distance)

    Args:
        site_name: Site identifier (e.g., "MSH0013-Bindura-Zaoga")
        cell_id: Optional cell ID (None = aggregate all cells at site)
        days: Days of history to retrieve (default 7)

    Returns:
        String containing formatted TA metrics

    Example:
        query_ta_metrics("MSH0013-Bindura-Zaoga", cell_id=1, days=7)
        Returns: TA distribution data for the past 7 days
    """
    try:
        if not os.path.exists(DB_PATH):
            return f"ERROR: Database not found at {DB_PATH}"

        conn = sqlite3.connect(DB_PATH)

        try:
            if cell_id is not None:
                # Single cell query
                query = """
                    SELECT * FROM timing_advance_data
                    WHERE site_name = ? AND cell_id = ?
                      AND timestamp >= datetime('now', ? || ' days')
                    ORDER BY timestamp DESC
                """
                df = pd.read_sql_query(query, conn, params=(site_name, cell_id, f"-{days}"))

            else:
                # Aggregate across all cells
                query = """
                    SELECT
                        timestamp,
                        site_name,
                        'aggregated' as cell_id,
                        SUM(ta_index_0) as ta_index_0,
                        SUM(ta_index_1) as ta_index_1,
                        SUM(ta_index_2) as ta_index_2,
                        SUM(ta_index_3) as ta_index_3,
                        SUM(ta_index_4) as ta_index_4,
                        SUM(ta_index_5) as ta_index_5,
                        SUM(ta_index_6) as ta_index_6,
                        SUM(ta_index_7) as ta_index_7,
                        SUM(ta_index_8) as ta_index_8,
                        SUM(ta_index_9) as ta_index_9,
                        SUM(ta_index_10) as ta_index_10,
                        SUM(ta_index_11) as ta_index_11,
                        SUM(total_ues) as total_ues,
                        AVG(avg_ta_index) as avg_ta_index,
                        AVG(overshoot_percentage) as overshoot_percentage,
                        AVG(cell_edge_percentage) as cell_edge_percentage,
                        AVG(integrity) as integrity,
                        AVG(rach_success_rate) as rach_success_rate
                    FROM timing_advance_data
                    WHERE site_name = ?
                      AND timestamp >= datetime('now', ? || ' days')
                    GROUP BY timestamp, site_name
                    ORDER BY timestamp DESC
                """
                df = pd.read_sql_query(query, conn, params=(site_name, f"-{days}"))

            conn.close()

            # Check if empty result
            if df.empty:
                return f"No TA data found for site '{site_name}'" + (f" cell {cell_id}" if cell_id else "") + f" in the past {days} days."

            # Format result
            result = "TA Distribution Query Results:\n"
            result += "=" * 100 + "\n"
            result += df.to_string(index=False, max_rows=100)
            result += "\n" + "=" * 100

            # Add summary statistics
            result += "\n\nSummary:\n"
            latest = df.iloc[0]
            result += f"  Latest Timestamp: {latest['timestamp']}\n"
            result += f"  Total UEs: {latest['total_ues']:,}\n"
            result += f"  Avg TA Index: {latest['avg_ta_index']:.2f}\n"
            result += f"  Overshoot %: {latest['overshoot_percentage']:.1f}% "
            result += "⚠️ HIGH\n" if latest['overshoot_percentage'] > 10 else "✓\n"
            result += f"  Cell Edge %: {latest['cell_edge_percentage']:.1f}% "
            result += "⚠️ HIGH\n" if latest['cell_edge_percentage'] > 20 else "✓\n"

            # Add coverage assessment
            if latest['overshoot_percentage'] > 15:
                result += "\n🔴 CRITICAL: High overshoot detected - immediate action required\n"
            elif latest['overshoot_percentage'] > 10:
                result += "\n⚠️ WARNING: Elevated overshoot - downtilt or power reduction recommended\n"

            if latest['cell_edge_percentage'] > 25:
                result += "🔴 CRITICAL: High cell edge loading - power increase required\n"
            elif latest['cell_edge_percentage'] > 20:
                result += "⚠️ WARNING: Elevated cell edge loading - consider power increase\n"

            if latest['avg_ta_index'] < 3:
                result += "⚠️ WARNING: Average distance too close - overshooting likely\n"
            elif latest['avg_ta_index'] > 8:
                result += "⚠️ WARNING: Average distance too far - undershooting or coverage gap\n"

            # Add row count
            row_count = len(df)
            result += f"\n[{row_count} record(s) returned]"

            return result

        except Exception as query_error:
            logger.error(f"TA query error: {query_error}")
            return f"ERROR: TA query failed: {str(query_error)}"

    except Exception as e:
        logger.error(f"Error querying TA metrics: {e}")
        return f"ERROR: {str(e)}"


# ============================================================================
# Helper Function: Get TA Data Direct (Non-Tool)
# ============================================================================

def get_ta_metrics_direct(site_name: str, cell_id: int = None, days: int = 7) -> Optional[list]:
    """
    Direct database query to get TA metrics for a site.
    Returns list of dictionaries with TA data.

    Args:
        site_name: Site identifier
        cell_id: Optional cell ID (None = aggregate)
        days: Days of history

    Returns:
        List of TA data records or None if not found
    """
    try:
        if not os.path.exists(DB_PATH):
            logger.error(f"Database not found at {DB_PATH}")
            return None

        conn = sqlite3.connect(DB_PATH)

        if cell_id is not None:
            query = """
                SELECT * FROM timing_advance_data
                WHERE site_name = ? AND cell_id = ?
                  AND timestamp >= datetime('now', ? || ' days')
                ORDER BY timestamp DESC
            """
            df = pd.read_sql_query(query, conn, params=(site_name, cell_id, f"-{days}"))
        else:
            query = """
                SELECT * FROM timing_advance_data
                WHERE site_name = ?
                  AND timestamp >= datetime('now', ? || ' days')
                ORDER BY timestamp DESC
            """
            df = pd.read_sql_query(query, conn, params=(site_name, f"-{days}"))

        conn.close()

        if df.empty:
            logger.warning(f"No TA data found for site {site_name}")
            return None

        # Convert to list of dictionaries
        ta_data = df.to_dict('records')
        logger.info(f"✅ Retrieved {len(ta_data)} TA records for {site_name}")
        return ta_data

    except Exception as e:
        logger.error(f"Direct TA query error: {e}")
        return None


# ============================================================================
# Tool List for Agent Registration
# ============================================================================

SQL_TOOLS = [
    execute_historical_sql,
    execute_lz_kpi_sql,
    query_ta_metrics  # New TA query tool
]


# ============================================================================
# Example Usage (for testing)
# ============================================================================

if __name__ == "__main__":
    # Example 1: Query latest KPIs
    result = execute_lz_kpi_sql.invoke({
        "sql_query": "SELECT site_name, COUNT(*) as record_count FROM kpi_data GROUP BY site_name"
    })
    print("KPI Query Result:")
    print(result)
    print("\n" + "=" * 80 + "\n")

    # Example 2: Query optimization history
    result = execute_historical_sql.invoke({
        "sql_query": "SELECT COUNT(*) as total_records FROM kpi_data"
    })
    print("Historical Query Result:")
    print(result)
    print("\n" + "=" * 80 + "\n")

    # Example 3: Get database schema
    print("Database Schema:")
    print(get_database_schema())
