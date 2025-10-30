"""
Execution Agent

Executes approved configuration changes.
"""

from typing import Dict, Any, List
from datetime import datetime

from liquid4g.agents.base_agent import BaseAgent
from liquid4g.domain.models.operation import Operation
from liquid4g.infrastructure.api import get_huawei_client
from liquid4g.infrastructure.repositories import KPIRepository, ParameterRepository
from liquid4g.llm import get_prompt_manager
from liquid4g.llm.response_parser import ExecutionResponse
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import HuaweiAPIError

logger = get_logger(__name__)


class ExecutionAgent(BaseAgent):
    """
    Execution agent

    Responsibilities:
    - Execute pre-change snapshots
    - Execute parameter modifications
    - Monitor KPIs during execution
    - Execute rollback if needed
    - Verify post-change state
    """

    def __init__(self):
        """Initialize execution agent"""
        super().__init__(agent_id="execution_agent", agent_type="execution_agent")

        self.api_client = get_huawei_client()
        self.kpi_repo = KPIRepository()
        self.param_repo = ParameterRepository()
        self.prompt_manager = get_prompt_manager()

    def _execute_with_llm(self, operation: Operation, **kwargs) -> Dict[str, Any]:
        """Execute with LLM (planning/monitoring)"""
        # LLM is used for planning and decision-making
        # Actual execution is done via API (same for both LLM and rules)

        cell_id = kwargs.get("cell_id") or operation.target_cell
        validated_changes = kwargs.get("validated_changes", [])
        mml_commands = kwargs.get("mml_commands", {})
        execution_plan = kwargs.get("execution_plan", "Standard execution")

        # Execute the changes
        return self._execute_changes(cell_id, validated_changes, mml_commands)

    def _execute_with_rules(self, operation: Operation, **kwargs) -> Dict[str, Any]:
        """Execute with rules (same as LLM for execution)"""
        cell_id = kwargs.get("cell_id") or operation.target_cell
        validated_changes = kwargs.get("validated_changes", [])
        mml_commands = kwargs.get("mml_commands", {})

        # Execute the changes
        return self._execute_changes(cell_id, validated_changes, mml_commands)

    def _execute_changes(
        self,
        cell_id: str,
        validated_changes: List[Dict],
        mml_commands: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Execute configuration changes

        Args:
            cell_id: Cell identifier
            validated_changes: List of validated changes
            mml_commands: MML commands to execute

        Returns:
            Dict[str, Any]: Execution results
        """
        commands_executed = []
        rollback_required = False
        execution_status = "completed"

        try:
            # Step 1: Pre-change snapshot
            logger.info(f"Executing pre-change snapshot for {cell_id}")
            for cmd in mml_commands.get("pre_change_commands", []):
                try:
                    response = self.api_client.execute_mml_command(cmd, site_id=cell_id)
                    commands_executed.append({
                        "command": cmd,
                        "status": "success",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except HuaweiAPIError as e:
                    logger.warning(f"Pre-change snapshot failed: {e}")
                    commands_executed.append({
                        "command": cmd,
                        "status": "failed",
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_message": str(e)
                    })

            # Step 2: Execute modifications
            logger.info(f"Executing {len(mml_commands.get('modification_commands', []))} modifications")
            for cmd in mml_commands.get("modification_commands", []):
                try:
                    response = self.api_client.execute_mml_command(cmd, site_id=cell_id)
                    commands_executed.append({
                        "command": cmd,
                        "status": "success",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                    # Record parameter change
                    self._record_parameter_change(cell_id, validated_changes)

                except HuaweiAPIError as e:
                    logger.error(f"Modification failed: {e}")
                    commands_executed.append({
                        "command": cmd,
                        "status": "failed",
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_message": str(e)
                    })
                    rollback_required = True
                    execution_status = "failed"
                    break

            # Step 3: Verification
            if not rollback_required:
                logger.info("Verifying changes")
                for cmd in mml_commands.get("verification_commands", []):
                    try:
                        response = self.api_client.execute_mml_command(cmd, site_id=cell_id)
                        commands_executed.append({
                            "command": cmd,
                            "status": "success",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except HuaweiAPIError as e:
                        logger.warning(f"Verification failed: {e}")

            # Step 4: Rollback if needed
            if rollback_required:
                logger.error("Executing rollback")
                execution_status = "rolled_back"
                for cmd in mml_commands.get("rollback_commands", []):
                    try:
                        response = self.api_client.execute_mml_command(cmd, site_id=cell_id)
                        commands_executed.append({
                            "command": cmd,
                            "status": "success",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except HuaweiAPIError as e:
                        logger.error(f"Rollback failed: {e}")
                        commands_executed.append({
                            "command": cmd,
                            "status": "failed",
                            "timestamp": datetime.utcnow().isoformat(),
                            "error_message": str(e)
                        })

        except Exception as e:
            logger.error(f"Execution error: {e}")
            execution_status = "failed"
            rollback_required = True

        # Get post-change KPIs
        post_change_kpis = self._get_post_change_kpis(cell_id)

        execution_notes = f"Executed {len(commands_executed)} commands. Status: {execution_status}"

        return {
            "execution_status": execution_status,
            "commands_executed": commands_executed,
            "rollback_required": rollback_required,
            "post_change_kpis": post_change_kpis,
            "execution_notes": execution_notes
        }

    def _record_parameter_change(self, cell_id: str, validated_changes: List[Dict]):
        """Record parameter changes in database"""
        from liquid4g.domain.models.parameter import ParameterChange

        for change in validated_changes:
            param_change = ParameterChange(
                change_id=f"CHG_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{change['param_key']}",
                cell_id=cell_id,
                param_key=change["param_key"],
                old_value=change["current_value"],
                new_value=change["recommended_value"],
                change_type="optimization",
                reason=change.get("expected_improvement", "Automated optimization"),
                requested_by=self.agent_id,
                requested_at=datetime.utcnow()
            )

            try:
                self.param_repo.create_change(param_change)
            except Exception as e:
                logger.error(f"Failed to record parameter change: {e}")

    def _get_post_change_kpis(self, cell_id: str) -> Dict[str, Any]:
        """Get KPIs after change execution"""
        post_kpis = {}

        for kpi_key in ["network_access_success", "drop_rate", "handover_success_rate"]:
            kpi = self.kpi_repo.get_latest_for_cell(cell_id, kpi_key)
            if kpi:
                post_kpis[kpi_key] = kpi.value

        return post_kpis
