"""Domain layer for Cassava 4G Network Optimiser."""

from cassava_optimizer.domain.enums import (
    AgentStatus,
    CommandExecutionStatus,
    KPIDirection,
    KPISeverity,
    KPITier,
    OptimizationCategory,
    ParameterType,
)
from cassava_optimizer.domain.exceptions import (
    CassavaOptimiserError,
    ConfigurationError,
    DatabaseError,
    HuaweiAPIError,
    KPIAnalysisError,
    LLMError,
    MMLCommandError,
    NetworkError,
    ValidationError,
)
from cassava_optimizer.domain.models import (
    Cell,
    CommandResult,
    HistoricalRecord,
    KPIMetric,
    KPIScore,
    MMLCommand,
    OptimizationRecommendation,
    ParameterChange,
    Site,
)

__all__ = [
    # Enums
    "AgentStatus",
    "CommandExecutionStatus",
    "KPIDirection",
    "KPISeverity",
    "KPITier",
    "OptimizationCategory",
    "ParameterType",
    # Exceptions
    "CassavaOptimiserError",
    "ConfigurationError",
    "DatabaseError",
    "HuaweiAPIError",
    "KPIAnalysisError",
    "LLMError",
    "MMLCommandError",
    "NetworkError",
    "ValidationError",
    # Models
    "Cell",
    "CommandResult",
    "HistoricalRecord",
    "KPIMetric",
    "KPIScore",
    "MMLCommand",
    "OptimizationRecommendation",
    "ParameterChange",
    "Site",
]
