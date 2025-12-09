"""
Domain enumerations for type-safe status and category handling.
"""

from enum import Enum, auto


class AgentType(str, Enum):
    """Types of agents in the optimization workflow."""
    
    DATA_COLLECTOR = "data_collector"
    ANALYZER = "analyzer"
    STRATEGY_PLANNER = "strategy_planner"
    COMMANDER = "commander"
    VALIDATOR = "validator"
    REVIEWER = "reviewer"
    REPORTER = "reporter"
    
    @property
    def display_name(self) -> str:
        """Human-readable agent name."""
        return self.value.replace("_", " ").title()


class OptimizationStatus(str, Enum):
    """Status of an optimization workflow."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    
    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self in (self.COMPLETED, self.FAILED, self.CANCELLED)


class OptimizationType(str, Enum):
    """Types of optimization actions."""
    
    COVERAGE = "coverage"
    CAPACITY = "capacity"
    QUALITY = "quality"
    HANDOVER = "handover"
    POWER = "power"
    INTERFERENCE = "interference"


class KPICategory(str, Enum):
    """Categories of KPIs."""
    
    ACCESSIBILITY = "accessibility"
    RETAINABILITY = "retainability"
    INTEGRITY = "integrity"
    AVAILABILITY = "availability"
    MOBILITY = "mobility"
    UTILIZATION = "utilization"


class KPIStatus(str, Enum):
    """Status of a KPI measurement."""
    
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """Severity levels for issues and recommendations."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    
    @property
    def priority(self) -> int:
        """Numeric priority (lower = more urgent)."""
        return {
            self.CRITICAL: 1,
            self.HIGH: 2,
            self.MEDIUM: 3,
            self.LOW: 4,
        }[self]


class RiskLevel(str, Enum):
    """Risk level for optimization recommendations."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    
    @property
    def requires_approval(self) -> bool:
        """Check if this risk level requires manual approval."""
        return self in (self.HIGH, self.CRITICAL)


class SiteStatus(str, Enum):
    """Operational status of a site."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEGRADED = "degraded"


class CellStatus(str, Enum):
    """Operational status of a cell."""
    
    ACTIVE = "active"
    BLOCKED = "blocked"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


class RecommendationStatus(str, Enum):
    """Status of a recommendation."""
    
    PENDING = "pending"
    APPROVED = "approved"
    APPLIED = "applied"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


class KPITier(str, Enum):
    """KPI tier classification based on business impact."""
    
    FOUNDATION = "foundation"
    REVENUE_EXPERIENCE = "revenue_experience"
    EFFICIENCY = "efficiency"
    
    @property
    def weight(self) -> float:
        """Get the tier weight for scoring."""
        weights = {
            self.FOUNDATION: 0.25,
            self.REVENUE_EXPERIENCE: 0.50,
            self.EFFICIENCY: 0.25,
        }
        return weights[self]
    
    @property
    def display_name(self) -> str:
        """Human-readable tier name."""
        names = {
            self.FOUNDATION: "Foundation",
            self.REVENUE_EXPERIENCE: "Revenue & Experience",
            self.EFFICIENCY: "Efficiency",
        }
        return names[self]


class KPIDirection(str, Enum):
    """Indicates whether higher or lower values are better for a KPI."""
    
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    TARGET_RANGE = "target_range"
    INFORMATIONAL = "informational"


class KPISeverity(str, Enum):
    """Severity level for KPI threshold breaches."""
    
    CRITICAL = "critical"
    WARNING = "warning"
    TARGET = "target"
    HEALTHY = "healthy"
    
    @property
    def color(self) -> str:
        """Get the display color for this severity."""
        colors = {
            self.CRITICAL: "#FF4444",
            self.WARNING: "#FFAA00",
            self.TARGET: "#00CC00",
            self.HEALTHY: "#00FF00",
        }
        return colors[self]
    
    @property
    def priority(self) -> int:
        """Get numeric priority (lower = more urgent)."""
        priorities = {
            self.CRITICAL: 1,
            self.WARNING: 2,
            self.TARGET: 3,
            self.HEALTHY: 4,
        }
        return priorities[self]


class AgentStatus(str, Enum):
    """Status of an agent during workflow execution."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    
    @property
    def is_terminal(self) -> bool:
        """Check if this status represents a terminal state."""
        return self in (self.COMPLETED, self.FAILED, self.SKIPPED)
    
    @property
    def icon(self) -> str:
        """Get a display icon for the status."""
        icons = {
            self.PENDING: "⏳",
            self.RUNNING: "🔄",
            self.COMPLETED: "✅",
            self.FAILED: "❌",
            self.SKIPPED: "⏭️",
        }
        return icons[self]


class OptimizationCategory(str, Enum):
    """Categories of network optimization actions."""
    
    COVERAGE = "coverage"
    CAPACITY = "capacity"
    QUALITY = "quality"
    HANDOVER = "handover"
    POWER = "power"
    INTERFERENCE = "interference"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    ACCESSIBILITY = "accessibility"
    RETAINABILITY = "retainability"
    
    @property
    def description(self) -> str:
        """Get a description for this category."""
        descriptions = {
            self.COVERAGE: "RF coverage optimization including antenna tilt and power adjustments",
            self.CAPACITY: "Capacity enhancement through resource allocation and load balancing",
            self.QUALITY: "Signal quality improvements via interference management",
            self.HANDOVER: "Mobility and handover parameter optimization",
            self.POWER: "Power control and energy efficiency optimization",
            self.INTERFERENCE: "Interference detection and mitigation",
            self.THROUGHPUT: "Data throughput optimization",
            self.LATENCY: "Latency reduction strategies",
            self.ACCESSIBILITY: "Connection setup success improvements",
            self.RETAINABILITY: "Call and session drop prevention",
        }
        return descriptions[self]


class ParameterType(str, Enum):
    """Types of network parameters that can be optimized."""
    
    TX_POWER = "tx_power"
    ANTENNA_TILT = "antenna_tilt"
    PCI = "pci"
    TAC = "tac"
    EARFCN = "earfcn"
    BANDWIDTH = "bandwidth"
    MIMO_MODE = "mimo_mode"
    SCHEDULER = "scheduler"
    HANDOVER_MARGIN = "handover_margin"
    TTT = "time_to_trigger"
    A3_OFFSET = "a3_offset"
    CIO = "cell_individual_offset"
    QRXLEVMIN = "qrxlevmin"
    THRESHXHIGH = "thresh_x_high"
    THRESHXLOW = "thresh_x_low"
    PRACH_CONFIG = "prach_config"
    SRS_CONFIG = "srs_config"


class CommandExecutionStatus(str, Enum):
    """Status of MML command execution."""
    
    PENDING = "pending"
    VALIDATED = "validated"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    
    @property
    def is_final(self) -> bool:
        """Check if this is a final state."""
        return self in (self.SUCCESS, self.FAILED, self.ROLLED_BACK)


class CellState(str, Enum):
    """Operational state of a cell."""
    
    ACTIVE = "active"
    BLOCKED = "blocked"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class ConnectionState(str, Enum):
    """State of API connections."""
    
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    ERROR = "error"
