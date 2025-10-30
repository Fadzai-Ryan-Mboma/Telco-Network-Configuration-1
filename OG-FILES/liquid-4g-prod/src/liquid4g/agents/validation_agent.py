"""
Validation Agent

Validates proposed changes before execution.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from liquid4g.agents.base_agent import BaseAgent
from liquid4g.domain.models.operation import Operation
from liquid4g.infrastructure.repositories import ParameterRepository, NetworkRepository
from liquid4g.llm import get_prompt_manager
from liquid4g.llm.response_parser import ValidationResponse
from liquid4g.core.logging import get_logger

logger = get_logger(__name__)


class ValidationAgent(BaseAgent):
    """
    Validation agent

    Responsibilities:
    - Validate parameter values are within range
    - Check for parameter dependencies
    - Assess impact and risk
    - Make approval decisions
    """

    def __init__(self):
        """Initialize validation agent"""
        super().__init__(agent_id="validation_agent", agent_type="validation_agent")

        self.param_repo = ParameterRepository()
        self.network_repo = NetworkRepository()
        self.prompt_manager = get_prompt_manager()

        # Load validation rules
        rules_file = Path(__file__).parent.parent.parent.parent / "config" / "rules" / "optimization_rules.yaml"
        with open(rules_file, "r") as f:
            self.rules = yaml.safe_load(f)

    def _execute_with_llm(self, operation: Operation, **kwargs) -> Dict[str, Any]:
        """Execute validation with LLM"""
        cell_id = kwargs.get("cell_id") or operation.target_cell
        site_id = kwargs.get("site_id")
        proposed_changes = kwargs.get("proposed_changes", [])

        # Get network status
        cell = self.network_repo.get_cell_by_id(cell_id)
        network_status = f"Cell Status: {cell.status}" if cell else "Unknown"

        # Get parameter definitions
        definitions = self.param_repo.list_definitions()
        parameter_definitions = self.prompt_manager.format_parameter_definitions([
            {
                "param_key": d.param_key,
                "display_name": d.display_name,
                "min_value": d.min_value,
                "max_value": d.max_value,
                "impact_level": d.impact_level
            }
            for d in definitions
        ])

        # Format proposed changes
        changes_str = "\n".join([
            f"- {c['param_key']}: {c['current_value']} → {c['recommended_value']} (risk: {c['risk_level']})"
            for c in proposed_changes
        ])

        # Execute LLM
        result = self.llm_executor.execute(
            agent_type=self.agent_type,
            task_name="validate_changes",
            response_model=ValidationResponse,
            task_variables={
                "cell_id": cell_id,
                "site_id": site_id or "Unknown",
                "proposed_changes": changes_str,
                "parameter_definitions": parameter_definitions,
                "network_status": network_status
            }
        )

        return {
            "validation_results": [vr.model_dump() for vr in result.validation_results],
            "overall_assessment": result.overall_assessment,
            "risk_level": result.risk_level,
            "approval_decision": result.approval_decision,
            "conditions": result.conditions,
            "rejection_reasons": result.rejection_reasons
        }

    def _execute_with_rules(self, operation: Operation, **kwargs) -> Dict[str, Any]:
        """Execute validation with rule-based logic"""
        proposed_changes = kwargs.get("proposed_changes", [])

        validation_results = []
        rejection_reasons = []
        conditions = []

        # Get parameter definitions
        definitions = {d.param_key: d for d in self.param_repo.list_definitions()}

        # Check each proposed change
        for change in proposed_changes:
            param_key = change["param_key"]
            proposed_value = change["recommended_value"]

            defn = definitions.get(param_key)
            if not defn:
                validation_results.append({
                    "param_key": param_key,
                    "proposed_value": proposed_value,
                    "is_valid": False,
                    "within_range": False,
                    "no_conflicts": False,
                    "validation_notes": "Parameter definition not found"
                })
                rejection_reasons.append(f"Unknown parameter: {param_key}")
                continue

            # Check if within range
            within_range = True
            if defn.min_value is not None and proposed_value < defn.min_value:
                within_range = False
                rejection_reasons.append(f"{param_key} below minimum: {proposed_value} < {defn.min_value}")

            if defn.max_value is not None and proposed_value > defn.max_value:
                within_range = False
                rejection_reasons.append(f"{param_key} above maximum: {proposed_value} > {defn.max_value}")

            # Check impact level
            if defn.impact_level == "high":
                conditions.append(f"High-risk parameter {param_key} requires manual approval")

            validation_results.append({
                "param_key": param_key,
                "proposed_value": proposed_value,
                "is_valid": within_range,
                "within_range": within_range,
                "no_conflicts": True,  # Simplified for rule-based
                "validation_notes": f"Value is {'within' if within_range else 'outside'} valid range"
            })

        # Apply time-based rules
        current_hour = datetime.utcnow().hour
        if 8 <= current_hour <= 22:
            conditions.append("Execute during low traffic window (off-peak hours)")

        # Determine approval decision
        if rejection_reasons:
            approval_decision = "rejected"
            overall_assessment = "rejected"
            risk_level = "high"
        elif conditions:
            approval_decision = "approved"
            overall_assessment = "conditional"
            risk_level = "medium"
        else:
            approval_decision = "approved"
            overall_assessment = "approved"
            risk_level = "low"

        return {
            "validation_results": validation_results,
            "overall_assessment": overall_assessment,
            "risk_level": risk_level,
            "approval_decision": approval_decision,
            "conditions": conditions,
            "rejection_reasons": rejection_reasons
        }
