# LIQUID ZIMBABWE 4G NETWORK OPTIMIZER - PRODUCTION REMEDIATION PLAN

**Date:** October 8, 2025
**Status:** ❌ NOT PRODUCTION READY - CRITICAL REMEDIATION REQUIRED
**Estimated Effort:** 25-36 working days (5-7 weeks)
**Priority:** CRITICAL - Security and data integrity issues identified

---

## EXECUTIVE SUMMARY

Comprehensive production validation audit identified **critical security vulnerabilities, extensive use of simulated data, database architecture chaos, and incomplete API integration** that make the system unsuitable for production deployment.

**Overall Production Readiness Score: 2.4/10**

This document provides a detailed, actionable remediation plan to transform the system into a production-ready enterprise solution.

---

## PHASE 1: CRITICAL SECURITY FIXES (Week 1 - Days 1-5)

### Priority: CRITICAL | Effort: 5-7 days | Blockers: None

### 1.1 Remove Hardcoded Credentials

**Files to Modify:**
- `/liquid-4g-core/agents/huawei_api_client.py` (Line 87)
- `/archive/agentic_llm_workflow/huawei_api_client.py` (Line 79)
- All 7+ files with `#Pass123#` hardcoded

**Actions:**
```python
# BEFORE (CRITICAL SECURITY ISSUE):
self.password = password or os.getenv('HUAWEI_PASSWORD', '#Pass123#')

# AFTER:
self.password = password or os.getenv('HUAWEI_PASSWORD')
if not self.password:
    raise ValueError("HUAWEI_PASSWORD environment variable must be set")
```

**Task List:**
- [ ] Search and remove ALL instances of `#Pass123#`
- [ ] Remove password fallback defaults
- [ ] Implement mandatory environment variable validation
- [ ] Add startup checks for required credentials
- [ ] Document required environment variables

### 1.2 Secure .env File

**Current Issue:**
```bash
# /.env - COMMITTED TO GIT (CRITICAL SECURITY ISSUE)
LZ_API_URL=https://41.174.191.214:31127
LZ_API_USERNAME=cassava.ai
LZ_API_PASSWORD=#Pass123#
```

**Actions:**
```bash
# 1. Add .env to .gitignore
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
echo "!.env.example" >> .gitignore

# 2. Remove from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 3. Create .env.example template
cat > .env.example << EOF
# Huawei MAE API Configuration
LZ_API_URL=https://your-huawei-api-server:port
LZ_API_USERNAME=your_username
LZ_API_PASSWORD=your_secure_password

# Database Configuration
LZ_DB_PATH=/path/to/database

# Environment
LZ_ENV=production
LZ_DOCKER=0
EOF
```

**Task List:**
- [ ] Add .env to .gitignore
- [ ] Create .env.example template
- [ ] Remove .env from git history
- [ ] Update deployment documentation
- [ ] Implement secrets manager integration (Azure Key Vault/AWS Secrets Manager)

### 1.3 Enable SSL Verification

**Current Issue:**
```python
# SECURITY RISK - MITM attacks possible
self.session.verify = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

**Solution:**
```python
# Option 1: Use proper certificate
self.session.verify = os.getenv('HUAWEI_CA_CERT_PATH', True)

# Option 2: If internal CA, add to trust store
import certifi
ca_bundle = certifi.where()
self.session.verify = ca_bundle

# Option 3: Custom CA certificate
if os.getenv('HUAWEI_CA_CERT_PATH'):
    self.session.verify = os.getenv('HUAWEI_CA_CERT_PATH')
else:
    self.session.verify = True  # Enforce verification
```

**Task List:**
- [ ] Enable SSL verification in all API clients
- [ ] Document certificate requirements
- [ ] Provide CA certificate installation guide
- [ ] Add certificate path to configuration
- [ ] Remove SSL warning suppressions

### 1.4 Implement Secrets Management

**Create: `/liquid-4g-core/config/secrets_manager.py`**
```python
"""
Secure secrets management for production deployment
"""
import os
from typing import Optional
from abc import ABC, abstractmethod

class SecretsProvider(ABC):
    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        pass

class EnvironmentSecretsProvider(SecretsProvider):
    """Get secrets from environment variables"""
    def get_secret(self, key: str) -> Optional[str]:
        return os.getenv(key)

class AzureKeyVaultProvider(SecretsProvider):
    """Get secrets from Azure Key Vault"""
    def __init__(self, vault_url: str):
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=credential)

    def get_secret(self, key: str) -> Optional[str]:
        try:
            return self.client.get_secret(key).value
        except Exception as e:
            logger.error(f"Failed to retrieve secret {key}: {e}")
            return None

class SecretsManager:
    """Centralized secrets management"""
    def __init__(self, provider: SecretsProvider = None):
        self.provider = provider or EnvironmentSecretsProvider()

    def get_api_credentials(self) -> dict:
        url = self.provider.get_secret('LZ_API_URL')
        username = self.provider.get_secret('LZ_API_USERNAME')
        password = self.provider.get_secret('LZ_API_PASSWORD')

        if not all([url, username, password]):
            raise ValueError("Missing required API credentials")

        return {
            'url': url,
            'username': username,
            'password': password
        }
```

**Task List:**
- [ ] Create secrets_manager.py module
- [ ] Implement environment provider
- [ ] Add Azure Key Vault provider (optional)
- [ ] Add AWS Secrets Manager provider (optional)
- [ ] Update all credential access to use SecretsManager
- [ ] Add validation for required secrets on startup

---

## PHASE 2: REMOVE SIMULATION/MOCK DATA (Week 1-2 - Days 6-10)

### Priority: CRITICAL | Effort: 5 days | Blockers: Phase 1 complete

### 2.1 Remove Simulated KPI Data Generation

**File: `/liquid-4g-core/agents/liquid_zimbabwe_kpi.py`**

**Remove Lines 487-514:**
```python
# DELETE THIS ENTIRE FUNCTION:
def _get_simulated_kpi_data(self, site_id: str = None) -> Dict:
    """Generate simulated KPI data for testing purposes"""
    # ... 28 lines of random data generation
```

**Remove Lines 428-429, 485:**
```python
# DELETE: Automatic fallback to simulation
if not api_client.is_authenticated():
    self.logger.warning("API client not authenticated, using simulated data")
    return self._get_simulated_kpi_data(site_id)  # DELETE THIS
```

**Replace with:**
```python
if not api_client.is_authenticated():
    raise ConnectionError("API client not authenticated. Cannot retrieve live KPI data.")

# Add proper error handling
try:
    kpi_data = api_client.get_kpi_data(ne_names, start_time, end_time)
    if not kpi_data:
        raise ValueError("No KPI data returned from API")
    return kpi_data
