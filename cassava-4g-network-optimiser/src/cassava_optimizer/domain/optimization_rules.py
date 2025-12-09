"""
Optimization rules engine for generating recommendations.

Contains domain knowledge about network optimization strategies and their
applicability conditions.
"""

from dataclasses import dataclass, field
from typing import Callable

from cassava_optimizer.domain.enums import OptimizationCategory, ParameterType
from cassava_optimizer.domain.models import KPIMetric, KPIScore, ParameterChange


@dataclass(frozen=True)
class OptimizationRule:
    """
    A rule that maps KPI conditions to optimization recommendations.
    
    Attributes:
        id: Unique rule identifier
        name: Human-readable rule name
        category: Optimization category
        description: Detailed description of what the rule addresses
        condition_description: Description of when this rule applies
        applicable_kpis: KPIs that trigger this rule
        parameter_types: Parameters that can be adjusted
        priority: Rule priority (1=highest, 5=lowest)
        risk_level: Risk level of applying this rule
        typical_improvement: Expected improvement range
    """
    
    id: str
    name: str
    category: OptimizationCategory
    description: str
    condition_description: str
    applicable_kpis: tuple[str, ...]
    parameter_types: tuple[ParameterType, ...]
    priority: int = 3
    risk_level: str = "low"
    typical_improvement: str = ""
    min_confidence: float = 0.7
    requires_validation: bool = True


# =============================================================================
# Core Optimization Rules
# =============================================================================

