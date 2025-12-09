"""
Command service for managing MML command execution history.

Provides methods to track and retrieve command execution history.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from cassava_optimizer.infrastructure.database import (
    get_session,
    CommandExecutionModel,
)

logger = logging.getLogger(__name__)


class CommandService:
    """Service for managing MML command history."""
    
    async def get_command_history(
        self,
        site_name: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get MML command execution history from the database.
        
        Args:
            site_name: Optional site name to filter by
            limit: Maximum number of records to return
            
        Returns:
            List of command execution records
        """
        try:
            async with get_session() as session:
                query = select(CommandExecutionModel).order_by(
                    desc(CommandExecutionModel.executed_at)
                ).limit(limit)
                
                if site_name:
                    query = query.where(CommandExecutionModel.site_id == site_name)
                
                result = await session.execute(query)
                records = result.scalars().all()
                
                return [
                    {
                        "id": r.id,
                        "command": r.command_text,
                        "status": r.status,
                        "executed_at": r.executed_at.strftime("%Y-%m-%d %H:%M:%S") if r.executed_at else "",
                        "site_name": r.site_id,
                        "execution_time_ms": r.execution_time_ms,
                        "result": r.output,
                        "error": r.error_message,
                        "run_id": r.session_id,
                    }
                    for r in records
                ]
        except Exception as e:
            logger.warning(f"Failed to get command history: {e}")
            return []
    
    async def log_command_execution(
        self,
        command: str,
        site_name: str,
        status: str,
        execution_time_ms: int = 0,
        result: Optional[str] = None,
        error: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> int:
        """
        Log a command execution to the database.
        
        Args:
            command: The MML command that was executed
            site_name: The site where the command was executed
            status: Execution status (success, failed)
            execution_time_ms: Execution time in milliseconds
            result: Command result output
            error: Error message if failed
            session_id: Associated optimization session ID
            
        Returns:
            ID of the created record
        """
        import uuid
        
        try:
            async with get_session() as session:
                record = CommandExecutionModel(
                    command_id=f"CMD-{uuid.uuid4().hex[:8].upper()}",
                    session_id=session_id or "",
                    site_id=site_name,
                    command_text=command,
                    status=status,
                    executed_at=datetime.now(),
                    execution_time_ms=execution_time_ms,
                    output=result or "",
                    error_message=error or "",
                )
                session.add(record)
                await session.commit()
                await session.refresh(record)
                return record.id
        except Exception as e:
            logger.error(f"Failed to log command execution: {e}")
            raise


# Singleton instance
_command_service: Optional[CommandService] = None


def get_command_service() -> CommandService:
    """Get the singleton command service instance."""
    global _command_service
    if _command_service is None:
        _command_service = CommandService()
    return _command_service
