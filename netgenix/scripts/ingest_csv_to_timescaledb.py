#!/usr/bin/env python3
"""
Initial data load: parse LTZIM LTE Main KPIs CSVs → TimescaleDB.

CSV format:
  - 5-row metadata header (skiprows=5)
  - Encoding: utf-8-sig
  - Last row is a footer summary (dropped)

Run:
  python scripts/ingest_csv_to_timescaledb.py

Env vars (or .env):
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
  DATABASE_URL  (overrides individual vars if set)
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT  = SCRIPT_DIR.parent
DATA_DIR   = REPO_ROOT / "data" / "LTZIM LTE Main KPIs Report_2_Query_Result_Aug 25_to_June 26"

CELL_CSV    = DATA_DIR / "LTZIM LTE Main KPIs Report_2_Query_Result_Aug 25_to_June 26(Cell Level KPIs).csv"
NETWORK_CSV = DATA_DIR / "LTZIM LTE Main KPIs Report_2_Query_Result_Aug 25_to_June 26(Whole Network Main KPIs).csv"

# ── DB connection ─────────────────────────────────────────────────────────────
def get_conn():
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5433)),
        dbname=os.getenv("DB_NAME", "netgenix"),
        user=os.getenv("DB_USER", "netgenix"),
        password=os.getenv("DB_PASSWORD", "netgenix_secure_2026"),
    )


# ── CSV helpers ───────────────────────────────────────────────────────────────
def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, skiprows=5, encoding="utf-8-sig")
    # Drop footer: last row usually has totals or "End of Report"
    last = df.iloc[-1]
    if pd.isna(last.iloc[2]) or str(last.iloc[0]).strip().lower().startswith("end"):
        df = df.iloc[:-1]
    return df


def _to_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _to_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _parse_date(val) -> datetime:
    """Parse 'YYYY-MM-DD' → aware UTC datetime (midnight)."""
    dt = pd.to_datetime(val, dayfirst=False, errors="coerce")
    if pd.isna(dt):
        raise ValueError(f"Cannot parse date: {val!r}")
    return dt.replace(tzinfo=timezone.utc)


# ── Cell-level ingestion ──────────────────────────────────────────────────────
CELL_INSERT = """
INSERT INTO kpi_cell (
    time, enodeb_name, cell_name, local_cell_id, enodeb_function_name, cell_fdd_tdd,
    integrity,
    radio_net_availability_rate,
    rrc_setup_success_rate_all, rrc_setup_success_rate_service, rrc_setup_success_rate_signal,
    erab_setup_success_rate, call_drop_rate,
    ho_success_rate_intra_freq, ho_success_rate_s1,
    paging_transfer_success_rate,
    total_traffic_gbit, dl_traffic_volume_gbit, ul_traffic_volume_gbit,
    l_traffic_user_avg, l_traffic_user_max,
    user_dl_pdcp_avg_throughput, user_ul_pdcp_avg_throughput,
    dl_ibler, ul_ibler,
    dl_retrans_rate, dl_packet_loss_rate, ul_packet_loss_rate,
    dl_prb_usage_rate, ul_prb_usage_rate,
    pucch_usage_rate, pdcch_cce_usage_rate,
    average_cqi, average_pdsch_mcs,
    data_access_time_ms, total_cell_unavail_duration_s,
    granularity, data_source
) VALUES %s
ON CONFLICT (time, cell_name, granularity) DO NOTHING
"""


def _cell_rows(df: pd.DataFrame) -> list[tuple]:
    rows = []
    for _, r in df.iterrows():
        try:
            ts = _parse_date(r["Date"])
        except ValueError as exc:
            log.warning("Skipping row — bad date: %s", exc)
            continue
        rows.append((
            ts,
            str(r["eNodeB Name"]).strip(),
            str(r["Cell Name"]).strip(),
            _to_int(r["LocalCell Id"]),
            str(r.get("eNodeB Function Name", "")).strip() or None,
            str(r.get("Cell FDD TDD Indication", "")).strip() or None,
            str(r.get("Integrity", "")).strip() or None,
            _to_float(r["Radio Net Availability Rate(%)"]),
            _to_float(r["RRC Setup Success Rate(all)"]),
            _to_float(r["RRC Setup Success Rate(Service)[%]"]),
            _to_float(r["RRC Setup Success Rate(Signal)[%]"]),
            _to_float(r["E-RAB Setup Success Rate (ALL)(%)"]),
            _to_float(r["Call Drop Rate (All)(%)"]),
            _to_float(r["HO Success Rate(Intra Freqency)"]),
            _to_float(r["HO Success Rate(S1)[%]"]),
            _to_float(r["Paging Transfer Success Rate"]),
            _to_float(r["Total Traffic (Gbit)"]),
            _to_float(r["DL Traffic Volume(Gbit)"]),
            _to_float(r["UL Traffic Volume(Gbit)"]),
            _to_float(r["L.Traffic.User.Avg"]),
            _to_float(r["L.Traffic.User.Max"]),
            _to_float(r["User DL PDCP Average Throughput"]),
            _to_float(r["User UL PDCP Average Throughput"]),
            _to_float(r["DL IBLER[%]"]),
            _to_float(r["UL IBLER[%]"]),
            _to_float(r["DL ReTrans Rate[%]"]),
            _to_float(r["DL Packet Loss Rate(all)"]),
            _to_float(r["UL Packet Loss Rate(all)"]),
            _to_float(r["DL PRB Usage Rate(%)"]),
            _to_float(r["UL PRB Usage Rate(%)"]),
            _to_float(r["PUCCHUsage Rate[%]"]),
            _to_float(r["PDCCH CCE Usage Rate[%]"]),
            _to_float(r["Average CQI"]),
            _to_float(r["Average PDSCH MCS"]),
            _to_float(r["Data Access Time (ms)"]),
            _to_float(r["Total Cell Unavail Duration(s)"]),
            "daily",
            "csv_initial_load",
        ))
    return rows


# ── Network-level ingestion ───────────────────────────────────────────────────
NETWORK_INSERT = """
INSERT INTO kpi_network (
    time, network_label, integrity,
    radio_net_availability_rate,
    rrc_setup_success_rate_all, rrc_setup_success_rate_service, rrc_setup_success_rate_signal,
    erab_setup_success_rate, call_drop_rate,
    ho_success_rate_intra_freq, ho_success_rate_s1,
    l_traffic_user_avg, l_traffic_user_max,
    dl_traffic_volume_gbit, ul_traffic_volume_gbit, total_traffic_gbit,
    user_dl_pdcp_avg_throughput, user_ul_pdcp_avg_throughput,
    paging_transfer_success_rate,
    dl_ibler, ul_ibler,
    dl_retrans_rate, dl_packet_loss_rate, ul_packet_loss_rate,
    dl_prb_usage_rate, ul_prb_usage_rate,
    pucch_usage_rate, pdcch_cce_usage_rate,
    average_cqi, average_pdsch_mcs,
    granularity, data_source
) VALUES %s
ON CONFLICT (time, granularity) DO NOTHING
"""


def _network_rows(df: pd.DataFrame) -> list[tuple]:
    rows = []
    for _, r in df.iterrows():
        try:
            ts = _parse_date(r["Date"])
        except ValueError as exc:
            log.warning("Skipping network row — bad date: %s", exc)
            continue
        rows.append((
            ts,
            str(r.get("Whole Network", "LTZIM")).strip() or "LTZIM",
            str(r.get("Integrity", "")).strip() or None,
            _to_float(r["Radio Net Availability Rate(%)"]),
            _to_float(r["RRC Setup Success Rate(all)"]),
            _to_float(r["RRC Setup Success Rate(Service)[%]"]),
            _to_float(r["RRC Setup Success Rate(Signal)[%]"]),
            _to_float(r["E-RAB Setup Success Rate (ALL)(%)"]),
            _to_float(r["Call Drop Rate (All)(%)"]),
            _to_float(r["HO Success Rate(Intra Freqency)"]),
            _to_float(r["HO Success Rate(S1)[%]"]),
            _to_float(r["L.Traffic.User.Avg"]),
            _to_float(r["L.Traffic.User.Max"]),
            _to_float(r["DL Traffic Volume(Gbit)"]),
            _to_float(r["UL Traffic Volume(Gbit)"]),
            _to_float(r["Total Traffic (Gbit)"]),
            _to_float(r["User DL PDCP Average Throughput"]),
            _to_float(r["User UL PDCP Average Throughput"]),
            _to_float(r["Paging Transfer Success Rate"]),
            _to_float(r["DL IBLER[%]"]),
            _to_float(r["UL IBLER[%]"]),
            _to_float(r["DL ReTrans Rate[%]"]),
            _to_float(r["DL Packet Loss Rate(all)"]),
            _to_float(r["UL Packet Loss Rate(all)"]),
            _to_float(r["DL PRB Usage Rate(%)"]),
            _to_float(r["UL PRB Usage Rate(%)"]),
            _to_float(r["PUCCHUsage Rate[%]"]),
            _to_float(r["PDCCH CCE Usage Rate[%]"]),
            _to_float(r["Average CQI"]),
            _to_float(r["Average PDSCH MCS"]),
            "daily",
            "csv_initial_load",
        ))
    return rows


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    run_at = datetime.now(tz=timezone.utc)

    log.info("Connecting to TimescaleDB …")
    try:
        conn = get_conn()
    except Exception as exc:
        log.error("Cannot connect to database: %s", exc)
        sys.exit(1)

    cur = conn.cursor()

    # ── Cell-level ──
    log.info("Reading cell-level CSV: %s", CELL_CSV)
    cell_df = _read_csv(CELL_CSV)
    log.info("  %d rows read", len(cell_df))
    cell_rows = _cell_rows(cell_df)
    log.info("  %d rows prepared for insert", len(cell_rows))

    BATCH = 2000
    cell_inserted = 0
    cell_skipped  = 0
    for i in range(0, len(cell_rows), BATCH):
        batch = cell_rows[i : i + BATCH]
        before = cur.rowcount
        psycopg2.extras.execute_values(cur, CELL_INSERT, batch, page_size=BATCH)
        conn.commit()
        cell_inserted += cur.rowcount if cur.rowcount >= 0 else len(batch)
        log.info("  Cell batch %d/%d — cumulative inserted ≈ %d",
                 i // BATCH + 1, (len(cell_rows) - 1) // BATCH + 1, cell_inserted)

    # rowcount after execute_values reflects rows that actually went in (ON CONFLICT skips ≠ rowcount)
    # Recalculate skipped
    cell_skipped = len(cell_rows) - cell_inserted

    # ── Network-level ──
    log.info("Reading network-level CSV: %s", NETWORK_CSV)
    net_df   = _read_csv(NETWORK_CSV)
    net_rows = _network_rows(net_df)
    log.info("  %d rows prepared", len(net_rows))
    psycopg2.extras.execute_values(cur, NETWORK_INSERT, net_rows, page_size=500)
    conn.commit()
    net_inserted = cur.rowcount if cur.rowcount >= 0 else len(net_rows)
    net_skipped  = len(net_rows) - net_inserted

    # ── Audit log ──
    cur.execute(
        """
        INSERT INTO ingestion_log
            (run_at, source, granularity, period_start, period_end,
             rows_inserted, rows_skipped, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            run_at,
            "csv_initial_load",
            "daily",
            cell_df["Date"].min() if not cell_df.empty else None,
            cell_df["Date"].max() if not cell_df.empty else None,
            cell_inserted + net_inserted,
            cell_skipped  + net_skipped,
            "ok",
        ),
    )
    conn.commit()
    cur.close()
    conn.close()

    log.info("─" * 60)
    log.info("Cell rows  → inserted: %d  skipped: %d", cell_inserted, cell_skipped)
    log.info("Network rows → inserted: %d  skipped: %d", net_inserted, net_skipped)
    log.info("Initial load complete.")


if __name__ == "__main__":
    main()
