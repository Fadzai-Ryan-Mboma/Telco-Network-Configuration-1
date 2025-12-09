"""
Optimization service for managing optimization runs.

Provides methods to create, retrieve, and manage optimization history.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from cassava_optimizer.infrastructure.database import (
    get_session,
    OptimizationHistoryModel,
)

logger = logging.getLogger(__name__)


class OptimizationService:
    """Service for managing optimization runs and history."""
    
    async def get_optimization_history(
        self,
        site_name: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get optimization history from the database.
        
        Args:
            site_name: Optional site name to filter by
            limit: Maximum number of records to return
            
        Returns:
            List of optimization run records
        """
        try:
            async with get_session() as session:
                query = select(OptimizationHistoryModel).order_by(
                    desc(OptimizationHistoryModel.started_at)
                ).limit(limit)
                
                if site_name:
                    query = query.where(OptimizationHistoryModel.site_id == site_name)
                
                result = await session.execute(query)
                records = result.scalars().all()
                
                return [
                    {
                        "id": r.id,
                        "run_id": r.session_id,
                        "site_name": r.site_id,
                        "status": "completed" if r.success else "failed",
                        "started_at": r.started_at,
                        "completed_at": r.completed_at,
                        "changes_count": 0,  # Would need to parse commands_json
                        "improvement": "",
                        "duration": f"{r.duration_seconds:.0f}s" if r.duration_seconds else "N/A",
                        "error_message": r.error_message,
                    }
                    for r in records
                ]
        except Exception as e:
            logger.warning(f"Failed to get optimization history: {e}")
            return []
    
    async def get_recent_optimization_runs(
        self,
        site_name: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get recent optimization runs for activity display.
        
        Args:
            site_name: Optional site name to filter by
            limit: Maximum number of records to return
            
        Returns:
            List of recent optimization runs
        """
        return await self.get_optimization_history(
            site_name=site_name,
            limit=limit,
        )
    
    async def create_optimization_run(
        self,
        site_name: str,
        user_query: Optional[str] = None,
        target_kpis: Optional[List[str]] = None,
    ) -> str:
        """
        Create a new optimization run record.
        
        Args:
            site_name: Name of the site being optimized
            user_query: User's natural language query
            target_kpis: List of KPIs to optimize
            
        Returns:
            Session ID of the created record
        """
        import uuid
        
        session_id = f"OPT-{uuid.uuid4().hex[:8].upper()}"
        
        try:
            async with get_session() as session:
                record = OptimizationHistoryModel(
                    session_id=session_id,
                    site_id=site_name,
                    query=user_query or "",
                    started_at=datetime.now(),
                    success=False,
                )
                session.add(record)
                await session.commit()
                return session_id
        except Exception as e:
            logger.error(f"Failed to create optimization run: {e}")
            raise
    
    async def update_optimization_run(
        self,
        session_id: str,
        success: bool,
        recommendations_json: str = "{}",
        commands_json: str = "{}",
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update an optimization run with results.
        
        Args:
            session_id: The session ID to update
            success: Whether the optimization succeeded
            recommendations_json: JSON string of recommendations
            commands_json: JSON string of executed commands
            error_message: Error message if failed
        """
        try:
            async with get_session() as session:
                query = select(OptimizationHistoryModel).where(
                    OptimizationHistoryModel.session_id == session_id
                )
                result = await session.execute(query)
                record = result.scalar_one_or_none()
                
                if record:
                    record.success = success
                    record.completed_at = datetime.now()
                    record.recommendations_json = recommendations_json
                    record.commands_json = commands_json
                    record.error_message = error_message or ""
                    
                    if record.started_at:
                        delta = datetime.now() - record.started_at
                        record.duration_seconds = delta.total_seconds()
                    
                    await session.commit()
        except Exception as e:
            logger.error(f"Failed to update optimization run: {e}")
            raise


# Singleton instance
_optimization_service: Optional[OptimizationService] = None


def get_optimization_service() -> OptimizationService:
    """Get the singleton optimization service instance."""
    global _optimization_service
    if _optimization_service is None:
        _optimization_service = OptimizationService()
    return _optimization_service
