"""
Database Migration System

Handles database schema initialization and versioning.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from liquid4g.core.config import get_settings
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import DatabaseError, MigrationError
from liquid4g.infrastructure.database.connection import get_db

logger = get_logger(__name__)


class MigrationManager:
    """
    Database migration manager

    Features:
    - Schema initialization from SQL file
    - Migration tracking
    - Version management
    - Checksum validation
    """

    def __init__(self):
        """Initialize migration manager"""
        self.db = get_db()
        self.settings = get_settings()
        self.schema_dir = Path(__file__).parent.parent.parent.parent.parent / "config" / "database"

    def _ensure_migration_table(self):
        """Create schema_migrations table if it doesn't exist"""
        try:
            with self.db.transaction() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version TEXT UNIQUE NOT NULL,
                        description TEXT,
                        applied_at TEXT NOT NULL,
                        checksum TEXT,
                        execution_time_seconds REAL
                    );
                """)
            logger.debug("Migration tracking table ensured")
        except Exception as e:
            raise MigrationError(f"Failed to create migration table: {e}")

    def _calculate_checksum(self, content: str) -> str:
        """
        Calculate checksum of SQL content

        Args:
            content: SQL content

        Returns:
            str: SHA256 checksum
        """
        return hashlib.sha256(content.encode()).hexdigest()

    def get_current_version(self) -> Optional[str]:
        """
        Get current database version

        Returns:
            Optional[str]: Current version or None if not initialized
        """
        self._ensure_migration_table()

        try:
            with self.db.cursor() as cur:
                cur.execute("""
                    SELECT version FROM schema_migrations
                    ORDER BY applied_at DESC
                    LIMIT 1;
                """)
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Failed to get current version: {e}")
            return None

    def is_initialized(self) -> bool:
        """
        Check if database is initialized

        Returns:
            bool: True if database has been initialized
        """
        try:
            # Check if core tables exist
            return (
                self.db.table_exists("network_sites")
                and self.db.table_exists("kpi_measurements")
                and self.db.table_exists("operations")
            )
        except Exception as e:
            logger.error(f"Failed to check initialization status: {e}")
            return False

    def initialize_schema(self) -> bool:
        """
        Initialize database schema from schema.sql

        Returns:
            bool: True if successful

        Raises:
            MigrationError: If schema initialization fails
        """
        if self.is_initialized():
            logger.info("Database already initialized, skipping schema creation")
            return True

        schema_file = self.schema_dir / "schema.sql"
        if not schema_file.exists():
            raise MigrationError(f"Schema file not found: {schema_file}")

        logger.info(f"Initializing database schema from {schema_file}")
        start_time = datetime.utcnow()

        try:
            # Read schema file
            with open(schema_file, "r") as f:
                schema_sql = f.read()

            checksum = self._calculate_checksum(schema_sql)

            # Execute schema
            with self.db.transaction() as conn:
                conn.executescript(schema_sql)

            # Record migration
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._ensure_migration_table()

            with self.db.transaction() as conn:
                conn.execute(
                    """
                    INSERT INTO schema_migrations (version, description, applied_at, checksum, execution_time_seconds)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        "1.0.0",
                        "Initial schema",
                        datetime.utcnow().isoformat(),
                        checksum,
                        execution_time,
                    ),
                )

            logger.info(
                f"Database schema initialized successfully in {execution_time:.2f}s"
            )
            return True

        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            raise MigrationError(f"Schema initialization failed: {e}")

    def verify_schema(self) -> bool:
        """
        Verify database schema integrity

        Returns:
            bool: True if schema is valid

        Raises:
            MigrationError: If schema is invalid
        """
        logger.info("Verifying database schema")

        required_tables = [
            # Network
            "network_sites",
            "network_cells",
            # KPI
            "kpi_definitions",
            "kpi_measurements",
            "kpi_alerts",
            # Parameters
            "parameter_definitions",
            "parameter_values",
            "parameter_changes",
            # Agents
            "agents",
            "operations",
            "operation_logs",
            "agent_metrics",
            # Validation
            "validation_requests",
            # System
            "schema_migrations",
            "system_config",
        ]

        missing_tables = []
        for table in required_tables:
            if not self.db.table_exists(table):
                missing_tables.append(table)

        if missing_tables:
            raise MigrationError(
                f"Schema verification failed. Missing tables: {', '.join(missing_tables)}"
            )

        logger.info("Schema verification successful")
        return True

    def get_migration_history(self) -> list:
        """
        Get migration history

        Returns:
            list: List of applied migrations
        """
        self._ensure_migration_table()

        try:
            with self.db.cursor() as cur:
                cur.execute("""
                    SELECT version, description, applied_at, execution_time_seconds
                    FROM schema_migrations
                    ORDER BY applied_at;
                """)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []

    def reset_database(self, confirm: bool = False):
        """
        Drop all tables and reset database

        Args:
            confirm: Must be True to proceed (safety check)

        Raises:
            MigrationError: If confirm is False or reset fails
        """
        if not confirm:
            raise MigrationError(
                "Database reset requires explicit confirmation (confirm=True)"
            )

        logger.warning("Resetting database - ALL DATA WILL BE LOST")

        try:
            with self.db.transaction() as conn:
                # Get all tables
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%';
                """)
                tables = [row[0] for row in cursor.fetchall()]

                # Drop all tables
                for table in tables:
                    conn.execute(f"DROP TABLE IF EXISTS {table};")

            logger.info(f"Database reset complete. Dropped {len(tables)} tables.")

        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            raise MigrationError(f"Database reset failed: {e}")


def get_migration_manager() -> MigrationManager:
    """
    Get migration manager instance

    Returns:
        MigrationManager: Migration manager
    """
    return MigrationManager()
