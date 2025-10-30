"""
Liquid Zimbabwe 4G Network Optimizer
====================================

Enterprise-grade 4G network optimization platform with intelligent hybrid agents.

Features:
- LLM-powered optimization with rule-based fallback
- 6-stage agentic workflow
- Single unified database
- Production monitoring and security
"""

__version__ = "2.0.0"
__author__ = "Cassava AI Team"
__license__ = "Proprietary"

from liquid4g.core.config import get_settings
from liquid4g.core.logging import get_logger

__all__ = ["__version__", "get_settings", "get_logger"]
