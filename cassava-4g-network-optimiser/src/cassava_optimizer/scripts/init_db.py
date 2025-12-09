#!/usr/bin/env python3
"""
Database Initialization Script.

Initializes the SQLite database with all required tables for the
Cassava 4G Network Optimizer.

Usage:
    python -m cassava_optimizer.scripts.init_db
    python -m cassava_optimizer.scripts.init_db --reset
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from cassava_optimizer.config import get_settings
from cassava_optimizer.infrastructure.database import DatabaseManager

logger = logging.getLogger(__name__)


async def init_database(reset: bool = False) -> None:
    """
    Initialize the database with all required tables.
    
    Args:
        reset: If True, drop existing tables before creating new ones
    """
    settings = get_settings()
    db_manager = DatabaseManager(settings.database_url)
    
    try:
        # Connect to database
        await db_manager.connect()
        logger.info(f"Connected to database: {settings.database_url}")
        
        if reset:
            logger.warning("Resetting database - all data will be lost!")
            await drop_all_tables(db_manager)
        
        # Create tables
        await create_all_tables(db_manager)
        
        # Create indexes
        await create_indexes(db_manager)
        
        # Insert default data
        await insert_default_data(db_manager)
        
        logger.info("Database initialization complete!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        await db_manager.disconnect()


async def drop_all_tables(db_manager: DatabaseManager) -> None:
    """Drop all existing tables."""
    tables = [
        "command_execution_log",
        "optimization_recommendations",
        "optimization_runs",
        "kpi_data",
        "cell_configurations",
        "cells",
        "sites",
        "kpi_thresholds",
        "system_config",
    ]
    
    for table in tables:
        try:
            await db_manager.execute(f"DROP TABLE IF EXISTS {table}")
            logger.info(f"Dropped table: {table}")
        except Exception as e:
            logger.warning(f"Could not drop table {table}: {e}")


async def create_all_tables(db_manager: DatabaseManager) -> None:
    """Create all required database tables."""
    
    # Sites table
    await db_manager.execute("""
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
    logger.info("Created table: sites")
    
    # Cells table
    await db_manager.execute("""
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
    logger.info("Created table: cells")
    
    # Cell configurations table
    await db_manager.execute("""
        CREATE TABLE IF NOT EXISTS cell_configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cell_id INTEGER NOT NULL,
            parameter_name TEXT NOT NULL,
            parameter_value TEXT NOT NULL,
            parameter_type TEXT,
            category TEXT,
            is_current BOOLEAN DEFAULT TRUE,
            effective_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            effective_to TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cell_id) REFERENCES cells(id)
        )
    """)
    logger.info("Created table: cell_configurations")
    
    # KPI data table
    await db_manager.execute("""
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
    logger.info("Created table: kpi_data")
    
    # Optimization runs table
    await db_manager.execute("""
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
    logger.info("Created table: optimization_runs")
    
    # Optimization recommendations table
    await db_manager.execute("""
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
    logger.info("Created table: optimization_recommendations")
    
    # Command execution log table
    await db_manager.execute("""
        CREATE TABLE IF NOT EXISTS command_execution_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recommendation_id INTEGER,
            site_id INTEGER,
            cell_id INTEGER,
            command_type TEXT NOT NULL,
            command_text TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT,
            error_message TEXT,
            execution_time_ms INTEGER,
            executed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recommendation_id) REFERENCES optimization_recommendations(id),
            FOREIGN KEY (site_id) REFERENCES sites(id),
            FOREIGN KEY (cell_id) REFERENCES cells(id)
        )
    """)
    logger.info("Created table: command_execution_log")
    
    # KPI thresholds table
    await db_manager.execute("""
        CREATE TABLE IF NOT EXISTS kpi_thresholds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kpi_name TEXT UNIQUE NOT NULL,
            warning_threshold REAL,
            critical_threshold REAL,
            target_value REAL,
            direction TEXT DEFAULT 'higher_is_better',
            weight REAL DEFAULT 1.0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logger.info("Created table: kpi_thresholds")
    
    # System config table
    await db_manager.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logger.info("Created table: system_config")


async def create_indexes(db_manager: DatabaseManager) -> None:
    """Create database indexes for better query performance."""
    
    indexes = [
        ("idx_cells_site_id", "cells", "site_id"),
        ("idx_kpi_data_cell_id", "kpi_data", "cell_id"),
        ("idx_kpi_data_site_id", "kpi_data", "site_id"),
        ("idx_kpi_data_timestamp", "kpi_data", "timestamp"),
        ("idx_kpi_data_kpi_name", "kpi_data", "kpi_name"),
        ("idx_optimization_runs_site_id", "optimization_runs", "site_id"),
        ("idx_optimization_runs_status", "optimization_runs", "status"),
        ("idx_recommendations_run_id", "optimization_recommendations", "run_id"),
        ("idx_recommendations_status", "optimization_recommendations", "status"),
        ("idx_command_log_site_id", "command_execution_log", "site_id"),
        ("idx_command_log_status", "command_execution_log", "status"),
    ]
    
    for idx_name, table, column in indexes:
        try:
            await db_manager.execute(
                f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})"
            )
            logger.info(f"Created index: {idx_name}")
        except Exception as e:
            logger.warning(f"Could not create index {idx_name}: {e}")


async def insert_default_data(db_manager: DatabaseManager) -> None:
    """Insert default KPI thresholds and system configuration."""
    
    # Default KPI thresholds
    kpi_thresholds = [
        ("call_setup_success_rate", 95.0, 90.0, 99.0, "higher_is_better", 1.0),
        ("call_drop_rate", 2.0, 5.0, 1.0, "lower_is_better", 1.0),
        ("handover_success_rate", 95.0, 90.0, 98.0, "higher_is_better", 0.9),
        ("rrc_setup_success_rate", 97.0, 95.0, 99.5, "higher_is_better", 0.8),
        ("erab_setup_success_rate", 97.0, 95.0, 99.0, "higher_is_better", 0.8),
        ("throughput_downlink", 30.0, 20.0, 50.0, "higher_is_better", 0.7),
        ("throughput_uplink", 10.0, 5.0, 25.0, "higher_is_better", 0.6),
        ("prb_utilization_dl", 80.0, 90.0, 60.0, "lower_is_better", 0.5),
        ("ue_count_active", None, None, None, "neutral", 0.3),
    ]
    
    for kpi_name, warning, critical, target, direction, weight in kpi_thresholds:
        try:
            await db_manager.execute(
                """
                INSERT OR IGNORE INTO kpi_thresholds 
                (kpi_name, warning_threshold, critical_threshold, target_value, direction, weight)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (kpi_name, warning, critical, target, direction, weight),
            )
        except Exception as e:
            logger.warning(f"Could not insert KPI threshold {kpi_name}: {e}")
    
    logger.info("Inserted default KPI thresholds")
    
    # Default system configuration
    system_config = [
        ("app_version", "1.0.0", "Application version"),
        ("max_recommendations_per_run", "10", "Maximum recommendations per optimization run"),
        ("confidence_threshold", "0.75", "Minimum confidence for recommendations"),
        ("auto_rollback_enabled", "true", "Enable automatic rollback on failure"),
        ("backup_before_change", "true", "Create backup before configuration changes"),
    ]
    
    for key, value, description in system_config:
        try:
            await db_manager.execute(
                """
                INSERT OR IGNORE INTO system_config (key, value, description)
                VALUES (?, ?, ?)
                """,
                (key, value, description),
            )
        except Exception as e:
            logger.warning(f"Could not insert system config {key}: {e}")
    
    logger.info("Inserted default system configuration")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize the Cassava Network Optimizer database"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the database (drop all tables and recreate)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    print("=" * 60)
    print("Cassava 4G Network Optimizer - Database Initialization")
    print("=" * 60)
    
    if args.reset:
        print("\n⚠️  WARNING: This will delete all existing data!\n")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Aborted.")
            sys.exit(0)
    
    try:
        asyncio.run(init_database(reset=args.reset))
        print("\n✅ Database initialization complete!")
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
