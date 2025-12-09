"""Infrastructure layer for external integrations."""

from cassava_optimizer.infrastructure.database import (
    async_session_factory,
    get_async_engine,
    init_database,
)
from cassava_optimizer.infrastructure.huawei_client import HuaweiMAEClient
from cassava_optimizer.infrastructure.llm_client import NVIDIANIMClient
from cassava_optimizer.infrastructure.repository import NetworkRepository

# Alias for backwards compatibility
LLMClient = NVIDIANIMClient

__all__ = [
    "async_session_factory",
    "get_async_engine",
    "init_database",
    "HuaweiMAEClient",
    "LLMClient",
    "NVIDIANIMClient",
    "NetworkRepository",
]
