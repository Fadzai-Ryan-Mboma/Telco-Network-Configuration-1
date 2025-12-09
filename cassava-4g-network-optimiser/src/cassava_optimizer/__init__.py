"""
Cassava 4G Network Optimiser

AI-powered 4G LTE network optimization for Huawei eNodeB infrastructure.
Built on NVIDIA NIM and LangGraph for intelligent, agentic optimization workflows.
"""

__version__ = "1.0.0"
__author__ = "Cassava Technologies"
__email__ = "ai@cassavatech.com"

from cassava_optimizer.config.settings import get_settings
from cassava_optimizer.workflow.orchestrator import NetworkOptimizer

__all__ = [
    "__version__",
    "get_settings",
    "NetworkOptimizer",
]
