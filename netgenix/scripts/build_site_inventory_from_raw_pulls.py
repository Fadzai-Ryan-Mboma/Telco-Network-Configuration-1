#!/usr/bin/env python3
"""Build NetGenix site inventory from MAE raw KPI exports."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.netgenix.reports.engine import load_tabular_file

DEFAULT_RAW_DIR = WORKSPACE_ROOT / "docs" / "raw pulls_30April"
DEFAULT_OUTPUT_CSV = PROJECT_ROOT / "data" / "site_inventory.csv"
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "data" / "site_inventory.json"


def number(value: Any) -> float:
    if value in ("", None):
        return 0.0
    try:
        return float(str(value).replace(",", "").replace("%", "").strip())
    except ValueError:
        return 0.0


def average(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def build_inventory(raw_dir: Path) -> list[dict[str, Any]]:
    cell_files = sorted(raw_dir.glob("*Cell Level KPIs*.csv"))
    rows: list[dict[str, Any]] = []
    for path in cell_files:
        rows.extend(load_tabular_file(path))

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        site_name = str(row.get("eNodeB Name") or row.get("eNodeB Function Name") or "").strip()
        if site_name:
            grouped[site_name].append(row)

    inventory = []
    for site_name, site_rows in sorted(grouped.items()):
        cell_names = sorted({str(row.get("Cell Name") or "").strip() for row in site_rows if row.get("Cell Name")})
        local_cell_ids = sorted({
            str(row.get("LocalCell Id") or "").strip()
            for row in site_rows
            if row.get("LocalCell Id") not in ("", None)
        }, key=lambda value: int(value) if value.isdigit() else value)
        dates = sorted({str(row.get("Date") or "").strip() for row in site_rows if row.get("Date")})

        inventory.append({
            "site_name": site_name,
            "mae_ne_name": site_name,
            "first_date": dates[0] if dates else "",
            "last_date": dates[-1] if dates else "",
            "record_count": len(site_rows),
            "cell_count": len(cell_names),
            "local_cell_ids": "|".join(local_cell_ids),
            "cell_names": "|".join(cell_names),
            "total_traffic_gbit": round(sum(number(row.get("Total Traffic (Gbit)")) for row in site_rows), 4),
            "total_traffic_gb": round(sum(number(row.get("Total Traffic (Gbit)")) for row in site_rows) / 8.0, 4),
            "avg_dl_prb_usage": average([number(row.get("DL PRB Usage Rate(%)")) for row in site_rows]),
            "avg_ul_prb_usage": average([number(row.get("UL PRB Usage Rate(%)")) for row in site_rows]),
            "avg_availability": average([number(row.get("Radio Net Availability Rate(%)")) for row in site_rows]),
            "avg_rrc_success": average([number(row.get("RRC Setup Success Rate(all)")) for row in site_rows]),
            "avg_erab_success": average([number(row.get("E-RAB Setup Success Rate (ALL)(%)")) for row in site_rows]),
            "avg_call_drop": average([number(row.get("Call Drop Rate (All)(%)")) for row in site_rows]),
            "source": "MAE raw KPI export",
        })

    return inventory


def write_inventory(inventory: list[dict[str, Any]], csv_path: Path, json_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if inventory:
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(inventory[0].keys()))
            writer.writeheader()
            writer.writerows(inventory)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "site_count": len(inventory),
        "cell_count": sum(int(site["cell_count"]) for site in inventory),
        "sites": inventory,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    inventory = build_inventory(DEFAULT_RAW_DIR)
    write_inventory(inventory, DEFAULT_OUTPUT_CSV, DEFAULT_OUTPUT_JSON)
    print(json.dumps({
        "raw_dir": str(DEFAULT_RAW_DIR),
        "site_count": len(inventory),
        "cell_count": sum(int(site["cell_count"]) for site in inventory),
        "csv": str(DEFAULT_OUTPUT_CSV),
        "json": str(DEFAULT_OUTPUT_JSON),
        "first_sites": [site["site_name"] for site in inventory[:10]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
