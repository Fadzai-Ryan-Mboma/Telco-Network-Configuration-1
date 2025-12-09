"""
CSV Data Importer for historical network KPI data.

Parses CSV files from Huawei iMaster MAE exports and populates the database
with Sites, Cells, and KPI records.

CSV Format Expected:
- Date, eNodeB Name, Cell Name, LocalCell Id, eNodeB Function Name
- KPIs: RACH Setup Success Rate(%), DL IBLER[%], UL IBLER[%], etc.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from cassava_optimizer.domain.enums import CellState, KPIDirection, KPITier
from cassava_optimizer.domain.models import Cell, KPIMetric, KPIThreshold, Site
from cassava_optimizer.infrastructure.database import (
    CellModel,
    KPIRecordModel,
    SiteModel,
    get_session,
)

logger = logging.getLogger(__name__)


# =============================================================================
# KPI Column Mappings
# =============================================================================

# Map CSV column names to internal KPI names
KPI_COLUMN_MAP: dict[str, str] = {
    "RACH Setup Success Rate(%)": "rach_success_rate",
    "DL IBLER[%]": "dl_ibler",
    "UL IBLER[%]": "ul_ibler",
    "PDCCH CCE Usage Rate[%]": "pdcch_cce_usage",
    "PUCCHUsage Rate[%]": "pucch_usage",
    "DL Cell PDCP Layer Average Throughput(kbit/s)": "dl_throughput",
    "UL Cell PDCP Layer Average Throughput(kbit/s)": "ul_throughput",
}

# KPI units
KPI_UNITS: dict[str, str] = {
    "rach_success_rate": "%",
    "dl_ibler": "%",
    "ul_ibler": "%",
    "pdcch_cce_usage": "%",
    "pucch_usage": "%",
    "dl_throughput": "kbit/s",
    "ul_throughput": "kbit/s",
}


# =============================================================================
# CSV Data Importer
# =============================================================================

class CSVDataImporter:
    """
    Import historical KPI data from CSV files into the database.
    
    Handles:
    - Auto-discovery of sites from CSV data
    - Cell extraction per site
    - KPI record creation with timestamps
    - Idempotent imports (skip duplicates)
    """
    
    def __init__(self, data_dir: str | Path | None = None) -> None:
        """
        Initialize the importer.
        
        Args:
            data_dir: Directory containing CSV files. Defaults to /app/data/ in Docker,
                     or ./data/ relative to workspace root.
        """
        import os
        
        if data_dir is None:
            # Check environment variable first (set in Docker)
            env_data_dir = os.getenv("CASSAVA_DATA_DIR")
            if env_data_dir:
                self.data_dir = Path(env_data_dir)
            # Check if running in Docker (/app/data exists)
            elif Path("/app/data").exists():
                self.data_dir = Path("/app/data")
            else:
                # Fall back to relative path from source file
                self.data_dir = Path(__file__).parent.parent.parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)
        
        logger.info(f"Data importer initialized with data_dir: {self.data_dir}")
        self._sites_cache: dict[str, dict[str, Any]] = {}
        self._cells_cache: dict[str, dict[str, Any]] = {}
    
    async def import_all_csv_files(self) -> dict[str, int]:
        """
        Import all CSV files from the data directory.
        
        Returns:
            Summary dict with counts: {'sites': N, 'cells': N, 'kpi_records': N}
        """
        csv_files = list(self.data_dir.glob("*.csv"))
        
        if not csv_files:
            logger.warning(f"No CSV files found in {self.data_dir}")
            return {"sites": 0, "cells": 0, "kpi_records": 0}
        
        total_sites = 0
        total_cells = 0
        total_kpis = 0
        
        for csv_file in csv_files:
            logger.info(f"Importing {csv_file.name}...")
            try:
                result = await self.import_csv_file(csv_file)
                total_sites += result["sites"]
                total_cells += result["cells"]
                total_kpis += result["kpi_records"]
            except Exception as e:
                logger.error(f"Error importing {csv_file.name}: {e}")
                raise
        
        logger.info(
            f"Import complete: {total_sites} sites, {total_cells} cells, "
            f"{total_kpis} KPI records"
        )
        
        return {
            "sites": total_sites,
            "cells": total_cells,
            "kpi_records": total_kpis,
        }
    
    async def import_csv_file(self, csv_path: Path) -> dict[str, int]:
        """
        Import a single CSV file.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            Summary dict with counts
        """
        # Parse CSV into structured data
        raw_data = self._parse_csv(csv_path)
        
        if not raw_data:
            return {"sites": 0, "cells": 0, "kpi_records": 0}
        
        # Extract unique sites and cells
        sites_data = self._extract_sites(raw_data)
        cells_data = self._extract_cells(raw_data)
        kpi_records = self._extract_kpi_records(raw_data)
        
        # Save to database
        async with get_session() as session:
            # Insert sites
            sites_created = 0
            for site_id, site_info in sites_data.items():
                # Check if site exists
                stmt = select(SiteModel).where(SiteModel.site_id == site_id)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    site_model = SiteModel(
                        site_id=site_id,
                        site_name=site_info["name"],
                        enodeb_id=site_info["enodeb_id"],
                        latitude=site_info["latitude"],
                        longitude=site_info["longitude"],
                        region=site_info["region"],
                        cluster=site_info["cluster"],
                    )
                    session.add(site_model)
                    sites_created += 1
                    logger.debug(f"Created site: {site_id}")
            
            # Flush to ensure sites exist before adding cells
            await session.flush()
            
            # Insert cells
            cells_created = 0
            for cell_id, cell_info in cells_data.items():
                stmt = select(CellModel).where(CellModel.cell_id == cell_id)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    cell_model = CellModel(
                        cell_id=cell_id,
                        local_cell_id=cell_info["local_cell_id"],
                        cell_name=cell_info["name"],
                        site_id=cell_info["site_id"],
                        pci=cell_info["pci"],
                        tac=cell_info["tac"],
                        earfcn=cell_info["earfcn"],
                        bandwidth=cell_info["bandwidth"],
                        azimuth=cell_info["azimuth"],
                        electrical_tilt=cell_info["electrical_tilt"],
                        mechanical_tilt=cell_info["mechanical_tilt"],
                        tx_power=cell_info["tx_power"],
                        state=CellState.ACTIVE.value,
                    )
                    session.add(cell_model)
                    cells_created += 1
                    logger.debug(f"Created cell: {cell_id}")
            
            await session.flush()
            
            # Insert KPI records
            kpis_created = 0
            for record in kpi_records:
                # Check for duplicate (same site, cell, kpi, timestamp)
                stmt = select(KPIRecordModel).where(
                    KPIRecordModel.site_id == record["site_id"],
                    KPIRecordModel.cell_id == record["cell_id"],
                    KPIRecordModel.kpi_name == record["kpi_name"],
                    KPIRecordModel.timestamp == record["timestamp"],
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    kpi_model = KPIRecordModel(
                        site_id=record["site_id"],
                        cell_id=record["cell_id"],
                        kpi_name=record["kpi_name"],
                        kpi_value=record["value"],
                        unit=record["unit"],
                        timestamp=record["timestamp"],
                        source="csv_import",
                    )
                    session.add(kpi_model)
                    kpis_created += 1
        
        logger.info(
            f"Imported from {csv_path.name}: {sites_created} sites, "
            f"{cells_created} cells, {kpis_created} KPI records"
        )
        
        return {
            "sites": sites_created,
            "cells": cells_created,
            "kpi_records": kpis_created,
        }
    
    def _parse_csv(self, csv_path: Path) -> list[dict[str, Any]]:
        """Parse CSV file into list of row dictionaries."""
        rows = []
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        
        logger.debug(f"Parsed {len(rows)} rows from {csv_path.name}")
        return rows
    
    def _extract_sites(self, raw_data: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """
        Extract unique sites from CSV data.
        
        Uses eNodeB Name as site identifier.
        Generates placeholder coordinates for Zimbabwe sites.
        """
        sites: dict[str, dict[str, Any]] = {}
        
        # Zimbabwe approximate coordinates for demo
        ZIMBABWE_BASE_LAT = -17.8252
        ZIMBABWE_BASE_LON = 31.0335
        
        for idx, row in enumerate(raw_data):
            enodeb_name = row.get("eNodeB Name", "").strip()
            
            if not enodeb_name or enodeb_name in sites:
                continue
            
            # Generate site_id from name (sanitize)
            site_id = enodeb_name.replace(" ", "_").replace("-", "_")
            
            # Extract region from name if possible
            region = "Zimbabwe"
            if "Bindura" in enodeb_name:
                region = "Mashonaland Central"
            elif "Chiwaridzo" in enodeb_name or "Chipadze" in enodeb_name:
                region = "Mashonaland Central"
            
            # Generate pseudo-random coordinates based on index
            lat_offset = (hash(enodeb_name) % 100) / 1000
            lon_offset = (hash(enodeb_name[::-1]) % 100) / 1000
            
            sites[site_id] = {
                "name": enodeb_name,
                "enodeb_id": hash(enodeb_name) % 100000,  # Generate from name
                "latitude": ZIMBABWE_BASE_LAT + lat_offset,
                "longitude": ZIMBABWE_BASE_LON + lon_offset,
                "region": region,
                "cluster": "Bindura Cluster",
            }
        
        return sites
    
    def _extract_cells(self, raw_data: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """
        Extract unique cells from CSV data.
        
        Uses combination of site + LocalCell Id as identifier.
        """
        cells: dict[str, dict[str, Any]] = {}
        
        for row in raw_data:
            enodeb_name = row.get("eNodeB Name", "").strip()
            cell_name = row.get("Cell Name", "").strip()
            local_cell_id_str = row.get("LocalCell Id", "0")
            
            if not enodeb_name or not cell_name:
                continue
            
            try:
                local_cell_id = int(local_cell_id_str)
            except ValueError:
                local_cell_id = 0
            
            site_id = enodeb_name.replace(" ", "_").replace("-", "_")
            cell_id = f"{site_id}_cell_{local_cell_id}"
            
            if cell_id in cells:
                continue
            
            # Generate reasonable cell parameters
            # PCI: 0-503, distributed based on local cell ID
            pci = (hash(cell_name) % 504)
            
            # TAC: Tracking Area Code, same for site
            tac = hash(site_id) % 65535
            
            # EARFCN: Common LTE bands for Zimbabwe (Band 3, 7, 28)
            earfcn_options = [1575, 2850, 9410]  # Band 3, 7, 28 DL
            earfcn = earfcn_options[local_cell_id % 3]
            
            # Bandwidth: 10 or 20 MHz
            bandwidth = 20 if local_cell_id % 2 == 0 else 10
            
            # Azimuth: Distribute sectors around 360 degrees
            azimuth = (local_cell_id * 60) % 360
            
            cells[cell_id] = {
                "local_cell_id": local_cell_id,
                "name": cell_name,
                "site_id": site_id,
                "pci": pci,
                "tac": tac,
                "earfcn": earfcn,
                "bandwidth": bandwidth,
                "azimuth": float(azimuth),
                "electrical_tilt": 3.0 + (local_cell_id % 3),
                "mechanical_tilt": 2.0,
                "tx_power": 43.0,  # Common LTE macro power
            }
        
        return cells
    
    def _extract_kpi_records(
        self,
        raw_data: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Extract KPI records from CSV data.
        
        Creates one record per cell per KPI per timestamp.
        """
        records: list[dict[str, Any]] = []
        
        for row in raw_data:
            enodeb_name = row.get("eNodeB Name", "").strip()
            cell_name = row.get("Cell Name", "").strip()
            local_cell_id_str = row.get("LocalCell Id", "0")
            date_str = row.get("Date", "").strip()
            
            if not enodeb_name or not date_str:
                continue
            
            try:
                local_cell_id = int(local_cell_id_str)
            except ValueError:
                local_cell_id = 0
            
            site_id = enodeb_name.replace(" ", "_").replace("-", "_")
            cell_id = f"{site_id}_cell_{local_cell_id}"
            
            # Parse date
            try:
                timestamp = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Invalid date format: {date_str}")
                continue
            
            # Extract each KPI column
            for csv_col, kpi_name in KPI_COLUMN_MAP.items():
                value_str = row.get(csv_col, "").strip()
                
                if not value_str:
                    continue
                
                try:
                    value = float(value_str)
                except ValueError:
                    logger.warning(f"Invalid KPI value: {value_str} for {kpi_name}")
                    continue
                
                records.append({
                    "site_id": site_id,
                    "cell_id": cell_id,
                    "kpi_name": kpi_name,
                    "value": value,
                    "unit": KPI_UNITS.get(kpi_name, ""),
                    "timestamp": timestamp,
                })
        
        return records
    
    async def get_sites_summary(self) -> list[dict[str, Any]]:
        """
        Get summary of all sites in the database.
        
        Returns:
            List of site summaries with cell counts and latest KPIs
        """
        from sqlalchemy import func, select
        
        async with get_session() as session:
            # Get sites with cell counts
            stmt = (
                select(
                    SiteModel.site_id,
                    SiteModel.site_name,
                    SiteModel.region,
                    func.count(CellModel.id).label("cell_count"),
                )
                .outerjoin(CellModel, SiteModel.site_id == CellModel.site_id)
                .group_by(SiteModel.site_id, SiteModel.site_name, SiteModel.region)
            )
            
            result = await session.execute(stmt)
            sites = result.all()
            
            return [
                {
                    "site_id": row.site_id,
                    "site_name": row.site_name,
                    "region": row.region,
                    "cell_count": row.cell_count,
                }
                for row in sites
            ]


# =============================================================================
# CLI Entry Point
# =============================================================================

async def run_import() -> None:
    """Run the CSV import from command line."""
    from cassava_optimizer.infrastructure.database import init_database
    
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    await init_database()
    
    # Run import
    importer = CSVDataImporter()
    result = await importer.import_all_csv_files()
    
    print(f"\n✅ Import Complete:")
    print(f"   Sites: {result['sites']}")
    print(f"   Cells: {result['cells']}")
    print(f"   KPI Records: {result['kpi_records']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_import())
