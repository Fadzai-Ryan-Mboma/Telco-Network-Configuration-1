"""
Data Collector Agent - First stage of the optimization pipeline.

Responsible for gathering all necessary data from Huawei MAE API
and local database before analysis can begin.
"""

from typing import Any

import structlog

from cassava_optimizer.agents.base import AgentContext, AgentExecutionError, BaseAgent
from cassava_optimizer.domain.enums import AgentType
from cassava_optimizer.domain.exceptions import HuaweiAPIError
from cassava_optimizer.domain.kpi_definitions import get_kpi_registry, get_all_kpi_names
from cassava_optimizer.infrastructure.huawei_client import HuaweiMAEClient
from cassava_optimizer.infrastructure.repository import NetworkRepository

logger = structlog.get_logger(__name__)


class DataCollectorAgent(BaseAgent):
    """
    Agent responsible for collecting network data from all sources.
    
    Collects:
    - Site configuration from Huawei MAE
    - Current KPI values from MAE performance API
    - Historical KPI data from local database
    - Cell parameters and configurations
    
    Fail-fast behavior: Raises error if any data source is unavailable.
    """
    
    def __init__(
        self,
        huawei_client: HuaweiMAEClient,
        repository: NetworkRepository,
    ) -> None:
        """
        Initialize the data collector agent.
        
        Args:
            huawei_client: Async client for Huawei MAE API
            repository: Database repository for historical data
        """
        super().__init__()
        self._huawei = huawei_client
        self._repo = repository
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.DATA_COLLECTOR
    
    async def _validate_preconditions(self, context: AgentContext) -> None:
        """Validate that we can connect to data sources."""
        await super()._validate_preconditions(context)
        
        # Validate Huawei connection
        try:
            await self._huawei.authenticate()
        except HuaweiAPIError as e:
            raise AgentExecutionError(
                f"Cannot connect to Huawei MAE API: {e}",
                agent_type=self.agent_type,
                step="precondition_check",
                cause=e,
            )
    
    async def _execute(self, context: AgentContext) -> dict[str, Any]:
        """
        Collect all necessary data for the optimization pipeline.
        
        Returns:
            Dictionary containing:
            - site: Site configuration details
            - cells: List of cell configurations
            - current_kpis: Current KPI values from live network
            - historical_kpis: Historical KPI data from database
            - parameters: Current parameter configurations
        """
        site_id = context.site_id
        
        self._log.info("Starting data collection", site_id=site_id)
        
        # 1. Get site details from Huawei MAE
        site = await self._collect_site_data(site_id)
        
        # 2. Get current KPIs from live network
        current_kpis = await self._collect_current_kpis(site_id)
        
        # 3. Get historical KPIs from database
        historical_kpis = await self._collect_historical_kpis(site_id)
        
        # 4. Get current parameter configurations
        parameters = await self._collect_parameters(site_id)
        
        # Build output dictionary
        output = {
            "site": {
                "site_id": site.site_id,
                "site_name": site.site_name,
                "enodeb_id": site.enodeb_id,
                "latitude": site.latitude,
                "longitude": site.longitude,
                "region": site.region,
                "cluster": site.cluster,
            },
            "cells": [
                {
                    "cell_id": cell.cell_id,
                    "cell_name": cell.cell_name,
                    "local_cell_id": cell.local_cell_id,
                    "pci": cell.pci,
                    "tac": cell.tac,
                    "earfcn": cell.earfcn,
                    "bandwidth": cell.bandwidth,
                    "azimuth": cell.azimuth,
                    "electrical_tilt": cell.electrical_tilt,
                    "mechanical_tilt": cell.mechanical_tilt,
                    "tx_power": cell.tx_power,
                    "state": cell.state.value,
                }
                for cell in site.cells
            ],
            "current_kpis": current_kpis,
            "historical_kpis": historical_kpis,
            "parameters": parameters,
            "collection_metadata": {
                "total_kpis_collected": len(current_kpis),
                "total_cells": len(site.cells),
                "historical_days": 7,
            },
        }
        
        # Store in shared context for other agents
        context.collected_data = output
        
        self._log.info(
            "Data collection complete",
            site_id=site_id,
            cells=len(site.cells),
            kpis=len(current_kpis),
        )
        
        return output
    
    async def _collect_site_data(self, site_id: str) -> Any:
        """
        Collect site configuration from Huawei MAE.
        
        Raises:
            HuaweiAPIError: If site data cannot be retrieved
        """
        self._log.debug("Collecting site data", site_id=site_id)
        
        try:
            site = await self._huawei.get_site_details(site_id)
            
            if not site:
                raise HuaweiAPIError(
                    f"Site {site_id} not found in network",
                    endpoint=f"/nodes/node={site_id}",
                )
            
            self._log.debug(
                "Site data collected",
                site_id=site_id,
                cells=len(site.cells),
            )
            
            return site
            
        except HuaweiAPIError:
            raise
        except Exception as e:
            raise HuaweiAPIError(
                f"Failed to collect site data: {e}",
                cause=e,
            )
    
    async def _collect_current_kpis(self, site_id: str) -> dict[str, dict[str, Any]]:
        """
        Collect current KPI values from live network.
        
        Returns:
            Dictionary mapping KPI names to their current values and metadata
        """
        self._log.debug("Collecting current KPIs", site_id=site_id)
        
        # Get all defined KPI names
        kpi_names = list(KPI_DEFINITIONS.keys())
        
        try:
            kpi_metrics = await self._huawei.get_kpi_data(site_id, kpi_names)
            
            # Convert to dictionary format
            kpis = {}
            for metric in kpi_metrics:
                kpis[metric.definition.name] = {
                    "value": metric.value,
                    "unit": metric.definition.unit,
                    "category": metric.definition.category.value,
                    "target_min": metric.definition.target_min,
                    "target_max": metric.definition.target_max,
                    "critical_threshold": metric.definition.critical_threshold,
                    "status": metric.status.value,
                    "timestamp": metric.timestamp.isoformat() if metric.timestamp else None,
                }
            
            self._log.debug("Current KPIs collected", count=len(kpis))
            return kpis
            
        except HuaweiAPIError:
            raise
        except Exception as e:
            raise HuaweiAPIError(
                f"Failed to collect KPI data: {e}",
                cause=e,
            )
    
    async def _collect_historical_kpis(
        self,
        site_id: str,
        days: int = 7,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Collect historical KPI data from local database.
        
        Args:
            site_id: Site identifier
            days: Number of days of history to retrieve
            
        Returns:
            Dictionary mapping KPI names to lists of historical values
        """
        self._log.debug("Collecting historical KPIs", site_id=site_id, days=days)
        
        try:
            # Get site from database by name/id
            site = await self._repo.get_site_by_name(site_id)
            
            if not site:
                self._log.warning(
                    "No historical data found for site",
                    site_id=site_id,
                )
                return {}
            
            # Get historical KPIs
            historical_kpis = await self._repo.get_kpis_for_site(
                site.site_id,
                days=days,
            )
            
            # Group by KPI name
            grouped: dict[str, list[dict[str, Any]]] = {}
            for kpi in historical_kpis:
                if kpi.kpi_name not in grouped:
                    grouped[kpi.kpi_name] = []
                
                grouped[kpi.kpi_name].append({
                    "value": kpi.value,
                    "timestamp": kpi.timestamp.isoformat(),
                    "cell_id": kpi.cell_id,
                })
            
            self._log.debug(
                "Historical KPIs collected",
                kpi_count=len(grouped),
                total_records=sum(len(v) for v in grouped.values()),
            )
            
            return grouped
            
        except Exception as e:
            # Historical data is helpful but not critical - log warning and continue
            self._log.warning(
                "Failed to collect historical KPIs",
                site_id=site_id,
                error=str(e),
            )
            return {}
    
    async def _collect_parameters(
        self,
        site_id: str,
    ) -> dict[str, dict[str, Any]]:
        """
        Collect current parameter configurations from database.
        
        Returns:
            Dictionary mapping parameter names to their configurations
        """
        self._log.debug("Collecting parameters", site_id=site_id)
        
        try:
            site = await self._repo.get_site_by_name(site_id)
            
            if not site:
                return {}
            
            parameters = await self._repo.get_parameters_for_site(site.site_id)
            
            params_dict = {}
            for param in parameters:
                params_dict[param.parameter_name] = {
                    "value": param.value,
                    "unit": param.unit,
                    "cell_id": param.cell_id,
                    "last_modified": param.last_modified.isoformat() if param.last_modified else None,
                }
            
            self._log.debug("Parameters collected", count=len(params_dict))
            return params_dict
            
        except Exception as e:
            self._log.warning(
                "Failed to collect parameters",
                site_id=site_id,
                error=str(e),
            )
            return {}
