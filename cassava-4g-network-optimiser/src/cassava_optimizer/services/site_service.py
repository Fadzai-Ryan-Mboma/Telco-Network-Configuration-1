"""
Site data service for UI integration.

Provides synchronous wrapper for repository methods,
suitable for use in Streamlit pages.
"""

import asyncio
import logging
from typing import Any

from cassava_optimizer.infrastructure.repository import NetworkRepository
from cassava_optimizer.infrastructure.database import get_session, init_database

logger = logging.getLogger(__name__)


class SiteService:
    """
    Service class for site data operations.
    
    Wraps the async NetworkRepository for synchronous UI use.
    """
    
    def __init__(self) -> None:
        """Initialize the service."""
        self._repository = NetworkRepository()
        self._initialized = False
    
    async def _ensure_initialized(self) -> None:
        """Ensure database is initialized."""
        if not self._initialized:
            await init_database()
            self._initialized = True
    
    async def list_sites(self) -> list[dict[str, Any]]:
        """
        Get all sites formatted for UI display.
        
        Returns:
            List of site dictionaries with name, region, cell_count, status
        """
        await self._ensure_initialized()
        
        try:
            sites = await self._repository.get_all_sites()
            
            return [
                {
                    "site_id": site.site_id,
                    "name": site.site_name,
                    "region": site.region,
                    "cell_count": site.cell_count,
                    "status": "online",  # TODO: Get actual status from API
                }
                for site in sites
            ]
        except Exception as e:
            logger.error(f"Failed to list sites: {e}")
            raise
    
    async def get_site(self, site_id: str) -> dict[str, Any]:
        """
        Get detailed site information.
        
        Args:
            site_id: Site identifier
            
        Returns:
            Site dictionary with full details
        """
        await self._ensure_initialized()
        
        site = await self._repository.get_site(site_id)
        
        return {
            "site_id": site.site_id,
            "name": site.site_name,
            "enodeb_id": site.enodeb_id,
            "latitude": site.latitude,
            "longitude": site.longitude,
            "region": site.region,
            "cluster": site.cluster,
            "cell_count": site.cell_count,
            "cells": [
                {
                    "cell_id": cell.cell_id,
                    "cell_name": cell.cell_name,
                    "local_cell_id": cell.local_cell_id,
                    "pci": cell.pci,
                    "state": cell.state.value if hasattr(cell.state, "value") else str(cell.state),
                }
                for cell in site.cells
            ],
        }
    
    async def get_site_ids(self) -> list[str]:
        """Get all site IDs."""
        await self._ensure_initialized()
        return await self._repository.get_site_ids()


