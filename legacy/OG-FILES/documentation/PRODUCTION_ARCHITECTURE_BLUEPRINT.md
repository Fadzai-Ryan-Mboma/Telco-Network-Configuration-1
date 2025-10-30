# LIQUID ZIMBABWE 4G NETWORK OPTIMIZER - PRODUCTION ARCHITECTURE BLUEPRINT

**Version:** 2.0 (Production-Ready)
**Date:** October 8, 2025
**Status:** Design Specification
**Target Deployment:** Q4 2025

---

## EXECUTIVE SUMMARY

This document defines the production-ready architecture for the Liquid Zimbabwe 4G Network Optimizer, addressing all critical issues identified in the production validation audit and establishing enterprise-grade patterns for:

- **Security:** Zero hardcoded credentials, full SSL verification, secrets management
- **Data Integrity:** Single source of truth, no simulated data, full validation
- **Scalability:** Microservices-ready, horizontal scaling capable
- **Maintainability:** Clean code, proper testing, comprehensive documentation
- **Reliability:** Error handling, retry logic, graceful degradation

**Current State:** 2.4/10 Production Readiness
**Target State:** 9.5/10 Production Readiness

---

## ARCHITECTURE OVERVIEW

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LIQUID ZIMBABWE 4G NETWORK                       │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  eNodeB 1   │  │  eNodeB 2   │  │  eNodeB N   │              │
│  │  Harare     │  │  Bulawayo   │  │  Mutare     │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┴────────────────┘                      │
│                          │                                        │
│                   ┌──────▼──────┐                                │
│                   │   Huawei    │                                │
│                   │  iMaster    │                                │
│                   │  MAE-CN     │                                │
│                   │   (API)     │                                │
│                   └──────┬──────┘                                │
└────────────────────────┬───────────────────────────────────────┘
                         │ HTTPS/REST API
                         │ (Authenticated)
                         │
            ┌────────────▼────────────┐
            │                         │
            │   LZ 4G OPTIMIZER       │
            │   (This System)         │
            │                         │
            └────────────┬────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
    ┌─────▼─────┐  ┌────▼────┐  ┌─────▼─────┐
    │ Network   │  │ AI/ML   │  │   Web     │
    │ Engineers │  │ Agents  │  │   UI      │
    └───────────┘  └─────────┘  └───────────┘
```

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Streamlit Web Application                       │  │
│  │  - Dashboard  - Parameter Query  - Agentic Operator         │  │
│  │  - KPI Visualization  - Alert Management  - Reports         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                         APPLICATION LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ KPI Manager  │  │   Parameter  │  │  Monitoring  │            │
│  │              │  │   Manager    │  │   Agent      │            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
│         │                 │                 │                     │
│  ┌──────▼─────────────────▼─────────────────▼───────┐            │
│  │        Optimization Engine (AI/ML)                │            │
│  │  - Pattern Recognition  - Predictive Analysis     │            │
│  │  - Recommendation Engine  - Anomaly Detection     │            │
│  └───────────────────────────┬───────────────────────┘            │
└───────────────────────────────┼─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                         INTEGRATION LAYER                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Huawei MAE API Client                           │  │
│  │  - Authentication  - MML Commands  - KPI Retrieval           │  │
│  │  - Retry Logic  - Error Handling  - Rate Limiting            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                         DATA LAYER                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│  │  PostgreSQL   │  │  TimescaleDB  │  │     Redis     │          │
│  │  (Metadata)   │  │ (Time-Series) │  │    (Cache)    │          │
│  └───────────────┘  └───────────────┘  └───────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Azure Key    │  │   Docker/    │  │  Azure/AWS   │            │
│  │   Vault      │  │  Kubernetes  │  │  Monitoring  │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## DETAILED COMPONENT ARCHITECTURE

### 1. API INTEGRATION LAYER

#### 1.1 Huawei MAE API Client

**Location:** `/liquid-4g-core/api/huawei_mae_client.py`

**Responsibilities:**
- Authenticate with Huawei iMaster MAE-CN API
- Execute MML commands on network elements
- Retrieve KPI data from network
- Query/modify cell parameters
- Manage network elements

**Key Features:**
```python
class HuaweiMAEClient:
    """Production-ready API client for Huawei MAE-CN"""

    # Core Operations
    def authenticate() -> bool
    def execute_mml_command(ne_name: str, command: str) -> Dict
    def get_kpi_data(cell_ids: List[int], kpi_codes: List[str],
                     start_time: datetime, end_time: datetime) -> Dict
    def get_cell_parameters(cell_id: int) -> Dict
    def update_cell_parameter(cell_id: int, param_code: str,
                              value: float) -> Dict
    def get_network_elements() -> List[NetworkElement]

    # Health & Management
    def is_authenticated() -> bool
    def health_check() -> Dict
    def get_api_stats() -> Dict
