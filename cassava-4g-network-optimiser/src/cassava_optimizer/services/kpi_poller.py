"""
KPI Polling Service for real-time network data collection.

Polls the Huawei iMaster MAE API at configurable intervals:
- 60 seconds for active optimization site
- 5 minutes for background monitoring

Implements fail-fast error handling with no cache fallback.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Callable

from cassava_optimizer.infrastructure.huawei_client import HuaweiMAEClient
from cassava_optimizer.infrastructure.repository import NetworkRepository
from cassava_optimizer.domain.exceptions import HuaweiAPIError

logger = logging.getLogger(__name__)


class KPIPoller:
    """
    Background KPI polling service.
    
    Polls the Huawei API at two different intervals:
    - Active site (user is optimizing): 60 seconds
    - Background sites: 5 minutes (300 seconds)
    """
    
    def __init__(
        self,
        active_interval: int = 60,
        background_interval: int = 300,
    ) -> None:
        """
        Initialize the KPI poller.
        
        Args:
            active_interval: Polling interval for active site (seconds)
            background_interval: Polling interval for background sites (seconds)
        """
        # Read from environment or use defaults
        self.active_interval = int(
            os.getenv("POLLING_ACTIVE_INTERVAL", str(active_interval))
        )
        self.background_interval = int(
            os.getenv("POLLING_BACKGROUND_INTERVAL", str(background_interval))
        )
        
        self._active_site: str | None = None
        self._running = False
        self._active_task: asyncio.Task | None = None
        self._background_task: asyncio.Task | None = None
        self._client: HuaweiMAEClient | None = None
        self._repository = NetworkRepository()
        
        # Callbacks for UI updates
        self._on_kpi_update: Callable[[str, dict], None] | None = None
        self._on_error: Callable[[str, Exception], None] | None = None
        
        logger.info(
            f"KPI Poller initialized: active={self.active_interval}s, "
            f"background={self.background_interval}s"
        )
    
    def set_callbacks(
        self,
        on_kpi_update: Callable[[str, dict], None] | None = None,
        on_error: Callable[[str, Exception], None] | None = None,
    ) -> None:
        """Set callbacks for KPI updates and errors."""
        self._on_kpi_update = on_kpi_update
        self._on_error = on_error
    
    def set_active_site(self, site_id: str | None) -> None:
        """
        Set the currently active site for optimization.
        
        The active site will be polled at the faster interval.
        
        Args:
            site_id: Site identifier or None to disable active polling
        """
        old_site = self._active_site
        self._active_site = site_id
        logger.info(f"Active site changed: {old_site} -> {site_id}")
    
    async def _create_client(self) -> HuaweiMAEClient:
        """Create and authenticate the Huawei API client."""
        host = os.getenv("MAE_HOST", "localhost")
        port = int(os.getenv("MAE_PORT", "31127"))
        username = os.getenv("MAE_USERNAME", "")
        password = os.getenv("MAE_PASSWORD", "")
        use_ssl = os.getenv("MAE_USE_SSL", "true").lower() == "true"
        
        client = HuaweiMAEClient(
            host=host,
            port=port,
            username=username,
            password=password,
            use_ssl=use_ssl,
            timeout=30,
            max_retries=3,
        )
        
        # Authenticate
        await client.authenticate()
        return client
    
    async def start(self) -> None:
        """Start the polling service."""
        if self._running:
            logger.warning("KPI Poller already running")
            return
        
        self._running = True
        logger.info("Starting KPI Poller...")
        
        try:
            self._client = await self._create_client()
        except Exception as e:
            logger.error(f"Failed to create Huawei client: {e}")
            self._running = False
            raise
        
        # Start polling tasks
        self._active_task = asyncio.create_task(self._poll_active_site())
        self._background_task = asyncio.create_task(self._poll_background_sites())
        
        logger.info("KPI Poller started")
    
    async def stop(self) -> None:
        """Stop the polling service."""
        if not self._running:
            return
        
        self._running = False
        logger.info("Stopping KPI Poller...")
        
        # Cancel tasks
        if self._active_task:
            self._active_task.cancel()
            try:
                await self._active_task
            except asyncio.CancelledError:
                pass
        
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        
        # Close client
        if self._client:
            await self._client.close()
            self._client = None
        
        logger.info("KPI Poller stopped")
    
    async def _poll_active_site(self) -> None:
        """Poll the active site at the faster interval."""
        while self._running:
            try:
                if self._active_site and self._client:
                    logger.debug(f"Polling active site: {self._active_site}")
                    kpis = await self._fetch_site_kpis(self._active_site)
                    
                    if kpis and self._on_kpi_update:
                        self._on_kpi_update(self._active_site, kpis)
                
                await asyncio.sleep(self.active_interval)
                
            except asyncio.CancelledError:
                break
            except HuaweiAPIError as e:
                # Fail-fast: report error, don't fall back to cache
                logger.error(f"API error polling active site: {e}")
                if self._on_error:
                    self._on_error(self._active_site or "", e)
                await asyncio.sleep(self.active_interval)
            except Exception as e:
                logger.exception(f"Unexpected error polling active site: {e}")
                await asyncio.sleep(self.active_interval)
    
    async def _poll_background_sites(self) -> None:
        """Poll all other sites at the slower interval."""
        while self._running:
            try:
                if self._client:
                    # Get all site IDs
                    site_ids = await self._repository.get_site_ids()
                    
                    for site_id in site_ids:
                        # Skip active site (handled by active poller)
                        if site_id == self._active_site:
                            continue
                        
                        if not self._running:
                            break
                        
                        logger.debug(f"Polling background site: {site_id}")
                        try:
                            kpis = await self._fetch_site_kpis(site_id)
                            if kpis and self._on_kpi_update:
                                self._on_kpi_update(site_id, kpis)
                        except HuaweiAPIError as e:
                            logger.warning(f"Failed to poll {site_id}: {e}")
                            if self._on_error:
                                self._on_error(site_id, e)
                        
                        # Small delay between sites to avoid rate limiting
                        await asyncio.sleep(1)
                
                await asyncio.sleep(self.background_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Unexpected error polling background sites: {e}")
                await asyncio.sleep(self.background_interval)
    
    async def _fetch_site_kpis(self, site_id: str) -> dict[str, Any]:
        """
        Fetch KPIs for a site from the Huawei API.
        
        Uses fail-fast error handling - no cache fallback.
        
        Args:
            site_id: Site identifier
            
        Returns:
            Dictionary of KPI values
            
        Raises:
            HuaweiAPIError: If API call fails
        """
        if not self._client:
            raise HuaweiAPIError("Huawei client not initialized")
        
        # Get KPIs from API
        kpi_data = await self._client.get_kpis(site_id)
        
        # Save to database for historical analysis
        if kpi_data:
            await self._save_kpis_to_db(site_id, kpi_data)
        
        return kpi_data
    
    async def _save_kpis_to_db(
        self,
        site_id: str,
        kpis: dict[str, Any],
    ) -> None:
        """Save KPI data to database for historical tracking."""
        try:
            from cassava_optimizer.domain.models import KPIMetric, KPIThreshold
            from cassava_optimizer.domain.enums import KPIDirection, KPITier
            
            metrics = []
            for kpi_name, value in kpis.items():
                if isinstance(value, (int, float)):
                    # Create minimal KPI metric for storage
                    metric = KPIMetric(
                        name=kpi_name,
                        display_name=kpi_name.replace("_", " ").title(),
                        value=float(value),
                        unit="%",
                        tier=KPITier.TIER_1,
                        direction=KPIDirection.HIGHER_IS_BETTER,
                        threshold=KPIThreshold(
                            critical=90.0,
                            warning=95.0,
                            target=99.0,
                        ),
                        site_id=site_id,
                        timestamp=datetime.utcnow(),
                    )
                    metrics.append(metric)
            
            if metrics:
                await self._repository.save_kpi_records(metrics)
                logger.debug(f"Saved {len(metrics)} KPI records for {site_id}")
                
        except Exception as e:
            logger.warning(f"Failed to save KPIs to database: {e}")
    
    async def poll_once(self, site_id: str) -> dict[str, Any]:
        """
        Poll a specific site once (on-demand).
        
        Useful for manual refresh or initial data load.
        
        Args:
            site_id: Site identifier
            
        Returns:
            Dictionary of KPI values
        """
        if not self._client:
            self._client = await self._create_client()
        
        return await self._fetch_site_kpis(site_id)


# =============================================================================
# Singleton Instance
# =============================================================================

_poller: KPIPoller | None = None


def get_kpi_poller() -> KPIPoller:
    """Get singleton KPI poller instance."""
    global _poller
    if _poller is None:
        _poller = KPIPoller()
    return _poller


async def start_polling() -> None:
    """Start the KPI polling service."""
    poller = get_kpi_poller()
    await poller.start()


async def stop_polling() -> None:
    """Stop the KPI polling service."""
    poller = get_kpi_poller()
    await poller.stop()
