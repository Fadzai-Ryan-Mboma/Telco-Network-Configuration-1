"""
Monitor Agent

Monitors network KPIs and identifies cells requiring attention.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta

from liquid4g.agents.base_agent import BaseAgent
from liquid4g.domain.models.operation import Operation
from liquid4g.infrastructure.repositories import KPIRepository, NetworkRepository
from liquid4g.llm import get_prompt_manager
from liquid4g.llm.response_parser import MonitoringResponse
from liquid4g.core.logging import get_logger

logger = get_logger(__name__)


class MonitorAgent(BaseAgent):
    """
    Network monitoring agent

    Responsibilities:
    - Monitor KPI data in real-time
    - Identify performance issues
    - Classify severity (critical/warning/info)
    - Prioritize cells requiring attention
    """

    def __init__(self):
        """Initialize monitor agent"""
        super().__init__(agent_id="monitor_agent", agent_type="monitor_agent")

        self.kpi_repo = KPIRepository()
        self.network_repo = NetworkRepository()
        self.prompt_manager = get_prompt_manager()

        # Load rules
        rules_file = Path(__file__).parent.parent.parent.parent / "config" / "rules" / "optimization_rules.yaml"
        with open(rules_file, "r") as f:
            self.rules = yaml.safe_load(f)

    def _execute_with_llm(self, operation: Operation, **kwargs) -> Dict[str, Any]:
        """Execute monitoring with LLM"""
        cell_id = kwargs.get("cell_id") or operation.target_cell

        # Get KPI data
        kpis = self._get_recent_kpis(cell_id)
        thresholds = self.kpi_repo.list_thresholds()

        # Format data for prompt
        kpi_data = self.prompt_manager.format_kpi_data([
            {
                "kpi_key": kpi.kpi_key,
                "value": kpi.value,
                "measurement_time": kpi.measurement_time.isoformat()
            }
            for kpi in kpis
        ])

        threshold_data = self.prompt_manager.format_kpi_thresholds([
            {
                "kpi_key": t.kpi_key,
                "optimal_min": t.optimal_min,
                "optimal_max": t.optimal_max,
                "critical_threshold": t.critical_threshold,
                "higher_is_better": t.higher_is_better
            }
            for t in thresholds
        ])

        # Execute LLM
        result = self.llm_executor.execute(
            agent_type=self.agent_type,
            task_name="monitor_kpis",
            response_model=MonitoringResponse,
            task_variables={
                "cell_id": cell_id,
                "kpi_data": kpi_data,
                "kpi_thresholds": threshold_data
            }
        )

        # Convert to dict
        return {
            "issues": [issue.model_dump() for issue in result.issues],
            "cells_requiring_attention": result.cells_requiring_attention,
            "summary": result.summary
        }

    def _execute_with_rules(self, operation: Operation, **kwargs) -> Dict[str, Any]:
        """Execute monitoring with rule-based logic"""
        cell_id = kwargs.get("cell_id") or operation.target_cell

        # Get KPI data
        kpis = self._get_recent_kpis(cell_id)

        issues = []
        cells_requiring_attention = []

        # Apply rules
        for kpi in kpis:
            threshold = self.rules["kpi_thresholds"].get(kpi.kpi_key)
            if not threshold:
                continue

            # Check if KPI is below/above threshold
            is_issue = False
            severity = "info"

            if threshold.get("higher_is_better"):
                if kpi.value < threshold.get("critical_threshold", 0):
                    is_issue = True
                    severity = "critical"
                elif kpi.value < threshold.get("optimal_min", 0):
                    is_issue = True
                    severity = "warning"
            else:
                if kpi.value > threshold.get("critical_threshold", float("inf")):
                    is_issue = True
                    severity = "critical"
                elif kpi.value > threshold.get("optimal_max", float("inf")):
                    is_issue = True
                    severity = "warning"

            if is_issue:
                issues.append({
                    "kpi_key": kpi.kpi_key,
                    "current_value": kpi.value,
                    "threshold_value": threshold.get("critical_threshold") or threshold.get("optimal_min") or threshold.get("optimal_max"),
                    "severity": severity,
                    "trend": "unknown",
                    "priority": "high" if severity == "critical" else "medium"
                })

                if cell_id not in cells_requiring_attention:
                    cells_requiring_attention.append(cell_id)

        summary = f"Found {len(issues)} issues across {len(cells_requiring_attention)} cells"

        return {
            "issues": issues,
            "cells_requiring_attention": cells_requiring_attention,
            "summary": summary
        }

    def _get_recent_kpis(self, cell_id: str, hours: int = 24) -> List[Any]:
        """Get recent KPI measurements for a cell"""
        # Get latest measurement for each KPI type
        kpi_keys = [
            "network_access_success",
            "drop_rate",
            "handover_success_rate",
            "average_rsrp"
        ]

        kpis = []
        for kpi_key in kpi_keys:
            kpi = self.kpi_repo.get_latest_for_cell(cell_id, kpi_key)
            if kpi:
                kpis.append(kpi)

        return kpis
