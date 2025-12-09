"""
Strategy Planner Agent - Third stage of the optimization pipeline.

Responsible for generating optimization recommendations based on
analysis results, using domain rules and LLM intelligence.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

import structlog

from cassava_optimizer.agents.base import AgentContext, AgentExecutionError, BaseAgent
from cassava_optimizer.domain.enums import AgentType, OptimizationType, Severity
from cassava_optimizer.domain.models import OptimizationRecommendation
from cassava_optimizer.domain.optimization_rules import (
    OPTIMIZATION_RULES,
    get_applicable_rules,
)
from cassava_optimizer.infrastructure.llm_client import NVIDIANIMClient

logger = structlog.get_logger(__name__)


class StrategyPlannerAgent(BaseAgent):
    """
    Agent responsible for generating optimization strategies.
    
    Strategy generation includes:
    - Rule-based recommendations from optimization rules
    - LLM-enhanced recommendations with context
    - Priority scoring and risk assessment
    - MML command generation
    
    Output is a prioritized list of recommendations.
    """
    
    # Parameters available for optimization
    AVAILABLE_PARAMETERS = [
        "tx_power",
        "electrical_tilt",
        "handover_threshold",
        "ho_margin",
        "qrxlevmin",
        "qqualmin",
        "a3_offset",
        "a3_time_to_trigger",
        "a2_threshold",
        "cio",
        "prach_root_sequence",
        "target_bler",
        "cqi_offset",
        "pcfich_power_offset",
        "pdcch_power_offset",
        "load_balancing_threshold",
    ]
    
    def __init__(self, llm_client: NVIDIANIMClient) -> None:
        """
        Initialize the strategy planner agent.
        
        Args:
            llm_client: LLM client for intelligent recommendations
        """
        super().__init__()
        self._llm = llm_client
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.STRATEGY_PLANNER
    
    async def _validate_preconditions(self, context: AgentContext) -> None:
        """Validate that analysis has been completed."""
        await super()._validate_preconditions(context)
        
        if not context.analysis_results:
            raise AgentExecutionError(
                "No analysis results found - run Analyzer first",
                agent_type=self.agent_type,
                step="precondition_check",
            )
        
        if not context.analysis_results.get("issues"):
            # No issues to address - this is actually OK
            self._log.info("No issues found in analysis - no optimizations needed")
    
    async def _execute(self, context: AgentContext) -> dict[str, Any]:
        """
        Generate optimization recommendations based on analysis.
        
        Returns:
            Dictionary containing:
            - recommendations: List of prioritized recommendations
            - summary: High-level summary of proposed changes
            - risk_assessment: Overall risk level
        """
        analysis = context.analysis_results
        collected_data = context.collected_data
        
        issues = analysis.get("issues", [])
        site_info = collected_data.get("site", {})
        current_params = collected_data.get("parameters", {})
        
        self._log.info(
            "Starting strategy planning",
            site_id=context.site_id,
            issues_count=len(issues),
        )
        
        if not issues:
            # No issues = no recommendations
            output = {
                "recommendations": [],
                "summary": "No performance issues detected - no optimizations required",
                "risk_assessment": "none",
                "total_expected_improvement": 0,
            }
            context.recommendations = []
            return output
        
        # 1. Generate rule-based recommendations
        rule_recommendations = self._generate_rule_based_recommendations(
            issues, current_params, context
        )
        
        # 2. Enhance with LLM recommendations
        llm_recommendations = await self._generate_llm_recommendations(
            analysis, site_info, current_params
        )
        
        # 3. Merge and deduplicate recommendations
        all_recommendations = self._merge_recommendations(
            rule_recommendations, llm_recommendations
        )
        
        # 4. Prioritize and limit recommendations
        prioritized = self._prioritize_recommendations(all_recommendations)
        
        # 5. Calculate overall risk
        risk_assessment = self._assess_overall_risk(prioritized)
        
        # 6. Generate summary
        summary = self._generate_summary(prioritized, issues)
        
        output = {
            "recommendations": [r.model_dump() if hasattr(r, 'model_dump') else r for r in prioritized],
            "summary": summary,
            "risk_assessment": risk_assessment,
            "total_recommendations": len(prioritized),
            "high_priority_count": sum(1 for r in prioritized if self._get_priority(r) <= 3),
        }
        
        # Store in context
        context.recommendations = prioritized
        
        self._log.info(
            "Strategy planning complete",
            recommendations=len(prioritized),
            risk=risk_assessment,
        )
        
        return output
    
    def _generate_rule_based_recommendations(
        self,
        issues: list[dict[str, Any]],
        current_params: dict[str, dict[str, Any]],
        context: AgentContext,
    ) -> list[dict[str, Any]]:
        """
        Generate recommendations based on predefined optimization rules.
        
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        for issue in issues:
            kpi_name = issue.get("kpi_name", "")
            
            # Find applicable rules
            applicable_rules = get_applicable_rules(kpi_name)
            
            for rule in applicable_rules:
                # Check if trigger conditions are met
                if not self._check_trigger(rule, issue):
                    continue
                
                # Generate recommendation from rule
                rec = self._rule_to_recommendation(
                    rule, issue, current_params, context
                )
                
                if rec:
                    recommendations.append(rec)
        
        self._log.debug(
            "Rule-based recommendations generated",
            count=len(recommendations),
        )
        
        return recommendations
    
    def _check_trigger(
        self,
        rule: Any,
        issue: dict[str, Any],
    ) -> bool:
        """Check if rule trigger conditions are met."""
        trigger = rule.trigger
        
        # Check KPI name match
        if trigger.kpi_name and trigger.kpi_name != issue.get("kpi_name"):
            return False
        
        # Check severity
        issue_severity = Severity(issue.get("severity", "info"))
        if trigger.min_severity:
            severity_order = {Severity.INFO: 0, Severity.WARNING: 1, Severity.CRITICAL: 2}
            if severity_order.get(issue_severity, 0) < severity_order.get(trigger.min_severity, 0):
                return False
        
        return True
    
    def _rule_to_recommendation(
        self,
        rule: Any,
        issue: dict[str, Any],
        current_params: dict[str, dict[str, Any]],
        context: AgentContext,
    ) -> dict[str, Any] | None:
        """Convert optimization rule to recommendation."""
        actions = rule.actions
        
        if not actions:
            return None
        
        parameters = []
        mml_commands = []
        
        for action in actions:
            param_name = action.parameter
            
            # Get current value
            current_value = current_params.get(param_name, {}).get("value")
            
            # Calculate recommended value
            recommended_value = self._calculate_recommended_value(
                action, current_value
            )
            
            if recommended_value is not None:
                parameters.append({
                    "name": param_name,
                    "current": current_value,
                    "recommended": recommended_value,
                    "unit": action.unit or "",
                    "change_type": action.adjustment_type,
                })
                
                # Generate MML command
                mml_cmd = self._generate_mml_command(
                    param_name, recommended_value, context.site_id
                )
                if mml_cmd:
                    mml_commands.append(mml_cmd)
        
        if not parameters:
            return None
        
        return {
            "id": str(uuid4()),
            "rule_id": rule.rule_id,
            "priority": rule.priority,
            "title": rule.name,
            "description": rule.description,
            "target_kpis": [issue.get("kpi_name")],
            "expected_improvement": {
                issue.get("kpi_name"): f"{rule.expected_improvement}%" if rule.expected_improvement else "improvement expected"
            },
            "risk_level": rule.risk_level.value,
            "parameters": parameters,
            "mml_commands": mml_commands,
            "validation_criteria": f"Verify {issue.get('kpi_name')} improves after change",
            "source": "rule",
        }
    
    def _calculate_recommended_value(
        self,
        action: Any,
        current_value: Any,
    ) -> Any:
        """Calculate the recommended parameter value."""
        if current_value is None and action.default_value is not None:
            return action.default_value
        
        if current_value is None:
            return None
        
        try:
            current = float(current_value)
        except (ValueError, TypeError):
            return action.default_value
        
        if action.adjustment_type == "increase":
            if action.adjustment_value:
                new_value = current + action.adjustment_value
            else:
                new_value = current * 1.1  # Default 10% increase
            
            # Respect max bound
            if action.max_value is not None:
                new_value = min(new_value, action.max_value)
            
            return round(new_value, 2)
        
        elif action.adjustment_type == "decrease":
            if action.adjustment_value:
                new_value = current - action.adjustment_value
            else:
                new_value = current * 0.9  # Default 10% decrease
            
            # Respect min bound
            if action.min_value is not None:
                new_value = max(new_value, action.min_value)
            
            return round(new_value, 2)
        
        elif action.adjustment_type == "set":
            return action.default_value
        
        return None
    
    def _generate_mml_command(
        self,
        param_name: str,
        value: Any,
        site_id: str,
    ) -> str | None:
        """Generate MML command for parameter change."""
        from cassava_optimizer.domain.mml_commands import get_mml_template
        
        template = get_mml_template(param_name)
        if template:
            try:
                return template.format(value=value, site_id=site_id)
            except KeyError:
                return f"MOD {param_name.upper()}:{param_name}={value};"
        
        return f"MOD CELL:{param_name}={value};"
    
    async def _generate_llm_recommendations(
        self,
        analysis: dict[str, Any],
        site_info: dict[str, Any],
        current_params: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Generate recommendations using LLM for intelligent analysis.
        
        Returns:
            List of LLM-generated recommendations
        """
        self._log.info("Generating LLM-based recommendations")
        
        try:
            recommendations = await self._llm.generate_recommendations(
                analysis=analysis,
                site_context=site_info,
                available_parameters=self.AVAILABLE_PARAMETERS,
            )
            
            # Mark source as LLM
            for rec in recommendations:
                rec["source"] = "llm"
            
            return recommendations
            
        except Exception as e:
            self._log.warning(
                "LLM recommendation generation failed",
                error=str(e),
            )
            return []
    
    def _merge_recommendations(
        self,
        rule_recs: list[dict[str, Any]],
        llm_recs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Merge and deduplicate recommendations from different sources.
        
        Rule-based recommendations take precedence for same parameters.
        """
        merged = {}
        
        # Add rule-based first (higher trust)
        for rec in rule_recs:
            key = self._get_rec_key(rec)
            merged[key] = rec
        
        # Add LLM recommendations if not duplicate
        for rec in llm_recs:
            key = self._get_rec_key(rec)
            if key not in merged:
                merged[key] = rec
            else:
                # Merge additional info from LLM
                existing = merged[key]
                if not existing.get("description"):
                    existing["description"] = rec.get("description", "")
        
        return list(merged.values())
    
    def _get_rec_key(self, rec: dict[str, Any]) -> str:
        """Generate unique key for recommendation deduplication."""
        params = rec.get("parameters", [])
        param_names = sorted([p.get("name", "") for p in params])
        target_kpis = sorted(rec.get("target_kpis", []))
        return f"{'-'.join(param_names)}:{'-'.join(target_kpis)}"
    
    def _prioritize_recommendations(
        self,
        recommendations: list[dict[str, Any]],
        max_count: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Prioritize and limit recommendations.
        
        Prioritization factors:
        - Priority score (lower = higher priority)
        - Risk level (lower risk preferred)
        - Expected improvement
        """
        def priority_key(rec: dict[str, Any]) -> tuple:
            priority = rec.get("priority", 5)
            risk_order = {"low": 0, "medium": 1, "high": 2}
            risk = risk_order.get(rec.get("risk_level", "medium"), 1)
            
            # Extract improvement percentage if available
            improvements = rec.get("expected_improvement", {})
            if improvements:
                first_value = list(improvements.values())[0]
                if isinstance(first_value, str) and "%" in first_value:
                    try:
                        improvement = float(first_value.replace("%", ""))
                    except ValueError:
                        improvement = 0
                else:
                    improvement = 0
            else:
                improvement = 0
            
            return (priority, risk, -improvement)
        
        sorted_recs = sorted(recommendations, key=priority_key)
        return sorted_recs[:max_count]
    
    def _get_priority(self, rec: dict[str, Any]) -> int:
        """Get priority value from recommendation."""
        return rec.get("priority", 5)
    
    def _assess_overall_risk(
        self,
        recommendations: list[dict[str, Any]],
    ) -> str:
        """Assess overall risk level of proposed changes."""
        if not recommendations:
            return "none"
        
        risk_levels = [rec.get("risk_level", "medium") for rec in recommendations]
        
        if "high" in risk_levels:
            high_count = risk_levels.count("high")
            if high_count > len(recommendations) / 2:
                return "high"
            return "medium"
        
        if "medium" in risk_levels:
            return "medium"
        
        return "low"
    
    def _generate_summary(
        self,
        recommendations: list[dict[str, Any]],
        issues: list[dict[str, Any]],
    ) -> str:
        """Generate human-readable summary of recommendations."""
        if not recommendations:
            return "No optimizations required - network is performing within targets."
        
        issue_count = len(issues)
        rec_count = len(recommendations)
        
        # Count high priority
        high_priority = sum(1 for r in recommendations if r.get("priority", 5) <= 3)
        
        # List affected KPIs
        affected_kpis = set()
        for rec in recommendations:
            affected_kpis.update(rec.get("target_kpis", []))
        
        summary_parts = [
            f"Identified {issue_count} performance issues.",
            f"Generated {rec_count} optimization recommendations.",
        ]
        
        if high_priority:
            summary_parts.append(f"{high_priority} are high priority.")
        
        if affected_kpis:
            summary_parts.append(f"Targeting KPIs: {', '.join(list(affected_kpis)[:5])}")
        
        return " ".join(summary_parts)
