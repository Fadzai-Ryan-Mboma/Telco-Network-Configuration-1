-- Liquid Zimbabwe 4G Optimizer - Database Schema
-- Single Unified Database (liquid4g.db)
-- Version: 2.0.0

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- ============================================
-- NETWORK INFRASTRUCTURE
-- ============================================

-- Network Sites (eNodeB locations)
CREATE TABLE IF NOT EXISTS network_sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT UNIQUE NOT NULL,
    site_name TEXT NOT NULL,
    location TEXT,
    latitude REAL,
    longitude REAL,
    region TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (status IN ('active', 'inactive', 'maintenance', 'decommissioned')),
    CHECK (latitude IS NULL OR (latitude >= -90 AND latitude <= 90)),
    CHECK (longitude IS NULL OR (longitude >= -180 AND longitude <= 180))
);

-- Network Cells (individual cells within sites)
CREATE TABLE IF NOT EXISTS network_cells (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cell_id TEXT UNIQUE NOT NULL,
    site_id TEXT NOT NULL,
    cell_name TEXT,
    technology TEXT DEFAULT '4G',
    frequency_band TEXT,
    pci INTEGER,
    sector INTEGER,
    azimuth INTEGER,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (site_id) REFERENCES network_sites(site_id) ON DELETE CASCADE,
    CHECK (technology IN ('4G', '4G+', '5G')),
    CHECK (status IN ('active', 'inactive', 'maintenance', 'blocked')),
    CHECK (pci IS NULL OR (pci >= 0 AND pci <= 503)),
    CHECK (sector IS NULL OR (sector >= 1 AND sector <= 3)),
    CHECK (azimuth IS NULL OR (azimuth >= 0 AND azimuth <= 360))
);

-- ============================================
-- KPI DATA (Normalized Design)
-- ============================================

-- KPI Definitions (metadata about each KPI)
CREATE TABLE IF NOT EXISTS kpi_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kpi_key TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    unit TEXT,
    category TEXT NOT NULL,
    higher_is_better BOOLEAN NOT NULL,
    optimal_min REAL,
    optimal_max REAL,
    warning_threshold REAL,
    critical_threshold REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (category IN ('accessibility', 'retainability', 'quality', 'capacity', 'coverage'))
);

-- KPI Measurements (actual data points)
CREATE TABLE IF NOT EXISTS kpi_measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    measurement_time TIMESTAMP NOT NULL,
    cell_id TEXT NOT NULL,
    kpi_key TEXT NOT NULL,
    value REAL NOT NULL,
    data_source TEXT DEFAULT 'api',
    quality_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (cell_id) REFERENCES network_cells(cell_id) ON DELETE CASCADE,
    FOREIGN KEY (kpi_key) REFERENCES kpi_definitions(kpi_key),
    CHECK (data_source IN ('api', 'database', 'simulation', 'manual')),
    CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1))
);

-- KPI Alerts (threshold violations)
CREATE TABLE IF NOT EXISTS kpi_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id TEXT UNIQUE NOT NULL,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    cell_id TEXT NOT NULL,
    kpi_key TEXT NOT NULL,
    severity TEXT NOT NULL,
    current_value REAL NOT NULL,
    threshold_value REAL NOT NULL,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'active',

    FOREIGN KEY (cell_id) REFERENCES network_cells(cell_id),
    FOREIGN KEY (kpi_key) REFERENCES kpi_definitions(kpi_key),
    CHECK (severity IN ('info', 'warning', 'critical')),
    CHECK (status IN ('active', 'acknowledged', 'resolved', 'closed'))
);

-- ============================================
-- NETWORK PARAMETERS
-- ============================================

-- Parameter Definitions (metadata)
CREATE TABLE IF NOT EXISTS parameter_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    param_key TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    unit TEXT,
    category TEXT NOT NULL,
    min_value REAL,
    max_value REAL,
    default_value REAL,
    step_size REAL,
    mml_query_command TEXT,
    mml_modify_command TEXT,
    impact_level TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (category IN ('power_control', 'mobility', 'radio_resource', 'timing', 'scheduling')),
    CHECK (impact_level IN ('low', 'medium', 'high', 'critical'))
);

-- Parameter Values (current settings)
CREATE TABLE IF NOT EXISTS parameter_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cell_id TEXT NOT NULL,
    param_key TEXT NOT NULL,
    value REAL NOT NULL,
    measured_at TIMESTAMP NOT NULL,
    data_source TEXT DEFAULT 'api',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (cell_id) REFERENCES network_cells(cell_id) ON DELETE CASCADE,
    FOREIGN KEY (param_key) REFERENCES parameter_definitions(param_key)
);

-- Parameter Changes (audit trail)
CREATE TABLE IF NOT EXISTS parameter_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_id TEXT UNIQUE NOT NULL,
    cell_id TEXT NOT NULL,
    param_key TEXT NOT NULL,
    old_value REAL,
    new_value REAL NOT NULL,
    change_type TEXT NOT NULL,
    change_reason TEXT,
    requested_by TEXT NOT NULL,
    approved_by TEXT,
    executed_at TIMESTAMP,
    success BOOLEAN,
    error_message TEXT,
    rollback_available BOOLEAN DEFAULT TRUE,
    rollback_command TEXT,
    kpi_snapshot_before TEXT,
    kpi_snapshot_after TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (cell_id) REFERENCES network_cells(cell_id),
    FOREIGN KEY (param_key) REFERENCES parameter_definitions(param_key),
    CHECK (change_type IN ('optimization', 'maintenance', 'emergency', 'rollback', 'manual'))
);

