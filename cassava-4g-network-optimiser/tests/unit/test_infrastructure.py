"""Unit tests for infrastructure layer."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio


class TestDatabaseManager:
    """Tests for DatabaseManager class."""

    @pytest.mark.asyncio
    async def test_connect_creates_engine(self, test_settings):
        """Test that connect creates async engine."""
        from cassava_optimizer.infrastructure.database import DatabaseManager
        
        manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
        await manager.connect()
        
        assert manager._engine is not None
        
        await manager.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect_disposes_engine(self, test_settings):
        """Test that disconnect disposes engine."""
        from cassava_optimizer.infrastructure.database import DatabaseManager
        
        manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
        await manager.connect()
        await manager.disconnect()
        
        assert manager._engine is None

    @pytest.mark.asyncio
    async def test_execute_runs_query(self, db_manager):
        """Test executing a query."""
        # Insert test data
        await db_manager.execute(
            "INSERT INTO sites (name, region) VALUES (?, ?)",
            ("TestSite", "Region1")
        )
        
        # Query data
        result = await db_manager.execute("SELECT * FROM sites")
        rows = await result.fetchall()
        
        assert len(rows) == 1
        assert rows[0][1] == "TestSite"

    @pytest.mark.asyncio
    async def test_transaction_commit(self, db_manager):
        """Test transaction commit."""
        async with db_manager.transaction():
            await db_manager.execute(
                "INSERT INTO sites (name, region) VALUES (?, ?)",
                ("TxSite", "TxRegion")
            )
        
        result = await db_manager.execute(
            "SELECT * FROM sites WHERE name = ?",
            ("TxSite",)
        )
        rows = await result.fetchall()
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, db_manager):
        """Test transaction rollback on error."""
        from cassava_optimizer.domain.exceptions import DatabaseError
        
        try:
            async with db_manager.transaction():
                await db_manager.execute(
                    "INSERT INTO sites (name, region) VALUES (?, ?)",
                    ("RollbackSite", "Region")
                )
                # Force an error
                raise DatabaseError("Test error")
        except DatabaseError:
            pass
        
        result = await db_manager.execute(
            "SELECT * FROM sites WHERE name = ?",
            ("RollbackSite",)
        )
        rows = await result.fetchall()
        # Should be rolled back
        assert len(rows) == 0


class TestSiteRepository:
    """Tests for SiteRepository class."""

    @pytest.mark.asyncio
    async def test_get_by_id(self, seeded_db):
        """Test getting site by ID."""
        from cassava_optimizer.infrastructure.repositories import SiteRepository
        
        repo = SiteRepository(seeded_db)
        site = await repo.get_by_id(1)
        
        assert site is not None
        assert site.name == "TestSite001"
        assert site.region == "Harare"

    @pytest.mark.asyncio
    async def test_get_by_name(self, seeded_db):
        """Test getting site by name."""
        from cassava_optimizer.infrastructure.repositories import SiteRepository
        
        repo = SiteRepository(seeded_db)
        site = await repo.get_by_name("TestSite001")
        
        assert site is not None
        assert site.id == 1

    @pytest.mark.asyncio
    async def test_get_all(self, seeded_db):
        """Test getting all sites."""
        from cassava_optimizer.infrastructure.repositories import SiteRepository
        
        repo = SiteRepository(seeded_db)
        sites = await repo.get_all()
        
        assert len(sites) >= 1
        assert any(s.name == "TestSite001" for s in sites)

    @pytest.mark.asyncio
    async def test_create(self, db_manager):
        """Test creating a site."""
        from cassava_optimizer.infrastructure.repositories import SiteRepository
        from cassava_optimizer.domain.models import Site
        
        repo = SiteRepository(db_manager)
        site = Site(
            name="NewSite",
            region="NewRegion",
            latitude=-18.0,
            longitude=32.0,
        )
        
        created = await repo.create(site)
        
        assert created.id is not None
        assert created.name == "NewSite"


class TestCellRepository:
    """Tests for CellRepository class."""

    @pytest.mark.asyncio
    async def test_get_by_site_id(self, seeded_db):
        """Test getting cells by site ID."""
        from cassava_optimizer.infrastructure.repositories import CellRepository
        
        repo = CellRepository(seeded_db)
        cells = await repo.get_by_site_id(1)
        
        assert len(cells) == 3
        assert all(c.site_id == 1 for c in cells)

    @pytest.mark.asyncio
    async def test_get_by_cell_id(self, seeded_db):
        """Test getting cell by cell ID."""
        from cassava_optimizer.infrastructure.repositories import CellRepository
        
        repo = CellRepository(seeded_db)
        cell = await repo.get_by_cell_id("Cell001")
        
        assert cell is not None
        assert cell.cell_name == "TestSite001_Cell1"


class TestKPIRepository:
    """Tests for KPIRepository class."""

    @pytest.mark.asyncio
    async def test_get_latest_for_cell(self, seeded_db):
        """Test getting latest KPIs for cell."""
        from cassava_optimizer.infrastructure.repositories import KPIRepository
        
        repo = KPIRepository(seeded_db)
        kpis = await repo.get_latest_for_cell(1)
        
        assert len(kpis) >= 1
        assert any(k.kpi_name == "call_setup_success_rate" for k in kpis)

    @pytest.mark.asyncio
    async def test_get_for_site(self, seeded_db):
        """Test getting KPIs for site."""
        from cassava_optimizer.infrastructure.repositories import KPIRepository
        
        repo = KPIRepository(seeded_db)
        kpis = await repo.get_for_site(1)
        
        assert len(kpis) >= 1

    @pytest.mark.asyncio
    async def test_save_kpi_data(self, db_manager):
        """Test saving KPI data."""
        from cassava_optimizer.infrastructure.repositories import KPIRepository
        from cassava_optimizer.domain.models import KPIData
        
        repo = KPIRepository(db_manager)
        
        kpi = KPIData(
            cell_id=1,
            site_id=1,
            kpi_name="test_kpi",
            kpi_value=99.0,
            kpi_unit="%",
            timestamp=datetime.now(timezone.utc),
        )
        
        saved = await repo.save(kpi)
        assert saved.id is not None


class TestRecommendationRepository:
    """Tests for RecommendationRepository class."""

    @pytest.mark.asyncio
    async def test_get_by_run_id(self, seeded_db):
        """Test getting recommendations by run ID."""
        from cassava_optimizer.infrastructure.repositories import RecommendationRepository
        
        repo = RecommendationRepository(seeded_db)
        
        # First create an optimization run and recommendation
        run_id = "test-run-123"
        await seeded_db.execute(
            """
            INSERT INTO optimization_runs (run_id, site_id, status)
            VALUES (?, ?, ?)
            """,
            (run_id, 1, "completed"),
        )
        
        await seeded_db.execute(
            """
            INSERT INTO optimization_recommendations 
            (run_id, cell_id, parameter_name, recommended_value, confidence)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, 1, "testParam", "10", 0.85),
        )
        
        recs = await repo.get_by_run_id(run_id)
        
        assert len(recs) == 1
        assert recs[0].parameter_name == "testParam"

    @pytest.mark.asyncio
    async def test_get_pending(self, seeded_db):
        """Test getting pending recommendations."""
        from cassava_optimizer.infrastructure.repositories import RecommendationRepository
        
        repo = RecommendationRepository(seeded_db)
        
        # Create pending recommendation
        run_id = "test-run-pending"
        await seeded_db.execute(
            "INSERT INTO optimization_runs (run_id, site_id, status) VALUES (?, ?, ?)",
            (run_id, 1, "completed"),
        )
        await seeded_db.execute(
            """
            INSERT INTO optimization_recommendations 
            (run_id, cell_id, parameter_name, recommended_value, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, 1, "pendingParam", "20", "pending"),
        )
        
        pending = await repo.get_pending()
        assert len(pending) >= 1


class TestCacheManager:
    """Tests for CacheManager class."""

    @pytest.mark.asyncio
    async def test_get_set(self):
        """Test cache get and set."""
        from cassava_optimizer.infrastructure.cache import CacheManager
        
        cache = CacheManager()
        
        await cache.set("test_key", {"data": "value"})
        result = await cache.get("test_key")
        
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self):
        """Test getting nonexistent key."""
        from cassava_optimizer.infrastructure.cache import CacheManager
        
        cache = CacheManager()
        result = await cache.get("nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test cache delete."""
        from cassava_optimizer.infrastructure.cache import CacheManager
        
        cache = CacheManager()
        
        await cache.set("delete_key", "value")
        await cache.delete("delete_key")
        result = await cache.get("delete_key")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test cache clear."""
        from cassava_optimizer.infrastructure.cache import CacheManager
        
        cache = CacheManager()
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None


class TestUnitOfWork:
    """Tests for UnitOfWork class."""

    @pytest.mark.asyncio
    async def test_commit_saves_changes(self, db_manager):
        """Test that commit saves changes."""
        from cassava_optimizer.infrastructure.unit_of_work import UnitOfWork
        
        async with UnitOfWork(db_manager) as uow:
            await uow.execute(
                "INSERT INTO sites (name, region) VALUES (?, ?)",
                ("UoWSite", "UoWRegion"),
            )
            await uow.commit()
        
        result = await db_manager.execute(
            "SELECT * FROM sites WHERE name = ?",
            ("UoWSite",),
        )
        rows = await result.fetchall()
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_rollback_discards_changes(self, db_manager):
        """Test that rollback discards changes."""
        from cassava_optimizer.infrastructure.unit_of_work import UnitOfWork
        
        async with UnitOfWork(db_manager) as uow:
            await uow.execute(
                "INSERT INTO sites (name, region) VALUES (?, ?)",
                ("RollbackUoW", "Region"),
            )
            await uow.rollback()
        
        result = await db_manager.execute(
            "SELECT * FROM sites WHERE name = ?",
            ("RollbackUoW",),
        )
        rows = await result.fetchall()
        assert len(rows) == 0
