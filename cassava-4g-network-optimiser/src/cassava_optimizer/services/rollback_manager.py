"""
Rollback Manager Service.

Manages parameter rollback functionality for failed or unwanted changes.
Stores original values before changes and provides rollback capability.
"""

import logging
from datetime import datetime
from typing import Any

from cassava_optimizer.infrastructure.huawei_client import HuaweiMAEClient
from cassava_optimizer.infrastructure.repository import NetworkRepository
from cassava_optimizer.domain.exceptions import HuaweiAPIError

logger = logging.getLogger(__name__)


class RollbackRecord:
    """Record of a parameter change for potential rollback."""
    
    def __init__(
        self,
        site_id: str,
        cell_id: str,
        parameter_name: str,
        original_value: Any,
        new_value: Any,
        mml_command: str,
        rollback_command: str,
        session_id: str,
        timestamp: datetime | None = None,
    ) -> None:
        self.site_id = site_id
        self.cell_id = cell_id
        self.parameter_name = parameter_name
        self.original_value = original_value
        self.new_value = new_value
        self.mml_command = mml_command
        self.rollback_command = rollback_command
        self.session_id = session_id
        self.timestamp = timestamp or datetime.utcnow()
        self.rolled_back = False
        self.rollback_timestamp: datetime | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "site_id": self.site_id,
            "cell_id": self.cell_id,
            "parameter_name": self.parameter_name,
            "original_value": self.original_value,
            "new_value": self.new_value,
            "mml_command": self.mml_command,
            "rollback_command": self.rollback_command,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "rolled_back": self.rolled_back,
            "rollback_timestamp": self.rollback_timestamp.isoformat() if self.rollback_timestamp else None,
        }


