#!/usr/bin/env python3
"""
Agentic Operator Database Integration
Provides persistent storage for agentic operations, agent status, and history tracking
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger('LZ-Agentic-DB')

class AgenticDatabase:
    """Database interface for agentic operator persistence"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Use existing database structure
            db_path = str(Path(__file__).parent.parent / "data" / "lz_platform.db")
        
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize agentic operator database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create agent_status table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    active_tasks INTEGER DEFAULT 0,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Create operations table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS agentic_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT UNIQUE NOT NULL,
                    operation_type TEXT NOT NULL,
                    target_site TEXT,
                    status TEXT NOT NULL,
                    parameters TEXT,
                    results TEXT,
                    agent_name TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    metadata TEXT
                )
                """)
                
                # Create operation_history table for detailed logs
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS operation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    log_level TEXT DEFAULT 'INFO',
                    message TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY (operation_id) REFERENCES agentic_operations (operation_id)
                )
                """)
                
                # Create agent_metrics table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active_agents INTEGER DEFAULT 0,
                    operations_today INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    auto_optimizations INTEGER DEFAULT 0,
                    metadata TEXT
                )
                """)
                
                conn.commit()
                logger.info("Agentic database tables initialized successfully")
                
                # Initialize default data if tables are empty
                self._init_default_data(cursor)
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to initialize agentic database: {e}")
            raise
    
    def _init_default_data(self, cursor):
        """Initialize default agent status and metrics"""
        # Check if agents exist
        cursor.execute("SELECT COUNT(*) FROM agent_status")
        if cursor.fetchone()[0] == 0:
            # Insert default agents
            default_agents = [
                ("Monitor Agent", "active", 3, {"capabilities": ["KPI monitoring", "threshold checking", "alert generation"]}),
                ("Optimizer Agent", "standby", 0, {"capabilities": ["parameter optimization", "performance tuning", "automated configuration"]}),
                ("Analyzer Agent", "active", 1, {"capabilities": ["trend analysis", "anomaly detection", "performance assessment"]})
            ]
            
            for name, status, tasks, metadata in default_agents:
                cursor.execute("""
                INSERT INTO agent_status (agent_name, status, active_tasks, metadata)
                VALUES (?, ?, ?, ?)
                """, (name, status, tasks, json.dumps(metadata)))
        
        # Check if metrics exist
        cursor.execute("SELECT COUNT(*) FROM agent_metrics")
        if cursor.fetchone()[0] == 0:
            # Insert initial metrics
            cursor.execute("""
            INSERT INTO agent_metrics (active_agents, operations_today, success_rate, auto_optimizations)
            VALUES (3, 12, 95.8, 7)
            """)
    
    def get_agent_status(self) -> List[Dict]:
        """Get current status of all agents"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT agent_name, status, active_tasks, last_activity, metadata
                FROM agent_status
                ORDER BY agent_name
                """)
                
                agents = []
                for row in cursor.fetchall():
                    agent = dict(row)
                    if agent['metadata']:
                        agent['metadata'] = json.loads(agent['metadata'])
                    agents.append(agent)
                
                return agents
                
        except Exception as e:
            logger.error(f"Failed to get agent status: {e}")
            return []
    
    def update_agent_status(self, agent_name: str, status: str, active_tasks: Optional[int] = None, metadata: Optional[Dict] = None):
        """Update agent status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                update_fields = ["status = ?", "last_activity = CURRENT_TIMESTAMP", "updated_at = CURRENT_TIMESTAMP"]
                values = [status]
                
                if active_tasks is not None:
                    update_fields.append("active_tasks = ?")
                    values.append(active_tasks)
                
                if metadata is not None:
                    update_fields.append("metadata = ?")
                    values.append(json.dumps(metadata))
                
                values.append(agent_name)
                
                cursor.execute(f"""
                UPDATE agent_status 
                SET {', '.join(update_fields)}
                WHERE agent_name = ?
                """, values)
                
                conn.commit()
                logger.info(f"Updated agent status for {agent_name}: {status}")
                
        except Exception as e:
            logger.error(f"Failed to update agent status: {e}")
    
    def create_operation(self, operation_type: str, target_site: Optional[str] = None, parameters: Optional[Dict] = None, agent_name: Optional[str] = None) -> Optional[str]:
        """Create a new operation record"""
        try:
            operation_id = f"OP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{operation_type.replace(' ', '_').upper()}"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                INSERT INTO agentic_operations 
                (operation_id, operation_type, target_site, status, parameters, agent_name)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (operation_id, operation_type, target_site, "initiated", 
                     json.dumps(parameters) if parameters else None, agent_name))
                
                # Add initial log entry
                cursor.execute("""
                INSERT INTO operation_history (operation_id, message, log_level)
                VALUES (?, ?, ?)
                """, (operation_id, f"Operation {operation_type} initiated", "INFO"))
                
                conn.commit()
                logger.info(f"Created operation: {operation_id}")
                return operation_id
                
        except Exception as e:
            logger.error(f"Failed to create operation: {e}")
            return None
    
    def update_operation_status(self, operation_id: str, status: str, results: Optional[Dict] = None, error_message: Optional[str] = None):
        """Update operation status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                update_fields = ["status = ?"]
                values = [status]
                
                if status in ["completed", "failed"]:
                    update_fields.append("completed_at = CURRENT_TIMESTAMP")
                
                if results:
                    update_fields.append("results = ?")
                    values.append(json.dumps(results))
                
                if error_message:
                    update_fields.append("error_message = ?")
                    values.append(error_message)
                
                values.append(operation_id)
                
                cursor.execute(f"""
                UPDATE agentic_operations 
                SET {', '.join(update_fields)}
                WHERE operation_id = ?
                """, values)
                
                # Add log entry
                log_level = "ERROR" if status == "failed" else "INFO"
                message = error_message if error_message else f"Operation status updated to {status}"
                
                cursor.execute("""
                INSERT INTO operation_history (operation_id, message, log_level, details)
                VALUES (?, ?, ?, ?)
                """, (operation_id, message, log_level, json.dumps(results) if results else None))
                
                conn.commit()
                logger.info(f"Updated operation {operation_id}: {status}")
                
        except Exception as e:
            logger.error(f"Failed to update operation status: {e}")
    
    def add_operation_log(self, operation_id: str, message: str, log_level: str = "INFO", details: Optional[Dict] = None):
        """Add a log entry for an operation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                INSERT INTO operation_history (operation_id, message, log_level, details)
                VALUES (?, ?, ?, ?)
                """, (operation_id, message, log_level, json.dumps(details) if details else None))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to add operation log: {e}")
    
    def get_recent_operations(self, limit: int = 10) -> List[Dict]:
        """Get recent operations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT operation_id, operation_type, target_site, status, 
                       started_at, completed_at, agent_name, error_message
                FROM agentic_operations
                ORDER BY started_at DESC
                LIMIT ?
                """, (limit,))
                
                operations = []
                for row in cursor.fetchall():
                    op = dict(row)
                    operations.append(op)
                
                return operations
                
        except Exception as e:
            logger.error(f"Failed to get recent operations: {e}")
            return []
    
    def get_operation_logs(self, operation_id: str) -> List[Dict]:
        """Get logs for a specific operation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT timestamp, log_level, message, details
                FROM operation_history
                WHERE operation_id = ?
                ORDER BY timestamp ASC
                """, (operation_id,))
                
                logs = []
                for row in cursor.fetchall():
                    log = dict(row)
                    if log['details']:
                        try:
                            log['details'] = json.loads(log['details'])
                        except:
                            pass
                    logs.append(log)
                
                return logs
                
        except Exception as e:
            logger.error(f"Failed to get operation logs: {e}")
            return []
    
    def get_current_metrics(self) -> Dict:
        """Get current agent metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get latest metrics
                cursor.execute("""
                SELECT active_agents, operations_today, success_rate, auto_optimizations
                FROM agent_metrics
                ORDER BY timestamp DESC
                LIMIT 1
                """)
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                else:
                    return {
                        "active_agents": 0,
                        "operations_today": 0,
                        "success_rate": 0.0,
                        "auto_optimizations": 0
                    }
                
        except Exception as e:
            logger.error(f"Failed to get current metrics: {e}")
            return {}
    
    def update_metrics(self, active_agents: Optional[int] = None, operations_today: Optional[int] = None, 
                      success_rate: Optional[float] = None, auto_optimizations: Optional[int] = None):
        """Update agent metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current metrics
                current = self.get_current_metrics()
                
                # Update with new values
                if active_agents is not None:
                    current['active_agents'] = active_agents
                if operations_today is not None:
                    current['operations_today'] = operations_today
                if success_rate is not None:
                    current['success_rate'] = success_rate
                if auto_optimizations is not None:
                    current['auto_optimizations'] = auto_optimizations
                
                # Insert new metrics record
                cursor.execute("""
                INSERT INTO agent_metrics (active_agents, operations_today, success_rate, auto_optimizations)
                VALUES (?, ?, ?, ?)
                """, (current['active_agents'], current['operations_today'], 
                     current['success_rate'], current['auto_optimizations']))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")