-- ============================================
-- AGENTIC SYSTEM
-- ============================================

-- Agents (autonomous operators)
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT UNIQUE NOT NULL,
    agent_type TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'idle',
    current_task TEXT,
    capabilities TEXT,
    config TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP,

    CHECK (agent_type IN ('monitor', 'analyzer', 'optimizer', 'validator', 'executor', 'orchestrator')),
    CHECK (status IN ('idle', 'running', 'paused', 'error', 'maintenance'))
);

-- Operations (workflow executions)
CREATE TABLE IF NOT EXISTS operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id TEXT UNIQUE NOT NULL,
    operation_type TEXT NOT NULL,
    stage TEXT,
    target_site TEXT,
    target_cell TEXT,
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'normal',
    parameters TEXT,
    results TEXT,
    agent_id TEXT,
    parent_operation_id TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,
    error_message TEXT,

    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (parent_operation_id) REFERENCES operations(operation_id),
    CHECK (operation_type IN ('full_optimization', 'kpi_analysis', 'parameter_query', 'validation', 'execution', 'monitoring')),
    CHECK (status IN ('pending', 'running', 'paused', 'completed', 'failed', 'cancelled')),
    CHECK (priority IN ('low', 'normal', 'high', 'urgent'))
);

-- Operation Logs (detailed execution logs)
CREATE TABLE IF NOT EXISTS operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id TEXT NOT NULL,
    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    log_level TEXT DEFAULT 'INFO',
    stage TEXT,
    message TEXT NOT NULL,
    details TEXT,

    FOREIGN KEY (operation_id) REFERENCES operations(operation_id) ON DELETE CASCADE,
    CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- Agent Metrics (performance tracking)
CREATE TABLE IF NOT EXISTS agent_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    llm_executions INTEGER DEFAULT 0,
    rule_executions INTEGER DEFAULT 0,
    circuit_breaker_open BOOLEAN DEFAULT FALSE,
    average_duration_seconds REAL,
    metadata TEXT,

    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- ============================================
-- VALIDATION & APPROVAL
-- ============================================

-- Validation Requests (human approval workflow)
CREATE TABLE IF NOT EXISTS validation_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT UNIQUE NOT NULL,
    operation_id TEXT NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    requested_by TEXT,
    change_summary TEXT NOT NULL,
    impact_assessment TEXT,
    safety_score REAL,
    requires_human_approval BOOLEAN DEFAULT FALSE,
    approved_by TEXT,
    approved_at TIMESTAMP,
    approval_status TEXT DEFAULT 'pending',
    approval_notes TEXT,

    FOREIGN KEY (operation_id) REFERENCES operations(operation_id),
    CHECK (approval_status IN ('pending', 'approved', 'rejected', 'cancelled')),
    CHECK (safety_score IS NULL OR (safety_score >= 0 AND safety_score <= 1))
);

-- ============================================
-- SYSTEM METADATA
-- ============================================

-- Schema Migrations (track applied migrations)
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Config (runtime configuration)
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Network indexes
CREATE INDEX IF NOT EXISTS idx_network_sites_status ON network_sites(status);
CREATE INDEX IF NOT EXISTS idx_network_sites_region ON network_sites(region);
CREATE INDEX IF NOT EXISTS idx_network_cells_site ON network_cells(site_id);
CREATE INDEX IF NOT EXISTS idx_network_cells_status ON network_cells(status);

-- KPI indexes
CREATE INDEX IF NOT EXISTS idx_kpi_measurements_cell_time ON kpi_measurements(cell_id, measurement_time DESC);
CREATE INDEX IF NOT EXISTS idx_kpi_measurements_kpi_time ON kpi_measurements(kpi_key, measurement_time DESC);
CREATE INDEX IF NOT EXISTS idx_kpi_alerts_cell_status ON kpi_alerts(cell_id, status);
CREATE INDEX IF NOT EXISTS idx_kpi_alerts_triggered ON kpi_alerts(triggered_at DESC);

-- Parameter indexes
CREATE INDEX IF NOT EXISTS idx_parameter_values_cell_param ON parameter_values(cell_id, param_key);
CREATE INDEX IF NOT EXISTS idx_parameter_changes_cell ON parameter_changes(cell_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_parameter_changes_executed ON parameter_changes(executed_at DESC);

-- Agent indexes
CREATE INDEX IF NOT EXISTS idx_operations_status ON operations(status, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_operations_site ON operations(target_site);
CREATE INDEX IF NOT EXISTS idx_operations_agent ON operations(agent_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_operation ON operation_logs(operation_id, log_time DESC);

-- ============================================
-- INITIAL DATA
-- ============================================

-- Insert schema version
INSERT OR IGNORE INTO schema_migrations (version, name) VALUES (1, 'initial_schema');

-- Insert system config
INSERT OR IGNORE INTO system_config (key, value, description) VALUES
    ('schema_version', '2.0.0', 'Database schema version'),
    ('created_at', datetime('now'), 'Database creation timestamp'),
    ('environment', 'production', 'Environment: development|production|testing');

-- End of schema
