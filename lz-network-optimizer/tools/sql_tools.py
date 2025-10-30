"""
Liquid Zimbabwe 4G Network Optimizer - SQL Database Tools
Purpose: LangChain tools for querying historical and live KPI data from SQLite
Created: 2025-10-30

These tools allow agents to query the unified database for KPI analysis and optimization history.
Pattern follows Nvidia's execute_xapp_sql implementation.
"""

from langchain_core.tools import tool
from typing import Annotated
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
# Tool List for Agent Registration
# ============================================================================

SQL_TOOLS = [
    execute_historical_sql,
    execute_lz_kpi_sql
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
