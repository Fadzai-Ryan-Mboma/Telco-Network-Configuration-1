"""
Reviewer Agent - Final stage of the optimization pipeline.

Responsible for post-execution review, comparing before/after KPIs,
and generating optimization reports.
"""

from datetime import datetime
from typing import Any

import structlog

from cassava_optimizer.agents.base import AgentContext, AgentExecutionError, BaseAgent
from cassava_optimizer.domain.enums import AgentType, OptimizationStatus
from cassava_optimizer.infrastructure.huawei_client import HuaweiMAEClient
from cassava_optimizer.infrastructure.llm_client import NVIDIANIMClient
from cassava_optimizer.infrastructure.repository import NetworkRepository

logger = structlog.get_logger(__name__)


class ReviewerAgent(BaseAgent):
    """
    Agent responsible for reviewing optimization results.
    
    Review process:
    1. Collect post-optimization KPIs
    2. Compare with pre-optimization baseline
    3. Calculate improvement metrics
    4. Generate optimization report
    5. Recommend follow-up actions
    
    Uses LLM for intelligent effectiveness assessment.
    """
    
    # Minimum wait time after changes before measuring (seconds)
    MIN_STABILIZATION_TIME = 60
    
    def __init__(
        self,
        huawei_client: HuaweiMAEClient,
        llm_client: NVIDIANIMClient,
        repository: NetworkRepository,
    ) -> None:
        """
        Initialize the reviewer agent.
        
        Args:
            huawei_client: Async client for Huawei MAE API
            llm_client: LLM client for effectiveness assessment
            repository: Database repository for recording results
        """
        super().__init__()
        self._huawei = huawei_client
        self._llm = llm_client
        self._repo = repository
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.REVIEWER
    
    async def _validate_preconditions(self, context: AgentContext) -> None:
        """Validate that execution has completed."""
        await super()._validate_preconditions(context)
        
        # Reviewer can run even without applied commands (to generate report)
        if not context.collected_data:
            raise AgentExecutionError(
                "No collected data found - cannot compare results",
                agent_type=self.agent_type,
                step="precondition_check",
            )
    
    async def _execute(self, context: AgentContext) -> dict[str, Any]:
        """
        Review optimization results and generate report.
        
        Returns:
            Dictionary containing:
            - before_kpis: Pre-optimization KPI values
            - after_kpis: Post-optimization KPI values
            - kpi_changes: Per-KPI comparison
            - effectiveness_score: Overall effectiveness (0-100)
            - successful_changes: Changes that improved KPIs
            - unsuccessful_changes: Changes that didn't help
            - rollback_recommended: Whether rollback is suggested
            - report: Human-readable optimization report
            - next_steps: Recommended follow-up actions
        """
        site_id = context.site_id
        applied_commands = context.applied_commands
        collected_data = context.collected_data
        analysis_results = context.analysis_results
        
        self._log.info(
            "Starting review",
            site_id=site_id,
            commands_applied=len(applied_commands),
        )
        
        # 1. Get before KPIs from collected data
        before_kpis = collected_data.get("current_kpis", {})
        
        # 2. Collect after KPIs (if commands were applied)
        if applied_commands:
            after_kpis = await self._collect_after_kpis(site_id)
        else:
            # No changes applied - use same as before
            after_kpis = before_kpis
        
        # 3. Compare KPIs
        kpi_changes = self._compare_kpis(before_kpis, after_kpis)
        
        # 4. Calculate effectiveness score
        effectiveness_score = self._calculate_effectiveness_score(
            kpi_changes, analysis_results.get("issues", [])
        )
        
        # 5. Categorize changes
        successful, unsuccessful = self._categorize_changes(
            applied_commands, kpi_changes
        )
        
        # 6. Determine if rollback is recommended
        rollback_recommended = self._should_recommend_rollback(
            effectiveness_score, kpi_changes
        )
        
        # 7. Use LLM for intelligent validation
        llm_validation = {}
        if applied_commands:
            llm_validation = await self._llm_validation(
                before_kpis, after_kpis, applied_commands
            )
        
        # 8. Generate report
        report = self._generate_report(
            context, kpi_changes, effectiveness_score,
            successful, unsuccessful, rollback_recommended
        )
        
        # 9. Determine next steps
        next_steps = self._determine_next_steps(
            effectiveness_score, kpi_changes, rollback_recommended
        )
        
        # 10. Store validation results
        context.validation_results = {
            "effectiveness_score": effectiveness_score,
            "kpi_changes": kpi_changes,
            "rollback_recommended": rollback_recommended,
        }
        
        # 11. Record optimization completion
        await self._record_optimization_result(context, effectiveness_score)
        
        output = {
            "before_kpis": {k: v.get("value") for k, v in before_kpis.items()},
            "after_kpis": after_kpis,
            "kpi_changes": kpi_changes,
            "effectiveness_score": effectiveness_score,
            "successful_changes": successful,
            "unsuccessful_changes": unsuccessful,
            "rollback_recommended": rollback_recommended,
            "llm_validation": llm_validation,
            "report": report,
            "next_steps": next_steps,
        }
        
        self._log.info(
            "Review complete",
            effectiveness_score=effectiveness_score,
            rollback_recommended=rollback_recommended,
        )
        
        return output
    
    async def _collect_after_kpis(self, site_id: str) -> dict[str, float]:
        """Collect KPI values after optimization."""
        self._log.debug("Collecting post-optimization KPIs", site_id=site_id)
        
        try:
            kpi_metrics = await self._huawei.get_kpi_data(site_id)
            
            return {
                metric.definition.name: metric.value
                for metric in kpi_metrics
            }
            
        except Exception as e:
            self._log.warning(
                "Failed to collect post-optimization KPIs",
                error=str(e),
            )
            return {}
    
    def _compare_kpis(
        self,
        before: dict[str, dict[str, Any]],
        after: dict[str, float],
    ) -> list[dict[str, Any]]:
        """
        Compare before and after KPI values.
        
        Returns:
            List of KPI change records
        """
        changes = []
        
        for kpi_name, before_data in before.items():
            before_value = before_data.get("value", 0)
            after_value = after.get(kpi_name, before_value)
            
            # Calculate change
            if before_value != 0:
                change_percent = ((after_value - before_value) / abs(before_value)) * 100
            else:
                change_percent = 0 if after_value == 0 else 100
            
            # Determine if improved based on KPI direction
            higher_is_better = self._is_higher_better(kpi_name)
            improved = (change_percent > 0) if higher_is_better else (change_percent < 0)
            
            changes.append({
                "kpi": kpi_name,
                "before": round(before_value, 2),
                "after": round(after_value, 2),
                "change_percent": round(change_percent, 2),
                "improved": improved,
                "significant": abs(change_percent) >= 2,  # 2% threshold
                "category": before_data.get("category", "unknown"),
            })
        
        return changes
    
    def _is_higher_better(self, kpi_name: str) -> bool:
        """Determine if higher values are better for a KPI."""
        # KPIs where higher is better
        higher_better = {
            "rrc_success_rate", "erab_success_rate", "volte_success_rate",
            "cssr", "cdr", "dl_throughput", "ul_throughput",
            "availability", "service_integrity", "retainability",
        }
        
        kpi_lower = kpi_name.lower()
        return any(hb in kpi_lower for hb in higher_better)
    
    def _calculate_effectiveness_score(
        self,
        kpi_changes: list[dict[str, Any]],
        original_issues: list[dict[str, Any]],
    ) -> float:
        """
        Calculate overall effectiveness score (0-100).
        
        Score is based on:
        - How many issues were addressed
        - Magnitude of improvements
        - Whether any KPIs degraded
        """
        if not kpi_changes:
            return 0.0
        
        # Weight factors
        improvement_weight = 0.6
        degradation_penalty = 0.3
        issue_resolution_weight = 0.1
        
        # Calculate improvement score
        significant_improvements = [
            c for c in kpi_changes
            if c.get("improved") and c.get("significant")
        ]
        improvement_ratio = len(significant_improvements) / len(kpi_changes) if kpi_changes else 0
        improvement_score = improvement_ratio * 100
        
        # Calculate degradation penalty
        degradations = [
            c for c in kpi_changes
            if not c.get("improved") and c.get("significant")
        ]
        degradation_ratio = len(degradations) / len(kpi_changes) if kpi_changes else 0
        degradation_score = (1 - degradation_ratio) * 100
        
        # Calculate issue resolution
        issue_kpis = {i.get("kpi_name") for i in original_issues}
        resolved_issues = [
            c for c in kpi_changes
            if c.get("kpi") in issue_kpis and c.get("improved")
        ]
        resolution_ratio = len(resolved_issues) / len(issue_kpis) if issue_kpis else 1
        resolution_score = resolution_ratio * 100
        
        # Weighted total
        total_score = (
            improvement_score * improvement_weight +
            degradation_score * degradation_penalty +
            resolution_score * issue_resolution_weight
        )
        
        return round(min(100, max(0, total_score)), 1)
    
    def _categorize_changes(
        self,
        applied_commands: list[dict[str, Any]],
        kpi_changes: list[dict[str, Any]],
    ) -> tuple[list[str], list[str]]:
        """
        Categorize applied changes as successful or unsuccessful.
        
        Returns:
            Tuple of (successful_descriptions, unsuccessful_descriptions)
        """
        successful = []
        unsuccessful = []
        
        # Group KPI changes by improvement status
        improved_kpis = {
            c["kpi"] for c in kpi_changes
            if c.get("improved") and c.get("significant")
        }
        degraded_kpis = {
            c["kpi"] for c in kpi_changes
            if not c.get("improved") and c.get("significant")
        }
        
        # Map commands to outcomes
        for cmd in applied_commands:
            rec_id = cmd.get("rec_id", "")
            command = cmd.get("command", "")[:50]
            
            # Simple heuristic - in production would need better tracking
            if improved_kpis:
                successful.append(f"Command executed successfully (rec: {rec_id[:8]})")
            else:
                unsuccessful.append(f"Command may not have achieved desired effect (rec: {rec_id[:8]})")
        
        return successful, unsuccessful
    
    def _should_recommend_rollback(
        self,
        effectiveness_score: float,
        kpi_changes: list[dict[str, Any]],
    ) -> bool:
        """Determine if rollback should be recommended."""
        # Rollback if effectiveness is very low
        if effectiveness_score < 20:
            return True
        
        # Rollback if critical KPIs degraded significantly
        critical_categories = {"revenue", "experience"}
        critical_degradations = [
            c for c in kpi_changes
            if c.get("category") in critical_categories
            and not c.get("improved")
            and abs(c.get("change_percent", 0)) >= 5  # 5% degradation
        ]
        
        if critical_degradations:
            return True
        
        return False
    
    async def _llm_validation(
        self,
        before_kpis: dict[str, dict[str, Any]],
        after_kpis: dict[str, float],
        applied_changes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Use LLM for intelligent effectiveness validation."""
        self._log.info("Running LLM-based validation")
        
        try:
            before_simple = {k: v.get("value") for k, v in before_kpis.items()}
            
            result = await self._llm.validate_changes(
                before_kpis=before_simple,
                after_kpis=after_kpis,
                applied_changes=applied_changes,
            )
            
            return result
            
        except Exception as e:
            self._log.warning(
                "LLM validation failed",
                error=str(e),
            )
            return {}
    
    def _generate_report(
        self,
        context: AgentContext,
        kpi_changes: list[dict[str, Any]],
        effectiveness_score: float,
        successful: list[str],
        unsuccessful: list[str],
        rollback_recommended: bool,
    ) -> str:
        """Generate human-readable optimization report."""
        lines = [
            "=" * 60,
            "NETWORK OPTIMIZATION REPORT",
            "=" * 60,
            "",
            f"Site: {context.site_name} ({context.site_id})",
            f"Optimization ID: {context.optimization_id}",
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "-" * 60,
            "SUMMARY",
            "-" * 60,
            f"Effectiveness Score: {effectiveness_score}/100",
            f"Commands Applied: {len(context.applied_commands)}",
            f"Rollback Recommended: {'Yes' if rollback_recommended else 'No'}",
            "",
        ]
        
        # KPI Changes section
        lines.extend([
            "-" * 60,
            "KPI CHANGES",
            "-" * 60,
        ])
        
        improved = [c for c in kpi_changes if c.get("improved") and c.get("significant")]
        degraded = [c for c in kpi_changes if not c.get("improved") and c.get("significant")]
        unchanged = [c for c in kpi_changes if not c.get("significant")]
        
        if improved:
            lines.append("\nImproved KPIs:")
            for c in improved:
                lines.append(
                    f"  ✓ {c['kpi']}: {c['before']} → {c['after']} ({c['change_percent']:+.1f}%)"
                )
        
        if degraded:
            lines.append("\nDegraded KPIs:")
            for c in degraded:
                lines.append(
                    f"  ✗ {c['kpi']}: {c['before']} → {c['after']} ({c['change_percent']:+.1f}%)"
                )
        
        if unchanged:
            lines.append(f"\nUnchanged KPIs: {len(unchanged)}")
        
        # Recommendations
        lines.extend([
            "",
            "-" * 60,
            "NEXT STEPS",
            "-" * 60,
        ])
        
        if rollback_recommended:
            lines.append("⚠️  ROLLBACK RECOMMENDED - Performance degradation detected")
        elif effectiveness_score >= 80:
            lines.append("✓ Optimization successful - Continue monitoring")
        elif effectiveness_score >= 50:
            lines.append("⚡ Partial improvement - Consider additional optimization")
        else:
            lines.append("⚠️  Limited improvement - Review strategy and retry")
        
        lines.extend(["", "=" * 60])
        
        return "\n".join(lines)
    
    def _determine_next_steps(
        self,
        effectiveness_score: float,
        kpi_changes: list[dict[str, Any]],
        rollback_recommended: bool,
    ) -> list[str]:
        """Determine recommended next steps."""
        steps = []
        
        if rollback_recommended:
            steps.append("Initiate rollback to restore previous configuration")
            steps.append("Analyze why optimization was ineffective")
            steps.append("Review parameter bounds and constraints")
        elif effectiveness_score >= 80:
            steps.append("Continue monitoring KPIs for 24-48 hours")
            steps.append("Document successful optimization for future reference")
            steps.append("Consider applying similar changes to similar sites")
        elif effectiveness_score >= 50:
            steps.append("Monitor KPIs closely for the next 24 hours")
            steps.append("Identify remaining underperforming KPIs")
            steps.append("Plan follow-up optimization cycle")
        else:
            steps.append("Review analysis results and recommendations")
            steps.append("Consider manual review of network conditions")
            steps.append("Check for external factors affecting performance")
        
        return steps
    
    async def _record_optimization_result(
        self,
        context: AgentContext,
        effectiveness_score: float,
    ) -> None:
        """Record optimization result in database."""
        try:
            from cassava_optimizer.domain.models import OptimizationHistory
            
            site = await self._repo.get_site_by_name(context.site_id)
            
            if site:
                history = OptimizationHistory(
                    site_id=site.site_id,
                    optimization_type="review_complete",
                    recommendation_id=context.optimization_id,
                    mml_command="",
                    status=OptimizationStatus.APPLIED if effectiveness_score >= 50 else OptimizationStatus.FAILED,
                    result_summary=f"Effectiveness: {effectiveness_score}/100",
                    applied_by="system",
                )
                
                await self._repo.save_optimization_history(history)
                
        except Exception as e:
            self._log.warning(
                "Failed to record optimization result",
                error=str(e),
            )
