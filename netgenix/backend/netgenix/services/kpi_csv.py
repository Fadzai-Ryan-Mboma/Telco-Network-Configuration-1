"""Read-only KPI fallback backed by Evaluation GUI CSV exports."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "LTZIM LTE Main KPIs Report_2_Query_Result_Aug 25_to_June 26"
CELL_CSV = DATA_DIR / "LTZIM LTE Main KPIs Report_2_Query_Result_Aug 25_to_June 26(Cell Level KPIs).csv"
NETWORK_CSV = DATA_DIR / "LTZIM LTE Main KPIs Report_2_Query_Result_Aug 25_to_June 26(Whole Network Main KPIs).csv"

KPI_COLUMN_MAP = {
    "radio_net_availability_rate": "Radio Net Availability Rate(%)",
    "rrc_setup_success_rate_all": "RRC Setup Success Rate(all)",
    "rrc_setup_success_rate_service": "RRC Setup Success Rate(Service)[%]",
    "rrc_setup_success_rate_signal": "RRC Setup Success Rate(Signal)[%]",
    "erab_setup_success_rate": "E-RAB Setup Success Rate (ALL)(%)",
    "call_drop_rate": "Call Drop Rate (All)(%)",
    "ho_success_rate_intra_freq": "HO Success Rate(Intra Freqency)",
    "ho_success_rate_s1": "HO Success Rate(S1)[%]",
    "paging_transfer_success_rate": "Paging Transfer Success Rate",
    "total_traffic_gbit": "Total Traffic (Gbit)",
    "dl_traffic_volume_gbit": "DL Traffic Volume(Gbit)",
    "ul_traffic_volume_gbit": "UL Traffic Volume(Gbit)",
    "l_traffic_user_avg": "L.Traffic.User.Avg",
    "l_traffic_user_max": "L.Traffic.User.Max",
    "user_dl_pdcp_avg_throughput": "User DL PDCP Average Throughput",
    "user_ul_pdcp_avg_throughput": "User UL PDCP Average Throughput",
    "dl_ibler": "DL IBLER[%]",
    "ul_ibler": "UL IBLER[%]",
    "dl_retrans_rate": "DL ReTrans Rate[%]",
    "dl_packet_loss_rate": "DL Packet Loss Rate(all)",
    "ul_packet_loss_rate": "UL Packet Loss Rate(all)",
    "dl_prb_usage_rate": "DL PRB Usage Rate(%)",
    "ul_prb_usage_rate": "UL PRB Usage Rate(%)",
    "pucch_usage_rate": "PUCCHUsage Rate[%]",
    "pdcch_cce_usage_rate": "PDCCH CCE Usage Rate[%]",
    "average_cqi": "Average CQI",
    "average_pdsch_mcs": "Average PDSCH MCS",
    "data_access_time_ms": "Data Access Time (ms)",
    "total_cell_unavail_duration_s": "Total Cell Unavail Duration(s)",
    "integrity": "Integrity",
}


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.rstrip("%"), errors="coerce")


@lru_cache(maxsize=2)
def _read_export(path_value: str) -> pd.DataFrame:
    frame = pd.read_csv(path_value, skiprows=5, encoding="utf-8-sig")
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    return frame.dropna(subset=["Date"])


def _window(frame: pd.DataFrame, days: int) -> pd.DataFrame:
    if frame.empty:
        return frame
    latest = frame["Date"].max()
    return frame[frame["Date"] >= latest - pd.Timedelta(days=max(days - 1, 0))]


def get_csv_enodeb_summary(enodeb_name: str, days: int) -> Optional[dict]:
    frame = _read_export(str(CELL_CSV))
    site_frame = frame[frame["eNodeB Name"].astype(str).str.strip() == enodeb_name]
    site_frame = _window(site_frame, days)
    if site_frame.empty:
        return None

    result = {}
    for key, column in KPI_COLUMN_MAP.items():
        value = _numeric(site_frame[column]).mean() if column in site_frame else float("nan")
        result[key] = None if pd.isna(value) else float(value)
    return result


def get_csv_enodeb_history(enodeb_name: str, kpi_name: str, days: int) -> list[dict]:
    column = KPI_COLUMN_MAP.get(kpi_name)
    if not column:
        raise ValueError(f"Unknown KPI column: {kpi_name!r}")

    frame = _read_export(str(CELL_CSV))
    frame = frame[frame["eNodeB Name"].astype(str).str.strip() == enodeb_name].copy()
    frame = _window(frame, days)
    if frame.empty or column not in frame:
        return []

    frame["value"] = _numeric(frame[column])
    grouped = frame.groupby(frame["Date"].dt.date)["value"].mean().dropna()
    return [{"date": str(date), "value": float(value)} for date, value in grouped.items()]


def get_csv_network_latest() -> Optional[dict]:
    frame = _read_export(str(NETWORK_CSV))
    if frame.empty:
        return None
    row = frame.sort_values("Date").iloc[-1]
    result = {"time": row["Date"].isoformat()}
    for key, column in KPI_COLUMN_MAP.items():
        if column not in frame:
            continue
        value = _numeric(pd.Series([row[column]])).iloc[0]
        result[key] = None if pd.isna(value) else float(value)
    return result


def get_csv_network_history(kpi_name: str, days: int) -> list[dict]:
    column = KPI_COLUMN_MAP.get(kpi_name)
    if not column:
        raise ValueError(f"Unknown KPI column: {kpi_name!r}")
    frame = _window(_read_export(str(NETWORK_CSV)).copy(), days)
    if frame.empty or column not in frame:
        return []
    frame["value"] = _numeric(frame[column])
    return [
        {"date": str(row.Date.date()), "value": float(row.value)}
        for row in frame[["Date", "value"]].dropna().itertuples(index=False)
    ]
