"""
Query Parser Service for Natural Language Intent Extraction.

Parses user queries to extract optimization intent, target KPIs,
and relevant parameters for the LangGraph workflow.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class OptimizationIntent(Enum):
    """Types of optimization intents."""
    
    IMPROVE_KPI = "improve_kpi"
    FIX_ISSUE = "fix_issue"
    ANALYZE = "analyze"
    CONFIGURE = "configure"
    DIAGNOSE = "diagnose"
    GENERAL = "general"


class KPICategory(Enum):
    """KPI categories for optimization."""
    
    ACCESSIBILITY = "accessibility"  # RACH, RRC Setup
    RETAINABILITY = "retainability"  # Call Drop, E-RAB Drop
    MOBILITY = "mobility"  # Handover
    THROUGHPUT = "throughput"  # DL/UL Throughput
    QUALITY = "quality"  # BLER, SINR
    CAPACITY = "capacity"  # PRB, CCE Usage
    UNKNOWN = "unknown"


@dataclass
class ParsedQuery:
    """Result of parsing a user query."""
    
    original_query: str
    intent: OptimizationIntent
    kpi_categories: list[KPICategory]
    target_kpis: list[str]
    cell_ids: list[str]
    parameters_mentioned: list[str]
    severity: str  # low, medium, high, critical
    confidence: float  # 0.0 to 1.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for workflow state."""
        return {
            "original_query": self.original_query,
            "intent": self.intent.value,
            "kpi_categories": [c.value for c in self.kpi_categories],
            "target_kpis": self.target_kpis,
            "cell_ids": self.cell_ids,
            "parameters_mentioned": self.parameters_mentioned,
            "severity": self.severity,
            "confidence": self.confidence,
        }