except Exception as e:
    self.logger.error(f"Failed to collect live KPI data: {e}")
    # Log to monitoring system
    self._record_data_collection_failure(str(e))
    raise  # Don't fallback, fail explicitly
```

**Task List:**
- [ ] Delete `_get_simulated_kpi_data()` function
- [ ] Remove all calls to simulation function
- [ ] Replace with proper error handling
- [ ] Add data collection failure logging
- [ ] Add alerting for data collection failures
- [ ] Update tests to use mock API responses

### 2.2 Remove Sample Database Initialization

**File: `/liquid-4g-core/unified_database.py`**

**Remove Lines 95-175:**
```python
# DELETE: _populate_sample_data() entire function
def _populate_sample_data(self):
    """Populate with realistic sample data"""
    # DELETE all 80 lines of random data generation
```

**Replace with:**
```python
def _verify_schema_initialized(self):
    """Verify database schema exists without populating fake data"""
    with sqlite3.connect(self.main_db) as conn:
        cursor = conn.cursor()

        # Check if required tables exist
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='table' AND name IN (
                'network_elements', 'kpi_data', 'parameter_data'
            )
        """)

        table_count = cursor.fetchone()[0]
        if table_count < 3:
            raise DatabaseError("Required tables not initialized")

        self.logger.info("Database schema verified")
```

**Update `__init__` method:**
```python
def __init__(self, base_path: str = None):
    # ... existing initialization code ...
    self._initialize_unified_database()
    self._verify_schema_initialized()  # Changed from _populate_sample_data()

    # Verify we have real data or fail
    self._validate_production_data()
```

**Add validation:**
```python
def _validate_production_data(self):
    """Ensure database contains real production data"""
    with sqlite3.connect(self.main_db) as conn:
        cursor = conn.cursor()

        # Check for sample/simulated data
        cursor.execute("""
            SELECT COUNT(*) FROM kpi_data
            WHERE data_source IN ('sample', 'simulated', 'test')
        """)

        sample_count = cursor.fetchone()[0]
        if sample_count > 0:
            raise DataIntegrityError(
                f"Found {sample_count} sample/simulated records. "
                "Production database must contain only real data."
            )

        # Check if we have any data at all
        cursor.execute("SELECT COUNT(*) FROM network_elements")
        ne_count = cursor.fetchone()[0]

        if ne_count == 0:
            raise DataIntegrityError(
                "No network elements configured. "
                "Load production configuration before starting."
            )
```

**Task List:**
- [ ] Delete `_populate_sample_data()` function
- [ ] Create `_verify_schema_initialized()` method
- [ ] Create `_validate_production_data()` method
- [ ] Add data source validation
- [ ] Document production data loading process
- [ ] Create data import scripts for real network data

### 2.3 Remove Hardcoded Network Elements

**File: `/liquid-4g-core/agents/huawei_api_client.py`**

**Remove Lines 185-206:**
```python
# DELETE: Hardcoded fallback network elements
self.logger.info("Using hardcoded network elements configuration")
return [
    NetworkElement(
        name="MSH-0112-Bindura Hospital",
        # ... hardcoded data
    ),
    # DELETE ALL HARDCODED ELEMENTS
]
```

**Replace with:**
```python
def _load_network_elements_from_api(self) -> List[NetworkElement]:
    """Load network elements from Huawei MAE API"""
    if not self.is_authenticated():
        raise ConnectionError("Must authenticate before loading network elements")

    try:
        response = self.session.get(
            f"{self.base_url}/api/rest/networkManagement/v1/elements",
            headers={"accessSession": self.access_token},
            timeout=30
        )
        response.raise_for_status()

        elements_data = response.json()
        network_elements = []

        for element in elements_data.get('data', []):
            ne = NetworkElement(
                name=element['neName'],
                site_id=element['siteId'],
                cell_ids=element.get('cellIds', []),
                location=element.get('location', 'Unknown')
            )
            network_elements.append(ne)

        if not network_elements:
            raise ValueError("No network elements returned from API")

        self.logger.info(f"Loaded {len(network_elements)} network elements from API")
        return network_elements

    except Exception as e:
        self.logger.error(f"Failed to load network elements from API: {e}")
        raise  # Fail explicitly, no fallback
```

**Task List:**
- [ ] Delete all hardcoded network element definitions
- [ ] Implement API-based network element loading
- [ ] Add validation for network element data
- [ ] Document API endpoint for network elements
- [ ] Create manual configuration file as emergency backup (not auto-loaded)

### 2.4 Remove Random Parameter Defaults

**File: `/liquid-4g-core/agents/liquid_zimbabwe_parameters.py`**

**Remove Lines 179-229:**
```python
# DELETE: Random parameter value generation
import random
variation_factor = random.uniform(0.85, 1.15)  # DELETE
varied_value = default_value * variation_factor  # DELETE
```

**Replace with:**
```python
def _load_current_parameters_from_api(self, site_id: str) -> Dict:
    """Load actual current parameter values from network"""
    try:
        params = self.api_client.get_cell_parameters(site_id)

        if not params:
            raise ValueError(f"No parameters returned for site {site_id}")

        self.logger.info(f"Loaded {len(params)} parameters from network for {site_id}")
        return params

    except Exception as e:
        self.logger.error(f"Failed to load parameters for {site_id}: {e}")
        raise  # No defaults, fail explicitly
```

**Task List:**
- [ ] Delete random variation code
- [ ] Delete default parameter value initialization
- [ ] Implement API-based parameter loading
- [ ] Add parameter validation
- [ ] Add parameter synchronization checks

### 2.5 Create Separate Demo Mode (Optional)

**Create: `/liquid-4g-core/demo/demo_mode.py`**
```python
"""
Demo mode for training and demonstrations
NEVER used in production
"""
import os

class DemoModeError(Exception):
    """Raised when demo mode is used incorrectly"""
    pass

def is_demo_mode() -> bool:
    """Check if system is running in demo mode"""
    return os.getenv('LZ_DEMO_MODE', '').lower() == 'true'

def enforce_production_mode():
    """Ensure system is NOT in demo mode"""
    if is_demo_mode():
        raise DemoModeError(
            "System is in DEMO MODE. Cannot perform production operations. "
            "Set LZ_DEMO_MODE=false for production use."
        )

def demo_data_generator():
    """Demo data generation - isolated from production code"""
    if not is_demo_mode():
        raise DemoModeError("Demo data can only be used in demo mode")

    # All simulation code goes here
    # Clearly separated from production
```

**Task List:**
- [ ] Create demo/ directory
- [ ] Move all simulation code to demo module
- [ ] Add demo mode checks
- [ ] Add visual indicators when in demo mode
- [ ] Document demo mode usage
- [ ] Add startup warning if demo mode enabled

---

## PHASE 3: DATABASE CONSOLIDATION (Week 2-3 - Days 11-15)

### Priority: CRITICAL | Effort: 5 days | Blockers: Phase 2 complete

### 3.1 Database Inventory and Analysis

**Current State:**
```
/data/lz_platform.db (94 KB)
/data/liquid_zimbabwe.db (94 KB)
/data/live_network.db (32 KB)
/data/historical_db (11 MB)
/liquid-4g-core/data/lz_platform.db (duplicate)
/liquid-4g-core/data/liquid_zimbabwe.db (duplicate)
/liquid-4g-core/data/live_network.db (duplicate)
/archive/agentic_llm_workflow/data/liquid_zimbabwe.db (old)
```

**Decision: Consolidate to SINGLE production database**

**Task List:**
- [ ] Document all tables across all databases
- [ ] Map table relationships
- [ ] Identify overlapping/duplicate tables
- [ ] Determine canonical schema
- [ ] Plan migration strategy

### 3.2 Design Unified Production Schema

**Create: `/liquid-4g-core/database/schema.sql`**
```sql
-- ============================================================================
-- LIQUID ZIMBABWE 4G NETWORK OPTIMIZER - PRODUCTION DATABASE SCHEMA
-- Version: 2.0
-- Date: 2025-10-08
-- ============================================================================

-- Network Infrastructure
-- ============================================================================

CREATE TABLE IF NOT EXISTS network_elements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ne_id TEXT UNIQUE NOT NULL,           -- Huawei network element ID
    ne_name TEXT UNIQUE NOT NULL,          -- Network element name
    site_id TEXT NOT NULL,                 -- Site identifier
    location TEXT,                         -- Physical location
    ne_type TEXT NOT NULL,                 -- eNodeB, gNodeB, etc.
    vendor TEXT DEFAULT 'Huawei',
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'maintenance')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_ne_site (site_id),
    INDEX idx_ne_status (status)
);

CREATE TABLE IF NOT EXISTS cells (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cell_id INTEGER NOT NULL,
    cell_name TEXT NOT NULL,
    ne_id TEXT NOT NULL,
    local_cell_id INTEGER,
    pci INTEGER,                           -- Physical Cell ID
    frequency_band TEXT,
    bandwidth INTEGER,                     -- MHz
    azimuth INTEGER,                       -- Antenna direction
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'maintenance')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ne_id) REFERENCES network_elements(ne_id) ON DELETE CASCADE,
    UNIQUE(ne_id, local_cell_id),
    INDEX idx_cell_ne (ne_id),
    INDEX idx_cell_status (status)
);

-- KPI Data Management
-- ============================================================================

CREATE TABLE IF NOT EXISTS kpi_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kpi_code TEXT UNIQUE NOT NULL,         -- e.g., 'RACH_SETUP_SUCCESS'
    kpi_name TEXT NOT NULL,                -- Human-readable name
    kpi_category TEXT NOT NULL,            -- accessibility, retainability, etc.
    unit TEXT,                             -- %, Mbps, ms, etc.
    threshold_critical REAL,
    threshold_warning REAL,
    threshold_target REAL,
    description TEXT,
    formula TEXT,                          -- Calculation formula
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kpi_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    cell_id INTEGER NOT NULL,
    kpi_code TEXT NOT NULL,
    value REAL NOT NULL,
    sample_count INTEGER,                  -- Number of samples in aggregation
    data_quality REAL DEFAULT 100.0,       -- 0-100 quality indicator
    collection_method TEXT DEFAULT 'api' CHECK(
        collection_method IN ('api', 'import', 'manual')
    ),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE,
    FOREIGN KEY (kpi_code) REFERENCES kpi_definitions(kpi_code),
    INDEX idx_kpi_timestamp (timestamp),
    INDEX idx_kpi_cell_code (cell_id, kpi_code),
    INDEX idx_kpi_collection (collection_method),

    -- Prevent duplicate measurements
    UNIQUE(timestamp, cell_id, kpi_code)
);

CREATE TABLE IF NOT EXISTS kpi_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    cell_id INTEGER NOT NULL,
    kpi_code TEXT NOT NULL,
    current_value REAL NOT NULL,
    threshold_value REAL NOT NULL,
    alert_level TEXT NOT NULL CHECK(alert_level IN ('critical', 'warning')),
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'acknowledged', 'resolved')),
    acknowledged_by TEXT,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE,
    FOREIGN KEY (kpi_code) REFERENCES kpi_definitions(kpi_code),
    INDEX idx_alert_status (status),
    INDEX idx_alert_level (alert_level),
    INDEX idx_alert_timestamp (timestamp)
);

-- Parameter Management
-- ============================================================================

CREATE TABLE IF NOT EXISTS parameter_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    param_code TEXT UNIQUE NOT NULL,       -- e.g., 'REFERENCE_SIGNAL_POWER'
    param_name TEXT NOT NULL,
    param_type TEXT NOT NULL,              -- integer, float, enum
    unit TEXT,
    min_value REAL,
    max_value REAL,
    allowed_values TEXT,                   -- JSON array for enum types
    default_value REAL,
    mml_command_template TEXT NOT NULL,    -- MOD command template
    impact_level TEXT CHECK(impact_level IN ('low', 'medium', 'high', 'critical')),
    requires_approval BOOLEAN DEFAULT 1,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parameter_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    cell_id INTEGER NOT NULL,
    param_code TEXT NOT NULL,
    current_value REAL NOT NULL,
    unit TEXT,
    data_quality REAL DEFAULT 100.0,
    collection_method TEXT DEFAULT 'api' CHECK(
        collection_method IN ('api', 'import', 'manual')
    ),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE,
    FOREIGN KEY (param_code) REFERENCES parameter_definitions(param_code),
    INDEX idx_param_timestamp (timestamp),
    INDEX idx_param_cell_code (cell_id, param_code),

    UNIQUE(timestamp, cell_id, param_code)
);

CREATE TABLE IF NOT EXISTS parameter_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cell_id INTEGER NOT NULL,
    param_code TEXT NOT NULL,
    old_value REAL,
    new_value REAL NOT NULL,
    change_reason TEXT NOT NULL,
    change_type TEXT CHECK(change_type IN ('manual', 'optimization', 'rollback')),
    requested_by TEXT NOT NULL,
    approved_by TEXT,
    approved_at TIMESTAMP,
    executed_at TIMESTAMP,
    execution_status TEXT CHECK(
        execution_status IN ('pending', 'approved', 'executing', 'success', 'failed', 'rolled_back')
    ),
    mml_command TEXT,
    api_response TEXT,
    error_message TEXT,
    rollback_change_id INTEGER,            -- Reference to rollback change

    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE,
    FOREIGN KEY (param_code) REFERENCES parameter_definitions(param_code),
    FOREIGN KEY (rollback_change_id) REFERENCES parameter_changes(id),
    INDEX idx_change_timestamp (timestamp),
    INDEX idx_change_status (execution_status),
    INDEX idx_change_cell (cell_id)
);

-- Optimization & AI Agent Management
-- ============================================================================

CREATE TABLE IF NOT EXISTS optimization_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cell_id INTEGER NOT NULL,
    kpi_issue TEXT NOT NULL,               -- KPI that triggered optimization
    param_code TEXT NOT NULL,              -- Parameter to modify
    current_value REAL NOT NULL,
    recommended_value REAL NOT NULL,
    expected_improvement TEXT,
    confidence_score REAL,                 -- 0.0-1.0
    priority INTEGER DEFAULT 5,            -- 1-10
    status TEXT DEFAULT 'pending' CHECK(
        status IN ('pending', 'approved', 'rejected', 'implemented')
    ),
    created_by TEXT DEFAULT 'optimization_agent',
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    notes TEXT,

    FOREIGN KEY (cell_id) REFERENCES cells(id) ON DELETE CASCADE,
    FOREIGN KEY (param_code) REFERENCES parameter_definitions(param_code),
    INDEX idx_recommendation_status (status),
    INDEX idx_recommendation_timestamp (timestamp)
);

CREATE TABLE IF NOT EXISTS agent_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id TEXT UNIQUE NOT NULL,
    agent_name TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    target_cells TEXT,                     -- JSON array of cell IDs
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT CHECK(status IN ('running', 'completed', 'failed', 'cancelled')),
    result_summary TEXT,
    error_details TEXT,

    INDEX idx_operation_status (status),
    INDEX idx_operation_agent (agent_name),
    INDEX idx_operation_timestamp (started_at)
);

-- Audit & Compliance
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,           -- network_element, parameter, kpi, etc.
    resource_id TEXT,
    old_value TEXT,
    new_value TEXT,
    ip_address TEXT,
    user_agent TEXT,
    status TEXT CHECK(status IN ('success', 'failure')),
    error_message TEXT
);

-- System Metadata
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES ('2.0', 'Production schema with referential integrity');

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert standard KPI definitions
INSERT OR IGNORE INTO kpi_definitions (kpi_code, kpi_name, kpi_category, unit, threshold_critical, threshold_warning, threshold_target, description) VALUES
('RACH_SETUP_SUCCESS', 'Network Access Success Rate', 'accessibility', '%', 95.0, 97.0, 99.0, 'RACH Setup Success Rate'),
('DL_IBLER', 'Download Quality (DL IBLER)', 'quality', '%', 5.0, 2.0, 1.0, 'Downlink Initial Block Error Rate'),
('UL_IBLER', 'Upload Quality (UL IBLER)', 'quality', '%', 10.0, 5.0, 2.0, 'Uplink Initial Block Error Rate'),
('PDCCH_CCE_USAGE', 'Control Channel Load', 'capacity', '%', 80.0, 70.0, 50.0, 'PDCCH CCE Usage Rate'),
('PUCCH_USAGE', 'Feedback Channel Load', 'capacity', '%', 70.0, 60.0, 40.0, 'PUCCH Resource Usage'),
('DL_THROUGHPUT', 'Download Speed', 'performance', 'Mbps', 10.0, 15.0, 20.0, 'Average DL User Throughput'),
('UL_THROUGHPUT', 'Upload Speed', 'performance', 'Mbps', 3.0, 5.0, 8.0, 'Average UL User Throughput');

-- Insert standard parameter definitions
INSERT OR IGNORE INTO parameter_definitions (param_code, param_name, param_type, unit, min_value, max_value, mml_command_template, impact_level, requires_approval) VALUES
('REFERENCE_SIGNAL_POWER_RS', 'Reference Signal Power (RS)', 'integer', 'dBm', -600, 500, 'MOD CELLRS:LOCALCELLID={cell_id},REFERENCESIGNALPWR={value};', 'high', 1),
('REFERENCE_SIGNAL_POWER_PDSCH', 'Reference Signal Power (PDSCH)', 'integer', 'dBm', -600, 500, 'MOD CELLPDSCHCFG:LOCALCELLID={cell_id},REFERENCESIGNALPWR={value};', 'high', 1),
('A3_EVENT_OFFSET', 'A3 Event Offset', 'integer', 'dB', 0, 15, 'MOD EUTRANINFREQOFFSET:LOCALCELLID={cell_id},A3OFFSET={value};', 'medium', 1),
('T310_TIMER', 'T310 Timer', 'enum', 'ms', NULL, NULL, 'MOD CELLRESEL:LOCALCELLID={cell_id},T310={value};', 'medium', 1),
('P0_NOMINAL_PUSCH', 'P0 Nominal PUSCH', 'integer', 'dBm', -126, 24, 'MOD CELLPUSCHPWR:LOCALCELLID={cell_id},P0NOMINALPUSCH={value};', 'high', 1);
```

**Task List:**
- [ ] Create schema.sql with complete production schema
- [ ] Add foreign key constraints
- [ ] Add proper indexes
- [ ] Add data validation constraints
- [ ] Document all tables and relationships
- [ ] Create ERD diagram

### 3.3 Implement Database Migration

**Create: `/liquid-4g-core/database/migration.py`**
```python
"""
Database migration from multiple legacy databases to unified schema
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

