"""
Analyzer Agent - Second stage of the optimization pipeline.

Responsible for analyzing collected KPI data to identify performance
issues, correlations, and root causes.
"""

from typing import Any

import structlog

from cassava_optimizer.agents.base import AgentContext, AgentExecutionError, BaseAgent
from cassava_optimizer.domain.enums import AgentType, KPICategory, KPIStatus, Severity
from cassava_optimizer.domain.kpi_definitions import get_kpi_definition, get_kpi_registry
from cassava_optimizer.infrastructure.llm_client import NVIDIANIMClient

logger = structlog.get_logger(__name__)


class AnalyzerAgent(BaseAgent):
    """
    Agent responsible for analyzing network performance data.
    
    Analysis includes:
    - KPI threshold violations
    - Trend analysis from historical data
    - Correlation between related KPIs
    - Root cause identification
    - Health scoring
    
    Uses LLM for intelligent correlation and root cause analysis.
    """
    
    def __init__(self, llm_client: NVIDIANIMClient) -> None:
        """
        Initialize the analyzer agent.
        
        Args:
            llm_client: LLM client for intelligent analysis
        """
        super().__init__()
        self._llm = llm_client
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.ANALYZER
    
    async def _validate_preconditions(self, context: AgentContext) -> None:
        """Validate that data collection has been completed."""
        await super()._validate_preconditions(context)
        
        if not context.collected_data:
            raise AgentExecutionError(
                "No collected data found - run Data Collector first",
                agent_type=self.agent_type,
                step="precondition_check",
            )
        
        if "current_kpis" not in context.collected_data:
            raise AgentExecutionError(
                "No KPI data found in collected data",
                agent_type=self.agent_type,
                step="precondition_check",
            )
    
    async def _execute(self, context: AgentContext) -> dict[str, Any]:
        """
        Analyze collected data to identify issues and opportunities.
        
        Returns:
            Dictionary containing:
            - health_score: Overall site health (0-100)
            - kpi_analysis: Per-KPI analysis results
            - issues: List of identified issues
            - correlations: Identified KPI correlations
            - root_causes: Potential root causes
            - category_scores: Health scores by KPI category
        """
        collected_data = context.collected_data
        current_kpis = collected_data.get("current_kpis", {})
        historical_kpis = collected_data.get("historical_kpis", {})
        site_info = collected_data.get("site", {})
        
        self._log.info(
            "Starting analysis",
            site_id=context.site_id,
            kpi_count=len(current_kpis),
        )
        
        # 1. Analyze individual KPIs against thresholds
        kpi_analysis = self._analyze_kpis(current_kpis, historical_kpis)
        
        # 2. Identify issues (threshold violations)
        issues = self._identify_issues(kpi_analysis)
        
        # 3. Calculate health scores
        health_score, category_scores = self._calculate_health_scores(kpi_analysis)
        
        # 4. Use LLM for intelligent analysis if there are issues
        llm_analysis = {}
        if issues:
            llm_analysis = await self._llm_analysis(
                current_kpis,
                site_info,
                issues,
            )
        
        # Build output
        output = {
            "health_score": health_score,
            "category_scores": category_scores,
            "kpi_analysis": kpi_analysis,
            "issues": issues,
            "correlations": llm_analysis.get("correlations", []),
            "root_causes": llm_analysis.get("root_causes", []),
            "recommended_focus_areas": llm_analysis.get("recommended_focus_areas", []),
            "analysis_metadata": {
                "total_kpis_analyzed": len(kpi_analysis),
                "issues_found": len(issues),
                "critical_issues": sum(1 for i in issues if i.get("severity") == "critical"),
            },
        }
        
        # Store in context for next agents
        context.analysis_results = output
        
        self._log.info(
            "Analysis complete",
            health_score=health_score,
            issues_found=len(issues),
        )
        
        return output
    
    def _analyze_kpis(
        self,
        current_kpis: dict[str, dict[str, Any]],
        historical_kpis: dict[str, list[dict[str, Any]]],
    ) -> dict[str, dict[str, Any]]:
        """
        Analyze each KPI against thresholds and historical trends.
        
        Returns:
            Dictionary of KPI analysis results
        """
        analysis = {}
        
        for kpi_name, kpi_data in current_kpis.items():
            kpi_def = get_kpi_definition(kpi_name)
            
            if not kpi_def:
                self._log.debug(f"Unknown KPI: {kpi_name}")
                continue
            
            current_value = kpi_data.get("value", 0)
            
            # Determine status
            status = self._determine_kpi_status(kpi_def, current_value)
            
            # Calculate trend from historical data
            history = historical_kpis.get(kpi_name, [])
            trend = self._calculate_trend(history)
            
            # Calculate deviation from target
            deviation = self._calculate_deviation(kpi_def, current_value)
            
            analysis[kpi_name] = {
                "value": current_value,
                "unit": kpi_def.unit,
                "category": kpi_def.category.value,
                "status": status.value,
                "target_min": kpi_def.target_min,
                "target_max": kpi_def.target_max,
                "critical_threshold": kpi_def.critical_threshold,
                "deviation_percent": deviation,
                "trend": trend,
                "trend_direction": self._get_trend_direction(history),
                "weight": kpi_def.weight,
            }
        
        return analysis
    
    def _determine_kpi_status(self, kpi_def: Any, value: float) -> KPIStatus:
        """Determine the status of a KPI value."""
        # Check critical threshold first
        if kpi_def.critical_threshold is not None:
            if kpi_def.higher_is_better:
                if value < kpi_def.critical_threshold:
                    return KPIStatus.CRITICAL
            else:
                if value > kpi_def.critical_threshold:
                    return KPIStatus.CRITICAL
        
        # Check target range
        in_target = True
        if kpi_def.target_min is not None and value < kpi_def.target_min:
            in_target = False
        if kpi_def.target_max is not None and value > kpi_def.target_max:
            in_target = False
        
        if in_target:
            return KPIStatus.HEALTHY
        
        # Not in target but not critical = warning
        return KPIStatus.WARNING
    
    def _calculate_deviation(self, kpi_def: Any, value: float) -> float:
        """Calculate percentage deviation from target."""
        if kpi_def.higher_is_better and kpi_def.target_min is not None:
            if kpi_def.target_min > 0:
                return ((value - kpi_def.target_min) / kpi_def.target_min) * 100
        elif not kpi_def.higher_is_better and kpi_def.target_max is not None:
            if kpi_def.target_max > 0:
                return ((kpi_def.target_max - value) / kpi_def.target_max) * 100
        
        return 0.0
    
    def _calculate_trend(self, history: list[dict[str, Any]]) -> str:
        """Calculate trend from historical data."""
        if len(history) < 2:
            return "insufficient_data"
        
        # Sort by timestamp and get values
        sorted_history = sorted(history, key=lambda x: x.get("timestamp", ""))
        values = [h.get("value", 0) for h in sorted_history]
        
        # Simple trend calculation using linear regression slope
        n = len(values)
        sum_x = sum(range(n))
        sum_y = sum(values)
        sum_xy = sum(i * v for i, v in enumerate(values))
        sum_x2 = sum(i * i for i in range(n))
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return "stable"
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # Determine trend based on slope magnitude
        avg_value = sum_y / n if n > 0 else 1
        relative_slope = (slope / avg_value) * 100 if avg_value != 0 else 0
        
        if relative_slope > 2:
            return "improving"
        elif relative_slope < -2:
            return "degrading"
        else:
            return "stable"
    
    def _get_trend_direction(self, history: list[dict[str, Any]]) -> str:
        """Get simple trend direction."""
        if len(history) < 2:
            return "unknown"
        
        sorted_history = sorted(history, key=lambda x: x.get("timestamp", ""))
        first = sorted_history[0].get("value", 0)
        last = sorted_history[-1].get("value", 0)
        
        if last > first * 1.02:  # 2% threshold
            return "up"
        elif last < first * 0.98:
            return "down"
        else:
            return "flat"
    
    def _identify_issues(
        self,
        kpi_analysis: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Identify issues from KPI analysis.
        
        Returns:
            List of identified issues sorted by severity
        """
        issues = []
        
        for kpi_name, analysis in kpi_analysis.items():
            status = analysis.get("status", "healthy")
            
            if status in ["critical", "warning"]:
                severity = Severity.CRITICAL if status == "critical" else Severity.WARNING
                
                issue = {
                    "kpi_name": kpi_name,
                    "severity": severity.value,
                    "current_value": analysis.get("value"),
                    "target_min": analysis.get("target_min"),
                    "target_max": analysis.get("target_max"),
                    "deviation_percent": analysis.get("deviation_percent"),
                    "category": analysis.get("category"),
                    "trend": analysis.get("trend"),
                    "description": self._generate_issue_description(kpi_name, analysis),
                    "impact": self._assess_impact(kpi_name, analysis),
                }
                
                issues.append(issue)
        
        # Sort by severity (critical first) then by deviation
        issues.sort(
            key=lambda x: (
                0 if x["severity"] == "critical" else 1,
                -abs(x.get("deviation_percent", 0)),
            )
        )
        
        return issues
    
    def _generate_issue_description(
        self,
        kpi_name: str,
        analysis: dict[str, Any],
    ) -> str:
        """Generate human-readable issue description."""
        kpi_def = get_kpi_definition(kpi_name)
        value = analysis.get("value", 0)
        unit = analysis.get("unit", "")
        
        if analysis.get("status") == "critical":
            return f"{kpi_name} is critically low at {value:.2f}{unit}, below threshold"
        else:
            target_min = analysis.get("target_min")
            target_max = analysis.get("target_max")
            
            if target_min and value < target_min:
                return f"{kpi_name} at {value:.2f}{unit} is below target of {target_min}{unit}"
            elif target_max and value > target_max:
                return f"{kpi_name} at {value:.2f}{unit} exceeds target of {target_max}{unit}"
            
            return f"{kpi_name} at {value:.2f}{unit} requires attention"
    
    def _assess_impact(
        self,
        kpi_name: str,
        analysis: dict[str, Any],
    ) -> str:
        """Assess business impact of the issue."""
        category = analysis.get("category", "")
        weight = analysis.get("weight", 1.0)
        
        if category == KPICategory.REVENUE.value:
            if weight >= 3.0:
                return "Direct revenue impact - prioritize immediately"
            return "Revenue affecting - address promptly"
        elif category == KPICategory.EXPERIENCE.value:
            return "User experience degradation - affects customer satisfaction"
        elif category == KPICategory.EFFICIENCY.value:
            return "Resource utilization issue - may affect capacity"
        elif category == KPICategory.FOUNDATION.value:
            return "Foundation metric - may cause cascading issues"
        
        return "Performance degradation detected"
    
    def _calculate_health_scores(
        self,
        kpi_analysis: dict[str, dict[str, Any]],
    ) -> tuple[float, dict[str, float]]:
        """
        Calculate overall and per-category health scores.
        
        Returns:
            Tuple of (overall_score, category_scores)
        """
        category_scores: dict[str, list[float]] = {
            cat.value: [] for cat in KPICategory
        }
        
        for kpi_name, analysis in kpi_analysis.items():
            category = analysis.get("category", KPICategory.FOUNDATION.value)
            status = analysis.get("status", "healthy")
            weight = analysis.get("weight", 1.0)
            
            # Calculate KPI score (0-100)
            if status == "healthy":
                score = 100.0
            elif status == "warning":
                # Score based on deviation
                deviation = abs(analysis.get("deviation_percent", 0))
                score = max(50, 100 - deviation)
            else:  # critical
                deviation = abs(analysis.get("deviation_percent", 0))
                score = max(0, 50 - deviation)
            
            # Weight the score
            weighted_score = score * weight
            category_scores[category].append(weighted_score)
        
        # Calculate per-category averages
        category_averages = {}
        for category, scores in category_scores.items():
            if scores:
                category_averages[category] = sum(scores) / len(scores)
            else:
                category_averages[category] = 100.0  # No data = assume healthy
        
        # Calculate overall score using category weights
        # Foundation: 25%, Revenue: 25%, Experience: 25%, Efficiency: 25%
        category_weights = {
            KPICategory.FOUNDATION.value: 0.25,
            KPICategory.REVENUE.value: 0.25,
            KPICategory.EXPERIENCE.value: 0.25,
            KPICategory.EFFICIENCY.value: 0.25,
        }
        
        overall_score = sum(
            category_averages.get(cat, 100) * weight
            for cat, weight in category_weights.items()
        )
        
        return round(overall_score, 1), {k: round(v, 1) for k, v in category_averages.items()}
    
    async def _llm_analysis(
        self,
        current_kpis: dict[str, dict[str, Any]],
        site_info: dict[str, Any],
        issues: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Use LLM for intelligent correlation and root cause analysis.
        
        Returns:
            Dictionary with correlations and root causes
        """
        self._log.info("Running LLM-based analysis")
        
        try:
            # Prepare KPI data for LLM
            kpi_data = {
                name: {
                    "value": data.get("value"),
                    "unit": data.get("unit"),
                    "status": data.get("status"),
                }
                for name, data in current_kpis.items()
            }
            
            result = await self._llm.analyze_kpis(kpi_data, site_info)
            
            return {
                "correlations": result.get("correlations", []),
                "root_causes": result.get("root_causes", []),
                "recommended_focus_areas": result.get("recommended_focus_areas", []),
            }
            
        except Exception as e:
            self._log.warning(
                "LLM analysis failed, continuing with rule-based analysis",
                error=str(e),
            )
            return {}
