"""
Agent Repository

Data access layer for agents and agent metrics.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import json

from liquid4g.domain.models.agent import Agent, AgentStatus
from liquid4g.infrastructure.repositories.base_repository import BaseRepository
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import DatabaseError

logger = get_logger(__name__)


class AgentRepository(BaseRepository[Agent]):
    """Repository for agent data"""

    # ===== Agent Operations =====

    def create(self, agent: Agent) -> Agent:
        """Create a new agent"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO agents (
                        agent_id, agent_type, display_name, description,
                        status, current_task, capabilities, config,
                        created_at, last_active_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        agent.agent_id,
                        agent.agent_type.value if hasattr(agent.agent_type, 'value') else agent.agent_type,
                        agent.display_name,
                        agent.description,
                        agent.status.value if hasattr(agent.status, 'value') else agent.status,
                        agent.current_task,
                        json.dumps(agent.capabilities),
                        json.dumps(agent.config),
                        agent.created_at.isoformat(),
                        agent.last_active_at.isoformat() if agent.last_active_at else None,
                    ),
                )
                agent.id = cursor.lastrowid

            logger.info(f"Created agent: {agent.agent_id}")
            return agent

        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise DatabaseError(f"Failed to create agent: {e}")

    def get_by_id(self, agent_id: int) -> Optional[Agent]:
        """Get agent by database ID"""
        try:
            with self.db.cursor() as cur:
                cur.execute("SELECT * FROM agents WHERE id = ?;", (agent_id,))
                row = cur.fetchone()
                return self._row_to_agent(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get agent by ID: {e}")
            return None

    def get_by_agent_id(self, agent_id: str) -> Optional[Agent]:
        """
        Get agent by agent_id

        Args:
            agent_id: Agent identifier

        Returns:
            Optional[Agent]: Agent or None
        """
        try:
            with self.db.cursor() as cur:
                cur.execute("SELECT * FROM agents WHERE agent_id = ?;", (agent_id,))
                row = cur.fetchone()
                return self._row_to_agent(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            return None

    def update(self, agent: Agent) -> Agent:
        """Update agent"""
        try:
            with self.db.transaction() as conn:
                conn.execute(
                    """
                    UPDATE agents
                    SET agent_type = ?, display_name = ?, description = ?,
                        status = ?, current_task = ?, capabilities = ?,
                        config = ?, last_active_at = ?
                    WHERE agent_id = ?;
                    """,
                    (
                        agent.agent_type.value if hasattr(agent.agent_type, 'value') else agent.agent_type,
                        agent.display_name,
                        agent.description,
                        agent.status.value if hasattr(agent.status, 'value') else agent.status,
                        agent.current_task,
                        json.dumps(agent.capabilities),
                        json.dumps(agent.config),
                        datetime.utcnow().isoformat(),
                        agent.agent_id,
                    ),
                )

            logger.info(f"Updated agent: {agent.agent_id}")
            return agent

        except Exception as e:
            logger.error(f"Failed to update agent: {e}")
            raise DatabaseError(f"Failed to update agent: {e}")

    def delete(self, agent_id: int) -> bool:
        """Delete agent by database ID"""
        try:
            with self.db.transaction() as conn:
                conn.execute("DELETE FROM agents WHERE id = ?;", (agent_id,))
            logger.info(f"Deleted agent ID: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete agent: {e}")
            return False

    def list_all(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[Agent]:
        """List all agents"""
        query = "SELECT * FROM agents ORDER BY agent_id"
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"

        try:
            with self.db.cursor() as cur:
                cur.execute(query)
                return [self._row_to_agent(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return []

    def list_by_status(self, status: str) -> List[Agent]:
        """
        List agents by status

        Args:
            status: Agent status (idle/running/paused/error/maintenance)

        Returns:
            List[Agent]: Agents with matching status
        """
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM agents WHERE status = ? ORDER BY agent_id;",
                    (status,),
                )
                return [self._row_to_agent(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list agents by status: {e}")
            return []

    def list_by_type(self, agent_type: str) -> List[Agent]:
        """List agents by type"""
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM agents WHERE agent_type = ? ORDER BY agent_id;",
                    (agent_type,),
                )
                return [self._row_to_agent(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list agents by type: {e}")
            return []

    # ===== Agent Metrics Operations =====

    def get_metrics(self, agent_id: str) -> Optional[AgentStatus]:
        """
        Get agent metrics/status

        Args:
            agent_id: Agent identifier

        Returns:
            Optional[AgentStatus]: Agent metrics or None
        """
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    "SELECT * FROM agent_metrics WHERE agent_id = ?;", (agent_id,)
                )
                row = cur.fetchone()
                return self._row_to_status(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get agent metrics: {e}")
            return None

    def update_metrics(self, status: AgentStatus) -> AgentStatus:
        """Update agent metrics"""
        try:
            with self.db.transaction() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO agent_metrics (
                        agent_id, timestamp, status, active_tasks, last_activity,
                        total_executions, successful_executions, failed_executions,
                        llm_executions, rule_executions, circuit_breaker_open,
                        average_duration_seconds, last_error, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        status.agent_id,
                        status.timestamp.isoformat(),
                        status.status.value if hasattr(status.status, 'value') else status.status,
                        status.active_tasks,
                        status.last_activity.isoformat() if status.last_activity else None,
                        status.total_executions,
                        status.successful_executions,
                        status.failed_executions,
                        status.llm_executions,
                        status.rule_executions,
                        status.circuit_breaker_open,
                        status.average_duration_seconds,
                        status.last_error,
                        json.dumps(status.metadata),
                    ),
                )

            logger.debug(f"Updated metrics for agent: {status.agent_id}")
            return status

        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
            raise DatabaseError(f"Failed to update metrics: {e}")

    def increment_execution_count(
        self,
        agent_id: str,
        success: bool,
        used_llm: bool,
        duration_seconds: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Increment execution counters for an agent

        Args:
            agent_id: Agent identifier
            success: Whether execution was successful
            used_llm: Whether LLM was used (vs rule fallback)
            duration_seconds: Execution duration
            error_message: Error message if failed

        Returns:
            bool: True if successful
        """
        try:
            # Get current metrics or create new
            metrics = self.get_metrics(agent_id)
            if not metrics:
                metrics = AgentStatus(
                    agent_id=agent_id,
                    status="idle",
                    total_executions=0,
                    successful_executions=0,
                    failed_executions=0,
                    llm_executions=0,
                    rule_executions=0,
                )

            # Update counters
            metrics.total_executions += 1
            if success:
                metrics.successful_executions += 1
            else:
                metrics.failed_executions += 1
                metrics.last_error = error_message

            if used_llm:
                metrics.llm_executions += 1
            else:
                metrics.rule_executions += 1

            # Update average duration
            if duration_seconds is not None:
                if metrics.average_duration_seconds is None:
                    metrics.average_duration_seconds = duration_seconds
                else:
                    # Moving average
                    metrics.average_duration_seconds = (
                        metrics.average_duration_seconds * 0.9 + duration_seconds * 0.1
                    )

            metrics.timestamp = datetime.utcnow()
            metrics.last_activity = datetime.utcnow()

            self.update_metrics(metrics)
            return True

        except Exception as e:
            logger.error(f"Failed to increment execution count: {e}")
            return False

    # ===== Helper Methods =====

    def _row_to_agent(self, row) -> Agent:
        """Convert database row to Agent"""
        return Agent(
            id=row["id"],
            agent_id=row["agent_id"],
            agent_type=row["agent_type"],
            display_name=row["display_name"],
            description=row["description"],
            status=row["status"],
            current_task=row["current_task"],
            capabilities=json.loads(row["capabilities"]),
            config=json.loads(row["config"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            last_active_at=(
                datetime.fromisoformat(row["last_active_at"])
                if row["last_active_at"]
                else None
            ),
        )

    def _row_to_status(self, row) -> AgentStatus:
        """Convert database row to AgentStatus"""
        return AgentStatus(
            agent_id=row["agent_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            status=row["status"],
            active_tasks=row["active_tasks"],
            last_activity=(
                datetime.fromisoformat(row["last_activity"])
                if row["last_activity"]
                else None
            ),
            total_executions=row["total_executions"],
            successful_executions=row["successful_executions"],
            failed_executions=row["failed_executions"],
            llm_executions=row["llm_executions"],
            rule_executions=row["rule_executions"],
            circuit_breaker_open=bool(row["circuit_breaker_open"]),
            average_duration_seconds=row["average_duration_seconds"],
            last_error=row["last_error"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )
