#!/usr/bin/env python3
"""
Generate conservative synthetic KPI data to fill gaps from the last
timestamp in the `kpi_data` table up to a target end date.

This script is intentionally NOT executed by the assistant. It is provided
so you can review and run it locally when ready.

Behavior (conservative):
- Default: fill from (max timestamp + 1 day) up to min(max + 90 days, today).
- Generate 6 measurements per day to match existing pattern.
- Follow observed historical means and small variance; apply a tiny
  downward trend for throughput KPIs to simulate gradual degradation.
- Insert rows with `data_source='synthetic'` and notes indicating generation.

Usage (example):
  python3 scripts/populate_synthetic_kpi_data.py --db data/lz_network.db --dry-run

"""
from __future__ import annotations

import argparse
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple


DB_DEFAULT = Path(__file__).resolve().parents[1] / "data" / "lz_network.db"
MEASUREMENTS_PER_DAY = 6
MAX_DAYS = 90  # cap at 90 days by default


def get_sites(conn: sqlite3.Connection) -> List[str]:
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT site_name FROM kpi_data ORDER BY site_name")
    return [row[0] for row in cur.fetchall()]


def get_latest_timestamp(conn: sqlite3.Connection) -> datetime | None:
    cur = conn.cursor()
    cur.execute("SELECT MAX(timestamp) FROM kpi_data")
    r = cur.fetchone()
    if r and r[0]:
        return datetime.fromisoformat(r[0])
    return None


def get_site_stats(conn: sqlite3.Connection, site: str) -> Dict[str, Tuple[float, float]]:
    """Return mean and stddev for each KPI for the given site."""
    cur = conn.cursor()
    cur.execute(
        "SELECT network_access_success, download_speed, download_quality, upload_speed, upload_quality, control_channel_load, feedback_channel_load FROM kpi_data WHERE site_name = ?",
        (site,)
    )
    rows = cur.fetchall()
    if not rows:
        raise RuntimeError(f"No data for site {site}")

    # transpose
    cols = list(zip(*rows))
    names = [
        "network_access_success",
        "download_speed",
        "download_quality",
        "upload_speed",
        "upload_quality",
        "control_channel_load",
        "feedback_channel_load",
    ]

    stats: Dict[str, Tuple[float, float]] = {}
    for name, col in zip(names, cols):
        vals = [v for v in col if v is not None]
        if not vals:
            stats[name] = (0.0, 0.0)
            continue
        mean = sum(vals) / len(vals)
        var = sum((x - mean) ** 2 for x in vals) / max(len(vals) - 1, 1)
        std = var ** 0.5
        stats[name] = (mean, std)

    return stats


def clamp(value: float, minv: float, maxv: float) -> float:
    return max(minv, min(maxv, value))


def generate_for_day(
    base_stats: Dict[str, Tuple[float, float]],
    days_since_start: int,
    measurement_index: int,
    total_days: int,
) -> Dict[str, float]:
    """Generate a single measurement following conservative trend rules."""
    result: Dict[str, float] = {}

    # small relative daily trends (conservative)
    trends = {
        "network_access_success": 0.0,  # keep stable
        "download_speed": -0.0008,      # slight degradation per day (~-7% over 90d)
        "download_quality": 0.0,
        "upload_speed": -0.0004,
        "upload_quality": 0.0,
        "control_channel_load": 0.0,
        "feedback_channel_load": 0.0,
    }

    for k, (mean, std) in base_stats.items():
        # Add small periodic component so not completely random
        phase = (measurement_index / MEASUREMENTS_PER_DAY) * 2 * 3.14159
        periodic = 0.01 * mean * (0.5 * (1 + random.uniform(-1, 1))) * (random.random())

        # trend component (relative)
        trend_factor = trends.get(k, 0.0)
        trend_component = mean * (trend_factor * days_since_start)

        noise = random.gauss(0, max(std, 1e-3)) * 0.5  # dampen noise for conservative values

        raw = mean + trend_component + noise + periodic

        # Apply sensible bounds
        if "speed" in k:
            val = clamp(raw, 0.0, max(mean * 3, 100.0))
        else:
            # percentages
            val = clamp(raw, 0.0, 100.0)

        result[k] = round(val, 4)

    return result


def insert_records(conn: sqlite3.Connection, site: str, rows: List[Tuple]):
    cur = conn.cursor()
    cur.executemany(
        """
        INSERT INTO kpi_data (timestamp, site_name, cell_id, network_access_success, download_speed, download_quality, upload_speed, upload_quality, control_channel_load, feedback_channel_load, data_source, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Populate conservative synthetic KPI data (dry-run by default)")
    parser.add_argument("--db", default=str(DB_DEFAULT), help="Path to SQLite DB")
    parser.add_argument("--max-days", type=int, default=MAX_DAYS, help="Maximum days to generate (cap)")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to DB; just report counts")
    parser.add_argument("--start-date", default=None, help="Optional start date (YYYY-MM-DD). Overrides DB detection")
    parser.add_argument("--end-date", default=None, help="Optional end date (YYYY-MM-DD). Defaults to min(start+max_days, today)")
    args = parser.parse_args(argv)

    db_path = Path(args.db)
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    latest_ts = get_latest_timestamp(conn)
    if args.start_date:
        start_date = datetime.fromisoformat(args.start_date)
    else:
        if not latest_ts:
            raise RuntimeError("No existing KPI data to base synthetic generation on")
        start_date = (latest_ts + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Determine end date
    if args.end_date:
        end_date = datetime.fromisoformat(args.end_date)
    else:
        limit_date = start_date + timedelta(days=args.max_days - 1)
        end_date = min(limit_date, today)

    if end_date < start_date:
        print("Nothing to generate; end date is before start date.")
        return 0

    total_days = (end_date - start_date).days + 1
    print(f"Generating conservative synthetic KPI data for {total_days} days: {start_date.date()} -> {end_date.date()}")

    sites = get_sites(conn)
    summary = {}

    for site in sites:
        stats = get_site_stats(conn, site)
        rows_to_insert: List[Tuple] = []

        for d_idx in range(total_days):
            day = start_date + timedelta(days=d_idx)
            for m_idx in range(MEASUREMENTS_PER_DAY):
                values = generate_for_day(stats, d_idx, m_idx, total_days)
                # simple cell_id rotation (1..n) to mimic multiple cells; keep as 1 for conservative
                cell_id = (m_idx % 3) + 1

                ts = (day + timedelta(hours= m_idx * (24 // MEASUREMENTS_PER_DAY))).replace(microsecond=0)

                row = (
                    ts.isoformat(sep=' '),
                    site,
                    cell_id,
                    values['network_access_success'],
                    values['download_speed'],
                    values['download_quality'],
                    values['upload_speed'],
                    values['upload_quality'],
                    values['control_channel_load'],
                    values['feedback_channel_load'],
                    'synthetic',
                    f"Generated synthetic conservative trend; source=script"
                )
                rows_to_insert.append(row)

        summary[site] = len(rows_to_insert)

        print(f"Site {site}: prepared {len(rows_to_insert)} synthetic rows")

        if not args.dry_run:
            insert_records(conn, site, rows_to_insert)
            print(f"Inserted {len(rows_to_insert)} rows for {site}")

    conn.close()

    print("Generation complete. Summary:")
    for s, cnt in summary.items():
        print(f"  {s}: {cnt} rows (data_source='synthetic')")

    print("NOTE: Script defaults to dry-run usage; pass --dry-run to avoid writes. Review outputs before executing.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
