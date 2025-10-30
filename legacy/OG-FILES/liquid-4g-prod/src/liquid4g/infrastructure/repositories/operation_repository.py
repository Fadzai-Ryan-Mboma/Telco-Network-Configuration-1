"""
Operation Repository

Data access layer for operations and operation logs.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import json

from liquid4g.domain.models.operation import Operation, OperationLog
from liquid4g.infrastructure.repositories.base_repository import BaseRepository
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import DatabaseError

logger = get_logger(__name__)


class OperationRepository(BaseRepository[Operation]):
    """Repository for operation data"""

    # ===== Operation Operations =====

    def create(self, operation: Operation) -> Operation:
        """Create a new operation"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO operations (
                        operation_id, operation_type, stage, target_site, target_cell,
                        status, priority, parameters, results, agent_id,
                        parent_operation_id, started_at, completed_at, duration_seconds,
                        error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        operation.operation_id,
                        operation.operation_type.value if hasattr(operation.operation_type, 'value') else operation.operation_type,
                        operation.stage.value if operation.stage and hasattr(operation.stage, 'value') else operation.stage,
                        operation.target_site,
                        operation.target_cell,
                        operation.status.value if hasattr(operation.status, 'value') else operation.status,
                        operation.priority.value if hasattr(operation.priority, 'value') else operation.priority,
                        json.dumps(operation.parameters),
                        json.dumps(operation.results),
                        operation.agent_id,
                        operation.parent_operation_id,
                        operation.started_at.isoformat(),
                        operation.completed_at.isoformat() if operation.completed_at else None,
                        operation.duration_seconds,
                        operation.error_message,
                    ),
                )
                operation.id = cursor.lastrowid

            logger.info(f"Created operation: {operation.operation_id}")
            return operation

        except Exception as e:
            logger.error(f"Failed to create operation: {e}")
            raise DatabaseError(f"Failed to create operation: {e}")

    def get_by_id(self, operation_id: int) -> Optional[Operation]:
        """Get operation by database ID"""
        try:
            with self.db.cursor() as cur:
                cur.execute("SELECT * FROM operations WHERE id = ?;", (operation_id,))
                row = cur.fetchone()
                return self._row_to_operation(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get operation by ID: {e}")
            return None

    def get_by_operation_id(self, operation_id: str) -> Optional[Operation]:
        """
        Get operation by operation_id

        Args:
            operation_id: Operation identifier

        Returns:
            Optional[Operation]: Operation or None
        """
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM operations WHERE operation_id = ?;", (operation_id,)
                )
                row = cur.fetchone()
                return self._row_to_operation(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get operation {operation_id}: {e}")
            return None

    def update(self, operation: Operation) -> Operation:
        """Update operation"""
        try:
            with self.db.transaction() as conn:
                conn.execute(
                    """
                    UPDATE operations
                    SET operation_type = ?, stage = ?, target_site = ?, target_cell = ?,
                        status = ?, priority = ?, parameters = ?, results = ?,
                        agent_id = ?, completed_at = ?, duration_seconds = ?,
                        error_message = ?
                    WHERE operation_id = ?;
                    """,
                    (
                        operation.operation_type.value if hasattr(operation.operation_type, 'value') else operation.operation_type,
                        operation.stage.value if operation.stage and hasattr(operation.stage, 'value') else operation.stage,
                        operation.target_site,
                        operation.target_cell,
                        operation.status.value if hasattr(operation.status, 'value') else operation.status,
                        operation.priority.value if hasattr(operation.priority, 'value') else operation.priority,
                        json.dumps(operation.parameters),
                        json.dumps(operation.results),
                        operation.agent_id,
                        operation.completed_at.isoformat() if operation.completed_at else None,
                        operation.duration_seconds,
                        operation.error_message,
                        operation.operation_id,
                    ),
                )

            logger.info(f"Updated operation: {operation.operation_id}")
            return operation

        except Exception as e:
            logger.error(f"Failed to update operation: {e}")
            raise DatabaseError(f"Failed to update operation: {e}")

    def delete(self, operation_id: int) -> bool:
        """Delete operation by database ID"""
        try:
            with self.db.transaction() as conn:
                conn.execute("DELETE FROM operations WHERE id = ?;", (operation_id,))
            logger.info(f"Deleted operation ID: {operation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete operation: {e}")
            return False

    def list_all(
        self, limit: Optional[int] = 100, offset: int = 0
    ) -> List[Operation]:
        """List all operations"""
        query = "SELECT * FROM operations ORDER BY started_at DESC"
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"

        try:
            with self.db.cursor() as cur:
                cur.execute(query)
                return [self._row_to_operation(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list operations: {e}")
            return []

    def list_by_status(self, status: str, limit: Optional[int] = None) -> List[Operation]:
        """
        List operations by status

        Args:
            status: Operation status (pending/running/completed/failed/cancelled)
            limit: Optional limit

        Returns:
            List[Operation]: Operations with matching status
        """
        query = "SELECT * FROM operations WHERE status = ? ORDER BY started_at DESC"
        if limit:
            query += f" LIMIT {limit}"

        try:
            with self.db.cursor() as cur:
                cur.execute(query, (status,))
                return [self._row_to_operation(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list operations by status: {e}")
            return []

    def list_by_site(self, site_id: str, limit: Optional[int] = None) -> List[Operation]:
        """List operations for a site"""
        query = "SELECT * FROM operations WHERE target_site = ? ORDER BY started_at DESC"
        if limit:
            query += f" LIMIT {limit}"

        try:
            with self.db.cursor() as cur:
                cur.execute(query, (site_id,))
                return [self._row_to_operation(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list operations by site: {e}")
            return []

    def list_by_agent(self, agent_id: str, limit: Optional[int] = None) -> List[Operation]:
        """List operations for an agent"""
        query = "SELECT * FROM operations WHERE agent_id = ? ORDER BY started_at DESC"
        if limit:
            query += f" LIMIT {limit}"

        try:
            with self.db.cursor() as cur:
                cur.execute(query, (agent_id,))
                return [self._row_to_operation(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list operations by agent: {e}")
            return []

    def list_children(self, parent_operation_id: str) -> List[Operation]:
        """List child operations"""
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM operations
                    WHERE parent_operation_id = ?
                    ORDER BY started_at;
                    """,
                    (parent_operation_id,),
                )
                return [self._row_to_operation(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list child operations: {e}")
            return []

    # ===== Operation Log Operations =====

    def create_log(self, log: OperationLog) -> OperationLog:
        """Create an operation log entry"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO operation_logs (
                        operation_id, log_time, log_level, stage, message, details
                    ) VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        log.operation_id,
                        log.log_time.isoformat(),
                        log.log_level.value if hasattr(log.log_level, 'value') else log.log_level,
                        log.stage.value if log.stage and hasattr(log.stage, 'value') else log.stage,
                        log.message,
                        json.dumps(log.details) if log.details else None,
                    ),
                )
                log.id = cursor.lastrowid

            logger.debug(f"Created operation log for {log.operation_id}")
            return log

        except Exception as e:
            logger.error(f"Failed to create operation log: {e}")
            raise DatabaseError(f"Failed to create operation log: {e}")

    def get_logs(
        self, operation_id: str, log_level: Optional[str] = None
    ) -> List[OperationLog]:
        """
        Get logs for an operation

        Args:
            operation_id: Operation identifier
            log_level: Optional log level filter (DEBUG/INFO/WARNING/ERROR/CRITICAL)

        Returns:
            List[OperationLog]: Operation logs
        """
        query = "SELECT * FROM operation_logs WHERE operation_id = ?"
        params = [operation_id]

        if log_level:
            query += " AND log_level = ?"
            params.append(log_level)

        query += " ORDER BY log_time"

        try:
            with self.db.cursor() as cur:
                cur.execute(query, tuple(params))
                return [self._row_to_log(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get operation logs: {e}")
            return []

    # ===== Statistics =====

    def get_operation_statistics(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get operation statistics

        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Dict[str, Any]: Statistics
        """
        where_clause = []
        params = []

        if start_time:
            where_clause.append("started_at >= ?")
            params.append(start_time.isoformat())

        if end_time:
            where_clause.append("started_at <= ?")
            params.append(end_time.isoformat())

        where_sql = " AND ".join(where_clause) if where_clause else "1=1"

        try:
            with self.db.cursor() as cur:
                # Total operations
                cur.execute(
                    f"SELECT COUNT(*) FROM operations WHERE {where_sql};", tuple(params)
                )
                total = cur.fetchone()[0]

                # By status
                cur.execute(
                    f"""
                    SELECT status, COUNT(*)
                    FROM operations
                    WHERE {where_sql}
                    GROUP BY status;
                    """,
                    tuple(params),
                )
                by_status = {row[0]: row[1] for row in cur.fetchall()}

                # Average duration
                cur.execute(
                    f"""
                    SELECT AVG(duration_seconds)
                    FROM operations
                    WHERE {where_sql} AND duration_seconds IS NOT NULL;
                    """,
                    tuple(params),
                )
                avg_duration = cur.fetchone()[0]

                return {
                    "total_operations": total,
                    "by_status": by_status,
                    "average_duration_seconds": avg_duration,
                }

        except Exception as e:
            logger.error(f"Failed to get operation statistics: {e}")
            return {}

    # ===== Helper Methods =====

    def _row_to_operation(self, row) -> Operation:
        """Convert database row to Operation"""
        return Operation(
            id=row["id"],
            operation_id=row["operation_id"],
            operation_type=row["operation_type"],
            stage=row["stage"],
            target_site=row["target_site"],
            target_cell=row["target_cell"],
            status=row["status"],
            priority=row["priority"],
            parameters=json.loads(row["parameters"]) if row["parameters"] else {},
            results=json.loads(row["results"]) if row["results"] else {},
            agent_id=row["agent_id"],
            parent_operation_id=row["parent_operation_id"],
            started_at=datetime.fromisoformat(row["started_at"]),
            completed_at=(
                datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
            ),
            duration_seconds=row["duration_seconds"],
            error_message=row["error_message"],
        )

    def _row_to_log(self, row) -> OperationLog:
        """Convert database row to OperationLog"""
        return OperationLog(
            id=row["id"],
            operation_id=row["operation_id"],
            log_time=datetime.fromisoformat(row["log_time"]),
            log_level=row["log_level"],
            stage=row["stage"],
            message=row["message"],
            details=json.loads(row["details"]) if row["details"] else None,
        )