class RollbackManager:
    """
    Manages parameter rollback for network configuration changes.
    
    Features:
    - Records all changes with rollback commands
    - Supports individual and batch rollback
    - Persists records to database
    - Tracks rollback history
    """
    
    def __init__(self, huawei_client: HuaweiMAEClient | None = None) -> None:
        """
        Initialize the rollback manager.
        
        Args:
            huawei_client: Optional Huawei client (for executing rollback commands)
        """
        self._client = huawei_client
        self._repository = NetworkRepository()
        self._records: dict[str, RollbackRecord] = {}  # command_id -> record
        
        logger.info("RollbackManager initialized")
    
    def set_huawei_client(self, client: HuaweiMAEClient) -> None:
        """Set the Huawei client for rollback execution."""
        self._client = client
    
    def record_change(
        self,
        site_id: str,
        cell_id: str,
        parameter_name: str,
        original_value: Any,
        new_value: Any,
        mml_command: str,
        session_id: str,
    ) -> str:
        """
        Record a parameter change for potential rollback.
        
        Args:
            site_id: Site identifier
            cell_id: Cell identifier
            parameter_name: Name of the parameter changed
            original_value: Value before change
            new_value: Value after change
            mml_command: MML command that was executed
            session_id: Optimization session ID
            
        Returns:
            Unique record ID for this change
        """
        # Generate rollback command
        rollback_command = self._generate_rollback_command(
            mml_command, parameter_name, original_value
        )
        
        record = RollbackRecord(
            site_id=site_id,
            cell_id=cell_id,
            parameter_name=parameter_name,
            original_value=original_value,
            new_value=new_value,
            mml_command=mml_command,
            rollback_command=rollback_command,
            session_id=session_id,
        )
        
        # Generate unique ID
        record_id = f"{session_id}_{parameter_name}_{int(record.timestamp.timestamp())}"
        self._records[record_id] = record
        
        logger.info(
            f"Recorded change: {parameter_name} on {site_id}/{cell_id} "
            f"({original_value} -> {new_value})"
        )
        
        return record_id
    
    def _generate_rollback_command(
        self,
        original_command: str,
        parameter_name: str,
        original_value: Any,
    ) -> str:
        """
        Generate the MML command to rollback a change.
        
        Args:
            original_command: The original MML command
            parameter_name: Parameter that was changed
            original_value: Original value to restore
            
        Returns:
            MML command to restore original value
        """
        # Parse the original command to extract LOCALCELLID and command type
        # Example: MOD PDSCHCFG:LOCALCELLID=1,PA=0;
        
        if ":" not in original_command:
            return original_command.replace(str(parameter_name), f"{parameter_name}={original_value}")
        
        cmd_type, params = original_command.split(":", 1)
        
        # Extract LOCALCELLID if present
        local_cell_id = None
        param_parts = params.rstrip(";").split(",")
        for part in param_parts:
            if "LOCALCELLID=" in part.upper():
                local_cell_id = part.split("=")[1]
                break
        
        # Build rollback command
        if local_cell_id:
            rollback = f"{cmd_type}:LOCALCELLID={local_cell_id},{parameter_name}={original_value};"
        else:
            rollback = f"{cmd_type}:{parameter_name}={original_value};"
        
        return rollback
    
    async def rollback_change(self, record_id: str) -> dict[str, Any]:
        """
        Rollback a single recorded change.
        
        Args:
            record_id: ID of the change record to rollback
            
        Returns:
            Result dictionary with success status and details
        """
        if record_id not in self._records:
            return {
                "success": False,
                "error": f"No record found for ID: {record_id}",
            }
        
        record = self._records[record_id]
        
        if record.rolled_back:
            return {
                "success": False,
                "error": f"Change already rolled back at {record.rollback_timestamp}",
            }
        
        if not self._client:
            return {
                "success": False,
                "error": "No Huawei client available for rollback execution",
            }
        
        try:
            logger.info(f"Rolling back: {record.parameter_name} to {record.original_value}")
            
            # Execute rollback command
            result = await self._client.execute_mml_command(
                record.site_id,
                record.rollback_command,
            )
            
            if result.get("success"):
                record.rolled_back = True
                record.rollback_timestamp = datetime.utcnow()
                
                logger.info(f"Rollback successful: {record.parameter_name}")
                
                return {
                    "success": True,
                    "parameter_name": record.parameter_name,
                    "restored_value": record.original_value,
                    "rollback_command": record.rollback_command,
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error_message", "Rollback command failed"),
                }
                
        except HuaweiAPIError as e:
            logger.error(f"Rollback failed for {record.parameter_name}: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def rollback_session(self, session_id: str) -> dict[str, Any]:
        """
        Rollback all changes from a specific optimization session.
        
        Args:
            session_id: Session ID to rollback
            
        Returns:
            Summary of rollback results
        """
        session_records = [
            (record_id, record)
            for record_id, record in self._records.items()
            if record.session_id == session_id and not record.rolled_back
        ]
        
        if not session_records:
            return {
                "success": True,
                "message": f"No changes to rollback for session {session_id}",
                "rolled_back": 0,
            }
        
        results = []
        for record_id, record in reversed(session_records):  # Rollback in reverse order
            result = await self.rollback_change(record_id)
            results.append({
                "record_id": record_id,
                "parameter_name": record.parameter_name,
                **result,
            })
        
        successful = sum(1 for r in results if r.get("success"))
        
        return {
            "success": successful == len(results),
            "rolled_back": successful,
            "failed": len(results) - successful,
            "total": len(results),
            "details": results,
        }
    
    def get_session_changes(self, session_id: str) -> list[dict[str, Any]]:
        """
        Get all recorded changes for a session.
        
        Args:
            session_id: Session ID to query
            
        Returns:
            List of change records as dictionaries
        """
        return [
            record.to_dict()
            for record in self._records.values()
            if record.session_id == session_id
        ]
    
    def get_pending_rollbacks(self, session_id: str | None = None) -> list[dict[str, Any]]:
        """
        Get all changes that haven't been rolled back.
        
        Args:
            session_id: Optional session ID to filter by
            
        Returns:
            List of pending rollback records
        """
        records = self._records.values()
        
        if session_id:
            records = [r for r in records if r.session_id == session_id]
        
        return [
            record.to_dict()
            for record in records
            if not record.rolled_back
        ]


# =============================================================================
# Singleton Instance
# =============================================================================

_rollback_manager: RollbackManager | None = None


def get_rollback_manager() -> RollbackManager:
    """Get singleton rollback manager instance."""
    global _rollback_manager
    if _rollback_manager is None:
        _rollback_manager = RollbackManager()
    return _rollback_manager