class DatabaseMigration:
    """Migrate from legacy databases to unified production schema"""

    def __init__(self, source_dbs: List[str], target_db: str):
        self.source_dbs = source_dbs
        self.target_db = target_db
        self.migration_log = []

    def validate_source_data(self) -> Dict:
        """Validate source databases before migration"""
        validation_results = {}

        for source_db in self.source_dbs:
            results = {
                'exists': Path(source_db).exists(),
                'readable': False,
                'tables': [],
                'record_count': 0,
                'has_sample_data': False
            }

            if results['exists']:
                try:
                    with sqlite3.connect(source_db) as conn:
                        cursor = conn.cursor()
                        results['readable'] = True

                        # Get tables
                        cursor.execute(
                            "SELECT name FROM sqlite_master WHERE type='table'"
                        )
                        results['tables'] = [row[0] for row in cursor.fetchall()]

                        # Count records
                        for table in results['tables']:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cursor.fetchone()[0]
                            results['record_count'] += count

                        # Check for sample data
                        if 'kpi_data' in results['tables']:
                            cursor.execute("""
                                SELECT COUNT(*) FROM kpi_data
                                WHERE data_source IN ('sample', 'simulated', 'test')
                                OR collection_method = 'sample'
                            """)
                            sample_count = cursor.fetchone()[0]
                            results['has_sample_data'] = sample_count > 0

                except Exception as e:
                    logger.error(f"Error validating {source_db}: {e}")
                    results['error'] = str(e)

            validation_results[source_db] = results

        return validation_results

    def migrate_network_elements(self):
        """Migrate network elements from all sources"""
        logger.info("Migrating network elements...")

        # Implementation details...
        pass

    def migrate_kpi_data(self, exclude_sample_data=True):
        """Migrate KPI data, excluding sample/simulated data"""
        logger.info("Migrating KPI data...")

        if exclude_sample_data:
            logger.info("Excluding all sample/simulated data")

        # Implementation details...
        pass

    def migrate_parameter_data(self):
        """Migrate parameter data"""
        logger.info("Migrating parameter data...")

        # Implementation details...
        pass

    def run_migration(self, dry_run=True):
        """Execute full migration"""
        logger.info(f"Starting database migration (dry_run={dry_run})")

        # Validate sources
        validation = self.validate_source_data()
        for db, results in validation.items():
            if results.get('has_sample_data'):
                logger.warning(f"{db} contains sample data - will be excluded")

        if dry_run:
            logger.info("Dry run complete - no changes made")
            return validation

        # Create target database
        self.create_target_database()

        # Migrate data
        self.migrate_network_elements()
        self.migrate_kpi_data(exclude_sample_data=True)
        self.migrate_parameter_data()

        logger.info("Migration complete")
        return self.migration_log
