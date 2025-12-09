"""
Pytest Configuration and Fixtures.

Provides shared fixtures for all tests including:
- Async event loop configuration
- Database fixtures with test data
- Mock clients for external services
- Configuration fixtures
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest
import pytest_asyncio

# Add source to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================================
# Event Loop Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_settings() -> MagicMock:
    """Create test settings."""
    settings = MagicMock()
    settings.database_url = "sqlite+aiosqlite:///:memory:"
    settings.nvidia_api_key = "test-api-key"
    settings.nvidia_nim_url = "https://test.api.nvidia.com"
    settings.nvidia_model_name = "meta/llama-3.1-70b-instruct"
    settings.huawei_mae_url = "https://test.mae.huawei.com"
    settings.huawei_mae_username = "test_user"
    settings.huawei_mae_password = "test_pass"
    settings.log_level = "DEBUG"
    settings.log_file = "/tmp/test.log"
    settings.log_json_format = False
    settings.confidence_threshold = 0.75
    settings.max_recommendations = 10
    settings.enable_auto_rollback = True
    settings.monitor_interval = 60
    settings.ui_port = 8501
    return settings


@pytest.fixture
def mock_settings(test_settings: MagicMock) -> Generator[MagicMock, None, None]:
    """Patch get_settings to return test settings."""
    with patch("cassava_optimizer.config.get_settings", return_value=test_settings):
        yield test_settings


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def db_manager(test_settings: MagicMock) -> AsyncGenerator:
    """Create a test database manager with in-memory SQLite."""
    from cassava_optimizer.infrastructure.database import DatabaseManager
    
    manager = DatabaseManager(test_settings.database_url)
    await manager.connect()
    
    # Create tables
    await manager.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            region TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            status TEXT DEFAULT 'online',
            ne_id TEXT,
            ne_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await manager.execute("""
        CREATE TABLE IF NOT EXISTS cells (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            cell_id TEXT NOT NULL,
            cell_name TEXT NOT NULL,
            technology TEXT DEFAULT 'LTE',
            band TEXT,
            pci INTEGER,
            earfcn INTEGER,
            azimuth INTEGER,
            tilt REAL,
            power REAL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id),
            UNIQUE (site_id, cell_id)
        )
    """)
    
    await manager.execute("""
        CREATE TABLE IF NOT EXISTS kpi_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cell_id INTEGER,
            site_id INTEGER,
            kpi_name TEXT NOT NULL,
            kpi_value REAL NOT NULL,
            kpi_unit TEXT,
            timestamp TIMESTAMP NOT NULL,
            granularity TEXT DEFAULT 'hourly',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cell_id) REFERENCES cells(id),
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)
    
    await manager.execute("""
        CREATE TABLE IF NOT EXISTS optimization_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT UNIQUE NOT NULL,
            site_id INTEGER,
            status TEXT DEFAULT 'pending',
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            total_recommendations INTEGER DEFAULT 0,
            approved_recommendations INTEGER DEFAULT 0,
            executed_recommendations INTEGER DEFAULT 0,
            rolled_back_recommendations INTEGER DEFAULT 0,
            error_message TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)
    
    await manager.execute("""
        CREATE TABLE IF NOT EXISTS optimization_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            cell_id INTEGER,
            parameter_name TEXT NOT NULL,
            current_value TEXT,
            recommended_value TEXT NOT NULL,
            confidence REAL,
            risk_level TEXT,
            expected_improvement REAL,
            reasoning TEXT,
            kpi_name TEXT,
            category TEXT,
            status TEXT DEFAULT 'pending',
            approved_at TIMESTAMP,
            executed_at TIMESTAMP,
            rolled_back_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES optimization_runs(run_id),
            FOREIGN KEY (cell_id) REFERENCES cells(id)
        )
    """)
    
    yield manager
    
    await manager.disconnect()


@pytest_asyncio.fixture
async def seeded_db(db_manager) -> AsyncGenerator:
    """Database with test seed data."""
    # Insert test site
    await db_manager.execute(
        """
        INSERT INTO sites (name, region, latitude, longitude, ne_id, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("TestSite001", "Harare", -17.8292, 31.0522, "NE001", "online"),
    )
    
    # Insert test cells
    cells = [
        (1, "Cell001", "TestSite001_Cell1", "LTE", "B3", 100, 1850, 0, 4.0, 40.0),
        (1, "Cell002", "TestSite001_Cell2", "LTE", "B3", 101, 1850, 120, 6.0, 40.0),
        (1, "Cell003", "TestSite001_Cell3", "LTE", "B3", 102, 1850, 240, 5.0, 40.0),
    ]
    
    for cell in cells:
        await db_manager.execute(
            """
            INSERT INTO cells (site_id, cell_id, cell_name, technology, band, pci, earfcn, azimuth, tilt, power)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            cell,
        )
    
    # Insert test KPI data
    now = datetime.now(timezone.utc)
    kpis = [
        (1, 1, "call_setup_success_rate", 97.5, "%", now),
        (1, 1, "call_drop_rate", 1.8, "%", now),
        (1, 1, "handover_success_rate", 96.2, "%", now),
        (2, 1, "call_setup_success_rate", 92.1, "%", now),
        (2, 1, "call_drop_rate", 4.5, "%", now),
        (3, 1, "call_setup_success_rate", 98.9, "%", now),
    ]
    
    for kpi in kpis:
        await db_manager.execute(
            """
            INSERT INTO kpi_data (cell_id, site_id, kpi_name, kpi_value, kpi_unit, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            kpi,
        )
    
    yield db_manager


# ============================================================================
# Mock Client Fixtures
# ============================================================================

@pytest.fixture
def mock_mae_client() -> MagicMock:
    """Create a mock Huawei MAE client."""
    client = AsyncMock()
    
    # Mock get_managed_elements
    client.get_managed_elements.return_value = [
        {
            "ne_id": "NE001",
            "name": "TestSite001",
            "type": "eNodeB",
            "status": "online",
            "ip_address": "192.168.1.100",
        },
    ]
    
    # Mock get_cell_configuration
    client.get_cell_configuration.return_value = {
        "cell_id": "Cell001",
        "parameters": {
            "rsrpThreshold": -110,
            "rsrqThreshold": -12,
            "tac": 1234,
            "pci": 100,
        },
    }
    
    # Mock get_performance_data
    client.get_performance_data.return_value = [
        {
            "kpi_name": "call_setup_success_rate",
            "value": 97.5,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        {
            "kpi_name": "call_drop_rate",
            "value": 1.8,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    ]
    
    # Mock execute_mml_command
    client.execute_mml_command.return_value = {
        "success": True,
        "output": "Command executed successfully",
        "execution_time_ms": 150,
    }
    
    return client


@pytest.fixture
def mock_llm() -> MagicMock:
    """Create a mock LLM for testing."""
    llm = MagicMock()
    
    # Mock ainvoke for analysis
    llm.ainvoke = AsyncMock(return_value=MagicMock(
        content="""
        Based on the analysis of TestSite001:
        
        **Findings:**
        - Cell002 has elevated call drop rate (4.5%)
        - Possible handover issues detected
        
        **Recommendations:**
        1. Adjust handover parameters for Cell002
        2. Consider increasing pilot power
        """
    ))
    
    return llm


# ============================================================================
# Domain Model Fixtures
# ============================================================================

@pytest.fixture
def sample_site() -> dict:
    """Create a sample site dictionary."""
    return {
        "id": 1,
        "name": "TestSite001",
        "region": "Harare",
        "latitude": -17.8292,
        "longitude": 31.0522,
        "ne_id": "NE001",
        "status": "online",
    }


@pytest.fixture
def sample_cell() -> dict:
    """Create a sample cell dictionary."""
    return {
        "id": 1,
        "site_id": 1,
        "cell_id": "Cell001",
        "cell_name": "TestSite001_Cell1",
        "technology": "LTE",
        "band": "B3",
        "pci": 100,
        "earfcn": 1850,
        "azimuth": 0,
        "tilt": 4.0,
        "power": 40.0,
        "status": "active",
    }


@pytest.fixture
def sample_kpi_data() -> list[dict]:
    """Create sample KPI data."""
    now = datetime.now(timezone.utc)
    return [
        {
            "kpi_name": "call_setup_success_rate",
            "value": 97.5,
            "unit": "%",
            "timestamp": now,
        },
        {
            "kpi_name": "call_drop_rate",
            "value": 1.8,
            "unit": "%",
            "timestamp": now,
        },
        {
            "kpi_name": "handover_success_rate",
            "value": 96.2,
            "unit": "%",
            "timestamp": now,
        },
    ]


@pytest.fixture
def sample_recommendation() -> dict:
    """Create a sample recommendation."""
    return {
        "id": 1,
        "run_id": str(uuid.uuid4()),
        "cell_id": 1,
        "parameter_name": "handoverMargin",
        "current_value": "3",
        "recommended_value": "5",
        "confidence": 0.85,
        "risk_level": "low",
        "expected_improvement": 2.5,
        "reasoning": "Increasing handover margin may reduce ping-pong handovers",
        "kpi_name": "handover_success_rate",
        "category": "mobility",
        "status": "pending",
    }


# ============================================================================
# Workflow State Fixtures
# ============================================================================

@pytest.fixture
def initial_workflow_state() -> dict:
    """Create an initial workflow state for testing."""
    return {
        "run_id": str(uuid.uuid4()),
        "site_id": 1,
        "site_name": "TestSite001",
        "status": "initialized",
        "current_agent": None,
        "collected_data": {},
        "analysis_results": {},
        "recommendations": [],
        "approved_recommendations": [],
        "execution_results": [],
        "validation_results": {},
        "report": None,
        "errors": [],
        "dry_run": False,
        "auto_approve": False,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }


# ============================================================================
# Utility Functions
# ============================================================================

def create_test_run_id() -> str:
    """Create a unique test run ID."""
    return f"test-run-{uuid.uuid4().hex[:8]}"


# ============================================================================
# Markers
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
