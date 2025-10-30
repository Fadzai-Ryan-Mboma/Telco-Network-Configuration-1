"""
Base Repository

Abstract base class for all repositories.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

from liquid4g.infrastructure.database.connection import DatabaseManager, get_db
from liquid4g.core.logging import get_logger

T = TypeVar("T")

logger = get_logger(__name__)


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository

    Provides common database operations for all repositories.
    """

    def __init__(self, db: Optional[DatabaseManager] = None):
        """
        Initialize repository

        Args:
            db: Database manager instance (uses global if not provided)
        """
        self.db = db or get_db()

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity"""
        pass

    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """Get entity by ID"""
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity"""
        pass

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Delete an entity"""
        pass

    @abstractmethod
    def list_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """List all entities with pagination"""
        pass

    def count(self, table_name: str, where_clause: str = "", params: tuple = ()) -> int:
        """
        Count entities

        Args:
            table_name: Table name
            where_clause: Optional WHERE clause
            params: Query parameters

        Returns:
            int: Count of entities
        """
        query = f"SELECT COUNT(*) FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"

        with self.db.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()[0]