```

**Task List:**
- [ ] Create migration.py script
- [ ] Implement data validation
- [ ] Implement dry-run mode
- [ ] Add rollback capability
- [ ] Test migration with sample data
- [ ] Document migration process
- [ ] Create migration runbook

### 3.4 Delete Legacy Databases

**After successful migration:**
```bash
# Create backup directory
mkdir -p /backup/databases/$(date +%Y%m%d)

# Backup old databases
mv data/*.db /backup/databases/$(date +%Y%m%d)/

# Remove duplicates
rm -f liquid-4g-core/data/*.db
rm -f archive/agentic_llm_workflow/data/*.db

# Keep only production database
mv /backup/databases/$(date +%Y%m%d)/lz_production.db data/
```

**Task List:**
- [ ] Backup all existing databases
- [ ] Verify migration success
- [ ] Remove legacy database files
- [ ] Update all database connections
- [ ] Update configuration files
- [ ] Test all database operations

---

## PHASE 4: API CLIENT CONSOLIDATION (Week 3 - Days 16-20)

### Priority: HIGH | Effort: 5 days | Blockers: Phase 1 complete

### 4.1 Choose Canonical API Client

**Decision: Use `/liquid-4g-core/network/huawei_api_client.py` as base**

**Rationale:**
- Better structured with separate methods for different operations
- More comprehensive error handling
- Clearer separation of concerns
- Better retry logic

**Task List:**
- [ ] Review both implementations thoroughly
- [ ] Document decision rationale
- [ ] Plan code merge strategy
- [ ] Identify unique features in each

### 4.2 Merge Duplicate Implementations

**Create: `/liquid-4g-core/api/huawei_mae_client.py` (NEW location)**
```python
"""
Huawei MAE-CN (iMaster NCE Campus Network) API Client
Production-ready client for network automation
"""
import requests
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from functools import wraps

from config.secrets_manager import SecretsManager

logger = logging.getLogger(__name__)

class HuaweiMAEError(Exception):
    """Base exception for Huawei MAE API errors"""
    pass

class AuthenticationError(HuaweiMAEError):
    """Authentication failed"""
    pass

class APIError(HuaweiMAEError):
    """API request failed"""
    pass

def retry_on_failure(max_retries=3, backoff_factor=2):
    """Decorator for API call retries"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.Timeout,
                        requests.exceptions.ConnectionError) as e:
                    retries += 1
                    if retries >= max_retries:
                        raise APIError(f"Max retries exceeded: {e}")

                    wait_time = backoff_factor ** retries
                    logger.warning(
                        f"API call failed, retrying in {wait_time}s "
                        f"(attempt {retries}/{max_retries})"
                    )
                    time.sleep(wait_time)

        return wrapper
    return decorator

class HuaweiMAEClient:
    """
    Production client for Huawei MAE-CN API

    Supports:
    - OAuth 2.0 authentication
    - MML command execution
    - KPI data retrieval
    - Parameter modification
    - Network element management
    """

    def __init__(self, secrets_manager: SecretsManager = None):
        """
        Initialize API client

        Args:
            secrets_manager: Secrets manager for credentials (uses env vars if None)
        """
        self.secrets_manager = secrets_manager or SecretsManager()

        # Get credentials from secrets manager
        creds = self.secrets_manager.get_api_credentials()
        self.base_url = creds['url'].rstrip('/')
        self.username = creds['username']
        self.password = creds['password']

        # Session management
        self.session = requests.Session()
        self.access_token = None
        self.token_expires_at = None

        # Configure SSL
        ca_cert = os.getenv('HUAWEI_CA_CERT_PATH')
        if ca_cert:
            self.session.verify = ca_cert
        else:
            self.session.verify = True  # Enforce SSL verification

        # Set timeouts
        self.timeout = int(os.getenv('HUAWEI_API_TIMEOUT', '30'))

        logger.info(f"Initialized Huawei MAE client for {self.base_url}")

    @retry_on_failure(max_retries=3)
    def authenticate(self) -> bool:
        """
        Authenticate with Huawei MAE API

        Returns:
            True if authentication successful

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/rest/securityManagement/v1/oauth/token",
                json={
                    "username": self.username,
                    "password": self.password,
                    "grant_type": "password"
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('accessSession')

                # Calculate token expiration
                expires_in = data.get('expires_in', 3600)
                self.token_expires_at = time.time() + expires_in

                logger.info("Authentication successful")
                return True
            else:
                raise AuthenticationError(
                    f"Authentication failed: {response.status_code} - {response.text}"
                )

        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"Authentication request failed: {e}")

    def is_authenticated(self) -> bool:
        """Check if client has valid authentication token"""
        if not self.access_token:
            return False

        # Check if token is expired (with 60s buffer)
        if self.token_expires_at and time.time() > (self.token_expires_at - 60):
            logger.info("Token expired, re-authenticating...")
            return False

        return True

    def ensure_authenticated(self):
        """Ensure client is authenticated, re-authenticate if needed"""
        if not self.is_authenticated():
            self.authenticate()

    @retry_on_failure(max_retries=3)
    def execute_mml_command(self, ne_name: str, command: str) -> Dict:
        """
        Execute MML command on network element

        Args:
            ne_name: Network element name
            command: MML command to execute

        Returns:
            API response with command result

        Raises:
            APIError: If command execution fails
        """
        self.ensure_authenticated()

        try:
            response = self.session.post(
                f"{self.base_url}/api/rest/mmlManagement/v1/command",
                headers={"accessSession": self.access_token},
                json={
                    "neName": ne_name,
                    "command": command
                },
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"MML command executed on {ne_name}: {command}")
            return result

        except requests.exceptions.RequestException as e:
            raise APIError(f"MML command execution failed: {e}")

    @retry_on_failure(max_retries=3)
    def get_kpi_data(self,
                     cell_ids: List[int],
                     kpi_codes: List[str],
                     start_time: datetime,
                     end_time: datetime) -> Dict:
        """
        Retrieve KPI data for cells

        Args:
            cell_ids: List of cell IDs
            kpi_codes: List of KPI codes to retrieve
            start_time: Start time for data range
            end_time: End time for data range

        Returns:
            KPI data

        Raises:
            APIError: If KPI retrieval fails
        """
        self.ensure_authenticated()

        try:
            response = self.session.post(
                f"{self.base_url}/api/rest/kpi/v1/query",
                headers={"accessSession": self.access_token},
                json={
                    "cellIds": cell_ids,
                    "kpiCodes": kpi_codes,
                    "startTime": start_time.isoformat(),
                    "endTime": end_time.isoformat(),
                    "granularity": "15MIN"  # 15-minute granularity
                },
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            logger.info(
                f"Retrieved KPI data for {len(cell_ids)} cells, "
                f"{len(kpi_codes)} KPIs"
            )
            return result

        except requests.exceptions.RequestException as e:
            raise APIError(f"KPI data retrieval failed: {e}")

    @retry_on_failure(max_retries=3)
    def get_cell_parameters(self, cell_id: int) -> Dict:
        """
        Get current parameter values for a cell

        Args:
            cell_id: Cell ID

        Returns:
            Dictionary of parameter values

        Raises:
            APIError: If parameter retrieval fails
        """
        self.ensure_authenticated()

        try:
            response = self.session.get(
                f"{self.base_url}/api/rest/configuration/v1/cells/{cell_id}/parameters",
                headers={"accessSession": self.access_token},
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Retrieved parameters for cell {cell_id}")
            return result

        except requests.exceptions.RequestException as e:
            raise APIError(f"Parameter retrieval failed: {e}")

    @retry_on_failure(max_retries=3)
    def get_network_elements(self) -> List[Dict]:
        """
        Get all network elements

        Returns:
            List of network elements

        Raises:
            APIError: If retrieval fails
        """
        self.ensure_authenticated()

        try:
            response = self.session.get(
                f"{self.base_url}/api/rest/networkManagement/v1/elements",
                headers={"accessSession": self.access_token},
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            elements = result.get('data', [])
            logger.info(f"Retrieved {len(elements)} network elements")
            return elements

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network element retrieval failed: {e}")
```

**Task List:**
- [ ] Create new consolidated API client
- [ ] Merge features from both implementations
- [ ] Add comprehensive error handling
- [ ] Add retry logic with exponential backoff
- [ ] Add authentication token management
- [ ] Add request/response logging
- [ ] Add timeout configuration
- [ ] Add rate limiting
- [ ] Create comprehensive unit tests
- [ ] Document all API methods

### 4.3 Delete Duplicate Implementation

**After consolidation complete:**
```bash
# Backup old implementations
mkdir -p archive/old_api_clients/
mv liquid-4g-core/agents/huawei_api_client.py archive/old_api_clients/
mv liquid-4g-core/network/huawei_api_client.py archive/old_api_clients/
```

**Task List:**
- [ ] Verify new client works correctly
- [ ] Update all imports to use new client
- [ ] Test all API operations
- [ ] Delete old implementations
- [ ] Remove unused imports

### 4.4 Update All Imports

**Files to update:**
- liquid-4g-core/agents/liquid_zimbabwe_kpi.py
- liquid-4g-core/agents/liquid_zimbabwe_parameters.py
- liquid-4g-core/agents/liquid_zimbabwe_monitoring.py
- liquid-4g-core/ui/ui.py

**Before:**
```python
from agents.huawei_api_client import HuaweiAPIClient
# OR
from network.huawei_api_client import HuaweiAPIClient
```

**After:**
```python
from api.huawei_mae_client import HuaweiMAEClient
```

**Task List:**
- [ ] Update all import statements
- [ ] Update client instantiation code
- [ ] Update method calls (if signatures changed)
- [ ] Test each module individually
- [ ] Run integration tests

---

## PHASE 5: FIX IMPORT SYSTEM (Week 4 - Days 21-25)

### Priority: MEDIUM | Effort: 5 days | Blockers: Phase 4 complete

### 5.1 Remove ALL sys.path Manipulations

**Files to modify:**
- ui/ui.py (7 instances)
- agents/huawei_api_client.py (2 instances)
- Multiple other files

**Before:**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

**After:** Delete all sys.path lines

**Task List:**
- [ ] Remove all sys.path.insert() calls
- [ ] Remove all sys.path.append() calls
- [ ] Document locations of removed code

### 5.2 Create Proper Package Structure

**Project structure:**
```
liquid-4g-core/
├── __init__.py                      # Main package init
├── setup.py                         # Package configuration
├── pyproject.toml                   # Modern Python project config
├── api/
│   ├── __init__.py
│   └── huawei_mae_client.py        # Consolidated API client
├── database/
│   ├── __init__.py
│   ├── models.py                    # Database models
│   ├── schema.sql                   # Schema definition
│   ├── migration.py                 # Migration tools
│   └── connection.py                # Connection management
├── agents/
│   ├── __init__.py
│   ├── kpi_manager.py               # Renamed from liquid_zimbabwe_kpi.py
│   ├── parameter_manager.py         # Renamed from liquid_zimbabwe_parameters.py
│   └── monitoring_agent.py          # Renamed
├── config/
│   ├── __init__.py
│   ├── secrets_manager.py
│   ├── settings.py
│   └── default_config.yaml
├── ui/
│   ├── __init__.py
│   └── app.py                       # Renamed from ui.py
├── utils/
│   ├── __init__.py
│   └── logging_config.py
└── tests/
    ├── __init__.py
    ├── test_api/
    ├── test_database/
    ├── test_agents/
    └── test_integration/
```

**Create: `/liquid-4g-core/setup.py`**
```python
"""
Liquid Zimbabwe 4G Network Optimizer
Production network optimization system for Huawei LTE infrastructure
"""
from setuptools import setup, find_packages

setup(
    name="liquid-zimbabwe-optimizer",
    version="2.0.0",
    description="Production network optimization system for Huawei LTE infrastructure",
    author="Cassava AI",
    packages=find_packages(exclude=["tests*", "archive*"]),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "streamlit>=1.25.0",
        "pandas>=1.5.0",
        "numpy>=1.23.0",
        "plotly>=5.14.0",
        "pyyaml>=6.0",
        "python-dotenv>=0.21.0",
        "azure-keyvault-secrets>=4.6.0",  # Optional
        "azure-identity>=1.12.0",          # Optional
    ],
    extras_require={
        "dev": [
            "pytest>=7.2.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "lz-optimizer=liquid_4g_core.main:main",
            "lz-migrate=liquid_4g_core.database.migration:main",
        ]
    }
)
```

**Create: `/liquid-4g-core/pyproject.toml`**
```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "liquid-zimbabwe-optimizer"
version = "2.0.0"
description = "Production network optimization system for Huawei LTE infrastructure"
requires-python = ">=3.8"

[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311']

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "--cov=liquid_4g_core --cov-report=html --cov-report=term"
```

**Task List:**
- [ ] Create setup.py
- [ ] Create pyproject.toml
- [ ] Ensure all __init__.py files exist
- [ ] Test package installation: `pip install -e .`
- [ ] Verify imports work without sys.path

### 5.3 Update All Import Statements

**Before:**
```python
# Brittle imports with sys.path manipulation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.liquid_zimbabwe_kpi import LiquidZimbabweKPIManager
```

**After:**
```python
# Clean package imports
from liquid_4g_core.agents.kpi_manager import KPIManager
from liquid_4g_core.api.huawei_mae_client import HuaweiMAEClient
from liquid_4g_core.database.connection import get_database_connection
```

**Task List:**
- [ ] Update all imports to use full package paths
- [ ] Use relative imports within packages
- [ ] Test each module can be imported
- [ ] Run full test suite

---

## PHASE 6: TESTING & QUALITY ASSURANCE (Week 5-6 - Days 26-30)

### Priority: HIGH | Effort: 5 days | Blockers: Phases 1-5 complete

### 6.1 Create Test Infrastructure

**Create: `/liquid-4g-core/tests/conftest.py`**
```python
"""
Pytest configuration and fixtures for Liquid Zimbabwe Optimizer
"""
import pytest
import os
import tempfile
from pathlib import Path

from liquid_4g_core.database.connection import DatabaseConnection
from liquid_4g_core.api.huawei_mae_client import HuaweiMAEClient
from liquid_4g_core.config.secrets_manager import SecretsManager

@pytest.fixture
def test_db():
    """Create temporary test database"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    # Initialize schema
    conn = DatabaseConnection(db_path)
    conn.initialize_schema()

    yield conn

    # Cleanup
    os.unlink(db_path)

@pytest.fixture
def mock_api_client(monkeypatch):
    """Mock Huawei MAE API client"""
    class MockHuaweiMAEClient:
        def __init__(self, *args, **kwargs):
            self.authenticated = False

        def authenticate(self):
            self.authenticated = True
            return True

        def is_authenticated(self):
            return self.authenticated

        def execute_mml_command(self, ne_name, command):
            return {
                "status": "success",
                "result": "Command executed successfully",
                "ne_name": ne_name,
                "command": command
            }

        def get_kpi_data(self, cell_ids, kpi_codes, start_time, end_time):
            return {
                "status": "success",
                "data": [
                    {
                        "cell_id": cell_id,
                        "kpi_code": kpi_code,
                        "value": 95.5,
                        "timestamp": "2025-10-08T00:00:00"
                    }
                    for cell_id in cell_ids
                    for kpi_code in kpi_codes
                ]
            }

    monkeypatch.setattr(
        "liquid_4g_core.api.huawei_mae_client.HuaweiMAEClient",
        MockHuaweiMAEClient
    )

    return MockHuaweiMAEClient()

@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        'api': {
            'url': 'https://test-api.example.com',
            'username': 'test_user',
            'password': 'test_password',
            'timeout': 10
        },
        'database': {
            'path': ':memory:'
        }
    }
```

**Task List:**
- [ ] Create test infrastructure
- [ ] Create pytest fixtures
- [ ] Create mock API client
- [ ] Create test database utilities

### 6.2 Unit Tests

**Create: `/liquid-4g-core/tests/test_api/test_huawei_mae_client.py`**
```python
"""
Unit tests for Huawei MAE API client
"""
import pytest
from liquid_4g_core.api.huawei_mae_client import (
    HuaweiMAEClient,
    HuaweiMAEError,
    AuthenticationError,
    APIError
)

class TestAuthentication:
    def test_authentication_success(self, mock_api_client):
        """Test successful authentication"""
        result = mock_api_client.authenticate()
        assert result is True
        assert mock_api_client.is_authenticated()

    def test_authentication_failure_invalid_credentials(self):
        """Test authentication failure with invalid credentials"""
        # Implementation
        pass

    def test_token_expiration_reauthentication(self):
        """Test automatic re-authentication on token expiration"""
        # Implementation
        pass

class TestMMLCommands:
    def test_execute_mml_command_success(self, mock_api_client):
        """Test successful MML command execution"""
        result = mock_api_client.execute_mml_command(
            "TEST_NE",
            "DSP CELL: LOCALCELLID=1;"
        )
        assert result['status'] == 'success'

    def test_execute_mml_command_without_authentication(self):
        """Test MML command fails without authentication"""
        # Implementation
        pass

class TestKPIRetrieval:
    def test_get_kpi_data_success(self, mock_api_client):
        """Test successful KPI data retrieval"""
        # Implementation
        pass

# More tests...
```

**Task List:**
- [ ] Write API client unit tests
- [ ] Write database unit tests
- [ ] Write KPI manager unit tests
- [ ] Write parameter manager unit tests
- [ ] Aim for >80% code coverage

### 6.3 Integration Tests

**Create: `/liquid-4g-core/tests/test_integration/test_end_to_end.py`**
```python
"""
Integration tests for end-to-end workflows
"""
import pytest
from datetime import datetime, timedelta

def test_kpi_collection_workflow(test_db, mock_api_client):
    """Test complete KPI collection workflow"""
    from liquid_4g_core.agents.kpi_manager import KPIManager

    kpi_manager = KPIManager(database=test_db, api_client=mock_api_client)

    # Collect KPI data
    result = kpi_manager.collect_kpi_data(
        cell_ids=[1, 2, 3],
        kpi_codes=['RACH_SETUP_SUCCESS', 'DL_IBLER'],
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now()
    )

    assert result['status'] == 'success'
    assert len(result['data']) > 0

    # Verify data stored in database
    stored_data = test_db.query_kpi_data(cell_id=1)
    assert len(stored_data) > 0

def test_parameter_optimization_workflow(test_db, mock_api_client):
    """Test complete parameter optimization workflow"""
    # Implementation
    pass

def test_alert_generation_workflow(test_db, mock_api_client):
    """Test alert generation on KPI threshold breach"""
    # Implementation
    pass
```

**Task List:**
- [ ] Write end-to-end workflow tests
- [ ] Write database integration tests
- [ ] Write API integration tests (with live API in staging)
- [ ] Create test data fixtures

### 6.4 Security Testing

**Task List:**
- [ ] Verify no hardcoded credentials
- [ ] Test SSL verification is enabled
- [ ] Test secrets manager integration
- [ ] Audit logging for sensitive operations
- [ ] Input validation testing
- [ ] SQL injection prevention tests

---

## PHASE 7: DOCUMENTATION & DEPLOYMENT (Week 7 - Days 31-35)

### Priority: MEDIUM | Effort: 5 days | Blockers: Phases 1-6 complete

### 7.1 API Documentation

**Create: `/documentation/API_INTEGRATION_GUIDE.md`**
```markdown
# Huawei MAE API Integration Guide

## API Endpoints

### Authentication
- **Endpoint:** `/api/rest/securityManagement/v1/oauth/token`
- **Method:** POST
- **Authentication:** Basic Auth
- **Request Body:**
  ```json
  {
    "username": "your_username",
    "password": "your_password",
    "grant_type": "password"
  }
  ```

### MML Commands
- **Endpoint:** `/api/rest/mmlManagement/v1/command`
- **Method:** POST
- **Authentication:** Bearer Token
- ...
```

**Task List:**
- [ ] Document all API endpoints
- [ ] Document authentication flow
- [ ] Document MML command syntax
- [ ] Provide request/response examples
- [ ] Document error codes
- [ ] Document rate limits

### 7.2 Database Documentation

**Create: `/documentation/DATABASE_SCHEMA.md`**
```markdown
# Database Schema Documentation

## Entity Relationship Diagram
[Include ERD]

## Tables

### network_elements
Stores network element (eNodeB) configuration

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| ne_id | TEXT | Huawei network element ID |
| ne_name | TEXT | Network element name |
...
```

**Task List:**
- [ ] Create ERD diagram
- [ ] Document all tables
- [ ] Document relationships
- [ ] Document indexes
- [ ] Provide query examples

### 7.3 Deployment Guide

**Create: `/documentation/DEPLOYMENT_GUIDE.md`**
```markdown
# Production Deployment Guide

## Prerequisites
- Python 3.8+
- PostgreSQL 13+ OR SQLite 3.35+
- Network access to Huawei MAE API
- SSL certificates configured

## Environment Setup

### 1. Install Dependencies
```bash
pip install -e .
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with production values
```

### 3. Initialize Database
```bash
lz-migrate --init --config production_config.yaml
```

### 4. Verify Configuration
```bash
lz-optimizer --check-config
```

### 5. Start Application
```bash
# Production mode
lz-optimizer --production

# Or with systemd
systemctl start lz-optimizer
```
```

**Task List:**
- [ ] Create deployment documentation
- [ ] Create systemd service file
- [ ] Create Docker deployment guide
- [ ] Document backup procedures
- [ ] Document rollback procedures
- [ ] Create runbook for common issues

---

## IMPLEMENTATION TIMELINE

### Week 1: Critical Security (Days 1-5)
- Remove hardcoded credentials
- Secure .env file
- Enable SSL verification
- Implement secrets management

### Week 1-2: Remove Simulations (Days 6-10)
- Delete simulated data functions
- Remove sample database initialization
- Remove hardcoded fallbacks
- Add proper error handling

### Week 2-3: Database Consolidation (Days 11-15)
- Design unified schema
- Implement migration tools
- Migrate data
- Delete legacy databases

### Week 3: API Consolidation (Days 16-20)
- Choose canonical implementation
- Merge features
- Delete duplicates
- Update all imports

### Week 4: Fix Imports (Days 21-25)
- Remove sys.path hacks
- Create proper package
- Update all imports
- Test installation

### Week 5-6: Testing (Days 26-30)
- Unit tests
- Integration tests
- Security tests
- Performance tests

### Week 7: Documentation (Days 31-35)
- API documentation
- Database documentation
- Deployment guide
- User documentation

---

## SUCCESS CRITERIA

### Must Have (Production Blockers)
- [ ] No hardcoded credentials anywhere
- [ ] .env file in .gitignore and removed from history
- [ ] SSL verification enabled
- [ ] All simulation/mock data removed
- [ ] Single unified database
- [ ] Single API client implementation
- [ ] No sys.path manipulations
- [ ] Unit test coverage >80%
- [ ] All integration tests passing
- [ ] API client works with live Huawei API
- [ ] Production deployment successful

### Should Have
- [ ] Secrets manager integration (Azure/AWS)
- [ ] Comprehensive error handling
- [ ] Audit logging
- [ ] Performance monitoring
- [ ] Automated backups
- [ ] Documentation complete

### Nice to Have
- [ ] CI/CD pipeline
- [ ] Automated deployment
- [ ] Monitoring dashboards
- [ ] Alerting system
- [ ] Load testing completed

---

## RISK MITIGATION

### Risk: Data Loss During Migration
**Mitigation:**
- Full backups before any changes
- Dry-run mode for migrations
- Rollback procedures documented
- Test migrations in non-production first

### Risk: API Integration Failures
**Mitigation:**
- Comprehensive error handling
- Retry logic with exponential backoff
- Graceful degradation where appropriate
- Detailed logging for troubleshooting

### Risk: Breaking Changes
**Mitigation:**
- Comprehensive test suite
- Staging environment testing
- Gradual rollout
- Quick rollback capability

---

## POST-REMEDIATION VALIDATION

### Checklist
- [ ] Run security scan (bandit, safety)
- [ ] Run code quality checks (flake8, mypy, black)
- [ ] Run full test suite
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Performance benchmark
- [ ] Security penetration testing
- [ ] Load testing
- [ ] Disaster recovery test
- [ ] Production deployment
- [ ] Post-deployment verification
- [ ] Documentation review

---

## CONCLUSION

This remediation plan addresses all critical issues identified in the production validation audit. Following this plan will transform the system from a prototype with 2.4/10 production readiness to a enterprise-grade solution ready for production deployment.

**Estimated Total Effort:** 25-36 working days
**Required Skills:** Python, SQL, API Integration, Security, DevOps
**Team Size:** 2-3 developers recommended

**Next Steps:**
1. Review and approve this plan
2. Allocate resources
3. Set up project tracking
4. Begin Phase 1 immediately