```

**Error Handling:**
```python
# Retry Logic with Exponential Backoff
@retry_on_failure(max_retries=3, backoff_factor=2)
def execute_mml_command(self, ne_name, command):
    """Auto-retry on transient failures"""
    pass

# Circuit Breaker Pattern
class CircuitBreaker:
    """Prevent cascading failures"""
    states = ['CLOSED', 'OPEN', 'HALF_OPEN']

    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            raise CircuitOpenError("Too many failures")
        # Execute and track failures
```

**Security:**
- OAuth 2.0 token-based authentication
- Token refresh before expiration
- SSL/TLS verification enforced
- Credentials from secrets manager only
- Request/response sanitization
- Rate limiting compliance

**Monitoring:**
- Request/response logging
- Performance metrics (latency, throughput)
- Error rate tracking
- Circuit breaker status

#### 1.2 API Response Schema Validation

**Create:** `/liquid-4g-core/api/schemas.py`

```python
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime

class KPIDataPoint(BaseModel):
    """Validate KPI data from API"""
    cell_id: int
    kpi_code: str
    value: float
    timestamp: datetime
    quality: Optional[float] = 100.0

    @validator('value')
    def value_must_be_valid(cls, v):
        if v < 0:
            raise ValueError('KPI value cannot be negative')
        return v

class MMLCommandResponse(BaseModel):
    """Validate MML command responses"""
    status: str
    result: str
    ne_name: str
    command: str
    execution_time: Optional[float]

    @validator('status')
    def status_must_be_valid(cls, v):
        if v not in ['success', 'failed', 'partial']:
            raise ValueError(f'Invalid status: {v}')
        return v
