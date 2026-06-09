-- Liquid Zimbabwe 4G Network Optimizer - Database Schema
-- Created: 2025-10-30
-- Purpose: Unified database for KPI tracking, parameter changes, and optimization history

-- ============================================================================
-- TABLE 1: kpi_data
-- Purpose: Store real-time and historical KPI measurements from sites
-- ============================================================================
CREATE TABLE IF NOT EXISTS kpi_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    site_name TEXT NOT NULL,
    cell_id INTEGER NOT NULL,

    -- 7 Weighted KPIs (3-Tier System: Foundation 25%, Revenue/Experience 50%, Efficiency 25%)
    -- Tier 1: Foundation (25%)
    network_access_success REAL,           -- Weight: 25%

    -- Tier 2: Revenue & Experience (50%)
    download_speed REAL,                   -- Weight: 20%
    download_quality REAL,                 -- Weight: 15%
    upload_speed REAL,                     -- Weight: 15%

    -- Tier 3: Efficiency (25%)
    upload_quality REAL,                   -- Weight: 10%
    control_channel_load REAL,             -- Weight: 10%
    feedback_channel_load REAL,            -- Weight: 5%

    -- Metadata
    data_source TEXT DEFAULT 'live',       -- 'live' or 'historical'
    notes TEXT
);

-- Indexes for kpi_data table
CREATE INDEX IF NOT EXISTS idx_kpi_site_timestamp ON kpi_data(site_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_kpi_site_cell ON kpi_data(site_name, cell_id);
CREATE INDEX IF NOT EXISTS idx_kpi_timestamp ON kpi_data(timestamp);

-- ============================================================================
-- TABLE 2: parameter_changes
-- Purpose: Track all parameter modifications with MML command execution logs
-- ============================================================================
CREATE TABLE IF NOT EXISTS parameter_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    site_name TEXT NOT NULL,
    cell_id INTEGER NOT NULL,

    -- Parameter details
    parameter_name TEXT NOT NULL,          -- e.g., 'reference_signal_power_pdschcfg'
    old_value TEXT,                        -- Previous value (NULL for first change)
    new_value TEXT NOT NULL,               -- New value applied

    -- Change metadata
    reason TEXT,                           -- Why the change was made
    mml_command TEXT,                      -- Actual MML command executed
    success BOOLEAN DEFAULT 0,             -- 0=failed, 1=success
    error_message TEXT,                    -- Error if success=0
    changed_by TEXT DEFAULT 'system',      -- 'system', 'user', 'agent_name'

    -- Impact tracking
    expected_kpi_impact TEXT              -- JSON: {"download_speed": "+5%", ...}
);

-- Indexes for parameter_changes table
CREATE INDEX IF NOT EXISTS idx_param_site_param ON parameter_changes(site_name, parameter_name);
CREATE INDEX IF NOT EXISTS idx_param_timestamp ON parameter_changes(timestamp);
CREATE INDEX IF NOT EXISTS idx_param_success ON parameter_changes(success);

-- ============================================================================
-- TABLE 3: optimization_history
-- Purpose: Track complete optimization cycles from trigger to outcome
-- ============================================================================
CREATE TABLE IF NOT EXISTS optimization_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    site_name TEXT NOT NULL,
    cell_id INTEGER NOT NULL,

    -- Trigger information
    kpi_issue TEXT NOT NULL,               -- e.g., 'Low Download Speed (42 Mbps < 50 Mbps)'
    trigger_reason TEXT,                   -- Detailed reason for optimization

    -- Changes made
    parameters_changed TEXT NOT NULL,      -- JSON: [{"param": "p0_nominal", "old": 10, "new": 15}, ...]
    mml_commands TEXT,                     -- All MML commands executed (newline-separated)

    -- Before state
    kpi_before TEXT NOT NULL,              -- JSON: {"download_speed": 42, "upload_speed": 18, ...}
    weighted_score_before REAL,            -- Calculated weighted KPI score (0-100)

    -- After state (NULL if measurement pending)
    kpi_after TEXT,                        -- JSON: {"download_speed": 58, "upload_speed": 20, ...}
    weighted_score_after REAL,             -- Calculated weighted KPI score after change
    weighted_improvement REAL,             -- score_after - score_before

    -- Outcome
    success BOOLEAN,                       -- Did optimization improve KPIs?
    rolled_back BOOLEAN DEFAULT 0,         -- Was change rolled back?
    rollback_reason TEXT,                  -- Why was it rolled back?

    -- Agent workflow metadata
    agent_workflow TEXT                   -- JSON: agent execution path and decisions
);

-- Indexes for optimization_history table
CREATE INDEX IF NOT EXISTS idx_opt_site_timestamp ON optimization_history(site_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_opt_success ON optimization_history(success);
CREATE INDEX IF NOT EXISTS idx_opt_rolled_back ON optimization_history(rolled_back);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Latest KPI per site
CREATE VIEW IF NOT EXISTS latest_kpi_per_site AS
SELECT
    site_name,
    cell_id,
    MAX(timestamp) as latest_timestamp,
    network_access_success,
    download_speed,
    download_quality,
    upload_speed,
    upload_quality,
    control_channel_load,
    feedback_channel_load,
    data_source
FROM kpi_data
GROUP BY site_name, cell_id;

-- View: Recent parameter changes (last 30 days)
CREATE VIEW IF NOT EXISTS recent_parameter_changes AS
SELECT
    timestamp,
    site_name,
    cell_id,
    parameter_name,
    old_value,
    new_value,
    reason,
    success,
    changed_by
FROM parameter_changes
WHERE timestamp >= datetime('now', '-30 days')
ORDER BY timestamp DESC;

-- View: Optimization success rate
CREATE VIEW IF NOT EXISTS optimization_success_rate AS
SELECT
    site_name,
    COUNT(*) as total_optimizations,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_optimizations,
    ROUND(100.0 * SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate_percent,
    AVG(weighted_improvement) as avg_weighted_improvement
FROM optimization_history
WHERE kpi_after IS NOT NULL
GROUP BY site_name;

-- ============================================================================
-- SAMPLE DATA NOTES
-- ============================================================================
-- Historical data will be imported from historical_data.csv
-- CSV columns: Date, Site Name, Download Speed (Mbps), Download Quality (%),
--              Upload Speed (Mbps), Upload Quality (%), Access Success Rate (%),
--              Control Channel Load (%), Feedback Channel Load (%)