class KPIService:
    """
    Service class for KPI data operations.
    
    Wraps the async NetworkRepository for synchronous UI use.
    """
    
    def __init__(self) -> None:
        """Initialize the service."""
        self._repository = NetworkRepository()
        self._initialized = False
    
    async def _ensure_initialized(self) -> None:
        """Ensure database is initialized."""
        if not self._initialized:
            await init_database()
            self._initialized = True

    async def _resolve_site_id(self, site_name_or_id: str) -> str | None:
        """
        Resolve site_id from site_name or return if already site_id.

        Handles mismatch between UI passing site_name with dashes
        (e.g., "MSH-0112-Bindura Hospital") and database storing site_id
        with underscores (e.g., "MSH_0112_Bindura_Hospital").

        Args:
            site_name_or_id: Either site_name (with dashes) or site_id (with underscores)

        Returns:
            Resolved site_id or None if not found
        """
        from sqlalchemy import select
        from cassava_optimizer.infrastructure.database import SiteModel, get_session

        await self._ensure_initialized()

        async with get_session() as session:
            # Try as site_id first (exact match)
            stmt = select(SiteModel).where(SiteModel.site_id == site_name_or_id)
            result = await session.execute(stmt)
            site = result.scalar_one_or_none()

            if site:
                logger.debug(f"Resolved site_id (exact match): {site_name_or_id}")
                return site.site_id

            # Try as site_name (UI passes this with dashes)
            stmt = select(SiteModel).where(SiteModel.site_name == site_name_or_id)
            result = await session.execute(stmt)
            site = result.scalar_one_or_none()

            if site:
                logger.debug(f"Resolved site_name '{site_name_or_id}' to site_id '{site.site_id}'")
                return site.site_id

            logger.warning(f"Could not resolve site: {site_name_or_id}")
            return None

    async def get_site_kpis(self, site_name_or_id: str) -> dict[str, dict[str, Any]]:
        """
        Get latest KPI values for a site.

        Args:
            site_name_or_id: Site name (from UI) or site_id

        Returns:
            Dictionary of KPI name -> {value, target, trend}
        """
        await self._ensure_initialized()

        # Resolve site_id from site_name if needed
        site_id = await self._resolve_site_id(site_name_or_id)

        if not site_id:
            logger.warning(f"Could not resolve site: {site_name_or_id}")
            return {}

        # Get latest KPIs from database
        kpis = {}
        
        kpi_configs = {
            "rach_success_rate": {
                "display_name": "RACH Setup Success Rate",
                "target": 99.0,
                "key": "call_setup_success_rate",
            },
            "dl_ibler": {
                "display_name": "DL IBLER",
                "target": 10.0,  # Lower is better
                "key": "dl_ibler",
            },
            "ul_ibler": {
                "display_name": "UL IBLER",
                "target": 10.0,  # Lower is better
                "key": "ul_ibler",
            },
            "pdcch_cce_usage": {
                "display_name": "PDCCH CCE Usage Rate",
                "target": 50.0,  # Lower is better for congestion
                "key": "pdcch_cce_usage",
            },
            "dl_throughput": {
                "display_name": "DL Throughput",
                "target": 20.0,  # Higher is better, in kbit/s converted to Mbps
                "key": "throughput_downlink",
            },
            "ul_throughput": {
                "display_name": "UL Throughput",
                "target": 10.0,
                "key": "ul_throughput",
            },
        }
        
        for kpi_name, config in kpi_configs.items():
            try:
                # Get historical data for trending
                history = await self._repository.get_historical_kpis(
                    site_id=site_id,
                    kpi_name=kpi_name,
                    days=90,  # Look back 90 days for historical/demo data
                )
                
                if history:
                    # Get most recent value
                    latest = history[0].kpi_value

                    # Apply scale correction for percentage-based KPIs stored as decimals
                    if kpi_name == "rach_success_rate":
                        latest = latest * 100  # Convert decimal to percentage

                    # Calculate trend (compare to previous if available)
                    if len(history) > 1:
                        previous = history[1].kpi_value
                        # Apply same scaling to previous value for trend calculation
                        if kpi_name == "rach_success_rate":
                            previous = previous * 100
                        diff = latest - previous
                        trend = f"+{diff:.2f}" if diff >= 0 else f"{diff:.2f}"
                    else:
                        trend = "N/A"

                    kpis[config["key"]] = {
                        "value": latest,
                        "target": config["target"],
                        "trend": trend,
                    }
            except Exception as e:
                logger.debug(f"No data for KPI {kpi_name}: {e}")
        
        return kpis
    
    async def get_live_kpis_from_api(self, site_name: str) -> dict[str, dict[str, Any]]:
        """
        Fetch live KPI data directly from Huawei PM API.
        
        Uses the Performance Management API to query PM counters and convert
        them to KPI values. Falls back to Alarm API for health status if
        PM data is not available.
        
        Args:
            site_name: Site name (e.g., "MSH-0049-Kadoma Rimuka")
            
        Returns:
            Dictionary of KPI name -> {value, target, trend, source}
        """
        import os
        from cassava_optimizer.infrastructure.huawei_client import HuaweiMAEClient
        
        kpis = {}
        
        try:
            host = os.environ.get("MAE_HOST", os.environ.get("HUAWEI_API_HOST", "41.174.191.214"))
            port = int(os.environ.get("MAE_PORT", os.environ.get("HUAWEI_API_PORT", "31127")))
            username = os.environ.get("MAE_USERNAME", os.environ.get("HUAWEI_API_USERNAME", "cassava.ai"))
            password = os.environ.get("MAE_PASSWORD", os.environ.get("HUAWEI_API_PASSWORD", "#Pass123#"))
            
            async with HuaweiMAEClient(
                host=host,
                port=port,
                username=username,
                password=password,
                timeout=60.0,  # PM queries can take longer
            ) as client:
                await client.authenticate()
                
                # Step 1: Try PM API for performance counters
                pm_data = await client.get_pm_data(
                    site_name=site_name,
                    period_minutes=15,
                    hours_back=2,
                )
                
                if pm_data.get("success") and pm_data.get("records"):
                    # Convert PM counters to KPIs
                    raw_kpis = client.convert_pm_to_kpis(pm_data, site_name)
                    
                    # Map to dashboard KPI format with targets
                    kpi_targets = {
                        "rrc_setup_success_rate": 99.5,
                        "erab_setup_success_rate": 99.0,
                        "dl_throughput": 20.0,  # Mbps
                        "ul_throughput": 10.0,  # Mbps
                        "handover_success_rate": 98.0,
                        "active_ue_dl": 100,
                        "active_ue_ul": 50,
                    }
                    
                    for kpi_name, value in raw_kpis.items():
                        if value is not None:
                            target = kpi_targets.get(kpi_name, 0)
                            kpis[kpi_name] = {
                                "value": round(value, 2),
                                "target": target,
                                "trend": self._calculate_trend(value, target),
                                "source": "pm_api",
                            }
                    
                    logger.info(f"PM KPIs retrieved for {site_name}: {len(kpis)} metrics")
                else:
                    # PM data not available - site may not have PM subscriptions
                    logger.warning(
                        f"PM data not available for {site_name} - "
                        "counter subscriptions may not be configured"
                    )
                    
                    # Fall back to alarm-based health status
                    alarm_data = await client.get_alarms(data_type="CURRENT", limit=500)
                    
                    if alarm_data.get("success"):
                        # Count alarms for this site
                        site_alarms = [
                            a for a in alarm_data.get("alarms", [])
                            if site_name in str(a.get("meName", "")) or 
                               site_name in str(a.get("objectInstance", ""))
                        ]
                        
                        critical = sum(1 for a in site_alarms if str(a.get("perceivedSeverity")) == "1")
                        major = sum(1 for a in site_alarms if str(a.get("perceivedSeverity")) == "2")
                        
                        # Create health-based KPIs
                        kpis = {
                            "network_health": {
                                "value": 100 - (critical * 20) - (major * 5),
                                "target": 95,
                                "trend": "stable" if critical == 0 else "degraded",
                                "source": "alarm_api",
                            },
                            "critical_alarms": {
                                "value": critical,
                                "target": 0,
                                "trend": "up" if critical > 0 else "stable",
                                "source": "alarm_api",
                            },
                            "major_alarms": {
                                "value": major,
                                "target": 0,
                                "trend": "up" if major > 0 else "stable",
                                "source": "alarm_api",
                            },
                        }
                        
                        logger.info(f"Alarm-based health for {site_name}: {len(site_alarms)} alarms")
                
        except Exception as e:
            logger.warning(f"Failed to fetch live KPIs from API for {site_name}: {e}")
            # Return empty dict - will fall back to CSV data
        
        return kpis
    
    def _calculate_trend(self, value: float, target: float) -> str:
        """Calculate trend indicator based on value vs target."""
        if target == 0:
            return "stable"
        
        ratio = value / target
        if ratio >= 1.0:
            return "up"
        elif ratio >= 0.9:
            return "stable"
        else:
            return "down"
    
    def _parse_mml_kpis(self, raw_data: dict, site_name: str) -> dict[str, dict[str, Any]]:
        """
        Parse MML command responses to extract KPI values.
        
        DEPRECATED: Use get_live_kpis_from_api with PM API instead.
        """
        kpis = {}
        
        # KPI targets
        targets = {
            "call_setup_success_rate": 99.0,
            "call_drop_rate": 1.0,
            "handover_success_rate": 98.0,
            "rrc_setup_success_rate": 99.5,
            "erab_setup_success_rate": 99.0,
            "throughput_downlink": 50.0,
        }
        
        # If we have cell_config data, the API is working - set basic status
        if raw_data:
            kpis = {
                "call_setup_success_rate": {"value": None, "target": 99.0, "trend": "N/A", "source": "mml"},
                "call_drop_rate": {"value": None, "target": 1.0, "trend": "N/A", "source": "mml"},
                "handover_success_rate": {"value": None, "target": 98.0, "trend": "N/A", "source": "mml"},
                "rrc_setup_success_rate": {"value": None, "target": 99.5, "trend": "N/A", "source": "mml"},
                "erab_setup_success_rate": {"value": None, "target": 99.0, "trend": "N/A", "source": "mml"},
                "throughput_downlink": {"value": None, "target": 50.0, "trend": "N/A", "source": "mml"},
            }
            
            logger.info(f"MML connection verified for site {site_name}")
        
        return kpis
    
    async def get_kpi_history(
        self,
        site_name: str,
        kpi_name: str,
        hours: int = 24,
    ) -> list[dict[str, Any]]:
        """
        Get historical KPI data for charting.
        
        Args:
            site_name: Site identifier
            kpi_name: Name of the KPI (e.g., call_setup_success_rate)
            hours: Number of hours of history to retrieve
            
        Returns:
            List of {timestamp, value} dictionaries for charting
        """
        await self._ensure_initialized()

        # Resolve site_id from site_name
        site_id = await self._resolve_site_id(site_name)

        if not site_id:
            logger.warning(f"Could not resolve site: {site_name}")
            return []

        try:
            # Convert hours to days for repository method
            days = max(1, hours // 24)

            history = await self._repository.get_historical_kpis(
                site_id=site_id,
                kpi_name=kpi_name,
                days=days,
            )
            
            return [
                {
                    "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M") if hasattr(record.timestamp, "strftime") else str(record.timestamp),
                    "value": record.kpi_value,
                }
                for record in history
            ]
        except Exception as e:
            logger.warning(f"Failed to get KPI history: {e}")
            return []


# =============================================================================
# Singleton Instances
# =============================================================================

_site_service: SiteService | None = None
_kpi_service: KPIService | None = None


def get_site_service() -> SiteService:
    """Get singleton site service instance."""
    global _site_service
    if _site_service is None:
        _site_service = SiteService()
    return _site_service


def get_kpi_service() -> KPIService:
    """Get singleton KPI service instance."""
    global _kpi_service
    if _kpi_service is None:
        _kpi_service = KPIService()
    return _kpi_service
