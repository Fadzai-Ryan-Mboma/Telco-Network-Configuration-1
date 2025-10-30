"""
External API Clients

Provides clients for external APIs (Huawei, etc.).
"""

from liquid4g.infrastructure.api.huawei_client import HuaweiAPIClient, get_huawei_client

__all__ = ["HuaweiAPIClient", "get_huawei_client"]
