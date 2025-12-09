"""
KPI definitions and threshold management.

Loads KPI configuration from YAML and provides utilities for KPI calculations.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from cassava_optimizer.domain.enums import KPIDirection, KPITier
from cassava_optimizer.domain.exceptions import ConfigurationError
from cassava_optimizer.domain.models import KPIMetric, KPIScore, KPIThreshold


class KPIDefinition:
    """Definition of a single KPI with thresholds and metadata."""
    
    def __init__(
        self,
        name: str,
        display_name: str,
        tier: KPITier,
        weight: float,
        unit: str,
        direction: KPIDirection,
        thresholds: dict[str, float],
        description: str = "",
        target_range: dict[str, float] | None = None,
    ) -> None:
        self.name = name
        self.display_name = display_name
        self.tier = tier
        self.weight = weight
        self.unit = unit
        self.direction = direction
        self.thresholds = thresholds
        self.description = description
        self.target_range = target_range
    
    @property
    def threshold_model(self) -> KPIThreshold:
        """Get threshold as Pydantic model."""
        return KPIThreshold(
            critical=self.thresholds.get("critical", 0.0),
            warning=self.thresholds.get("warning", 0.0),
            target=self.thresholds.get("target", 0.0),
        )
    
    def create_metric(self, value: float, site_id: str = "", cell_id: str = "") -> KPIMetric:
        """Create a KPIMetric instance with this definition."""
        return KPIMetric(
            name=self.name,
            display_name=self.display_name,
            value=value,
            unit=self.unit,
            tier=self.tier,
            direction=self.direction,
            threshold=self.threshold_model,
            site_id=site_id,
            cell_id=cell_id,
        )
    
    def __repr__(self) -> str:
        return f"KPIDefinition(name={self.name!r}, tier={self.tier.value})"


class KPIRegistry:
    """
    Registry of all KPI definitions loaded from configuration.
    
    Provides lookup and scoring utilities.
    """
    
    def __init__(self, definitions: dict[str, KPIDefinition]) -> None:
        self._definitions = definitions
        self._by_tier: dict[KPITier, list[KPIDefinition]] = {tier: [] for tier in KPITier}
        
        for defn in definitions.values():
            self._by_tier[defn.tier].append(defn)
    
    def get(self, name: str) -> KPIDefinition | None:
        """Get a KPI definition by name."""
        return self._definitions.get(name)
    
    def get_by_tier(self, tier: KPITier) -> list[KPIDefinition]:
        """Get all KPI definitions for a tier."""
        return self._by_tier.get(tier, [])
    
    def all_definitions(self) -> list[KPIDefinition]:
        """Get all KPI definitions."""
        return list(self._definitions.values())
    
    @property
    def kpi_names(self) -> list[str]:
        """Get list of all KPI names."""
        return list(self._definitions.keys())
    
    def calculate_tier_score(
        self,
        tier: KPITier,
        metrics: list[KPIMetric],
    ) -> float:
        """
        Calculate weighted score for a tier.
        
        Args:
            tier: The KPI tier to score
            metrics: List of KPI metrics with values
            
        Returns:
            Weighted score between 0 and 1
        """
        tier_defs = self.get_by_tier(tier)
        if not tier_defs:
            return 0.0
        
        total_weight = sum(d.weight for d in tier_defs)
        weighted_sum = 0.0
        
        for defn in tier_defs:
            # Find matching metric
            metric = next((m for m in metrics if m.name == defn.name), None)
            if metric:
                weighted_sum += metric.normalized_score * defn.weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def calculate_overall_score(
        self,
        site_id: str,
        metrics: list[KPIMetric],
        cell_id: str = "",
    ) -> KPIScore:
        """
        Calculate overall KPI score with tier breakdown.
        
        Uses tier weights: Foundation 25%, Revenue/Experience 50%, Efficiency 25%
        Applies penalty if any critical KPIs exist.
        
        Args:
            site_id: Site identifier
            metrics: List of all KPI metrics
            cell_id: Optional cell identifier
            
        Returns:
            Complete KPI score with tier breakdown
        """
        # Calculate tier scores
        foundation_score = self.calculate_tier_score(KPITier.FOUNDATION, metrics)
        revenue_score = self.calculate_tier_score(KPITier.REVENUE_EXPERIENCE, metrics)
        efficiency_score = self.calculate_tier_score(KPITier.EFFICIENCY, metrics)
        
        # Count severity levels
        critical_count = sum(1 for m in metrics if m.severity.value == "critical")
        warning_count = sum(1 for m in metrics if m.severity.value == "warning")
        
        # Calculate weighted overall score
        overall = (
            foundation_score * KPITier.FOUNDATION.weight
            + revenue_score * KPITier.REVENUE_EXPERIENCE.weight
            + efficiency_score * KPITier.EFFICIENCY.weight
        )
        
        # Apply penalty for critical KPIs (50% reduction)
        if critical_count > 0:
            overall *= 0.5
        
        # Foundation gate: if foundation < 90%, cap overall at 70%
        if foundation_score < 0.90:
            overall = min(overall, 0.70)
        
        return KPIScore(
            site_id=site_id,
            cell_id=cell_id,
            overall_score=overall,
            foundation_score=foundation_score,
            revenue_experience_score=revenue_score,
            efficiency_score=efficiency_score,
            metrics=tuple(metrics),
            critical_count=critical_count,
            warning_count=warning_count,
        )


def _parse_direction(direction_str: str) -> KPIDirection:
    """Parse direction string to enum."""
    mapping = {
        "higher_is_better": KPIDirection.HIGHER_IS_BETTER,
        "lower_is_better": KPIDirection.LOWER_IS_BETTER,
        "target_range": KPIDirection.TARGET_RANGE,
        "informational": KPIDirection.INFORMATIONAL,
    }
    return mapping.get(direction_str, KPIDirection.INFORMATIONAL)


def _parse_tier_kpis(
    tier: KPITier,
    tier_data: dict[str, Any],
) -> list[KPIDefinition]:
    """Parse KPI definitions from a tier configuration block."""
    definitions = []
    kpis_data = tier_data.get("kpis", {})
    
    for kpi_name, kpi_config in kpis_data.items():
        thresholds = kpi_config.get("threshold", {})
        definitions.append(
            KPIDefinition(
                name=kpi_name,
                display_name=kpi_config.get("name", kpi_name),
                tier=tier,
                weight=kpi_config.get("weight", 0.1),
                unit=kpi_config.get("unit", ""),
                direction=_parse_direction(kpi_config.get("direction", "higher_is_better")),
                thresholds=thresholds,
                description=kpi_config.get("description", ""),
                target_range=kpi_config.get("target_range"),
            )
        )
    
    return definitions


def load_kpi_config(config_path: Path | None = None) -> KPIRegistry:
    """
    Load KPI configuration from YAML file.
    
    Args:
        config_path: Path to kpi_weights.yaml. If None, uses default location.
        
    Returns:
        KPIRegistry with all KPI definitions
        
    Raises:
        ConfigurationError: If config file cannot be loaded or parsed
    """
    if config_path is None:
        # Default to package config
        config_path = Path(__file__).parent.parent / "config" / "kpi_weights.yaml"
    
    if not config_path.exists():
        raise ConfigurationError(
            f"KPI configuration file not found: {config_path}",
            details={"path": str(config_path)},
        )
    
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(
            f"Failed to parse KPI configuration: {e}",
            details={"path": str(config_path)},
            cause=e,
        )
    
    # Parse all tiers
    definitions: dict[str, KPIDefinition] = {}
    
    tier_mapping = {
        "foundation": KPITier.FOUNDATION,
        "revenue_experience": KPITier.REVENUE_EXPERIENCE,
        "efficiency": KPITier.EFFICIENCY,
    }
    
    for tier_key, tier_enum in tier_mapping.items():
        tier_data = config.get(tier_key, {})
        tier_defs = _parse_tier_kpis(tier_enum, tier_data)
        for defn in tier_defs:
            definitions[defn.name] = defn
    
    return KPIRegistry(definitions)


@lru_cache
def get_kpi_registry() -> KPIRegistry:
    """
    Get cached KPI registry.
    
    Returns:
        KPIRegistry with all KPI definitions loaded from configuration
    """
    return load_kpi_config()


# Convenience functions for common operations

def get_kpi_definition(name: str) -> KPIDefinition | None:
    """Get a single KPI definition by name."""
    return get_kpi_registry().get(name)


def get_all_kpi_names() -> list[str]:
    """Get list of all configured KPI names."""
    return get_kpi_registry().kpi_names


def calculate_kpi_score(
    site_id: str,
    metrics: list[KPIMetric],
    cell_id: str = "",
) -> KPIScore:
    """Calculate overall KPI score for a site or cell."""
    return get_kpi_registry().calculate_overall_score(site_id, metrics, cell_id)
