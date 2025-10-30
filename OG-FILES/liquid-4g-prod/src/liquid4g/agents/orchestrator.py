"""
Agent Orchestrator

Orchestrates the 6-stage optimization workflow.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from liquid4g.agents.monitor_agent import MonitorAgent
from liquid4g.agents.analyzer_agent import AnalyzerAgent
from liquid4g.agents.configuration_agent import ConfigurationAgent
from liquid4g.agents.validation_agent import ValidationAgent
from liquid4g.agents.execution_agent import ExecutionAgent
from liquid4g.domain.models.operation import Operation, OperationType
from liquid4g.infrastructure.repositories import OperationRepository, NetworkRepository
from liquid4g.core.logging import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the 6-stage network optimization workflow

    Stages:
    1. Monitor: Identify cells with performance issues
    2. Analyze: Root cause analysis and recommendations
    3. Configure: Generate MML commands
    4. Validate: Pre-execution validation
    5. Execute: Apply changes to network
    6. Verify: Post-execution verification
    """

    def __init__(self):
        """Initialize orchestrator"""
        self.monitor_agent = MonitorAgent()
        self.analyzer_agent = AnalyzerAgent()
        self.configuration_agent = ConfigurationAgent()
        self.validation_agent = ValidationAgent()
        self.execution_agent = ExecutionAgent()

        self.operation_repo = OperationRepository()
        self.network_repo = NetworkRepository()

        logger.info("Agent orchestrator initialized")

    def optimize_cell(
        self,
        cell_id: str,
        auto_execute: bool = False
    ) -> Dict[str, Any]:
        """
        Run full optimization workflow for a cell

        Args:
            cell_id: Cell identifier
            auto_execute: If True, automatically execute approved changes

        Returns:
            Dict[str, Any]: Optimization results
        """
        logger.info(f"Starting optimization workflow for cell: {cell_id}")

        # Create parent operation
        operation = Operation.create(
            operation_type=OperationType.FULL_OPTIMIZATION,
            target_cell=cell_id
        )
        operation = self.operation_repo.create(operation)

        try:
            # Stage 1: Monitor
            logger.info("Stage 1: Monitoring KPIs")
            operation.stage = "monitoring"
            self.operation_repo.update(operation)

            monitor_result = self.monitor_agent.execute(operation, cell_id=cell_id)

            if not monitor_result.success:
                return self._create_result(operation, "failed", "Monitoring failed", monitor_result)

            issues = monitor_result.data.get("issues", [])
            if not issues:
                logger.info("No issues found, optimization not needed")
                operation.complete({"message": "No issues found"})
                self.operation_repo.update(operation)
                return self._create_result(operation, "completed", "No issues found")

            # Stage 2: Analyze
            logger.info(f"Stage 2: Analyzing {len(issues)} issues")
            operation.stage = "analysis"
            self.operation_repo.update(operation)

            analyzer_result = self.analyzer_agent.execute(
                operation,
                cell_id=cell_id,
                issues=issues
            )

            if not analyzer_result.success:
                return self._create_result(operation, "failed", "Analysis failed", analyzer_result)

            recommended_changes = analyzer_result.data.get("recommended_changes", [])
            if not recommended_changes:
                logger.info("No parameter changes recommended")
                operation.complete({"message": "No changes recommended"})
                self.operation_repo.update(operation)
                return self._create_result(operation, "completed", "No changes recommended")

            # Stage 3: Configure
            logger.info(f"Stage 3: Generating MML commands for {len(recommended_changes)} changes")
            operation.stage = "configuration"
            self.operation_repo.update(operation)

            config_result = self.configuration_agent.execute(
                operation,
                cell_id=cell_id,
                approved_changes=recommended_changes
            )

            if not config_result.success:
                return self._create_result(operation, "failed", "Configuration failed", config_result)

            mml_commands = config_result.data

            # Stage 4: Validate
            logger.info("Stage 4: Validating proposed changes")
            operation.stage = "validation"
            self.operation_repo.update(operation)

            # Get site_id
            cell = self.network_repo.get_cell_by_id(cell_id)
            site_id = cell.site_id if cell else None

            validation_result = self.validation_agent.execute(
                operation,
                cell_id=cell_id,
                site_id=site_id,
                proposed_changes=recommended_changes
            )

            if not validation_result.success:
                return self._create_result(operation, "failed", "Validation failed", validation_result)

            approval_decision = validation_result.data.get("approval_decision")
            if approval_decision == "rejected":
                rejection_reasons = validation_result.data.get("rejection_reasons", [])
                logger.warning(f"Changes rejected: {rejection_reasons}")
                operation.complete({
                    "message": "Changes rejected",
                    "reasons": rejection_reasons
                })
                self.operation_repo.update(operation)
                return self._create_result(operation, "rejected", "Changes rejected", validation_result)

            # Stage 5: Execute (if auto_execute)
            if auto_execute:
                logger.info("Stage 5: Executing approved changes")
                operation.stage = "execution"
                self.operation_repo.update(operation)

                execution_result = self.execution_agent.execute(
                    operation,
                    cell_id=cell_id,
                    validated_changes=recommended_changes,
                    mml_commands=mml_commands
                )

                if not execution_result.success:
                    return self._create_result(operation, "failed", "Execution failed", execution_result)

                # Complete operation
                operation.complete({
                    "issues": issues,
                    "recommended_changes": recommended_changes,
                    "mml_commands": mml_commands,
                    "validation": validation_result.data,
                    "execution": execution_result.data
                })
                self.operation_repo.update(operation)

                return self._create_result(
                    operation,
                    "completed",
                    "Optimization completed successfully",
                    execution_result
                )

            else:
                # Changes approved but not executed
                logger.info("Changes approved, waiting for manual execution")
                operation.complete({
                    "issues": issues,
                    "recommended_changes": recommended_changes,
                    "mml_commands": mml_commands,
                    "validation": validation_result.data,
                    "message": "Changes approved, waiting for execution"
                })
                self.operation_repo.update(operation)

                return self._create_result(
                    operation,
                    "approved",
                    "Changes approved, awaiting execution",
                    validation_result
                )

        except Exception as e:
            logger.error(f"Orchestration error: {e}")
            operation.fail(str(e))
            self.operation_repo.update(operation)
            return self._create_result(operation, "failed", f"Orchestration error: {e}")

    def optimize_site(
        self,
        site_id: str,
        auto_execute: bool = False
    ) -> Dict[str, Any]:
        """
        Optimize all cells in a site

        Args:
            site_id: Site identifier
            auto_execute: If True, automatically execute approved changes

        Returns:
            Dict[str, Any]: Optimization results for all cells
        """
        logger.info(f"Starting site optimization for: {site_id}")

        # Get all cells for site
        cells = self.network_repo.list_cells_by_site(site_id)

        if not cells:
            return {
                "status": "failed",
                "message": f"No cells found for site: {site_id}",
                "results": []
            }

        results = []
        for cell in cells:
            logger.info(f"Optimizing cell: {cell.cell_id}")
            result = self.optimize_cell(cell.cell_id, auto_execute=auto_execute)
            results.append(result)

        # Aggregate results
        total = len(results)
        completed = sum(1 for r in results if r["status"] == "completed")
        failed = sum(1 for r in results if r["status"] == "failed")

        return {
            "status": "completed",
            "site_id": site_id,
            "total_cells": total,
            "completed": completed,
            "failed": failed,
            "results": results
        }

    def _create_result(
        self,
        operation: Operation,
        status: str,
        message: str,
        agent_result: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Create standardized result dictionary"""
        result = {
            "operation_id": operation.operation_id,
            "cell_id": operation.target_cell,
            "status": status,
            "message": message,
            "started_at": operation.started_at.isoformat(),
        }

        if operation.completed_at:
            result["completed_at"] = operation.completed_at.isoformat()
            result["duration_seconds"] = operation.duration_seconds

        if agent_result:
            result["agent_data"] = agent_result.data
            result["used_llm"] = agent_result.used_llm

        return result

    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an operation"""
        operation = self.operation_repo.get_by_operation_id(operation_id)

        if not operation:
            return None

        return {
            "operation_id": operation.operation_id,
            "operation_type": operation.operation_type,
            "stage": operation.stage,
            "status": operation.status,
            "target_cell": operation.target_cell,
            "started_at": operation.started_at.isoformat(),
            "completed_at": operation.completed_at.isoformat() if operation.completed_at else None,
            "duration_seconds": operation.duration_seconds,
            "results": operation.results
        }