class QueryParser:
    """
    Parses natural language queries into structured optimization requests.
    
    Uses pattern matching and keyword extraction for fast, deterministic parsing.
    Falls back to LLM for complex queries if needed.
    """
    
    # KPI keyword mappings
    KPI_KEYWORDS = {
        # Accessibility
        "rach": ("rach_success_rate", KPICategory.ACCESSIBILITY),
        "random access": ("rach_success_rate", KPICategory.ACCESSIBILITY),
        "rrc": ("rrc_setup_success_rate", KPICategory.ACCESSIBILITY),
        "rrc setup": ("rrc_setup_success_rate", KPICategory.ACCESSIBILITY),
        "e-rab": ("erab_setup_success_rate", KPICategory.ACCESSIBILITY),
        "erab": ("erab_setup_success_rate", KPICategory.ACCESSIBILITY),
        "call setup": ("call_setup_success_rate", KPICategory.ACCESSIBILITY),
        "accessibility": ("accessibility_rate", KPICategory.ACCESSIBILITY),
        
        # Retainability
        "call drop": ("call_drop_rate", KPICategory.RETAINABILITY),
        "drop rate": ("call_drop_rate", KPICategory.RETAINABILITY),
        "e-rab drop": ("erab_drop_rate", KPICategory.RETAINABILITY),
        "retainability": ("retainability_rate", KPICategory.RETAINABILITY),
        
        # Mobility
        "handover": ("handover_success_rate", KPICategory.MOBILITY),
        "ho success": ("handover_success_rate", KPICategory.MOBILITY),
        "mobility": ("handover_success_rate", KPICategory.MOBILITY),
        "ping pong": ("handover_success_rate", KPICategory.MOBILITY),
        
        # Throughput
        "throughput": ("throughput", KPICategory.THROUGHPUT),
        "dl throughput": ("dl_throughput", KPICategory.THROUGHPUT),
        "ul throughput": ("ul_throughput", KPICategory.THROUGHPUT),
        "downlink": ("dl_throughput", KPICategory.THROUGHPUT),
        "uplink": ("ul_throughput", KPICategory.THROUGHPUT),
        "speed": ("throughput", KPICategory.THROUGHPUT),
        "data rate": ("throughput", KPICategory.THROUGHPUT),
        
        # Quality
        "bler": ("bler", KPICategory.QUALITY),
        "dl bler": ("dl_bler", KPICategory.QUALITY),
        "ul bler": ("ul_bler", KPICategory.QUALITY),
        "ibler": ("bler", KPICategory.QUALITY),
        "block error": ("bler", KPICategory.QUALITY),
        "sinr": ("sinr", KPICategory.QUALITY),
        "cqi": ("cqi", KPICategory.QUALITY),
        "quality": ("quality", KPICategory.QUALITY),
        
        # Capacity
        "pdcch": ("pdcch_cce_usage", KPICategory.CAPACITY),
        "cce": ("pdcch_cce_usage", KPICategory.CAPACITY),
        "prb": ("prb_utilization", KPICategory.CAPACITY),
        "pucch": ("pucch_usage", KPICategory.CAPACITY),
        "congestion": ("pdcch_cce_usage", KPICategory.CAPACITY),
        "capacity": ("capacity", KPICategory.CAPACITY),
        "load": ("prb_utilization", KPICategory.CAPACITY),
    }
    
    # Intent keywords
    INTENT_KEYWORDS = {
        OptimizationIntent.IMPROVE_KPI: [
            "improve", "increase", "boost", "enhance", "optimize",
            "better", "higher", "maximize", "raise",
        ],
        OptimizationIntent.FIX_ISSUE: [
            "fix", "solve", "resolve", "address", "reduce",
            "lower", "decrease", "minimize", "stop", "prevent",
        ],
        OptimizationIntent.ANALYZE: [
            "analyze", "check", "review", "examine", "investigate",
            "look at", "assess", "evaluate", "inspect",
        ],
        OptimizationIntent.CONFIGURE: [
            "configure", "set", "change", "modify", "adjust",
            "update", "tune", "tweak",
        ],
        OptimizationIntent.DIAGNOSE: [
            "diagnose", "troubleshoot", "debug", "find problem",
            "root cause", "why", "what's wrong",
        ],
    }
    
    # Parameter keywords
    PARAMETER_KEYWORDS = {
        "power": ["power", "tx power", "transmit power", "rs power", "reference signal"],
        "tilt": ["tilt", "downtilt", "electrical tilt", "mechanical tilt"],
        "handover": ["cio", "offset", "hysteresis", "time to trigger", "ttt"],
        "rach": ["preamble", "power ramping", "target power"],
        "scheduler": ["cfi", "scheduler", "prb", "allocation"],
    }
    
    # Severity keywords
    SEVERITY_KEYWORDS = {
        "critical": ["critical", "urgent", "severe", "emergency", "asap", "immediately"],
        "high": ["high", "serious", "bad", "poor", "failing", "degraded"],
        "medium": ["medium", "moderate", "some", "occasional"],
        "low": ["low", "minor", "slight", "small"],
    }
    
    def __init__(self) -> None:
        """Initialize the query parser."""
        logger.info("QueryParser initialized")
    
    def parse(self, query: str) -> ParsedQuery:
        """
        Parse a natural language query into structured format.
        
        Args:
            query: User's natural language query
            
        Returns:
            ParsedQuery with extracted intent and parameters
        """
        query_lower = query.lower()
        
        # Extract intent
        intent = self._extract_intent(query_lower)
        
        # Extract KPIs and categories
        kpi_categories, target_kpis = self._extract_kpis(query_lower)
        
        # Extract cell IDs
        cell_ids = self._extract_cell_ids(query)
        
        # Extract mentioned parameters
        parameters = self._extract_parameters(query_lower)
        
        # Determine severity
        severity = self._extract_severity(query_lower)
        
        # Calculate confidence based on matches found
        confidence = self._calculate_confidence(
            intent, kpi_categories, target_kpis, parameters
        )
        
        parsed = ParsedQuery(
            original_query=query,
            intent=intent,
            kpi_categories=kpi_categories,
            target_kpis=target_kpis,
            cell_ids=cell_ids,
            parameters_mentioned=parameters,
            severity=severity,
            confidence=confidence,
        )
        
        logger.info(
            f"Parsed query: intent={intent.value}, "
            f"kpis={target_kpis}, confidence={confidence:.2f}"
        )
        
        return parsed
    
    def _extract_intent(self, query: str) -> OptimizationIntent:
        """Extract the optimization intent from query."""
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return intent
        return OptimizationIntent.GENERAL
    
    def _extract_kpis(self, query: str) -> tuple[list[KPICategory], list[str]]:
        """Extract KPI categories and specific KPIs from query."""
        categories = set()
        kpis = set()
        
        for keyword, (kpi_name, category) in self.KPI_KEYWORDS.items():
            if keyword in query:
                categories.add(category)
                kpis.add(kpi_name)
        
        return list(categories) or [KPICategory.UNKNOWN], list(kpis)
    
    def _extract_cell_ids(self, query: str) -> list[str]:
        """Extract cell IDs from query."""
        cell_ids = []
        
        # Pattern for "cell X" or "cells X, Y, Z"
        cell_pattern = r'cells?\s*(\d+(?:\s*[-,]\s*\d+)*)'
        matches = re.findall(cell_pattern, query, re.IGNORECASE)
        
        for match in matches:
            # Handle ranges like "1-3" and lists like "1, 2, 3"
            if '-' in match:
                parts = match.split('-')
                if len(parts) == 2:
                    try:
                        start, end = int(parts[0].strip()), int(parts[1].strip())
                        cell_ids.extend([str(i) for i in range(start, end + 1)])
                    except ValueError:
                        pass
            else:
                # Split by comma and extract numbers
                for part in match.split(','):
                    num = re.search(r'\d+', part.strip())
                    if num:
                        cell_ids.append(num.group())
        
        # Also look for "LOCALCELLID=X" pattern
        localcell_pattern = r'localcellid\s*=?\s*(\d+)'
        localcell_matches = re.findall(localcell_pattern, query, re.IGNORECASE)
        cell_ids.extend(localcell_matches)
        
        return list(set(cell_ids))
    
    def _extract_parameters(self, query: str) -> list[str]:
        """Extract mentioned parameters from query."""
        parameters = []
        
        for param_type, keywords in self.PARAMETER_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    parameters.append(param_type)
                    break
        
        return list(set(parameters))
    
    def _extract_severity(self, query: str) -> str:
        """Extract severity level from query."""
        for severity, keywords in self.SEVERITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return severity
        return "medium"  # Default severity
    
    def _calculate_confidence(
        self,
        intent: OptimizationIntent,
        categories: list[KPICategory],
        kpis: list[str],
        parameters: list[str],
    ) -> float:
        """Calculate parsing confidence score."""
        score = 0.3  # Base score
        
        # Intent found
        if intent != OptimizationIntent.GENERAL:
            score += 0.2
        
        # KPIs identified
        if kpis:
            score += 0.2
        
        # Categories identified (non-unknown)
        if categories and KPICategory.UNKNOWN not in categories:
            score += 0.15
        
        # Parameters mentioned
        if parameters:
            score += 0.15
        
        return min(score, 1.0)


# =============================================================================
# Singleton Instance
# =============================================================================

_parser: QueryParser | None = None


def get_query_parser() -> QueryParser:
    """Get singleton query parser instance."""
    global _parser
    if _parser is None:
        _parser = QueryParser()
    return _parser


def parse_optimization_query(query: str) -> ParsedQuery:
    """Convenience function to parse a query."""
    return get_query_parser().parse(query)