```

---

### 2. DATA LAYER

#### 2.1 Database Architecture

**Primary Database:** PostgreSQL 13+ (or SQLite for development)
**Time-Series Extension:** TimescaleDB (for production)
**Cache:** Redis (optional, for high-performance queries)

**Why PostgreSQL?**
- ACID compliance
- Foreign key constraints
- JSON support for flexible data
- Excellent performance with TimescaleDB extension
- Wide ecosystem and tooling

**Database Schema:** See `/liquid-4g-core/database/schema.sql`

#### 2.2 Database Connection Management

**Create:** `/liquid-4g-core/database/connection.py`

```python
"""
Database connection management with pooling
"""
import logging
from contextlib import contextmanager
from typing import Optional
import psycopg2
from psycopg2 import pool

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Manage database connections with connection pooling"""

    def __init__(self, config: dict):
        """
        Initialize database connection pool

        Args:
            config: Database configuration dict
                {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'lz_optimizer',
                    'user': 'lz_user',
                    'password': '<from secrets manager>',
                    'min_connections': 2,
                    'max_connections': 10
                }
        """
        self.pool = psycopg2.pool.SimpleConnectionPool(
            minconn=config.get('min_connections', 2),
            maxconn=config.get('max_connections', 10),
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        logger.info(f"Database pool initialized for {config['database']}")

    @contextmanager
    def get_connection(self):
        """Get database connection from pool"""
        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    def execute_query(self, query: str, params: tuple = None) -> list:
        """Execute SELECT query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results

    def execute_command(self, command: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(command, params)
            affected = cursor.rowcount
            cursor.close()
            return affected

    def close(self):
        """Close all connections in pool"""
        self.pool.closeall()
        logger.info("Database pool closed")
```

#### 2.3 Data Models (ORM)

**Create:** `/liquid-4g-core/database/models.py`

```python
"""
Database models using SQLAlchemy ORM
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class NetworkElement(Base):
    """Network element (eNodeB) model"""
    __tablename__ = 'network_elements'

    id = Column(Integer, primary_key=True)
    ne_id = Column(String, unique=True, nullable=False)
    ne_name = Column(String, unique=True, nullable=False)
    site_id = Column(String, nullable=False)
    location = Column(String)
    ne_type = Column(String, nullable=False)
    status = Column(String, default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cells = relationship("Cell", back_populates="network_element")

class Cell(Base):
    """Cell model"""
    __tablename__ = 'cells'

    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, nullable=False)
    cell_name = Column(String, nullable=False)
    ne_id = Column(String, ForeignKey('network_elements.ne_id'), nullable=False)
    local_cell_id = Column(Integer)
    pci = Column(Integer)
    status = Column(String, default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    network_element = relationship("NetworkElement", back_populates="cells")
    kpi_data = relationship("KPIData", back_populates="cell")
    parameter_values = relationship("ParameterValue", back_populates="cell")

class KPIDefinition(Base):
    """KPI definition model"""
    __tablename__ = 'kpi_definitions'

    id = Column(Integer, primary_key=True)
    kpi_code = Column(String, unique=True, nullable=False)
    kpi_name = Column(String, nullable=False)
    kpi_category = Column(String, nullable=False)
    unit = Column(String)
    threshold_critical = Column(Float)
    threshold_warning = Column(Float)
    threshold_target = Column(Float)
    description = Column(String)
    is_active = Column(Boolean, default=True)

class KPIData(Base):
    """KPI data model (time-series)"""
    __tablename__ = 'kpi_data'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    cell_id = Column(Integer, ForeignKey('cells.id'), nullable=False)
    kpi_code = Column(String, ForeignKey('kpi_definitions.kpi_code'), nullable=False)
    value = Column(Float, nullable=False)
    data_quality = Column(Float, default=100.0)
    collection_method = Column(String, default='api')
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cell = relationship("Cell", back_populates="kpi_data")

class ParameterDefinition(Base):
    """Parameter definition model"""
    __tablename__ = 'parameter_definitions'

    id = Column(Integer, primary_key=True)
    param_code = Column(String, unique=True, nullable=False)
    param_name = Column(String, nullable=False)
    param_type = Column(String, nullable=False)
    unit = Column(String)
    min_value = Column(Float)
    max_value = Column(Float)
    mml_command_template = Column(String, nullable=False)
    impact_level = Column(String)
    requires_approval = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

class ParameterValue(Base):
    """Current parameter values (time-series)"""
    __tablename__ = 'parameter_values'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    cell_id = Column(Integer, ForeignKey('cells.id'), nullable=False)
    param_code = Column(String, ForeignKey('parameter_definitions.param_code'), nullable=False)
    current_value = Column(Float, nullable=False)
    data_quality = Column(Float, default=100.0)
    collection_method = Column(String, default='api')
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cell = relationship("Cell", back_populates="parameter_values")

class ParameterChange(Base):
    """Parameter change history and approval workflow"""
    __tablename__ = 'parameter_changes'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    cell_id = Column(Integer, ForeignKey('cells.id'), nullable=False)
    param_code = Column(String, ForeignKey('parameter_definitions.param_code'), nullable=False)
    old_value = Column(Float)
    new_value = Column(Float, nullable=False)
    change_reason = Column(String, nullable=False)
    change_type = Column(String)
    requested_by = Column(String, nullable=False)
    approved_by = Column(String)
    approved_at = Column(DateTime)
    executed_at = Column(DateTime)
    execution_status = Column(String, default='pending')
    mml_command = Column(String)
    api_response = Column(String)
    error_message = Column(String)
```

---

### 3. APPLICATION LAYER

#### 3.1 KPI Manager

**Location:** `/liquid-4g-core/agents/kpi_manager.py`

**Responsibilities:**
- Collect KPI data from network via API
- Store KPI data in database
- Analyze KPI trends
- Generate KPI alerts
- Provide KPI summaries for UI

**Architecture:**
```python
class KPIManager:
    """Manage KPI collection, storage, and analysis"""

    def __init__(self, api_client: HuaweiMAEClient, database: DatabaseConnection):
        self.api_client = api_client
        self.database = database
        self.kpi_definitions = self._load_kpi_definitions()

    # Data Collection
    def collect_kpi_data(self, cell_ids: List[int],
                        kpi_codes: List[str],
                        start_time: datetime,
                        end_time: datetime) -> Dict:
        """
        Collect KPI data from network

        Returns:
            {
                'status': 'success',
                'records_collected': 150,
                'records_stored': 150,
                'errors': []
            }

        Raises:
            APIError: If API collection fails
            DatabaseError: If storage fails
        """
        # Validate inputs
        self._validate_cell_ids(cell_ids)
        self._validate_kpi_codes(kpi_codes)

        # Collect from API
        api_data = self.api_client.get_kpi_data(
            cell_ids, kpi_codes, start_time, end_time
        )

        # Validate response
        validated_data = self._validate_kpi_data(api_data)

        # Store in database
        stored_count = self._store_kpi_data(validated_data)

        # Check for alerts
        self._check_kpi_alerts(validated_data)

        return {
            'status': 'success',
            'records_collected': len(validated_data),
            'records_stored': stored_count
        }

    # Data Analysis
    def get_kpi_summary(self, site_id: Optional[str] = None) -> Dict:
        """Get aggregated KPI summary"""
        pass

    def analyze_kpi_trends(self, cell_id: int, kpi_code: str,
                          days: int = 7) -> Dict:
        """Analyze KPI trends over time"""
        pass

    def get_kpi_alerts(self, status: str = 'active') -> List[Dict]:
        """Get active KPI alerts"""
        pass

    # Internal Methods
    def _validate_kpi_data(self, data: Dict) -> List[KPIDataPoint]:
        """Validate KPI data from API"""
        validated = []
        for record in data.get('data', []):
            try:
                validated.append(KPIDataPoint(**record))
            except ValidationError as e:
                logger.error(f"Invalid KPI data: {e}")
        return validated

    def _store_kpi_data(self, data: List[KPIDataPoint]) -> int:
        """Store validated KPI data in database"""
        query = """
            INSERT INTO kpi_data
            (timestamp, cell_id, kpi_code, value, data_quality, collection_method)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (timestamp, cell_id, kpi_code) DO UPDATE
            SET value = EXCLUDED.value
        """

        count = 0
        for record in data:
            self.database.execute_command(query, (
                record.timestamp,
                record.cell_id,
                record.kpi_code,
                record.value,
                record.quality,
                'api'
            ))
            count += 1

        return count

    def _check_kpi_alerts(self, data: List[KPIDataPoint]):
        """Check if any KPI values breach thresholds"""
        for record in data:
            definition = self.kpi_definitions.get(record.kpi_code)
            if not definition:
                continue

            # Check critical threshold
            if definition.threshold_critical and record.value < definition.threshold_critical:
                self._create_alert(record, 'critical', definition.threshold_critical)

            # Check warning threshold
            elif definition.threshold_warning and record.value < definition.threshold_warning:
                self._create_alert(record, 'warning', definition.threshold_warning)
```

**Key Features:**
- NO simulated data - all data from API or explicit error
- Comprehensive validation using Pydantic schemas
- Database transactions for data integrity
- Automatic alert generation
- Detailed error logging

#### 3.2 Parameter Manager

**Location:** `/liquid-4g-core/agents/parameter_manager.py`

**Responsibilities:**
- Query current parameter values from network
- Validate parameter change requests
- Execute parameter changes via MML commands
- Track parameter change history
- Generate optimization recommendations

**Architecture:**
```python
class ParameterManager:
    """Manage network parameter queries and modifications"""

    def __init__(self, api_client: HuaweiMAEClient, database: DatabaseConnection):
        self.api_client = api_client
        self.database = database
        self.parameter_definitions = self._load_parameter_definitions()

    # Parameter Queries
    def get_current_parameter_value(self, cell_id: int, param_code: str) -> float:
        """
        Get current parameter value from network

        Returns:
            Current parameter value

        Raises:
            APIError: If API query fails
            ValueError: If parameter not found
        """
        # Query from API (NOT from defaults or simulation)
        params = self.api_client.get_cell_parameters(cell_id)

        if param_code not in params:
            raise ValueError(
                f"Parameter {param_code} not found for cell {cell_id}"
            )

        value = params[param_code]

        # Store in database for history
        self._store_parameter_value(cell_id, param_code, value)

        return value

    # Parameter Modifications
    def modify_parameter(self, cell_id: int, param_code: str,
                        new_value: float, reason: str,
                        requested_by: str) -> Dict:
        """
        Request parameter modification (approval workflow)

        Args:
            cell_id: Cell ID to modify
            param_code: Parameter code
            new_value: New parameter value
            reason: Reason for change
            requested_by: User requesting change

        Returns:
            {
                'change_id': 123,
                'status': 'pending_approval',
                'requires_approval': True
            }
        """
        # Validate parameter
        definition = self.parameter_definitions.get(param_code)
        if not definition:
            raise ValueError(f"Unknown parameter: {param_code}")

        # Validate value range
        if not self._validate_parameter_value(param_code, new_value):
            raise ValueError(
                f"Value {new_value} outside allowed range "
                f"[{definition.min_value}, {definition.max_value}]"
            )

        # Get current value
        current_value = self.get_current_parameter_value(cell_id, param_code)

        # Create change request
        change_id = self._create_parameter_change_request(
            cell_id=cell_id,
            param_code=param_code,
            old_value=current_value,
            new_value=new_value,
            reason=reason,
            requested_by=requested_by
        )

        # If high/critical impact, require approval
        if definition.impact_level in ['high', 'critical']:
            return {
                'change_id': change_id,
                'status': 'pending_approval',
                'requires_approval': True,
                'impact_level': definition.impact_level
            }
        else:
            # Auto-approve low impact changes
            return self.execute_parameter_change(change_id, approved_by='auto')

    def execute_parameter_change(self, change_id: int,
                                 approved_by: str) -> Dict:
        """
        Execute approved parameter change

        Args:
            change_id: Change request ID
            approved_by: User approving the change

        Returns:
            Execution result
        """
        # Get change request
        change = self._get_parameter_change(change_id)

        if change['execution_status'] == 'success':
            raise ValueError("Change already executed")

        # Get parameter definition
        definition = self.parameter_definitions[change['param_code']]

        # Format MML command
        mml_command = definition.mml_command_template.format(
            cell_id=change['cell_id'],
            value=change['new_value']
        )

        # Get network element name
        ne_name = self._get_ne_name_for_cell(change['cell_id'])

        try:
            # Execute MML command
            result = self.api_client.execute_mml_command(ne_name, mml_command)

            # Update change record
            self._update_parameter_change(
                change_id=change_id,
                approved_by=approved_by,
                execution_status='success',
                mml_command=mml_command,
                api_response=result
            )

            return {
                'status': 'success',
                'change_id': change_id,
                'mml_command': mml_command,
                'result': result
            }

        except APIError as e:
            # Update change record with error
            self._update_parameter_change(
                change_id=change_id,
                execution_status='failed',
                error_message=str(e)
            )

            raise

    # Optimization
    def get_optimization_recommendations(self, cell_id: int) -> List[Dict]:
        """
        Generate parameter optimization recommendations based on KPI analysis

        Returns:
            List of recommendations
        """
        # Get recent KPI performance
        kpi_issues = self._identify_kpi_issues(cell_id)

        recommendations = []

        for issue in kpi_issues:
            # Apply optimization rules
            param_recommendations = self._apply_optimization_rules(
                cell_id=cell_id,
                kpi_code=issue['kpi_code'],
                current_value=issue['current_value'],
                threshold=issue['threshold']
            )

            recommendations.extend(param_recommendations)

        # Prioritize recommendations
        recommendations = self._prioritize_recommendations(recommendations)

        return recommendations

    def _apply_optimization_rules(self, cell_id, kpi_code,
                                  current_value, threshold) -> List[Dict]:
        """
        Apply rule-based optimization logic

        Example Rules:
        - If DL_IBLER > 2%, increase REFERENCE_SIGNAL_POWER
        - If RACH_SETUP_SUCCESS < 98%, reduce A3_EVENT_OFFSET
        """
        rules = {
            'DL_IBLER': [
                {
                    'condition': lambda v: v > 2.0,
                    'param': 'REFERENCE_SIGNAL_POWER_RS',
                    'adjustment': +10,
                    'expected_improvement': '15-25% reduction in DL IBLER'
                }
            ],
            'RACH_SETUP_SUCCESS': [
                {
                    'condition': lambda v: v < 98.0,
                    'param': 'A3_EVENT_OFFSET',
                    'adjustment': -1,
                    'expected_improvement': '5-10% improvement in access success'
                }
            ]
            # ... more rules
        }

        recommendations = []

        for rule in rules.get(kpi_code, []):
            if rule['condition'](current_value):
                current_param_value = self.get_current_parameter_value(
                    cell_id, rule['param']
                )

                recommendations.append({
                    'cell_id': cell_id,
                    'kpi_issue': kpi_code,
                    'param_code': rule['param'],
                    'current_value': current_param_value,
                    'recommended_value': current_param_value + rule['adjustment'],
                    'expected_improvement': rule['expected_improvement'],
                    'confidence_score': 0.75
                })

        return recommendations
```

**Key Features:**
- NO random defaults - all values from API
- Comprehensive validation
- Approval workflow for high-impact changes
- MML command generation and execution
- Change history tracking
- Rule-based optimization engine

#### 3.3 Monitoring Agent

**Location:** `/liquid-4g-core/agents/monitoring_agent.py`

**Responsibilities:**
- Continuous KPI monitoring
- Threshold breach detection
- Alert generation and management
- Performance reporting

**Architecture:**
```python
class MonitoringAgent:
    """Continuous monitoring and alerting agent"""

    def __init__(self, kpi_manager: KPIManager,
                 alert_channels: List[AlertChannel]):
        self.kpi_manager = kpi_manager
        self.alert_channels = alert_channels
        self.monitoring_active = False

    def start_monitoring(self, interval_minutes: int = 15):
        """
        Start continuous monitoring

        Args:
            interval_minutes: Monitoring interval (default 15 min)
        """
        self.monitoring_active = True

        while self.monitoring_active:
            try:
                # Collect latest KPIs
                self._collect_latest_kpis()

                # Check for threshold breaches
                alerts = self.kpi_manager.get_kpi_alerts(status='active')

                # Send notifications
                for alert in alerts:
                    self._send_alert_notification(alert)

                # Wait for next interval
                time.sleep(interval_minutes * 60)

            except Exception as e:
                logger.error(f"Monitoring cycle error: {e}")
                time.sleep(60)  # Wait 1 minute before retry

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False

    def _send_alert_notification(self, alert: Dict):
        """Send alert via configured channels"""
        for channel in self.alert_channels:
            try:
                channel.send_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")
```

---

### 4. CONFIGURATION MANAGEMENT

#### 4.1 Centralized Configuration

**Create:** `/liquid-4g-core/config/settings.py`

```python
"""
Centralized configuration management
"""
import os
from typing import Dict, Any
from pathlib import Path
import yaml

class Settings:
    """Application settings"""

    def __init__(self, config_path: str = None, env: str = None):
        """
        Load configuration from file and environment

        Args:
            config_path: Path to YAML config file
            env: Environment (development, staging, production)
        """
        self.env = env or os.getenv('LZ_ENV', 'development')

        # Load base configuration
        if config_path:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = self._get_default_config()

        # Override with environment-specific settings
        self._load_environment_overrides()

    def _get_default_config(self) -> Dict:
        """Default configuration"""
        return {
            'api': {
                'timeout': 30,
                'max_retries': 3,
                'backoff_factor': 2
            },
            'database': {
                'pool_size': 10,
                'pool_timeout': 30
            },
            'monitoring': {
                'interval_minutes': 15,
                'alert_cooldown_minutes': 60
            },
            'kpi': {
                'collection_interval_minutes': 15,
                'retention_days': 90
            }
        }

    def _load_environment_overrides(self):
        """Load settings from environment variables"""
        # API settings
        if os.getenv('LZ_API_TIMEOUT'):
            self.config['api']['timeout'] = int(os.getenv('LZ_API_TIMEOUT'))

        # Database settings
        if os.getenv('LZ_DB_POOL_SIZE'):
            self.config['database']['pool_size'] = int(os.getenv('LZ_DB_POOL_SIZE'))

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.env == 'production'

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.env == 'development'
```

**Create:** `/config-production.yaml`

```yaml
# Production Configuration
environment: production

api:
  timeout: 30
  max_retries: 3
  backoff_factor: 2
  circuit_breaker:
    failure_threshold: 5
    timeout_seconds: 60

database:
  type: postgresql
  host: ${DB_HOST}
  port: 5432
  database: lz_optimizer_prod
  pool_size: 20
  pool_timeout: 30
  ssl_required: true

monitoring:
  interval_minutes: 15
  alert_cooldown_minutes: 60
  health_check_interval_minutes: 5

kpi:
  collection_interval_minutes: 15
  retention_days: 365
  aggregation_levels:
    - 15min
    - 1hour
    - 1day

security:
  ssl_verify: true
  token_refresh_margin_seconds: 300
  audit_logging: true

logging:
  level: INFO
  format: json
  output: file
  file_path: /var/log/lz-optimizer/app.log
  rotation: daily
  retention_days: 30
```

---

### 5. DEPLOYMENT ARCHITECTURE

#### 5.1 Container Architecture

**Create:** `/Dockerfile`

```dockerfile
# Production Dockerfile
FROM python:3.10-slim

# Set environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Create app user
RUN useradd -m -u 1000 lzuser && \
    mkdir -p /app /data /logs && \
    chown -R lzuser:lzuser /app /data /logs

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements-production.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-production.txt

# Copy application
COPY --chown=lzuser:lzuser . .

# Install application
RUN pip install -e .

# Switch to app user
USER lzuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "from liquid_4g_core.health import health_check; health_check()"

# Expose port
EXPOSE 8501

# Run application
CMD ["python", "-m", "liquid_4g_core.main", "--production"]
```

**Create:** `/docker-compose.production.yml`

```yaml
version: '3.8'

services:
  optimizer:
    build:
      context: .
      dockerfile: Dockerfile
    image: lz-optimizer:${VERSION:-latest}
    container_name: lz-optimizer-app
    restart: unless-stopped
    environment:
      - LZ_ENV=production
      - LZ_CONFIG_PATH=/app/config-production.yaml
    env_file:
      - .env.production  # Not committed to git
    volumes:
      - ./data:/data:rw
      - ./logs:/logs:rw
      - ./config-production.yaml:/app/config-production.yaml:ro
    ports:
      - "8501:8501"
    depends_on:
      - db
      - redis
    networks:
      - lz-network
    healthcheck:
      test: ["CMD", "python", "-c", "from liquid_4g_core.health import health_check; health_check()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: timescale/timescaledb:latest-pg13
    container_name: lz-optimizer-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=lz_optimizer_prod
      - POSTGRES_USER=lz_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
    ports:
      - "5432:5432"
    networks:
      - lz-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lz_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: lz-optimizer-cache
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    networks:
      - lz-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  db-data:
  redis-data:

networks:
  lz-network:
    driver: bridge
```

#### 5.2 Kubernetes Deployment (Optional)

**Create:** `/k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lz-optimizer
  namespace: production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: lz-optimizer
  template:
    metadata:
      labels:
        app: lz-optimizer
    spec:
      containers:
      - name: optimizer
        image: lz-optimizer:2.0.0
        ports:
        - containerPort: 8501
        env:
        - name: LZ_ENV
          value: "production"
        - name: LZ_API_URL
          valueFrom:
            secretKeyRef:
              name: lz-secrets
              key: api-url
        - name: LZ_API_USERNAME
          valueFrom:
            secretKeyRef:
              name: lz-secrets
              key: api-username
        - name: LZ_API_PASSWORD
          valueFrom:
            secretKeyRef:
              name: lz-secrets
              key: api-password
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8501
          initialDelaySeconds: 10
          periodSeconds: 5
```

---

## SECURITY ARCHITECTURE

### 1. Secrets Management

**Options:**

**Option A: Azure Key Vault**
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

vault_url = "https://lz-optimizer-vault.vault.azure.net"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=vault_url, credential=credential)

api_password = client.get_secret("huawei-api-password").value
```

**Option B: AWS Secrets Manager**
```python
import boto3

client = boto3.client('secretsmanager', region_name='us-east-1')
response = client.get_secret_value(SecretId='lz/huawei-api-password')
api_password = response['SecretString']
```

**Option C: HashiCorp Vault**
```python
import hvac

client = hvac.Client(url='https://vault.example.com')
client.auth.approle.login(
    role_id=os.getenv('VAULT_ROLE_ID'),
    secret_id=os.getenv('VAULT_SECRET_ID')
)

secret = client.secrets.kv.v2.read_secret_version(path='lz/huawei-api')
api_password = secret['data']['data']['password']
```

### 2. Authentication & Authorization

**Create:** `/liquid-4g-core/auth/authentication.py`

```python
"""
User authentication and authorization
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional

class AuthenticationManager:
    """Manage user authentication"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def create_token(self, user_id: str, role: str) -> str:
        """Create JWT token for user"""
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=8),
            'iat': datetime.utcnow()
        }

        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

class AuthorizationManager:
    """Manage user permissions"""

    ROLES = {
        'admin': {
            'permissions': ['*']  # All permissions
        },
        'engineer': {
            'permissions': [
                'view_kpis',
                'view_parameters',
                'request_parameter_changes',
                'view_alerts'
            ]
        },
        'viewer': {
            'permissions': [
                'view_kpis',
                'view_parameters',
                'view_alerts'
            ]
        }
    }

    def has_permission(self, role: str, permission: str) -> bool:
        """Check if role has permission"""
        role_perms = self.ROLES.get(role, {}).get('permissions', [])

        if '*' in role_perms:
            return True

        return permission in role_perms
```

### 3. Audit Logging

**Create:** `/liquid-4g-core/audit/audit_logger.py`

```python
"""
Audit logging for compliance and security
"""
import logging
from datetime import datetime
from typing import Dict, Any

class AuditLogger:
    """Log all user actions and system events"""

    def __init__(self, database: DatabaseConnection):
        self.database = database
        self.logger = logging.getLogger('audit')

    def log_action(self, user_id: str, action: str,
                   resource_type: str, resource_id: str,
                   old_value: Any = None, new_value: Any = None,
                   ip_address: str = None, user_agent: str = None,
                   status: str = 'success', error_message: str = None):
        """
        Log user action

        Args:
            user_id: User performing action
            action: Action performed (view, create, update, delete, execute)
            resource_type: Type of resource (kpi, parameter, alert)
            resource_id: ID of resource
            old_value: Previous value (for updates)
            new_value: New value (for updates)
            ip_address: User IP address
            user_agent: User agent string
            status: success or failure
            error_message: Error message if failed
        """
        query = """
            INSERT INTO audit_log
            (timestamp, user_id, action, resource_type, resource_id,
             old_value, new_value, ip_address, user_agent, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        self.database.execute_command(query, (
            datetime.utcnow(),
            user_id,
            action,
            resource_type,
            resource_id,
            str(old_value) if old_value else None,
            str(new_value) if new_value else None,
            ip_address,
            user_agent,
            status,
            error_message
        ))

        # Also log to file
        self.logger.info(
            f"AUDIT: user={user_id} action={action} "
            f"resource={resource_type}:{resource_id} status={status}"
        )
```

---

## MONITORING & OBSERVABILITY

### 1. Health Checks

**Create:** `/liquid-4g-core/health.py`

```python
"""
Health check endpoints
"""
from typing import Dict

def health_check() -> Dict:
    """Check system health"""
    checks = {
        'api_client': _check_api_connection(),
        'database': _check_database_connection(),
        'disk_space': _check_disk_space(),
        'memory': _check_memory_usage()
    }

    overall_status = 'healthy' if all(
        check['status'] == 'ok' for check in checks.values()
    ) else 'unhealthy'

    return {
        'status': overall_status,
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat()
    }

def _check_api_connection() -> Dict:
    """Check Huawei API connectivity"""
    try:
        client = HuaweiMAEClient()
        client.authenticate()
        return {'status': 'ok', 'latency_ms': 50}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def _check_database_connection() -> Dict:
    """Check database connectivity"""
    try:
        db = DatabaseConnection()
        db.execute_query("SELECT 1")
        return {'status': 'ok'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
```

### 2. Metrics Collection

**Create:** `/liquid-4g-core/metrics.py`

```python
"""
Application metrics for monitoring
"""
from prometheus_client import Counter, Histogram, Gauge

# API Metrics
api_requests_total = Counter(
    'lz_api_requests_total',
    'Total API requests',
    ['endpoint', 'status']
)

api_request_duration = Histogram(
    'lz_api_request_duration_seconds',
    'API request duration',
    ['endpoint']
)

# Database Metrics
db_queries_total = Counter(
    'lz_db_queries_total',
    'Total database queries',
    ['query_type']
)

db_query_duration = Histogram(
    'lz_db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

# KPI Metrics
kpi_collection_total = Counter(
    'lz_kpi_collection_total',
    'Total KPI collections',
    ['status']
)

active_alerts = Gauge(
    'lz_active_alerts',
    'Number of active alerts',
    ['severity']
)

# Parameter Change Metrics
parameter_changes_total = Counter(
    'lz_parameter_changes_total',
    'Total parameter changes',
    ['status']
)
```

---

## TESTING STRATEGY

### 1. Unit Tests (>80% Coverage)

**Files:**
- `/tests/test_api/test_huawei_mae_client.py`
- `/tests/test_database/test_connection.py`
- `/tests/test_agents/test_kpi_manager.py`
- `/tests/test_agents/test_parameter_manager.py`

### 2. Integration Tests

**Files:**
- `/tests/test_integration/test_end_to_end_workflows.py`
- `/tests/test_integration/test_database_integration.py`
- `/tests/test_integration/test_api_integration.py`

### 3. Performance Tests

**Create:** `/tests/performance/test_load.py`

```python
"""
Load testing for production readiness
"""
import pytest
from locust import HttpUser, task, between

class OptimizerUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_dashboard(self):
        self.client.get("/")

    @task(2)
    def query_kpis(self):
        self.client.post("/api/kpi/query", json={
            'cell_ids': [1, 2, 3],
            'kpi_codes': ['RACH_SETUP_SUCCESS'],
            'hours': 24
        })

    @task(1)
    def query_parameters(self):
        self.client.post("/api/parameters/query", json={
            'cell_id': 1,
            'param_code': 'REFERENCE_SIGNAL_POWER_RS'
        })
```

---

## MIGRATION PATH

### Phase 1: Security Hardening (Week 1)
1. Remove all hardcoded credentials
2. Implement secrets manager
3. Enable SSL verification
4. Secure .env file

### Phase 2: Code Cleanup (Week 2-3)
1. Remove simulation/mock data
2. Consolidate databases
3. Merge duplicate API clients
4. Fix import system

### Phase 3: Testing (Week 4-5)
1. Unit tests
2. Integration tests
3. Security tests
4. Performance tests

### Phase 4: Documentation (Week 6)
1. API documentation
2. Deployment guide
3. Runbooks

### Phase 5: Deployment (Week 7)
1. Staging deployment
2. Production deployment
3. Post-deployment validation

---

## SUCCESS METRICS

### Technical Metrics
- [ ] 0 hardcoded credentials
- [ ] 0 simulation/mock data in production code
- [ ] 1 unified database
- [ ] 1 API client implementation
- [ ] >80% test coverage
- [ ] <100ms average API response time
- [ ] >99.9% uptime

### Business Metrics
- [ ] Network parameter optimization success rate >90%
- [ ] KPI improvement after optimization >15%
- [ ] Alert response time <5 minutes
- [ ] User satisfaction score >4.5/5

---

## CONCLUSION

This production architecture blueprint provides a complete roadmap for transforming the Liquid Zimbabwe 4G Network Optimizer from a prototype (2.4/10 production readiness) to an enterprise-grade system (9.5/10).

**Key Improvements:**
1. **Security**: Zero hardcoded credentials, secrets management, SSL verification
2. **Data Integrity**: Single source of truth, no simulated data, full validation
3. **Code Quality**: Clean architecture, proper testing, comprehensive documentation
4. **Reliability**: Error handling, retry logic, monitoring, alerting
5. **Scalability**: Microservices-ready, containerized, cloud-native

**Next Steps:**
1. Review and approve architecture
2. Begin Phase 1 (Security Hardening)
3. Follow remediation plan timeline
4. Deploy to production in 7 weeks

