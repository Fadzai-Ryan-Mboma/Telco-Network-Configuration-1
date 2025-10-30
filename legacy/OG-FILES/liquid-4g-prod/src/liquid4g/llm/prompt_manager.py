"""
Prompt Manager

Manages prompt templates and provides formatted prompts for LLM calls.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from string import Template

try:
    from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatPromptTemplate = None  # type: ignore
    SystemMessagePromptTemplate = None  # type: ignore
    HumanMessagePromptTemplate = None  # type: ignore

from liquid4g.core.config import get_settings
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import ConfigurationError

logger = get_logger(__name__)


class PromptManager:
    """
    Manages prompt templates for LLM interactions

    Features:
    - Load prompts from YAML files
    - Template variable substitution
    - System and task prompt management
    - LangChain ChatPromptTemplate creation
    """

    def __init__(self):
        """Initialize prompt manager"""
        self.settings = get_settings()
        self.prompts_dir = Path(__file__).parent.parent.parent.parent / "config" / "prompts"

        # Load prompts
        self.system_prompts: Dict[str, str] = {}
        self.task_prompts: Dict[str, str] = {}

        self._load_prompts()

    def _load_prompts(self):
        """Load all prompt templates from YAML files"""
        try:
            # Load system prompts
            system_file = self.prompts_dir / "system_prompts.yaml"
            if system_file.exists():
                with open(system_file, "r") as f:
                    self.system_prompts = yaml.safe_load(f) or {}
                logger.info(f"Loaded {len(self.system_prompts)} system prompts")
            else:
                logger.warning(f"System prompts file not found: {system_file}")

            # Load task prompts
            task_file = self.prompts_dir / "task_prompts.yaml"
            if task_file.exists():
                with open(task_file, "r") as f:
                    self.task_prompts = yaml.safe_load(f) or {}
                logger.info(f"Loaded {len(self.task_prompts)} task prompts")
            else:
                logger.warning(f"Task prompts file not found: {task_file}")

        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            raise ConfigurationError(f"Failed to load prompts: {e}")

    def get_system_prompt(self, agent_type: str) -> str:
        """
        Get system prompt for an agent type

        Args:
            agent_type: Agent type (e.g., 'network_optimizer', 'monitor_agent')

        Returns:
            str: System prompt

        Raises:
            ConfigurationError: If prompt not found
        """
        key = f"{agent_type}_system"
        prompt = self.system_prompts.get(key)

        if prompt is None:
            raise ConfigurationError(f"System prompt not found for agent: {agent_type}")

        return prompt

    def get_task_prompt(self, task_name: str, **kwargs) -> str:
        """
        Get task prompt with variable substitution

        Args:
            task_name: Task name (e.g., 'monitor_kpis', 'analyze_performance')
            **kwargs: Variables to substitute in template

        Returns:
            str: Formatted task prompt

        Raises:
            ConfigurationError: If prompt not found
        """
        prompt_template = self.task_prompts.get(task_name)

        if prompt_template is None:
            raise ConfigurationError(f"Task prompt not found: {task_name}")

        # Substitute variables
        try:
            template = Template(prompt_template)
            return template.safe_substitute(**kwargs)
        except Exception as e:
            logger.error(f"Failed to format prompt {task_name}: {e}")
            raise ConfigurationError(f"Failed to format prompt: {e}")

    def create_chat_prompt(
        self,
        agent_type: str,
        task_name: str,
        **kwargs
    ) -> Any:
        """
        Create LangChain ChatPromptTemplate

        Args:
            agent_type: Agent type for system prompt
            task_name: Task name for user prompt
            **kwargs: Variables for task prompt

        Returns:
            ChatPromptTemplate: LangChain prompt template

        Raises:
            ConfigurationError: If prompts not found or LangChain unavailable
        """
        if not LANGCHAIN_AVAILABLE:
            raise ConfigurationError(
                "LangChain not available. Install with: pip install langchain"
            )

        # Get prompts
        system_prompt = self.get_system_prompt(agent_type)
        task_prompt = self.get_task_prompt(task_name, **kwargs)

        # Create chat prompt
        try:
            chat_prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(system_prompt),
                HumanMessagePromptTemplate.from_template(task_prompt),
            ])

            logger.debug(f"Created chat prompt: {agent_type} / {task_name}")
            return chat_prompt

        except Exception as e:
            logger.error(f"Failed to create chat prompt: {e}")
            raise ConfigurationError(f"Failed to create chat prompt: {e}")

    def format_kpi_data(self, kpis: list) -> str:
        """
        Format KPI data for prompts

        Args:
            kpis: List of KPI measurements

        Returns:
            str: Formatted KPI data
        """
        if not kpis:
            return "No KPI data available"

        lines = []
        for kpi in kpis:
            lines.append(
                f"- {kpi.get('kpi_key', 'unknown')}: {kpi.get('value', 'N/A')} "
                f"(measured at {kpi.get('measurement_time', 'unknown')})"
            )

        return "\n".join(lines)

    def format_parameters(self, parameters: list) -> str:
        """
        Format parameter data for prompts

        Args:
            parameters: List of parameter values

        Returns:
            str: Formatted parameter data
        """
        if not parameters:
            return "No parameter data available"

        lines = []
        for param in parameters:
            lines.append(
                f"- {param.get('param_key', 'unknown')}: {param.get('value', 'N/A')}"
            )

        return "\n".join(lines)

    def format_parameter_definitions(self, definitions: list) -> str:
        """
        Format parameter definitions for prompts

        Args:
            definitions: List of parameter definitions

        Returns:
            str: Formatted parameter definitions
        """
        if not definitions:
            return "No parameter definitions available"

        lines = []
        for defn in definitions:
            lines.append(
                f"- {defn.get('param_key', 'unknown')}: "
                f"{defn.get('display_name', 'N/A')}\n"
                f"  Range: [{defn.get('min_value', 'N/A')}, {defn.get('max_value', 'N/A')}]\n"
                f"  Default: {defn.get('default_value', 'N/A')}\n"
                f"  Impact: {defn.get('impact_level', 'N/A')}\n"
                f"  MML Query: {defn.get('mml_query_command', 'N/A')}\n"
                f"  MML Modify: {defn.get('mml_modify_command', 'N/A')}"
            )

        return "\n".join(lines)

    def format_kpi_thresholds(self, thresholds: list) -> str:
        """
        Format KPI thresholds for prompts

        Args:
            thresholds: List of KPI thresholds

        Returns:
            str: Formatted thresholds
        """
        if not thresholds:
            return "No threshold data available"

        lines = []
        for threshold in thresholds:
            lines.append(
                f"- {threshold.get('kpi_key', 'unknown')}: "
                f"Optimal: [{threshold.get('optimal_min', 'N/A')}, "
                f"{threshold.get('optimal_max', 'N/A')}], "
                f"Critical: {threshold.get('critical_threshold', 'N/A')} "
                f"({'higher is better' if threshold.get('higher_is_better') else 'lower is better'})"
            )

        return "\n".join(lines)

    def list_available_prompts(self) -> Dict[str, list]:
        """
        List all available prompts

        Returns:
            Dict[str, list]: Available system and task prompts
        """
        return {
            "system_prompts": list(self.system_prompts.keys()),
            "task_prompts": list(self.task_prompts.keys()),
        }

    def reload_prompts(self):
        """Reload all prompts from disk"""
        logger.info("Reloading prompts from disk")
        self.system_prompts.clear()
        self.task_prompts.clear()
        self._load_prompts()


# Global prompt manager instance
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """
    Get global prompt manager instance

    Returns:
        PromptManager: Singleton prompt manager
    """
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
