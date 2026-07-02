#!/usr/bin/env python3
"""
Adjust synthetic KPI rows to limit variance to +/-2% around site means.

This script updates rows with data_source='synthetic' so that each KPI
value is set to `mean_non_synthetic * (1 + delta)` where delta ~ Uniform(-0.02, 0.02).

It computes the site mean from non-synthetic rows when available; otherwise
it uses all rows as fallback.

Usage:
  python3 scripts/adjust_synthetic_kpi_variance.py --db data/lz_network.db

"""
from __future__ import annotations

import argparse
import sqlite3
import random
from pathlib import Path
from typing import Dict, Tuple


KPI_COLUMNS = [
    'network_access_success',
    'download_speed',
    'download_quality',
    'upload_speed',
    'upload_quality',
    'control_channel_load',
    'feedback_channel_load',
]


def compute_site_means(conn: sqlite3.Connection, site: str) -> Dict[str, float]:
    cur = conn.cursor()
    # Try to compute means from non-synthetic rows
    cur.execute(f"SELECT {', '.join('AVG('+c+')' for c in KPI_COLUMNS)} FROM kpi_data WHERE site_name=? AND data_source!='synthetic'", (site,))
    row = cur.fetchone()
    if row and any(v is not None for v in row):
        return {k: (row[i] if row[i] is not None else 0.0) for i, k in enumerate(KPI_COLUMNS)}

    # Fallback to all rows
    cur.execute(f"SELECT {', '.join('AVG('+c+')' for c in KPI_COLUMNS)} FROM kpi_data WHERE site_name=?", (site,))
    row = cur.fetchone()
    return {k: (row[i] if row[i] is not None else 0.0) for i, k in enumerate(KPI_COLUMNS)}


def adjust_row_values(means: Dict[str, float]) -> Dict[str, float]:
    # delta in [-0.02, 0.02]
    adjusted = {}
    for k, mean in means.items():
        delta = random.uniform(-0.02, 0.02)
        if mean is None:
            val = 0.0
        else:
            val = mean * (1.0 + delta)
        # clamp sensible bounds
        if 'speed' in k:
            val = max(0.0, val)
        else:
            val = max(0.0, min(100.0, val))
        adjusted[k] = round(val, 4)
    return adjusted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='data/lz_network.db')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get list of sites that have synthetic rows
    cur.execute("SELECT DISTINCT site_name FROM kpi_data WHERE data_source='synthetic'")
    sites = [r[0] for r in cur.fetchall()]
    total_updated = 0

    for site in sites:
        means = compute_site_means(conn, site)
        # select synthetic rows for this site
        cur.execute("SELECT id FROM kpi_data WHERE site_name=? AND data_source='synthetic'", (site,))
        ids = [r[0] for r in cur.fetchall()]

        print(f"Site {site}: {len(ids)} synthetic rows to adjust. Using means: {means}")

        for _id in ids:
            newvals = adjust_row_values(means)
            if args.dry_run:
                total_updated += 1
                continue

            cur.execute(
                """
                UPDATE kpi_data SET
                    network_access_success = ?,
                    download_speed = ?,
                    download_quality = ?,
                    upload_speed = ?,
                    upload_quality = ?,
                    control_channel_load = ?,
                    feedback_channel_load = ?
                WHERE id = ?
                """,
                (
                    newvals['network_access_success'],
                    newvals['download_speed'],
                    newvals['download_quality'],
                    newvals['upload_speed'],
                    newvals['upload_quality'],
                    newvals['control_channel_load'],
                    newvals['feedback_channel_load'],
                    _id,
                ),
            )
            total_updated += 1

    if not args.dry_run:
        conn.commit()

    conn.close()

    print(f"Adjustment complete. Rows processed: {total_updated}")


if __name__ == '__main__':
    main()
