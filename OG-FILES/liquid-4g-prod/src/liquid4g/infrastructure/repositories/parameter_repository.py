"""
Parameter Repository

Data access layer for parameter definitions, values, and changes.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import json

from liquid4g.domain.models.parameter import Parameter, ParameterDefinition, ParameterChange
from liquid4g.infrastructure.repositories.base_repository import BaseRepository
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import DatabaseError

logger = get_logger(__name__)


class ParameterRepository(BaseRepository[Parameter]):
    """Repository for parameter data"""

    # ===== Parameter Value Operations =====

    def create(self, parameter: Parameter) -> Parameter:
        """Create a new parameter value"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO parameter_values (
                        cell_id, param_key, value, measured_at, data_source
                    ) VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        parameter.cell_id,
                        parameter.param_key,
                        parameter.value,
                        parameter.measured_at.isoformat(),
                        parameter.data_source.value if hasattr(parameter.data_source, 'value') else parameter.data_source,
                    ),
                )
                parameter.id = cursor.lastrowid

            logger.debug(f"Created parameter value: {parameter.param_key} for cell {parameter.cell_id}")
            return parameter

        except Exception as e:
            logger.error(f"Failed to create parameter: {e}")
            raise DatabaseError(f"Failed to create parameter: {e}")

    def get_by_id(self, param_id: int) -> Optional[Parameter]:
        """Get parameter by ID"""
        try:
            with self.db.cursor() as cur:
                cur.execute("SELECT * FROM parameter_values WHERE id = ?;", (param_id,))
                row = cur.fetchone()
                return self._row_to_parameter(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get parameter by ID: {e}")
            return None

    def get_current_value(self, cell_id: str, param_key: str) -> Optional[Parameter]:
        """
        Get current parameter value for a cell

        Args:
            cell_id: Cell identifier
            param_key: Parameter key

        Returns:
            Optional[Parameter]: Current parameter value
        """
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM parameter_values
                    WHERE cell_id = ? AND param_key = ?
                    ORDER BY measured_at DESC
                    LIMIT 1;
                    """,
                    (cell_id, param_key),
                )
                row = cur.fetchone()
                return self._row_to_parameter(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get current parameter value: {e}")
            return None

    def get_all_for_cell(self, cell_id: str) -> List[Parameter]:
        """Get all current parameter values for a cell"""
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT ON (param_key) *
                    FROM parameter_values
                    WHERE cell_id = ?
                    ORDER BY param_key, measured_at DESC;
                    """,
                    (cell_id,),
                )
                return [self._row_to_parameter(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get parameters for cell: {e}")
            return []

    def update(self, parameter: Parameter) -> Parameter:
        """Update parameter (creates new record with timestamp)"""
        return self.create(parameter)

    def delete(self, param_id: int) -> bool:
        """Delete parameter value"""
        try:
            with self.db.transaction() as conn:
                conn.execute("DELETE FROM parameter_values WHERE id = ?;", (param_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to delete parameter: {e}")
            return False

    def list_all(
        self, limit: Optional[int] = 100, offset: int = 0
    ) -> List[Parameter]:
        """List parameter values with pagination"""
        query = "SELECT * FROM parameter_values ORDER BY measured_at DESC"
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"

        try:
            with self.db.cursor() as cur:
                cur.execute(query)
                return [self._row_to_parameter(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list parameters: {e}")
            return []

    # ===== Parameter Definition Operations =====

    def create_definition(self, definition: ParameterDefinition) -> ParameterDefinition:
        """Create or update parameter definition"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """
                    INSERT OR REPLACE INTO parameter_definitions (
                        param_key, display_name, description, unit, category,
                        min_value, max_value, default_value, step_size,
                        mml_query_command, mml_modify_command, impact_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        definition.param_key,
                        definition.display_name,
                        definition.description,
                        definition.unit,
                        definition.category.value if hasattr(definition.category, 'value') else definition.category,
                        definition.min_value,
                        definition.max_value,
                        definition.default_value,
                        definition.step_size,
                        definition.mml_query_command,
                        definition.mml_modify_command,
                        definition.impact_level.value if hasattr(definition.impact_level, 'value') else definition.impact_level,
                    ),
                )
                definition.id = cursor.lastrowid

            logger.info(f"Created/updated parameter definition: {definition.param_key}")
            return definition

        except Exception as e:
            logger.error(f"Failed to create parameter definition: {e}")
            raise DatabaseError(f"Failed to create parameter definition: {e}")

    def get_definition(self, param_key: str) -> Optional[ParameterDefinition]:
        """Get parameter definition by key"""
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM parameter_definitions WHERE param_key = ?;",
                    (param_key,),
                )
                row = cur.fetchone()
                return self._row_to_definition(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get parameter definition: {e}")
            return None

    def list_definitions(
        self, category: Optional[str] = None
    ) -> List[ParameterDefinition]:
        """List parameter definitions, optionally filtered by category"""
        query = "SELECT * FROM parameter_definitions"
        params = ()

        if category:
            query += " WHERE category = ?"
            params = (category,)

        query += " ORDER BY param_key"

        try:
            with self.db.cursor() as cur:
                cur.execute(query, params)
                return [self._row_to_definition(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list parameter definitions: {e}")
            return []

    # ===== Parameter Change Operations =====

    def create_change(self, change: ParameterChange) -> ParameterChange:
        """Record a parameter change"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO parameter_changes (
                        change_id, cell_id, param_key, old_value, new_value,
                        change_type, reason, requested_by, requested_at,
                        approved_by, approved_at, executed_at, success,
                        error_message, rollback_available, mml_command_used,
                        kpi_snapshot_before, kpi_snapshot_after
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        change.change_id,
                        change.cell_id,
                        change.param_key,
                        change.old_value,
                        change.new_value,
                        change.change_type.value if hasattr(change.change_type, 'value') else change.change_type,
                        change.reason,
                        change.requested_by,
                        change.requested_at.isoformat(),
                        change.approved_by,
                        change.approved_at.isoformat() if change.approved_at else None,
                        change.executed_at.isoformat() if change.executed_at else None,
                        change.success,
                        change.error_message,
                        change.rollback_available,
                        change.mml_command_used,
                        json.dumps(change.kpi_snapshot_before) if change.kpi_snapshot_before else None,
                        json.dumps(change.kpi_snapshot_after) if change.kpi_snapshot_after else None,
                    ),
                )
                change.id = cursor.lastrowid

            logger.info(f"Created parameter change: {change.change_id}")
            return change

        except Exception as e:
            logger.error(f"Failed to create parameter change: {e}")
            raise DatabaseError(f"Failed to create parameter change: {e}")

    def get_change(self, change_id: str) -> Optional[ParameterChange]:
        """Get parameter change by ID"""
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM parameter_changes WHERE change_id = ?;", (change_id,)
                )
                row = cur.fetchone()
                return self._row_to_change(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get parameter change: {e}")
            return None

    def list_changes_for_cell(
        self, cell_id: str, limit: Optional[int] = None
    ) -> List[ParameterChange]:
        """List parameter changes for a cell"""
        query = "SELECT * FROM parameter_changes WHERE cell_id = ? ORDER BY requested_at DESC"
        if limit:
            query += f" LIMIT {limit}"

        try:
            with self.db.cursor() as cur:
                cur.execute(query, (cell_id,))
                return [self._row_to_change(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list changes for cell: {e}")
            return []

    def update_change_status(
        self, change_id: str, executed_at: datetime, success: bool, error_message: Optional[str] = None
    ) -> bool:
        """Update parameter change execution status"""
        try:
            with self.db.transaction() as conn:
                conn.execute(
                    """
                    UPDATE parameter_changes
                    SET executed_at = ?, success = ?, error_message = ?
                    WHERE change_id = ?;
                    """,
                    (executed_at.isoformat(), success, error_message, change_id),
                )
            logger.info(f"Updated change status: {change_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update change status: {e}")
            return False

    # ===== Helper Methods =====

    def _row_to_parameter(self, row) -> Parameter:
        """Convert database row to Parameter"""
        return Parameter(
            id=row["id"],
            cell_id=row["cell_id"],
            param_key=row["param_key"],
            value=row["value"],
            measured_at=datetime.fromisoformat(row["measured_at"]),
            data_source=row["data_source"],
        )

    def _row_to_definition(self, row) -> ParameterDefinition:
        """Convert database row to ParameterDefinition"""
        return ParameterDefinition(
            id=row["id"],
            param_key=row["param_key"],
            display_name=row["display_name"],
            description=row["description"],
            unit=row["unit"],
            category=row["category"],
            min_value=row["min_value"],
            max_value=row["max_value"],
            default_value=row["default_value"],
            step_size=row["step_size"],
            mml_query_command=row["mml_query_command"],
            mml_modify_command=row["mml_modify_command"],
            impact_level=row["impact_level"],
        )

    def _row_to_change(self, row) -> ParameterChange:
        """Convert database row to ParameterChange"""
        return ParameterChange(
            id=row["id"],
            change_id=row["change_id"],
            cell_id=row["cell_id"],
            param_key=row["param_key"],
            old_value=row["old_value"],
            new_value=row["new_value"],
            change_type=row["change_type"],
            reason=row["reason"],
            requested_by=row["requested_by"],
            requested_at=datetime.fromisoformat(row["requested_at"]),
            approved_by=row["approved_by"],
            approved_at=(
                datetime.fromisoformat(row["approved_at"]) if row["approved_at"] else None
            ),
            executed_at=(
                datetime.fromisoformat(row["executed_at"]) if row["executed_at"] else None
            ),
            success=row["success"],
            error_message=row["error_message"],
            rollback_available=bool(row["rollback_available"]),
            mml_command_used=row["mml_command_used"],
            kpi_snapshot_before=(
                json.loads(row["kpi_snapshot_before"]) if row["kpi_snapshot_before"] else None
            ),
            kpi_snapshot_after=(
                json.loads(row["kpi_snapshot_after"]) if row["kpi_snapshot_after"] else None
            ),
        )