OPTIMIZATION_RULES: dict[str, OptimizationRule] = {
    # -------------------------------------------------------------------------
    # Coverage Optimization Rules
    # -------------------------------------------------------------------------
    "coverage_power_increase": OptimizationRule(
        id="coverage_power_increase",
        name="Increase TX Power for Coverage",
        category=OptimizationCategory.COVERAGE,
        description=(
            "Increase transmission power to extend cell coverage. "
            "Applicable when RSRP measurements indicate coverage gaps."
        ),
        condition_description="RRC setup success rate < 98% due to weak signal",
        applicable_kpis=("rrc_setup_success_rate", "cell_availability"),
        parameter_types=(ParameterType.TX_POWER,),
        priority=2,
        risk_level="low",
        typical_improvement="2-5% improvement in RRC success rate",
    ),
    
    "coverage_tilt_adjustment": OptimizationRule(
        id="coverage_tilt_adjustment",
        name="Adjust Antenna Tilt for Coverage",
        category=OptimizationCategory.COVERAGE,
        description=(
            "Modify electrical or mechanical antenna tilt to optimize coverage pattern. "
            "Downtilt reduces interference while uptilt extends coverage."
        ),
        condition_description="Coverage gaps or excessive interference detected",
        applicable_kpis=("rrc_setup_success_rate", "dl_throughput"),
        parameter_types=(ParameterType.ANTENNA_TILT,),
        priority=2,
        risk_level="medium",
        typical_improvement="3-8% improvement in coverage metrics",
    ),
    
    # -------------------------------------------------------------------------
    # Capacity Optimization Rules
    # -------------------------------------------------------------------------
    "capacity_prb_redistribution": OptimizationRule(
        id="capacity_prb_redistribution",
        name="PRB Utilization Balancing",
        category=OptimizationCategory.CAPACITY,
        description=(
            "Redistribute Physical Resource Block allocation to balance load "
            "across cells. Helps when some cells are congested while neighbors "
            "have spare capacity."
        ),
        condition_description="DL PRB utilization > 80% while neighbors < 50%",
        applicable_kpis=("dl_prb_utilization", "ul_prb_utilization", "dl_throughput"),
        parameter_types=(ParameterType.SCHEDULER, ParameterType.CIO),
        priority=2,
        risk_level="low",
        typical_improvement="10-20% better load distribution",
    ),
    
    "capacity_bandwidth_optimization": OptimizationRule(
        id="capacity_bandwidth_optimization",
        name="Bandwidth Configuration Optimization",
        category=OptimizationCategory.CAPACITY,
        description=(
            "Optimize channel bandwidth allocation based on traffic patterns "
            "and available spectrum resources."
        ),
        condition_description="Bandwidth not matched to traffic demand",
        applicable_kpis=("dl_prb_utilization", "spectral_efficiency"),
        parameter_types=(ParameterType.BANDWIDTH,),
        priority=3,
        risk_level="high",
        typical_improvement="Varies based on spectrum availability",
        requires_validation=True,
    ),
    
    # -------------------------------------------------------------------------
    # Quality Optimization Rules
    # -------------------------------------------------------------------------
    "quality_interference_mitigation": OptimizationRule(
        id="quality_interference_mitigation",
        name="Interference Mitigation",
        category=OptimizationCategory.INTERFERENCE,
        description=(
            "Reduce interference through PCI planning, power control, and "
            "ICIC (Inter-Cell Interference Coordination) parameter tuning."
        ),
        condition_description="High interference indicated by low SINR or mod3 PCI conflicts",
        applicable_kpis=("dl_throughput", "spectral_efficiency"),
        parameter_types=(ParameterType.PCI, ParameterType.TX_POWER),
        priority=1,
        risk_level="medium",
        typical_improvement="5-15% throughput improvement",
    ),
    
    "quality_erab_optimization": OptimizationRule(
        id="quality_erab_optimization",
        name="E-RAB Setup Optimization",
        category=OptimizationCategory.ACCESSIBILITY,
        description=(
            "Optimize E-RAB (E-UTRAN Radio Access Bearer) setup parameters "
            "to improve connection establishment success rate."
        ),
        condition_description="E-RAB setup success rate < 98%",
        applicable_kpis=("erab_setup_success_rate",),
        parameter_types=(ParameterType.PRACH_CONFIG,),
        priority=1,
        risk_level="low",
        typical_improvement="1-3% improvement in E-RAB success rate",
    ),
    
    # -------------------------------------------------------------------------
    # Handover Optimization Rules
    # -------------------------------------------------------------------------
    "handover_parameter_tuning": OptimizationRule(
        id="handover_parameter_tuning",
        name="Handover Parameter Optimization",
        category=OptimizationCategory.HANDOVER,
        description=(
            "Tune handover parameters including A3 offset, Time-to-Trigger (TTT), "
            "and hysteresis to reduce handover failures and ping-pong effects."
        ),
        condition_description="Handover success rate < 98% or excessive ping-pong",
        applicable_kpis=("handover_success_rate",),
        parameter_types=(
            ParameterType.A3_OFFSET,
            ParameterType.TTT,
            ParameterType.HANDOVER_MARGIN,
        ),
        priority=2,
        risk_level="medium",
        typical_improvement="2-5% improvement in handover success rate",
    ),
    
    "handover_neighbor_optimization": OptimizationRule(
        id="handover_neighbor_optimization",
        name="Neighbor Relation Optimization",
        category=OptimizationCategory.HANDOVER,
        description=(
            "Optimize neighbor cell relations by adding missing neighbors, "
            "removing unnecessary relations, and adjusting Cell Individual Offsets (CIO)."
        ),
        condition_description="Missing neighbors causing handover failures",
        applicable_kpis=("handover_success_rate",),
        parameter_types=(ParameterType.CIO,),
        priority=2,
        risk_level="low",
        typical_improvement="3-8% reduction in handover failures",
    ),
    
    # -------------------------------------------------------------------------
    # Throughput Optimization Rules
    # -------------------------------------------------------------------------
    "throughput_mimo_optimization": OptimizationRule(
        id="throughput_mimo_optimization",
        name="MIMO Mode Optimization",
        category=OptimizationCategory.THROUGHPUT,
        description=(
            "Optimize MIMO (Multiple Input Multiple Output) configuration "
            "based on radio conditions and user distribution."
        ),
        condition_description="Throughput below expected for available bandwidth",
        applicable_kpis=("dl_throughput", "ul_throughput", "spectral_efficiency"),
        parameter_types=(ParameterType.MIMO_MODE,),
        priority=3,
        risk_level="low",
        typical_improvement="10-30% throughput improvement",
    ),
    
    "throughput_scheduler_tuning": OptimizationRule(
        id="throughput_scheduler_tuning",
        name="Scheduler Algorithm Tuning",
        category=OptimizationCategory.THROUGHPUT,
        description=(
            "Adjust scheduler parameters to balance fairness and throughput "
            "based on traffic mix and QoS requirements."
        ),
        condition_description="Uneven throughput distribution among users",
        applicable_kpis=("dl_throughput", "latency"),
        parameter_types=(ParameterType.SCHEDULER,),
        priority=3,
        risk_level="low",
        typical_improvement="5-15% improvement in average throughput",
    ),
    
    # -------------------------------------------------------------------------
    # Retainability Optimization Rules
    # -------------------------------------------------------------------------
    "retainability_drop_analysis": OptimizationRule(
        id="retainability_drop_analysis",
        name="Call Drop Root Cause Analysis",
        category=OptimizationCategory.RETAINABILITY,
        description=(
            "Analyze and address root causes of call/session drops including "
            "coverage holes, interference, and handover issues."
        ),
        condition_description="VoLTE drop rate > 1% or data session drops elevated",
        applicable_kpis=("volte_drop_rate", "erab_setup_success_rate"),
        parameter_types=(ParameterType.TX_POWER, ParameterType.HANDOVER_MARGIN),
        priority=1,
        risk_level="medium",
        typical_improvement="20-50% reduction in drop rate",
    ),
}


