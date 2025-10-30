"""
Database Connection Manager

Provides thread-safe SQLite connection management with WAL mode and connection pooling.
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from liquid4g.core.config import get_settings
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import DatabaseError

logger = get_logger(__name__)


class DatabaseManager:
    """
    Thread-safe database connection manager

    Features:
    - Connection pooling with thread-local storage
    - WAL mode for concurrent reads/writes
    - Automatic foreign key enforcement
    - Context manager support
    """

    _instance: Optional["DatabaseManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern for database manager"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize database manager"""
        if not hasattr(self, "_initialized"):
            self.settings = get_settings()
            self.db_path = Path(self.settings.db_path)
            self._local = threading.local()
            self._initialized = True
            logger.info(f"Database manager initialized with path: {self.db_path}")

    def _create_connection(self) -> sqlite3.Connection:
        """
        Create a new database connection

        Returns:
            sqlite3.Connection: New database connection with proper settings
        """
        try:
            # Ensure database directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create connection
            conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0,
            )

            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL;")

            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON;")

            # Row factory for dict-like access
            conn.row_factory = sqlite3.Row

            logger.debug(f"Created new database connection to {self.db_path}")
            return conn

        except sqlite3.Error as e:
            logger.error(f"Failed to create database connection: {e}")
            raise DatabaseError(f"Failed to create database connection: {e}")

    def get_connection(self) -> sqlite3.Connection:
        """
        Get thread-local database connection

        Returns:
            sqlite3.Connection: Thread-local connection
        """
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = self._create_connection()
        return self._local.connection

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database transactions

        Usage:
            with db_manager.transaction() as conn:
                conn.execute("INSERT INTO ...")
                conn.execute("UPDATE ...")
            # Auto-commits on success, rolls back on exception

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise DatabaseError(f"Transaction failed: {e}")

    @contextmanager
    def cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        Context manager for database cursor

        Usage:
            with db_manager.cursor() as cur:
                cur.execute("SELECT * FROM ...")
                results = cur.fetchall()

        Yields:
            sqlite3.Cursor: Database cursor
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def execute(
        self, query: str, params: tuple = (), commit: bool = True
    ) -> sqlite3.Cursor:
        """
        Execute a single query

        Args:
            query: SQL query to execute
            params: Query parameters
            commit: Whether to commit after execution

        Returns:
            sqlite3.Cursor: Cursor with results
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            if commit:
                conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {e}\nQuery: {query}")
            raise DatabaseError(f"Query execution failed: {e}")

    def executemany(
        self, query: str, params_list: list, commit: bool = True
    ) -> sqlite3.Cursor:
        """
        Execute a query with multiple parameter sets

        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
            commit: Whether to commit after execution

        Returns:
            sqlite3.Cursor: Cursor with results
        """
        conn = self.get_connection()
        try:
            cursor = conn.executemany(query, params_list)
            if commit:
                conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Bulk execution failed: {e}")
            raise DatabaseError(f"Bulk execution failed: {e}")

    def close(self):
        """Close the thread-local connection"""
        if hasattr(self._local, "connection") and self._local.connection is not None:
            self._local.connection.close()
            self._local.connection = None
            logger.debug("Database connection closed")

    def close_all(self):
        """Close all connections (call on shutdown)"""
        self.close()
        logger.info("All database connections closed")

    def vacuum(self):
        """
        Vacuum the database to reclaim space

        Should be run periodically in maintenance windows.
        """
        try:
            conn = self.get_connection()
            conn.execute("VACUUM;")
            logger.info("Database vacuumed successfully")
        except sqlite3.Error as e:
            logger.error(f"Vacuum failed: {e}")
            raise DatabaseError(f"Vacuum failed: {e}")

    def get_table_info(self, table_name: str) -> list:
        """
        Get table schema information

        Args:
            table_name: Name of the table

        Returns:
            list: Table schema information
        """
        with self.cursor() as cur:
            cur.execute(f"PRAGMA table_info({table_name});")
            return cur.fetchall()

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists

        Args:
            table_name: Name of the table

        Returns:
            bool: True if table exists
        """
        with self.cursor() as cur:
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                (table_name,),
            )
            return cur.fetchone() is not None


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """
    Get global database manager instance

    Returns:
        DatabaseManager: Singleton database manager
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
