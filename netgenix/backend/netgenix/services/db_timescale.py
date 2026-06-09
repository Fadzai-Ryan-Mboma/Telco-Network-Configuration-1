"""
TimescaleDB query helpers — replaces SQLite-backed database.py for KPI data.

All functions return plain dicts / lists-of-dicts so callers don't need
to know about psycopg2 internals.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator, Optional

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Connection
# ─────────────────────────────────────────────────────────────────────────────

def _dsn() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5433')} "
        f"dbname={os.getenv('DB_NAME', 'netgenix')} "
        f"user={os.getenv('DB_USER', 'netgenix')} "
        f"password={os.getenv('DB_PASSWORD', 'netgenix_secure_2026')}"
    )


@contextmanager
def _conn() -> Generator[psycopg2.extensions.connection, None, None]:
    conn = psycopg2.connect(_dsn(), cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


def is_timescale_available() -> bool:
    try:
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
        return True
    except Exception as exc:
        log.debug("TimescaleDB not available: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Cell KPI queries
# ─────────────────────────────────────────────────────────────────────────────

# All 30 KPI columns in DB order (matches kpi_cell table)
KPI_COLUMNS = [
    "radio_net_availability_rate",
    "rrc_setup_success_rate_all",
    "rrc_setup_success_rate_service",
    "rrc_setup_success_rate_signal",
    "erab_setup_success_rate",
    "call_drop_rate",
    "ho_success_rate_intra_freq",
    "ho_success_rate_s1",
    "paging_transfer_success_rate",
    "total_traffic_gbit",
    "dl_traffic_volume_gbit",
    "ul_traffic_volume_gbit",
    "l_traffic_user_avg",
    "l_traffic_user_max",
    "user_dl_pdcp_avg_throughput",
    "user_ul_pdcp_avg_throughput",
    "dl_ibler",
    "ul_ibler",
    "dl_retrans_rate",
    "dl_packet_loss_rate",
    "ul_packet_loss_rate",
    "dl_prb_usage_rate",
    "ul_prb_usage_rate",
    "pucch_usage_rate",
    "pdcch_cce_usage_rate",
    "average_cqi",
    "average_pdsch_mcs",
    "data_access_time_ms",
    "total_cell_unavail_duration_s",
    "integrity",
]

_KPI_SELECT = ", ".join(KPI_COLUMNS)


def get_latest_cell_kpis(enodeb_name: str) -> list[dict]:
    """
    Return the most-recent row per cell for an eNodeB.
    Prefers hourly rows over daily when both exist in the latest window.
    """
    sql = f"""
        SELECT DISTINCT ON (cell_name)
            time, enodeb_name, cell_name, local_cell_id, cell_fdd_tdd,
            granularity, {_KPI_SELECT}
        FROM kpi_cell
        WHERE enodeb_name = %s
        ORDER BY cell_name, time DESC, granularity DESC
    """
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, (enodeb_name,))
        return [dict(r) for r in cur.fetchall()]


def get_cell_kpi_history(
    enodeb_name: str,
    kpi_name: str,
    days: int = 7,
    granularity: Optional[str] = None,
) -> list[dict]:
    """
    Return (time, value) pairs for one KPI across all cells in an eNodeB.
    Averages across cells per timestamp.
    """
    if kpi_name not in KPI_COLUMNS:
        raise ValueError(f"Unknown KPI column: {kpi_name!r}")

    gran_filter = "AND granularity = %s" if granularity else ""
    params: list[Any] = [enodeb_name, days]
    if granularity:
        params.append(granularity)

    sql = f"""
        SELECT
            time_bucket('1 day', time) AS bucket,
            AVG({kpi_name})            AS value
        FROM kpi_cell
        WHERE enodeb_name = %s
          AND time >= NOW() - (%s || ' days')::INTERVAL
          {gran_filter}
        GROUP BY bucket
        ORDER BY bucket ASC
    """
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return [{"date": str(r["bucket"].date()), "value": r["value"]} for r in cur.fetchall()]


def get_enodeb_summary(enodeb_name: str, days: int = 7) -> Optional[dict]:
    """
    Average all 30 KPIs across all cells and the requested window.
    Returns a single dict or None if no data.
    """
    avgs = ", ".join(f"AVG({c}) AS {c}" for c in KPI_COLUMNS if c != "integrity")
    sql = f"""
        SELECT {avgs}
        FROM kpi_cell
        WHERE enodeb_name = %s
          AND time >= NOW() - (%s || ' days')::INTERVAL
    """
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, (enodeb_name, days))
        row = cur.fetchone()
        return dict(row) if row else None


def list_enodebs() -> list[str]:
    """Return all distinct eNodeB names in the DB."""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT enodeb_name FROM kpi_cell ORDER BY enodeb_name")
        return [r["enodeb_name"] for r in cur.fetchall()]


def list_cells(enodeb_name: str) -> list[str]:
    """Return all cell names for an eNodeB."""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT cell_name FROM kpi_cell WHERE enodeb_name = %s ORDER BY cell_name",
            (enodeb_name,),
        )
        return [r["cell_name"] for r in cur.fetchall()]


# ─────────────────────────────────────────────────────────────────────────────
# Network-level queries
# ─────────────────────────────────────────────────────────────────────────────

NETWORK_KPI_COLUMNS = [
    "radio_net_availability_rate",
    "rrc_setup_success_rate_all",
    "rrc_setup_success_rate_service",
    "rrc_setup_success_rate_signal",
    "erab_setup_success_rate",
    "call_drop_rate",
    "ho_success_rate_intra_freq",
    "ho_success_rate_s1",
    "l_traffic_user_avg",
    "l_traffic_user_max",
    "dl_traffic_volume_gbit",
    "ul_traffic_volume_gbit",
    "total_traffic_gbit",
    "user_dl_pdcp_avg_throughput",
    "user_ul_pdcp_avg_throughput",
    "paging_transfer_success_rate",
    "dl_ibler",
    "ul_ibler",
    "dl_retrans_rate",
    "dl_packet_loss_rate",
    "ul_packet_loss_rate",
    "dl_prb_usage_rate",
    "ul_prb_usage_rate",
    "pucch_usage_rate",
    "pdcch_cce_usage_rate",
    "average_cqi",
    "average_pdsch_mcs",
    "integrity",
]


def get_latest_network_kpis() -> Optional[dict]:
    """Return the most recent network-level KPI row."""
    sql = f"""
        SELECT time, {', '.join(NETWORK_KPI_COLUMNS)}
        FROM kpi_network
        ORDER BY time DESC
        LIMIT 1
    """
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        row = cur.fetchone()
        return dict(row) if row else None


def get_network_kpi_history(kpi_name: str, days: int = 30) -> list[dict]:
    """Return daily network-level history for a single KPI."""
    if kpi_name not in NETWORK_KPI_COLUMNS:
        raise ValueError(f"Unknown network KPI column: {kpi_name!r}")
    sql = f"""
        SELECT time::date AS date, {kpi_name} AS value
        FROM kpi_network
        WHERE time >= NOW() - (%s || ' days')::INTERVAL
        ORDER BY time ASC
    """
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, (days,))
        return [{"date": str(r["date"]), "value": r["value"]} for r in cur.fetchall()]


# ─────────────────────────────────────────────────────────────────────────────
# Ingestion audit
# ─────────────────────────────────────────────────────────────────────────────

def get_ingestion_stats() -> dict:
    """Return row counts and latest timestamp from kpi_cell."""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*)          AS total_rows,
                COUNT(DISTINCT enodeb_name) AS enodebs,
                COUNT(DISTINCT cell_name)   AS cells,
                MAX(time)                   AS latest_time,
                MIN(time)                   AS earliest_time
            FROM kpi_cell
        """)
        row = cur.fetchone()
        return {
            "total_rows":   row["total_rows"],
            "enodebs":      row["enodebs"],
            "cells":        row["cells"],
            "latest_time":  str(row["latest_time"]) if row["latest_time"] else None,
            "earliest_time": str(row["earliest_time"]) if row["earliest_time"] else None,
        }
