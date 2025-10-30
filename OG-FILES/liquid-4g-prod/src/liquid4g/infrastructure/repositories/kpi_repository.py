"""
KPI Repository

Data access layer for KPI measurements, thresholds, and alerts.
"""

from datetime import datetime
from typing import List, Optional

from liquid4g.domain.models.kpi import KPI, KPIThreshold, KPIAlert
from liquid4g.infrastructure.repositories.base_repository import BaseRepository
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import DatabaseError

logger = get_logger(__name__)


class KPIRepository(BaseRepository[KPI]):
    """Repository for KPI data"""

    # ===== KPI Measurement Operations =====

    def create(self, kpi: KPI) -> KPI:
        """Create a new KPI measurement"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO kpi_measurements (
                        measurement_time, cell_id, kpi_key, value,
                        data_source, quality_score
                    ) VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        kpi.measurement_time.isoformat(),
                        kpi.cell_id,
                        kpi.kpi_key,
                        kpi.value,
                        kpi.data_source.value if hasattr(kpi.data_source, 'value') else kpi.data_source,
                        kpi.quality_score,
                    ),
                )
                kpi.id = cursor.lastrowid

            logger.debug(f"Created KPI measurement: {kpi.kpi_key} for cell {kpi.cell_id}")
            return kpi

        except Exception as e:
            logger.error(f"Failed to create KPI measurement: {e}")
            raise DatabaseError(f"Failed to create KPI measurement: {e}")

    def create_bulk(self, kpis: List[KPI]) -> int:
        """
        Create multiple KPI measurements in bulk

        Args:
            kpis: List of KPI measurements

        Returns:
            int: Number of records inserted
        """
        try:
            params_list = [
                (
                    kpi.measurement_time.isoformat(),
                    kpi.cell_id,
                    kpi.kpi_key,
                    kpi.value,
                    kpi.data_source.value if hasattr(kpi.data_source, 'value') else kpi.data_source,
                    kpi.quality_score,
                )
                for kpi in kpis
            ]

            self.db.executemany(
                """
                INSERT INTO kpi_measurements (
                    measurement_time, cell_id, kpi_key, value, data_source, quality_score
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                params_list,
            )

            logger.info(f"Created {len(kpis)} KPI measurements in bulk")
            return len(kpis)

        except Exception as e:
            logger.error(f"Failed to create bulk KPIs: {e}")
            raise DatabaseError(f"Failed to create bulk KPIs: {e}")

    def get_by_id(self, kpi_id: int) -> Optional[KPI]:
        """Get KPI measurement by ID"""
        try:
            with self.db.cursor() as cur:
                cur.execute("SELECT * FROM kpi_measurements WHERE id = ?;", (kpi_id,))
                row = cur.fetchone()
                return self._row_to_kpi(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get KPI by ID: {e}")
            return None

    def get_latest_for_cell(self, cell_id: str, kpi_key: str) -> Optional[KPI]:
        """
        Get latest KPI measurement for a cell

        Args:
            cell_id: Cell identifier
            kpi_key: KPI key

        Returns:
            Optional[KPI]: Latest KPI measurement
        """
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM kpi_measurements
                    WHERE cell_id = ? AND kpi_key = ?
                    ORDER BY measurement_time DESC
                    LIMIT 1;
                    """,
                    (cell_id, kpi_key),
                )
                row = cur.fetchone()
                return self._row_to_kpi(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get latest KPI: {e}")
            return None

    def get_time_series(
        self,
        cell_id: str,
        kpi_key: str,
        start_time: datetime,
        end_time: datetime,
        limit: Optional[int] = None,
    ) -> List[KPI]:
        """
        Get KPI time series data

        Args:
            cell_id: Cell identifier
            kpi_key: KPI key
            start_time: Start time
            end_time: End time
            limit: Optional limit

        Returns:
            List[KPI]: Time series data
        """
        query = """
            SELECT * FROM kpi_measurements
            WHERE cell_id = ? AND kpi_key = ?
              AND measurement_time >= ? AND measurement_time <= ?
            ORDER BY measurement_time DESC
        """
        if limit:
            query += f" LIMIT {limit}"

        try:
            with self.db.cursor() as cur:
                cur.execute(
                    query,
                    (cell_id, kpi_key, start_time.isoformat(), end_time.isoformat()),
                )
                return [self._row_to_kpi(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get time series: {e}")
            return []

    def list_all(
        self, limit: Optional[int] = 100, offset: int = 0
    ) -> List[KPI]:
        """List KPI measurements with pagination"""
        query = "SELECT * FROM kpi_measurements ORDER BY measurement_time DESC"
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"

        try:
            with self.db.cursor() as cur:
                cur.execute(query)
                return [self._row_to_kpi(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list KPIs: {e}")
            return []

    def update(self, kpi: KPI) -> KPI:
        """Update KPI measurement (rarely used)"""
        try:
            with self.db.transaction() as conn:
                conn.execute(
                    """
                    UPDATE kpi_measurements
                    SET value = ?, quality_score = ?
                    WHERE id = ?;
                    """,
                    (kpi.value, kpi.quality_score, kpi.id),
                )
            return kpi
        except Exception as e:
            logger.error(f"Failed to update KPI: {e}")
            raise DatabaseError(f"Failed to update KPI: {e}")

    def delete(self, kpi_id: int) -> bool:
        """Delete KPI measurement (rarely used)"""
        try:
            with self.db.transaction() as conn:
                conn.execute("DELETE FROM kpi_measurements WHERE id = ?;", (kpi_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to delete KPI: {e}")
            return False

    # ===== KPI Threshold Operations =====

    def create_threshold(self, threshold: KPIThreshold) -> KPIThreshold:
        """Create or update KPI threshold definition"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """
                    INSERT OR REPLACE INTO kpi_definitions (
                        kpi_key, display_name, description, unit, category,
                        higher_is_better, optimal_min, optimal_max,
                        warning_threshold, critical_threshold
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        threshold.kpi_key,
                        threshold.display_name,
                        threshold.description,
                        threshold.unit,
                        threshold.category.value if hasattr(threshold.category, 'value') else threshold.category,
                        threshold.higher_is_better,
                        threshold.optimal_min,
                        threshold.optimal_max,
                        threshold.warning_threshold,
                        threshold.critical_threshold,
                    ),
                )
                threshold.id = cursor.lastrowid

            logger.info(f"Created/updated KPI threshold: {threshold.kpi_key}")
            return threshold

        except Exception as e:
            logger.error(f"Failed to create threshold: {e}")
            raise DatabaseError(f"Failed to create threshold: {e}")

    def get_threshold(self, kpi_key: str) -> Optional[KPIThreshold]:
        """Get KPI threshold by key"""
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM kpi_definitions WHERE kpi_key = ?;", (kpi_key,)
                )
                row = cur.fetchone()
                return self._row_to_threshold(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get threshold: {e}")
            return None

    def list_thresholds(self) -> List[KPIThreshold]:
        """List all KPI thresholds"""
        try:
            with self.db.cursor() as cur:
                cur.execute("SELECT * FROM kpi_definitions ORDER BY kpi_key;")
                return [self._row_to_threshold(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list thresholds: {e}")
            return []

    # ===== KPI Alert Operations =====

    def create_alert(self, alert: KPIAlert) -> KPIAlert:
        """Create a new KPI alert"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO kpi_alerts (
                        alert_id, triggered_at, cell_id, kpi_key,
                        severity, current_value, threshold_value, status,
                        message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        alert.alert_id,
                        alert.triggered_at.isoformat(),
                        alert.cell_id,
                        alert.kpi_key,
                        alert.severity.value if hasattr(alert.severity, 'value') else alert.severity,
                        alert.current_value,
                        alert.threshold_value,
                        alert.status.value if hasattr(alert.status, 'value') else alert.status,
                        alert.message,
                    ),
                )
                alert.id = cursor.lastrowid

            logger.info(f"Created alert: {alert.alert_id}")
            return alert

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            raise DatabaseError(f"Failed to create alert: {e}")

    def get_alert(self, alert_id: str) -> Optional[KPIAlert]:
        """Get alert by alert_id"""
        try:
            with self.db.cursor() as cur:
                cur.execute("SELECT * FROM kpi_alerts WHERE alert_id = ?;", (alert_id,))
                row = cur.fetchone()
                return self._row_to_alert(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get alert: {e}")
            return None

    def list_active_alerts(self, cell_id: Optional[str] = None) -> List[KPIAlert]:
        """List active alerts, optionally filtered by cell"""
        query = "SELECT * FROM kpi_alerts WHERE status = 'active'"
        params = ()

        if cell_id:
            query += " AND cell_id = ?"
            params = (cell_id,)

        query += " ORDER BY triggered_at DESC"

        try:
            with self.db.cursor() as cur:
                cur.execute(query, params)
                return [self._row_to_alert(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list active alerts: {e}")
            return []

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark alert as resolved"""
        try:
            with self.db.transaction() as conn:
                conn.execute(
                    """
                    UPDATE kpi_alerts
                    SET status = 'resolved', resolved_at = ?
                    WHERE alert_id = ?;
                    """,
                    (datetime.utcnow().isoformat(), alert_id),
                )
            logger.info(f"Resolved alert: {alert_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return False

    # ===== Helper Methods =====

    def _row_to_kpi(self, row) -> KPI:
        """Convert database row to KPI"""
        return KPI(
            id=row["id"],
            measurement_time=datetime.fromisoformat(row["measurement_time"]),
            cell_id=row["cell_id"],
            kpi_key=row["kpi_key"],
            value=row["value"],
            data_source=row["data_source"],
            quality_score=row["quality_score"],
        )

    def _row_to_threshold(self, row) -> KPIThreshold:
        """Convert database row to KPIThreshold"""
        return KPIThreshold(
            id=row["id"],
            kpi_key=row["kpi_key"],
            display_name=row["display_name"],
            description=row["description"],
            unit=row["unit"],
            category=row["category"],
            higher_is_better=bool(row["higher_is_better"]),
            optimal_min=row["optimal_min"],
            optimal_max=row["optimal_max"],
            warning_threshold=row["warning_threshold"],
            critical_threshold=row["critical_threshold"],
        )

    def _row_to_alert(self, row) -> KPIAlert:
        """Convert database row to KPIAlert"""
        return KPIAlert(
            id=row["id"],
            alert_id=row["alert_id"],
            triggered_at=datetime.fromisoformat(row["triggered_at"]),
            resolved_at=(
                datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None
            ),
            cell_id=row["cell_id"],
            kpi_key=row["kpi_key"],
            severity=row["severity"],
            current_value=row["current_value"],
            threshold_value=row["threshold_value"],
            status=row["status"],
            message=row["message"],
        )
