"""
Network Repository

Data access layer for network sites and cells.
"""

from datetime import datetime
from typing import List, Optional

from liquid4g.domain.models.network import NetworkSite, NetworkCell
from liquid4g.infrastructure.repositories.base_repository import BaseRepository
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import DatabaseError

logger = get_logger(__name__)


class NetworkRepository(BaseRepository[NetworkSite]):
    """Repository for network sites and cells"""

    # ===== NetworkSite Operations =====

    def create(self, site: NetworkSite) -> NetworkSite:
        """
        Create a new network site

        Args:
            site: NetworkSite to create

        Returns:
            NetworkSite: Created site with ID
        """
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO network_sites (
                        site_id, site_name, location, latitude, longitude,
                        region, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        site.site_id,
                        site.site_name,
                        site.location,
                        site.latitude,
                        site.longitude,
                        site.region,
                        site.status.value if hasattr(site.status, 'value') else site.status,
                        site.created_at.isoformat(),
                        site.updated_at.isoformat() if site.updated_at else None,
                    ),
                )
                site.id = cursor.lastrowid

            logger.info(f"Created network site: {site.site_id}")
            return site

        except Exception as e:
            logger.error(f"Failed to create network site: {e}")
            raise DatabaseError(f"Failed to create network site: {e}")

    def get_by_id(self, site_id: int) -> Optional[NetworkSite]:
        """Get site by database ID"""
        try:
            with self.db.cursor() as cur:
                cur.execute("SELECT * FROM network_sites WHERE id = ?;", (site_id,))
                row = cur.fetchone()
                return self._row_to_site(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get site by ID: {e}")
            return None

    def get_by_site_id(self, site_id: str) -> Optional[NetworkSite]:
        """
        Get site by site_id

        Args:
            site_id: Site identifier (e.g., HARARE_001)

        Returns:
            Optional[NetworkSite]: Site or None
        """
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM network_sites WHERE site_id = ?;", (site_id,)
                )
                row = cur.fetchone()
                return self._row_to_site(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get site {site_id}: {e}")
            return None

    def update(self, site: NetworkSite) -> NetworkSite:
        """Update network site"""
        try:
            with self.db.transaction() as conn:
                conn.execute(
                    """
                    UPDATE network_sites
                    SET site_name = ?, location = ?, latitude = ?, longitude = ?,
                        region = ?, status = ?, updated_at = ?
                    WHERE site_id = ?;
                    """,
                    (
                        site.site_name,
                        site.location,
                        site.latitude,
                        site.longitude,
                        site.region,
                        site.status.value if hasattr(site.status, 'value') else site.status,
                        datetime.utcnow().isoformat(),
                        site.site_id,
                    ),
                )

            logger.info(f"Updated network site: {site.site_id}")
            return site

        except Exception as e:
            logger.error(f"Failed to update site: {e}")
            raise DatabaseError(f"Failed to update site: {e}")

    def delete(self, site_id: int) -> bool:
        """Delete network site by database ID"""
        try:
            with self.db.transaction() as conn:
                conn.execute("DELETE FROM network_sites WHERE id = ?;", (site_id,))
            logger.info(f"Deleted network site ID: {site_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete site: {e}")
            return False

    def list_all(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[NetworkSite]:
        """List all network sites"""
        query = "SELECT * FROM network_sites ORDER BY site_id"
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"

        try:
            with self.db.cursor() as cur:
                cur.execute(query)
                return [self._row_to_site(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list sites: {e}")
            return []

    def list_by_status(self, status: str) -> List[NetworkSite]:
        """
        List sites by status

        Args:
            status: Site status (active/inactive/maintenance)

        Returns:
            List[NetworkSite]: Sites with matching status
        """
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM network_sites WHERE status = ? ORDER BY site_id;",
                    (status,),
                )
                return [self._row_to_site(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list sites by status: {e}")
            return []

    def list_by_region(self, region: str) -> List[NetworkSite]:
        """List sites by region"""
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM network_sites WHERE region = ? ORDER BY site_id;",
                    (region,),
                )
                return [self._row_to_site(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list sites by region: {e}")
            return []

    # ===== NetworkCell Operations =====

    def create_cell(self, cell: NetworkCell) -> NetworkCell:
        """Create a new network cell"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO network_cells (
                        cell_id, site_id, cell_name, technology, frequency_band,
                        pci, sector, azimuth, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        cell.cell_id,
                        cell.site_id,
                        cell.cell_name,
                        cell.technology.value if hasattr(cell.technology, 'value') else cell.technology,
                        cell.frequency_band,
                        cell.pci,
                        cell.sector,
                        cell.azimuth,
                        cell.status.value if hasattr(cell.status, 'value') else cell.status,
                        cell.created_at.isoformat(),
                        cell.updated_at.isoformat() if cell.updated_at else None,
                    ),
                )
                cell.id = cursor.lastrowid

            logger.info(f"Created network cell: {cell.cell_id}")
            return cell

        except Exception as e:
            logger.error(f"Failed to create cell: {e}")
            raise DatabaseError(f"Failed to create cell: {e}")

    def get_cell_by_id(self, cell_id: str) -> Optional[NetworkCell]:
        """Get cell by cell_id"""
        try:
            with self.db.cursor() as cur:
                cur.execute("SELECT * FROM network_cells WHERE cell_id = ?;", (cell_id,))
                row = cur.fetchone()
                return self._row_to_cell(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get cell: {e}")
            return None

    def list_cells_by_site(self, site_id: str) -> List[NetworkCell]:
        """List all cells for a site"""
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM network_cells WHERE site_id = ? ORDER BY cell_id;",
                    (site_id,),
                )
                return [self._row_to_cell(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list cells for site: {e}")
            return []

    def update_cell(self, cell: NetworkCell) -> NetworkCell:
        """Update network cell"""
        try:
            with self.db.transaction() as conn:
                conn.execute(
                    """
                    UPDATE network_cells
                    SET cell_name = ?, technology = ?, frequency_band = ?,
                        pci = ?, sector = ?, azimuth = ?, status = ?, updated_at = ?
                    WHERE cell_id = ?;
                    """,
                    (
                        cell.cell_name,
                        cell.technology.value if hasattr(cell.technology, 'value') else cell.technology,
                        cell.frequency_band,
                        cell.pci,
                        cell.sector,
                        cell.azimuth,
                        cell.status.value if hasattr(cell.status, 'value') else cell.status,
                        datetime.utcnow().isoformat(),
                        cell.cell_id,
                    ),
                )

            logger.info(f"Updated cell: {cell.cell_id}")
            return cell

        except Exception as e:
            logger.error(f"Failed to update cell: {e}")
            raise DatabaseError(f"Failed to update cell: {e}")

    # ===== Helper Methods =====

    def _row_to_site(self, row) -> NetworkSite:
        """Convert database row to NetworkSite"""
        return NetworkSite(
            id=row["id"],
            site_id=row["site_id"],
            site_name=row["site_name"],
            location=row["location"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            region=row["region"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=(
                datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ),
        )

    def _row_to_cell(self, row) -> NetworkCell:
        """Convert database row to NetworkCell"""
        return NetworkCell(
            id=row["id"],
            cell_id=row["cell_id"],
            site_id=row["site_id"],
            cell_name=row["cell_name"],
            technology=row["technology"],
            frequency_band=row["frequency_band"],
            pci=row["pci"],
            sector=row["sector"],
            azimuth=row["azimuth"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=(
                datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ),
        )
