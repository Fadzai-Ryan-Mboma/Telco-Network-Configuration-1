"""
Repository pattern for database access.

Provides async methods for CRUD operations on network entities.
"""

from datetime import datetime, timedelta
from typing import Sequence

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cassava_optimizer.domain.enums import CellState
from cassava_optimizer.domain.exceptions import CellNotFoundError, DatabaseError, SiteNotFoundError
from cassava_optimizer.domain.models import Cell, HistoricalRecord, KPIMetric, Site
from cassava_optimizer.infrastructure.database import (
    CellModel,
    CommandExecutionModel,
    KPIRecordModel,
    OptimizationHistoryModel,
    SiteModel,
    get_session,
)


class NetworkRepository:
    """
    Repository for network topology and KPI data.
    
    All methods are async and use fail-fast error handling.
    """
    
    def __init__(self, session: AsyncSession | None = None) -> None:
        """
        Initialize repository.
        
        Args:
            session: Optional session for testing. If None, uses context manager.
        """
        self._session = session
    
    # =========================================================================
    # Site Operations
    # =========================================================================
    
    async def get_all_sites(self) -> list[Site]:
        """
        Get all sites with their cells.
        
        Returns:
            List of Site domain models
        """
        async with get_session() as session:
            stmt = select(SiteModel).options(selectinload(SiteModel.cells))
            result = await session.execute(stmt)
            site_models = result.scalars().all()
            
            return [self._site_model_to_domain(sm) for sm in site_models]
    
    async def get_site(self, site_id: str) -> Site:
        """
        Get a site by ID.
        
        Args:
            site_id: Site identifier
            
        Returns:
            Site domain model
            
        Raises:
            SiteNotFoundError: If site doesn't exist
        """
        async with get_session() as session:
            stmt = (
                select(SiteModel)
                .where(SiteModel.site_id == site_id)
                .options(selectinload(SiteModel.cells))
            )
            result = await session.execute(stmt)
            site_model = result.scalar_one_or_none()
            
            if site_model is None:
                raise SiteNotFoundError(site_id)
            
            return self._site_model_to_domain(site_model)
    
    async def get_site_ids(self) -> list[str]:
        """Get all site IDs."""
        async with get_session() as session:
            stmt = select(SiteModel.site_id).order_by(SiteModel.site_name)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def upsert_site(self, site: Site) -> None:
        """
        Insert or update a site.
        
        Args:
            site: Site domain model to save
        """
        async with get_session() as session:
            # Check if site exists
            stmt = select(SiteModel).where(SiteModel.site_id == site.site_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing
                await session.execute(
                    update(SiteModel)
                    .where(SiteModel.site_id == site.site_id)
                    .values(
                        site_name=site.site_name,
                        enodeb_id=site.enodeb_id,
                        latitude=site.latitude,
                        longitude=site.longitude,
                        region=site.region,
                        cluster=site.cluster,
                        updated_at=datetime.utcnow(),
                    )
                )
            else:
                # Insert new
                site_model = SiteModel(
                    site_id=site.site_id,
                    site_name=site.site_name,
                    enodeb_id=site.enodeb_id,
                    latitude=site.latitude,
                    longitude=site.longitude,
                    region=site.region,
                    cluster=site.cluster,
                )
                session.add(site_model)
            
            # Upsert cells
            for cell in site.cells:
                await self._upsert_cell(session, cell, site.site_id)
    
    # =========================================================================
    # Cell Operations
    # =========================================================================
    
    async def get_cell(self, cell_id: str) -> Cell:
        """
        Get a cell by ID.
        
        Args:
            cell_id: Cell identifier
            
        Returns:
            Cell domain model
            
        Raises:
            CellNotFoundError: If cell doesn't exist
        """
        async with get_session() as session:
            stmt = select(CellModel).where(CellModel.cell_id == cell_id)
            result = await session.execute(stmt)
            cell_model = result.scalar_one_or_none()
            
            if cell_model is None:
                raise CellNotFoundError(cell_id)
            
            return self._cell_model_to_domain(cell_model)
    
    async def get_cells_for_site(self, site_id: str) -> list[Cell]:
        """Get all cells for a site."""
        async with get_session() as session:
            stmt = select(CellModel).where(CellModel.site_id == site_id)
            result = await session.execute(stmt)
            return [self._cell_model_to_domain(cm) for cm in result.scalars().all()]
    
    async def _upsert_cell(
        self,
        session: AsyncSession,
        cell: Cell,
        site_id: str,
    ) -> None:
        """Insert or update a cell (internal method)."""
        stmt = select(CellModel).where(CellModel.cell_id == cell.cell_id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            await session.execute(
                update(CellModel)
                .where(CellModel.cell_id == cell.cell_id)
                .values(
                    local_cell_id=cell.local_cell_id,
                    cell_name=cell.cell_name,
                    pci=cell.pci,
                    tac=cell.tac,
                    earfcn=cell.earfcn,
                    bandwidth=cell.bandwidth,
                    azimuth=cell.azimuth,
                    electrical_tilt=cell.electrical_tilt,
                    mechanical_tilt=cell.mechanical_tilt,
                    tx_power=cell.tx_power,
                    state=cell.state.value,
                    updated_at=datetime.utcnow(),
                )
            )
        else:
            cell_model = CellModel(
                cell_id=cell.cell_id,
                local_cell_id=cell.local_cell_id,
                cell_name=cell.cell_name,
                site_id=site_id,
                pci=cell.pci,
                tac=cell.tac,
                earfcn=cell.earfcn,
                bandwidth=cell.bandwidth,
                azimuth=cell.azimuth,
                electrical_tilt=cell.electrical_tilt,
                mechanical_tilt=cell.mechanical_tilt,
                tx_power=cell.tx_power,
                state=cell.state.value,
            )
            session.add(cell_model)
    
    # =========================================================================
    # KPI Record Operations
    # =========================================================================
    
    async def save_kpi_records(
        self,
        records: list[KPIMetric],
    ) -> int:
        """
        Save KPI metrics as historical records.
        
        Args:
            records: List of KPI metrics to save
            
        Returns:
            Number of records saved
        """
        async with get_session() as session:
            for metric in records:
                record = KPIRecordModel(
                    site_id=metric.site_id,
                    cell_id=metric.cell_id,
                    kpi_name=metric.name,
                    kpi_value=metric.value,
                    unit=metric.unit,
                    timestamp=metric.timestamp,
                    source="api",
                )
                session.add(record)
            
            return len(records)
    
    async def get_historical_kpis(
        self,
        site_id: str,
        kpi_name: str,
        days: int = 7,
    ) -> list[HistoricalRecord]:
        """
        Get historical KPI values for a site.
        
        Args:
            site_id: Site identifier
            kpi_name: KPI name to retrieve
            days: Number of days of history
            
        Returns:
            List of historical records
        """
        async with get_session() as session:
            since = datetime.utcnow() - timedelta(days=days)
            
            stmt = (
                select(KPIRecordModel)
                .where(
                    KPIRecordModel.site_id == site_id,
                    KPIRecordModel.kpi_name == kpi_name,
                    KPIRecordModel.timestamp >= since,
                )
                .order_by(KPIRecordModel.timestamp.desc())
            )
            
            result = await session.execute(stmt)
            return [
                HistoricalRecord(
                    id=r.id,
                    site_id=r.site_id,
                    cell_id=r.cell_id,
                    timestamp=r.timestamp,
                    kpi_name=r.kpi_name,
                    kpi_value=r.kpi_value,
                )
                for r in result.scalars().all()
            ]
    
    async def get_kpi_baseline(
        self,
        site_id: str,
        kpi_name: str,
        days: int = 30,
    ) -> dict[str, float]:
        """
        Calculate KPI baseline statistics.
        
        Args:
            site_id: Site identifier
            kpi_name: KPI name
            days: Days for baseline calculation
            
        Returns:
            Dict with mean, min, max, stddev
        """
        async with get_session() as session:
            since = datetime.utcnow() - timedelta(days=days)
            
            stmt = (
                select(
                    func.avg(KPIRecordModel.kpi_value).label("mean"),
                    func.min(KPIRecordModel.kpi_value).label("min"),
                    func.max(KPIRecordModel.kpi_value).label("max"),
                    func.count(KPIRecordModel.id).label("count"),
                )
                .where(
                    KPIRecordModel.site_id == site_id,
                    KPIRecordModel.kpi_name == kpi_name,
                    KPIRecordModel.timestamp >= since,
                )
            )
            
            result = await session.execute(stmt)
            row = result.one()
            
            return {
                "mean": row.mean or 0.0,
                "min": row.min or 0.0,
                "max": row.max or 0.0,
                "count": row.count or 0,
            }
    
    # =========================================================================
    # Optimization History Operations
    # =========================================================================
    
    async def save_optimization_session(
        self,
        session_id: str,
        site_id: str,
        query: str,
        recommendations_json: str = "{}",
        commands_json: str = "{}",
        success: bool = False,
        error_message: str = "",
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        """Save optimization session to history."""
        async with get_session() as session:
            duration = None
            if started_at and completed_at:
                duration = (completed_at - started_at).total_seconds()
            
            record = OptimizationHistoryModel(
                session_id=session_id,
                site_id=site_id,
                query=query,
                recommendations_json=recommendations_json,
                commands_json=commands_json,
                success=success,
                error_message=error_message,
                started_at=started_at or datetime.utcnow(),
                completed_at=completed_at,
                duration_seconds=duration,
            )
            session.add(record)
    
    async def get_recent_optimizations(
        self,
        site_id: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Get recent optimization sessions."""
        async with get_session() as session:
            stmt = select(OptimizationHistoryModel)
            
            if site_id:
                stmt = stmt.where(OptimizationHistoryModel.site_id == site_id)
            
            stmt = stmt.order_by(OptimizationHistoryModel.started_at.desc()).limit(limit)
            
            result = await session.execute(stmt)
            return [
                {
                    "session_id": r.session_id,
                    "site_id": r.site_id,
                    "query": r.query,
                    "success": r.success,
                    "started_at": r.started_at,
                    "duration_seconds": r.duration_seconds,
                }
                for r in result.scalars().all()
            ]
    
    # =========================================================================
    # Model Converters
    # =========================================================================
    
    def _site_model_to_domain(self, model: SiteModel) -> Site:
        """Convert SiteModel to Site domain object."""
        cells = tuple(
            self._cell_model_to_domain(cm)
            for cm in model.cells
        )
        
        return Site(
            site_id=model.site_id,
            site_name=model.site_name,
            enodeb_id=model.enodeb_id,
            latitude=model.latitude,
            longitude=model.longitude,
            region=model.region or "",
            cluster=model.cluster or "",
            cells=cells,
            last_updated=model.updated_at or model.created_at,
        )
    
    def _cell_model_to_domain(self, model: CellModel) -> Cell:
        """Convert CellModel to Cell domain object."""
        return Cell(
            cell_id=model.cell_id,
            local_cell_id=model.local_cell_id,
            cell_name=model.cell_name,
            site_id=model.site_id,
            pci=model.pci,
            tac=model.tac,
            earfcn=model.earfcn,
            bandwidth=model.bandwidth,
            azimuth=model.azimuth,
            electrical_tilt=model.electrical_tilt or 0.0,
            mechanical_tilt=model.mechanical_tilt or 0.0,
            tx_power=model.tx_power,
            state=CellState(model.state) if model.state else CellState.UNKNOWN,
            last_updated=model.updated_at or model.created_at,
        )