def get_rule(rule_id: str) -> OptimizationRule | None:
    """Get an optimization rule by ID."""
    return OPTIMIZATION_RULES.get(rule_id)


def get_rules_by_category(category: OptimizationCategory) -> list[OptimizationRule]:
    """Get all rules for a specific optimization category."""
    return [rule for rule in OPTIMIZATION_RULES.values() if rule.category == category]


def get_rules_for_kpi(kpi_name: str) -> list[OptimizationRule]:
    """Get all rules applicable to a specific KPI."""
    return [
        rule for rule in OPTIMIZATION_RULES.values()
        if kpi_name in rule.applicable_kpis
    ]


def get_applicable_rules(kpi_score: KPIScore) -> list[OptimizationRule]:
    """
    Get rules applicable to the current KPI state.
    
    Analyzes KPI metrics and returns rules that could address issues.
    Rules are sorted by priority (1=highest).
    
    Args:
        kpi_score: Current KPI score with metrics
        
    Returns:
        List of applicable rules sorted by priority
    """
    applicable = []
    
    for metric in kpi_score.metrics:
        if not metric.is_healthy:
            rules = get_rules_for_kpi(metric.name)
            for rule in rules:
                if rule not in applicable:
                    applicable.append(rule)
    
    # Sort by priority
    return sorted(applicable, key=lambda r: r.priority)


# =============================================================================
# Parameter Adjustment Guidelines
# =============================================================================

@dataclass
class ParameterGuideline:
    """
    Guidelines for adjusting a specific parameter type.
    
    Defines safe ranges, step sizes, and constraints.
    """
    
    parameter: ParameterType
    min_value: float
    max_value: float
    typical_step: float
    unit: str
    description: str
    constraints: list[str] = field(default_factory=list)
    
    def is_valid_value(self, value: float) -> bool:
        """Check if a value is within valid range."""
        return self.min_value <= value <= self.max_value
    
    def suggest_adjustment(
        self,
        current: float,
        direction: str = "increase",
    ) -> float:
        """
        Suggest a safe adjustment value.
        
        Args:
            current: Current parameter value
            direction: "increase" or "decrease"
            
        Returns:
            Suggested new value within safe bounds
        """
        if direction == "increase":
            suggested = current + self.typical_step
            return min(suggested, self.max_value)
        else:
            suggested = current - self.typical_step
            return max(suggested, self.min_value)


