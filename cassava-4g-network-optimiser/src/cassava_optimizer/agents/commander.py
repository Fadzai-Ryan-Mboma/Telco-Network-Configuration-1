"""
Commander Agent - Execution stage.

Responsible for executing MML commands on the Huawei network
via the MAE API. Includes rollback capability on failure.
"""

from datetime import datetime
from typing import Any

import structlog

from cassava_optimizer.agents.base import AgentContext, AgentExecutionError, BaseAgent
from cassava_optimizer.domain.enums import AgentType, OptimizationStatus
from cassava_optimizer.domain.exceptions import HuaweiAPIError
from cassava_optimizer.infrastructure.huawei_client import HuaweiMAEClient
from cassava_optimizer.infrastructure.repository import NetworkRepository

logger = structlog.get_logger(__name__)


class CommanderAgent(BaseAgent):
    """
    Agent responsible for executing network configuration changes.
    
    Execution flow:
    1. Pre-execution snapshot (for rollback)
    2. Execute MML commands sequentially
    3. Verify command execution
    4. Record changes in database
    5. Rollback on failure if configured
    
    Fail-fast: Stops on first command failure.
    """
    
    def __init__(
        self,
        huawei_client: HuaweiMAEClient,
        repository: NetworkRepository,
    ) -> None:
        """
        Initialize the commander agent.
        
        Args:
            huawei_client: Async client for Huawei MAE API
            repository: Database repository for recording changes
        """
        super().__init__()
        self._huawei = huawei_client
        self._repo = repository
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.COMMANDER
    
    async def _validate_preconditions(self, context: AgentContext) -> None:
        """Validate that we have validated recommendations to execute."""
        await super()._validate_preconditions(context)
        
        if not context.recommendations:
            self._log.info("No recommendations to execute")
            return
        
        # Check if any require approval and aren't approved
        pending_approval = [
            r for r in context.recommendations
            if r.get("requires_approval") and not r.get("approved")
        ]
        
        if pending_approval and not context.auto_approve:
            raise AgentExecutionError(
                f"{len(pending_approval)} recommendations require human approval",
                agent_type=self.agent_type,
                step="precondition_check",
                recoverable=True,
            )
    
    async def _execute(self, context: AgentContext) -> dict[str, Any]:
        """
        Execute validated recommendations on the network.
        
        Returns:
            Dictionary containing:
            - executed_commands: List of successfully executed commands
            - failed_commands: List of failed commands
            - rollback_performed: Whether rollback was triggered
            - execution_summary: Summary of execution
        """
        recommendations = context.recommendations
        site_id = context.site_id
        
        self._log.info(
            "Starting command execution",
            site_id=site_id,
            recommendation_count=len(recommendations),
            dry_run=context.dry_run,
        )
        
        if not recommendations:
            return {
                "executed_commands": [],
                "failed_commands": [],
                "rollback_performed": False,
                "execution_summary": "No recommendations to execute",
            }
        
        # 1. Take pre-execution snapshot
        snapshot = await self._take_snapshot(site_id) if not context.dry_run else {}
        
        executed_commands = []
        failed_commands = []
        rollback_performed = False
        
        # 2. Execute each recommendation
        for rec in recommendations:
            rec_id = rec.get("id", "unknown")
            
            self._log.info(
                "Executing recommendation",
                rec_id=rec_id,
                title=rec.get("title"),
            )
            
            for cmd in rec.get("mml_commands", []):
                if context.dry_run:
                    # Dry run - just record what would be executed
                    executed_commands.append({
                        "command": cmd,
                        "rec_id": rec_id,
                        "status": "dry_run",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    continue
                
                # Actually execute the command
                result = await self._execute_command(site_id, cmd, rec_id)
                
                if result["success"]:
                    executed_commands.append(result)
                    
                    # Record in database
                    await self._record_command_execution(
                        site_id, cmd, rec_id, result, context.optimization_id
                    )
                else:
                    failed_commands.append(result)
                    
                    # Fail-fast: stop and consider rollback
                    self._log.error(
                        "Command execution failed",
                        command=cmd[:50],
                        error=result.get("error"),
                    )
                    
                    if executed_commands:
                        # Rollback executed commands
                        rollback_result = await self._rollback(
                            site_id, snapshot, executed_commands
                        )
                        rollback_performed = rollback_result["success"]
                    
                    break
            
            # Break outer loop if we had a failure
            if failed_commands:
                break
        
        # 3. Record changes in context
        context.applied_commands = executed_commands
        
        summary = self._generate_execution_summary(
            executed_commands, failed_commands, rollback_performed, context.dry_run
        )
        
        output = {
            "executed_commands": executed_commands,
            "failed_commands": failed_commands,
            "rollback_performed": rollback_performed,
            "execution_summary": summary,
            "snapshot": snapshot if not context.dry_run else None,
        }
        
        self._log.info(
            "Execution complete",
            executed=len(executed_commands),
            failed=len(failed_commands),
            rollback=rollback_performed,
        )
        
        return output
    
    async def _take_snapshot(self, site_id: str) -> dict[str, Any]:
        """
        Take snapshot of current configuration for rollback.
        
        Returns:
            Dictionary of current parameter values
        """
        self._log.debug("Taking configuration snapshot", site_id=site_id)
        
        try:
            # Get current KPIs
            kpis = await self._huawei.get_kpi_data(site_id)
            
            # Get site details with parameters
            site = await self._huawei.get_site_details(site_id)
            
            snapshot = {
                "timestamp": datetime.utcnow().isoformat(),
                "site_id": site_id,
                "kpis": {
                    m.definition.name: m.value for m in kpis
                } if kpis else {},
                "cells": [
                    {
                        "cell_id": c.cell_id,
                        "tx_power": c.tx_power,
                        "electrical_tilt": c.electrical_tilt,
                        "pci": c.pci,
                    }
                    for c in site.cells
                ] if site else [],
            }
            
            self._log.debug("Snapshot taken", kpi_count=len(snapshot.get("kpis", {})))
            return snapshot
            
        except Exception as e:
            self._log.warning(
                "Failed to take complete snapshot",
                error=str(e),
            )
            return {"timestamp": datetime.utcnow().isoformat(), "error": str(e)}
    
    async def _execute_command(
        self,
        site_id: str,
        command: str,
        rec_id: str,
    ) -> dict[str, Any]:
        """
        Execute a single MML command.
        
        Returns:
            Execution result with success flag and output/error
        """
        start_time = datetime.utcnow()
        
        try:
            result = await self._huawei.execute_mml_command(site_id, command)
            
            execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "command": command,
                "rec_id": rec_id,
                "success": result.get("success", False),
                "output": result.get("output", ""),
                "error": result.get("error_message") if not result.get("success") else None,
                "execution_time_ms": execution_time_ms,
                "timestamp": start_time.isoformat(),
            }
            
        except HuaweiAPIError as e:
            execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "command": command,
                "rec_id": rec_id,
                "success": False,
                "output": "",
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "timestamp": start_time.isoformat(),
            }
    
    async def _record_command_execution(
        self,
        site_id: str,
        command: str,
        rec_id: str,
        result: dict[str, Any],
        optimization_id: str,
    ) -> None:
        """Record command execution in database."""
        try:
            from cassava_optimizer.domain.models import OptimizationHistory
            
            # Get site from DB
            site = await self._repo.get_site_by_name(site_id)
            
            if site:
                history = OptimizationHistory(
                    site_id=site.site_id,
                    optimization_type="parameter_change",
                    recommendation_id=rec_id,
                    mml_command=command,
                    status=OptimizationStatus.APPLIED if result.get("success") else OptimizationStatus.FAILED,
                    result_summary=result.get("output", "")[:500],
                    applied_by="system",
                )
                
                await self._repo.save_optimization_history(history)
                
        except Exception as e:
            self._log.warning(
                "Failed to record command execution",
                error=str(e),
            )
    
    async def _rollback(
        self,
        site_id: str,
        snapshot: dict[str, Any],
        executed_commands: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Rollback executed commands using snapshot.
        
        Returns:
            Rollback result with success flag
        """
        self._log.warning(
            "Starting rollback",
            site_id=site_id,
            commands_to_rollback=len(executed_commands),
        )
        
        rollback_results = []
        
        # Rollback in reverse order
        for cmd_result in reversed(executed_commands):
            original_cmd = cmd_result.get("command", "")
            
            # Generate reverse command
            reverse_cmd = self._generate_reverse_command(original_cmd, snapshot)
            
            if reverse_cmd:
                try:
                    result = await self._huawei.execute_mml_command(site_id, reverse_cmd)
                    rollback_results.append({
                        "original": original_cmd,
                        "reverse": reverse_cmd,
                        "success": result.get("success", False),
                    })
                except Exception as e:
                    rollback_results.append({
                        "original": original_cmd,
                        "reverse": reverse_cmd,
                        "success": False,
                        "error": str(e),
                    })
        
        success_count = sum(1 for r in rollback_results if r.get("success"))
        total_count = len(rollback_results)
        
        self._log.info(
            "Rollback complete",
            success_count=success_count,
            total_count=total_count,
        )
        
        return {
            "success": success_count == total_count,
            "details": rollback_results,
        }
    
    def _generate_reverse_command(
        self,
        original_cmd: str,
        snapshot: dict[str, Any],
    ) -> str | None:
        """
        Generate a reverse command to undo a change.
        
        This is a simplified implementation - real implementation would
        need to parse the command and look up original values from snapshot.
        """
        # Extract parameter name and try to restore from snapshot
        # This is a basic implementation
        
        if "MOD" in original_cmd.upper():
            # Try to extract parameter and find in snapshot
            # Format: MOD PARAM:name=value;
            try:
                # Basic parsing
                parts = original_cmd.split(":")
                if len(parts) >= 2:
                    param_part = parts[1].rstrip(";")
                    param_name = param_part.split("=")[0].lower()
                    
                    # Look in snapshot cells for original value
                    for cell in snapshot.get("cells", []):
                        if param_name in cell:
                            original_value = cell[param_name]
                            return f"MOD CELL:{param_name}={original_value};"
            except Exception:
                pass
        
        return None
    
    def _generate_execution_summary(
        self,
        executed: list[dict[str, Any]],
        failed: list[dict[str, Any]],
        rollback: bool,
        dry_run: bool,
    ) -> str:
        """Generate human-readable execution summary."""
        if dry_run:
            return f"Dry run completed - {len(executed)} commands would be executed"
        
        parts = []
        
        if executed:
            parts.append(f"Successfully executed {len(executed)} commands")
        
        if failed:
            parts.append(f"{len(failed)} commands failed")
        
        if rollback:
            parts.append("Rollback was performed")
        
        if not executed and not failed:
            return "No commands were executed"
        
        return ". ".join(parts) + "."
