"""
Secrets Management

Provides secure credential storage and retrieval.
"""

from liquid4g.infrastructure.secrets.manager import SecretsManager, get_secrets_manager

__all__ = ["SecretsManager", "get_secrets_manager"]