PARAMETER_GUIDELINES: dict[ParameterType, ParameterGuideline] = {
    ParameterType.TX_POWER: ParameterGuideline(
        parameter=ParameterType.TX_POWER,
        min_value=30.0,
        max_value=46.0,
        typical_step=1.0,
        unit="dBm",
        description="eNodeB Reference Signal Power",
        constraints=[
            "Must comply with regulatory limits",
            "Consider interference to neighbors",
            "Power budget constraints apply",
        ],
    ),
    
    ParameterType.ANTENNA_TILT: ParameterGuideline(
        parameter=ParameterType.ANTENNA_TILT,
        min_value=0.0,
        max_value=15.0,
        typical_step=1.0,
        unit="degrees",
        description="Electrical antenna downtilt",
        constraints=[
            "Affects coverage and interference pattern",
            "Consider terrain and building heights",
            "Coordinate with physical tilt",
        ],
    ),
    
    ParameterType.A3_OFFSET: ParameterGuideline(
        parameter=ParameterType.A3_OFFSET,
        min_value=-6.0,
        max_value=6.0,
        typical_step=0.5,
        unit="dB",
        description="A3 event offset for handover trigger",
        constraints=[
            "Lower values = earlier handover",
            "Higher values = later handover",
            "Balance with hysteresis setting",
        ],
    ),
    
    ParameterType.TTT: ParameterGuideline(
        parameter=ParameterType.TTT,
        min_value=0,
        max_value=5120,
        typical_step=64,
        unit="ms",
        description="Time-to-Trigger for handover",
        constraints=[
            "Lower values reduce ping-pong but may cause premature HO",
            "Higher values improve stability but may cause drops",
            "Typical values: 64-256ms",
        ],
    ),
    
    ParameterType.CIO: ParameterGuideline(
        parameter=ParameterType.CIO,
        min_value=-24.0,
        max_value=24.0,
        typical_step=2.0,
        unit="dB",
        description="Cell Individual Offset for neighbor cells",
        constraints=[
            "Positive = prefer this neighbor",
            "Negative = avoid this neighbor",
            "Use sparingly to avoid oscillations",
        ],
    ),
    
    ParameterType.HANDOVER_MARGIN: ParameterGuideline(
        parameter=ParameterType.HANDOVER_MARGIN,
        min_value=0.0,
        max_value=10.0,
        typical_step=0.5,
        unit="dB",
        description="Hysteresis margin for handover decisions",
        constraints=[
            "Higher values prevent ping-pong",
            "Lower values enable faster handover",
            "Coordinate with TTT and A3 offset",
        ],
    ),
    
    ParameterType.PCI: ParameterGuideline(
        parameter=ParameterType.PCI,
        min_value=0,
        max_value=503,
        typical_step=1,
        unit="",
        description="Physical Cell Identity",
        constraints=[
            "Must be unique within interference range",
            "Avoid mod3 and mod6 conflicts with neighbors",
            "Plan with network-wide PCI scheme",
        ],
    ),
}


def get_parameter_guideline(param_type: ParameterType) -> ParameterGuideline | None:
    """Get guidelines for a parameter type."""
    return PARAMETER_GUIDELINES.get(param_type)


def validate_parameter_change(change: ParameterChange) -> tuple[bool, str]:
    """
    Validate a proposed parameter change against guidelines.
    
    Args:
        change: The proposed parameter change
        
    Returns:
        Tuple of (is_valid, reason)
    """
    guideline = get_parameter_guideline(change.parameter)
    
    if guideline is None:
        return True, "No guidelines defined for this parameter"
    
    if isinstance(change.recommended_value, (int, float)):
        if not guideline.is_valid_value(float(change.recommended_value)):
            return False, (
                f"Value {change.recommended_value} is outside valid range "
                f"[{guideline.min_value}, {guideline.max_value}]"
            )
    
    return True, "Parameter change is within guidelines"
