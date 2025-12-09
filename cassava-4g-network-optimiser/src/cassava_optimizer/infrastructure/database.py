"""
Async database setup using SQLAlchemy with aiosqlite.

Provides async engine, session factory, and ORM models.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    event,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from cassava_optimizer.domain.exceptions import DatabaseError


# =============================================================================
# SQLAlchemy Base and Models
# =============================================================================

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class SiteModel(Base):
    """ORM model for network sites."""
    
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(50), unique=True, nullable=False, index=True)
    site_name = Column(String(200), nullable=False)
    enodeb_id = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    region = Column(String(100), default="")
    cluster = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cells = relationship("CellModel", back_populates="site", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_sites_region_cluster", "region", "cluster"),
    )


class CellModel(Base):
    """ORM model for network cells."""
    
    __tablename__ = "cells"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cell_id = Column(String(50), unique=True, nullable=False, index=True)
    local_cell_id = Column(Integer, nullable=False)
    cell_name = Column(String(200), nullable=False)
    site_id = Column(String(50), ForeignKey("sites.site_id"), nullable=False)
    pci = Column(Integer, nullable=False)
    tac = Column(Integer, nullable=False)
    earfcn = Column(Integer, nullable=False)
    bandwidth = Column(Integer, nullable=False)
    azimuth = Column(Float, nullable=False)
    electrical_tilt = Column(Float, default=0.0)
    mechanical_tilt = Column(Float, default=0.0)
    tx_power = Column(Float, nullable=False)
    state = Column(String(20), default="unknown")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    site = relationship("SiteModel", back_populates="cells")
    
    __table_args__ = (
        Index("ix_cells_site_id", "site_id"),
        Index("ix_cells_pci", "pci"),
    )


class KPIRecordModel(Base):
    """ORM model for historical KPI records."""
    
    __tablename__ = "kpi_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(50), nullable=False, index=True)
    cell_id = Column(String(50), default="", index=True)
    kpi_name = Column(String(100), nullable=False, index=True)
    kpi_value = Column(Float, nullable=False)
    unit = Column(String(20), default="")
    timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String(50), default="api")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_kpi_records_lookup", "site_id", "kpi_name", "timestamp"),
        Index("ix_kpi_records_cell_lookup", "cell_id", "kpi_name", "timestamp"),
    )


class OptimizationHistoryModel(Base):
    """ORM model for optimization execution history."""
    
    __tablename__ = "optimization_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), unique=True, nullable=False, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    query = Column(Text, nullable=False)
    recommendations_json = Column(Text, default="{}")
    commands_json = Column(Text, default="{}")
    success = Column(Boolean, default=False)
    error_message = Column(Text, default="")
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_optimization_history_site_date", "site_id", "started_at"),
    )


class CommandExecutionModel(Base):
    """ORM model for MML command execution records."""
    
    __tablename__ = "command_executions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    command_id = Column(String(50), unique=True, nullable=False, index=True)
    session_id = Column(String(50), nullable=False, index=True)
    site_id = Column(String(50), nullable=False)
    cell_id = Column(String(50), default="")
    command_text = Column(Text, nullable=False)
    rollback_command = Column(Text, default="")
    status = Column(String(20), nullable=False)
    output = Column(Text, default="")
    error_message = Column(Text, default="")
    executed_at = Column(DateTime)
    execution_time_ms = Column(Integer, default=0)
    rollback_executed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_command_executions_session", "session_id"),
        Index("ix_command_executions_status", "status"),
    )


# =============================================================================
# Database Engine and Session Management
# =============================================================================

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_async_engine(
    database_url: str = "sqlite+aiosqlite:///./data/cassava_network.db",
    echo: bool = False,
) -> AsyncEngine:
    """
    Get or create the async database engine.
    
    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL statements
        
    Returns:
        AsyncEngine instance
    """
    global _engine
    
    if _engine is None:
        # Ensure data directory exists
        if database_url.startswith("sqlite"):
            db_path = database_url.split("///")[-1]
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        _engine = create_async_engine(
            database_url,
            echo=echo,
            future=True,
            pool_pre_ping=True,
        )
        
        # Enable foreign keys for SQLite
        if "sqlite" in database_url:
            @event.listens_for(_engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    
    return _engine


def async_session_factory(
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    """
    Get or create the async session factory.
    
    Args:
        engine: Optional engine to use. If None, uses default engine.
        
    Returns:
        Async session factory
    """
    global _session_factory
    
    if _session_factory is None:
        if engine is None:
            engine = get_async_engine()
        
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    
    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session.
    
    Yields:
        AsyncSession for database operations
        
    Raises:
        DatabaseError: If session creation fails
    """
    factory = async_session_factory()
    session = factory()
    
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise DatabaseError(
            f"Database session error: {e}",
            cause=e,
        )
    finally:
        await session.close()


async def init_database(
    database_url: str = "sqlite+aiosqlite:///./data/cassava_network.db",
    drop_existing: bool = False,
) -> None:
    """
    Initialize the database by creating all tables.
    
    Args:
        database_url: Database connection URL
        drop_existing: Whether to drop existing tables
        
    Raises:
        DatabaseError: If initialization fails
    """
    try:
        engine = get_async_engine(database_url)
        
        async with engine.begin() as conn:
            if drop_existing:
                await conn.run_sync(Base.metadata.drop_all)
            
            await conn.run_sync(Base.metadata.create_all)
        
    except Exception as e:
        raise DatabaseError(
            f"Failed to initialize database: {e}",
            cause=e,
        )


async def close_database() -> None:
    """Close the database connection pool."""
    global _engine, _session_factory
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


class DatabaseManager:
    """
    High-level database management class.
    
    Provides a convenient interface for database operations.
    """
    
    def __init__(self, database_url: str = "sqlite+aiosqlite:///./data/cassava_network.db"):
        """
        Initialize the database manager.
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
    
    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine, creating it if necessary."""
        if self._engine is None:
            # Ensure data directory exists
            if self.database_url.startswith("sqlite"):
                db_path = self.database_url.split("///")[-1]
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            self._engine = create_async_engine(
                self.database_url,
                echo=False,
                future=True,
                pool_pre_ping=True,
            )
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory, creating it if necessary."""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session.
        
        Yields:
            AsyncSession for database operations
        """
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise DatabaseError(
                f"Database session error: {e}",
                cause=e,
            )
        finally:
            await session.close()
    
    async def init_tables(self, drop_existing: bool = False) -> None:
        """
        Initialize the database by creating all tables.
        
        Args:
            drop_existing: Whether to drop existing tables
        """
        async with self.engine.begin() as conn:
            if drop_existing:
                await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self) -> None:
        """Close the database connection pool."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_database_manager(database_url: str | None = None) -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Args:
        database_url: Optional database URL. Uses default if not provided.
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    
    if _db_manager is None:
        url = database_url or "sqlite+aiosqlite:///./data/cassava_network.db"
        _db_manager = DatabaseManager(url)
    
    return _db_manager
