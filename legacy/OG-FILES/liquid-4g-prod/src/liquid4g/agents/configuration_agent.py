"""
Configuration Agent

Generates MML commands for parameter changes.
"""

from typing import Dict, Any, List

from liquid4g.agents.base_agent import BaseAgent
from liquid4g.domain.models.operation import Operation
from liquid4g.infrastructure.repositories import ParameterRepository
from liquid4g.llm import get_prompt_manager
from liquid4g.llm.response_parser import CommandSet
from liquid4g.core.logging import get_logger

logger = get_logger(__name__)


class ConfigurationAgent(BaseAgent):
    """
    Configuration generation agent

    Responsibilities:
    - Generate MML commands for approved changes
    - Create pre-change snapshot commands
    - Create verification commands
    - Create rollback commands
    """

    def __init__(self):
        """Initialize configuration agent"""
        super().__init__(agent_id="configuration_agent", agent_type="configuration_agent")

        self.param_repo = ParameterRepository()
        self.prompt_manager = get_prompt_manager()

    def _execute_with_llm(self, operation: Operation, **kwargs) -> Dict[str, Any]:
        """Execute configuration generation with LLM"""
        cell_id = kwargs.get("cell_id") or operation.target_cell
        approved_changes = kwargs.get("approved_changes", [])

        # Get parameter definitions
        definitions = self.param_repo.list_definitions()
        parameter_definitions = self.prompt_manager.format_parameter_definitions([
            {
                "param_key": d.param_key,
                "display_name": d.display_name,
                "min_value": d.min_value,
                "max_value": d.max_value,
                "mml_query_command": d.mml_query_command,
                "mml_modify_command": d.mml_modify_command
            }
            for d in definitions
        ])

        # Format approved changes
        changes_str = "\n".join([
            f"- {c['param_key']}: {c['current_value']} → {c['recommended_value']}"
            for c in approved_changes
        ])

        # Execute LLM
        result = self.llm_executor.execute(
            agent_type=self.agent_type,
            task_name="generate_mml_commands",
            response_model=CommandSet,
            task_variables={
                "cell_id": cell_id,
                "approved_changes": changes_str,
                "parameter_definitions": parameter_definitions
            }
        )

        return {
            "pre_change_commands": result.pre_change_commands,
            "modification_commands": result.modification_commands,
            "verification_commands": result.verification_commands,
            "rollback_commands": result.rollback_commands,
            "execution_notes": result.execution_notes
        }

    def _execute_with_rules(self, operation: Operation, **kwargs) -> Dict[str, Any]:
        """Execute configuration generation with rule-based logic"""
        cell_id = kwargs.get("cell_id") or operation.target_cell
        approved_changes = kwargs.get("approved_changes", [])

        pre_change_commands = []
        modification_commands = []
        verification_commands = []
        rollback_commands = []

        # Get parameter definitions
        definitions = {d.param_key: d for d in self.param_repo.list_definitions()}

        for change in approved_changes:
            param_key = change["param_key"]
            new_value = change["recommended_value"]
            old_value = change["current_value"]

            defn = definitions.get(param_key)
            if not defn:
                logger.warning(f"No definition found for parameter: {param_key}")
                continue

            # Generate commands using MML templates
            if defn.mml_query_command:
                query_cmd = defn.mml_query_command.replace("{cell_id}", cell_id)
                pre_change_commands.append(query_cmd)
                verification_commands.append(query_cmd)

            if defn.mml_modify_command:
                modify_cmd = defn.mml_modify_command.replace("{cell_id}", cell_id)
                modify_cmd = modify_cmd.replace("{value}", str(int(new_value)))

                modification_commands.append(modify_cmd)

                # Rollback command with old value
                rollback_cmd = defn.mml_modify_command.replace("{cell_id}", cell_id)
                rollback_cmd = rollback_cmd.replace("{value}", str(int(old_value)))
                rollback_commands.append(rollback_cmd)

        return {
            "pre_change_commands": pre_change_commands,
            "modification_commands": modification_commands,
            "verification_commands": verification_commands,
            "rollback_commands": rollback_commands,
            "execution_notes": f"Generated {len(modification_commands)} MML commands"
        }
