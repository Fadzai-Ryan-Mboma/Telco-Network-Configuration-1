"""
Analyzer Agent

Performs root cause analysis and recommends parameter changes.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta

from liquid4g.agents.base_agent import BaseAgent
from liquid4g.domain.models.operation import Operation
from liquid4g.infrastructure.repositories import (
    KPIRepository,
    ParameterRepository,
    NetworkRepository
)
from liquid4g.llm import get_prompt_manager
from liquid4g.llm.response_parser import AnalysisResponse
from liquid4g.core.logging import get_logger

logger = get_logger(__name__)


class AnalyzerAgent(BaseAgent):
    """
    Performance analysis agent

    Responsibilities:
    - Root cause analysis of performance issues
    - Correlation between KPIs and parameters
    - Recommend specific parameter adjustments
    - Assess risk level of changes
    """

    def __init__(self):
        """Initialize analyzer agent"""
        super().__init__(agent_id="analyzer_agent", agent_type="analyzer_agent")

        self.kpi_repo = KPIRepository()
        self.param_repo = ParameterRepository()
        self.network_repo = NetworkRepository()
        self.prompt_manager = get_prompt_manager()

        # Load rules
        rules_file = Path(__file__).parent.parent.parent.parent / "config" / "rules" / "optimization_rules.yaml"
        with open(rules_file, "r") as f:
            self.rules = yaml.safe_load(f)

    def _execute_with_llm(self, operation: Operation, **kwargs) -> Dict[str, Any]:
        """Execute analysis with LLM"""
        cell_id = kwargs.get("cell_id") or operation.target_cell
        issues = kwargs.get("issues", [])

        # Get cell info
        cell = self.network_repo.get_cell_by_id(cell_id)
        cell_info = f"Cell: {cell.cell_id}, Site: {cell.site_id}, Technology: {cell.technology}" if cell else "Unknown"

        # Get KPI time series
        kpis = self._get_kpi_time_series(cell_id, days=7)
        kpi_time_series = self.prompt_manager.format_kpi_data(kpis)

        # Get current parameters
        params = self.param_repo.get_all_for_cell(cell_id)
        current_parameters = self.prompt_manager.format_parameters([
            {"param_key": p.param_key, "value": p.value}
            for p in params
        ])

        # Get parameter definitions
        definitions = self.param_repo.list_definitions()
        parameter_definitions = self.prompt_manager.format_parameter_definitions([
            {
                "param_key": d.param_key,
                "display_name": d.display_name,
                "min_value": d.min_value,
                "max_value": d.max_value,
                "default_value": d.default_value,
                "impact_level": d.impact_level,
                "mml_query_command": d.mml_query_command,
                "mml_modify_command": d.mml_modify_command
            }
            for d in definitions
        ])

        # Execute LLM
        result = self.llm_executor.execute(
            agent_type=self.agent_type,
            task_name="analyze_performance",
            response_model=AnalysisResponse,
            task_variables={
                "cell_info": cell_info,
                "kpi_time_series": kpi_time_series,
                "current_parameters": current_parameters,
                "parameter_definitions": parameter_definitions
            }
        )

        return {
            "root_causes": [rc.model_dump() for rc in result.root_causes],
            "recommended_changes": [rc.model_dump() for rc in result.recommended_changes],
            "summary": result.summary
        }

    def _execute_with_rules(self, operation: Operation, **kwargs) -> Dict[str, Any]:
        """Execute analysis with rule-based logic"""
        cell_id = kwargs.get("cell_id") or operation.target_cell
        issues = kwargs.get("issues", [])

        root_causes = []
        recommended_changes = []

        # Get current KPIs
        kpis = {}
        for kpi_key in ["network_access_success", "drop_rate", "handover_success_rate", "average_rsrp"]:
            kpi = self.kpi_repo.get_latest_for_cell(cell_id, kpi_key)
            if kpi:
                kpis[kpi_key] = kpi.value

        # Get current parameters
        current_params = {}
        params = self.param_repo.get_all_for_cell(cell_id)
        for param in params:
            current_params[param.param_key] = param.value

        # Apply parameter rules
        for rule in self.rules.get("parameter_rules", []):
            condition = rule["condition"]
            kpi_key = condition["kpi"]
            operator = condition["operator"]
            threshold = condition["threshold"]

            # Check condition
            kpi_value = kpis.get(kpi_key)
            if kpi_value is None:
                continue

            condition_met = False
            if operator == "greater_than" and kpi_value > threshold:
                condition_met = True
            elif operator == "less_than" and kpi_value < threshold:
                condition_met = True

            if condition_met:
                # Add root cause
                root_causes.append({
                    "issue": f"{kpi_key} = {kpi_value}",
                    "likely_cause": rule["expected_improvement"],
                    "supporting_data": f"KPI value {kpi_value} exceeds threshold {threshold}"
                })

                # Calculate new value
                action = rule["action"]
                param_key = action["param_key"]
                current_value = current_params.get(param_key, 0)

                if action["adjustment"] == "increase":
                    new_value = min(current_value + action["delta"], action.get("max_value", float("inf")))
                else:  # decrease
                    new_value = max(current_value - action["delta"], action.get("min_value", 0))

                recommended_changes.append({
                    "param_key": param_key,
                    "current_value": current_value,
                    "recommended_value": new_value,
                    "expected_improvement": rule["expected_improvement"],
                    "risk_level": rule["risk_level"],
                    "justification": f"Rule-based recommendation for {kpi_key} = {kpi_value}"
                })

        summary = f"Identified {len(root_causes)} root causes and {len(recommended_changes)} parameter changes"

        return {
            "root_causes": root_causes,
            "recommended_changes": recommended_changes,
            "summary": summary
        }

    def _get_kpi_time_series(self, cell_id: str, days: int = 7) -> List[Dict]:
        """Get KPI time series data"""
        result = []
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        for kpi_key in ["network_access_success", "drop_rate", "handover_success_rate"]:
            kpis = self.kpi_repo.get_time_series(cell_id, kpi_key, start_time, end_time, limit=100)
            for kpi in kpis:
                result.append({
                    "kpi_key": kpi.kpi_key,
                    "value": kpi.value,
                    "measurement_time": kpi.measurement_time.isoformat()
                })

        return result
