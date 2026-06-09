"""Topology/NOC API endpoints."""

import csv
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter

from backend.models.schemas import TopologyResponse, TopologySite
from backend.netgenix.services.database import get_all_sites, get_site_info, get_site_kpis

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SITE_INVENTORY_PATH = PROJECT_ROOT / "data" / "site_inventory.csv"

APPROXIMATE_COORDINATES = {
    "MSH-0014-Chipadze": (-17.3026, 31.3303),
    "MSH-0112-Bindura Hospital": (-17.3042, 31.3318),
    "MSH-0331-Chiwaridzo 2": (-17.2868, 31.3198),
    "MSH0013-Bindura-Zaoga": (-17.3117, 31.3269),
}


def _site_status(network_access_success: float | None, control_channel_load: float | None) -> str:
    if network_access_success is None:
        return "unknown"
    if network_access_success < 90 or (control_channel_load is not None and control_channel_load > 70):
        return "critical"
    if network_access_success < 95 or (control_channel_load is not None and control_channel_load > 55):
        return "watch"
    return "healthy"


def _raw_site_status(availability: float | None, call_drop_rate: float | None, prb_usage: float | None) -> str:
    if availability is None and call_drop_rate is None and prb_usage is None:
        return "unknown"
    if (availability is not None and availability < 90) or (call_drop_rate is not None and call_drop_rate > 5):
        return "critical"
    if (availability is not None and availability < 97) or (call_drop_rate is not None and call_drop_rate > 2) or (prb_usage is not None and prb_usage > 75):
        return "watch"
    return "healthy"


def _float(value: str | None) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _inventory_sites() -> list[dict[str, str]]:
    if not SITE_INVENTORY_PATH.exists():
        return []
    with SITE_INVENTORY_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _pseudo_coordinates(index: int, total: int) -> tuple[float, float]:
    # Deterministic Zimbabwe-ish spread until true latitude/longitude inventory is available.
    columns = max(1, min(24, int(total ** 0.5) + 1))
    row = index // columns
    column = index % columns
    latitude = -22.0 + (row * 0.36)
    longitude = 25.2 + (column * 0.46)
    return latitude, longitude


@router.get("/sites", response_model=TopologyResponse)
async def get_topology_sites():
    """Return topology view using MAE-derived inventory when available."""
    inventory = _inventory_sites()
    if inventory:
        sites = []
        for index, site in enumerate(inventory):
            availability = _float(site.get("avg_availability"))
            call_drop_rate = _float(site.get("avg_call_drop"))
            prb_usage = _float(site.get("avg_dl_prb_usage"))
            latitude, longitude = _pseudo_coordinates(index, len(inventory))
            sites.append(TopologySite(
                site_name=site["site_name"],
                latitude=latitude,
                longitude=longitude,
                status=_raw_site_status(availability, call_drop_rate, prb_usage),
                network_access_success=_float(site.get("avg_rrc_success")),
                download_speed=None,
                control_channel_load=prb_usage,
                cell_count=int(site.get("cell_count") or 0),
                total_traffic_gb=_float(site.get("total_traffic_gb")),
                availability=availability,
                call_drop_rate=call_drop_rate,
                source=site.get("source") or "MAE raw KPI export",
                last_updated=site.get("last_date"),
            ))

        return TopologyResponse(
            sites=sites,
            site_count=len(sites),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    sites = []
    for index, site in enumerate(get_all_sites()):
        site_name = site["site_name"]
        kpis = get_site_kpis(site_name) or {}
        info = get_site_info(site_name) or {}
        fallback_lat = -17.30 + (index * 0.012)
        fallback_lon = 31.32 + (index * 0.01)
        latitude, longitude = APPROXIMATE_COORDINATES.get(site_name, (fallback_lat, fallback_lon))

        sites.append(TopologySite(
            site_name=site_name,
            latitude=latitude,
            longitude=longitude,
            status=_site_status(
                kpis.get("network_access_success"),
                kpis.get("control_channel_load"),
            ),
            network_access_success=kpis.get("network_access_success"),
            download_speed=kpis.get("download_speed"),
            control_channel_load=kpis.get("control_channel_load"),
            last_updated=info.get("last_updated"),
        ))

    return TopologyResponse(
        sites=sites,
        site_count=len(sites),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
