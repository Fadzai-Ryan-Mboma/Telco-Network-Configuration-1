"""
Secrets Manager

Multi-backend secrets management supporting:
- Environment variables
- Docker secrets
- HashiCorp Vault (future)
- AWS Secrets Manager (future)
"""

import os
from pathlib import Path
from typing import Optional, Dict
from enum import Enum

from liquid4g.core.config import get_settings
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import ConfigurationError

logger = get_logger(__name__)


class SecretBackend(str, Enum):
    """Supported secret backends"""

    ENVIRONMENT = "environment"
    DOCKER = "docker"
    VAULT = "vault"
    AWS = "aws"


class SecretsManager:
    """
    Secrets manager with multi-backend support

    Backends are tried in order:
    1. Docker secrets (/run/secrets/)
    2. Environment variables
    3. Vault (if configured)
    4. AWS Secrets Manager (if configured)
    """

    def __init__(self):
        """Initialize secrets manager"""
        self.settings = get_settings()
        self.docker_secrets_dir = Path("/run/secrets")
        self._cache: Dict[str, str] = {}

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret value

        Args:
            key: Secret key
            default: Default value if not found

        Returns:
            Optional[str]: Secret value or default

        Raises:
            ConfigurationError: If secret is required but not found
        """
        # Check cache first
        if key in self._cache:
            return self._cache[key]

        # Try Docker secrets
        secret = self._get_from_docker(key)
        if secret:
            self._cache[key] = secret
            return secret

        # Try environment variables
        secret = self._get_from_environment(key)
        if secret:
            self._cache[key] = secret
            return secret

        # Try Vault (if configured)
        if self._is_vault_enabled():
            secret = self._get_from_vault(key)
            if secret:
                self._cache[key] = secret
                return secret

        # Try AWS (if configured)
        if self._is_aws_enabled():
            secret = self._get_from_aws(key)
            if secret:
                self._cache[key] = secret
                return secret

        # Return default or None
        if default is not None:
            return default

        logger.warning(f"Secret not found: {key}")
        return None

    def get_required_secret(self, key: str) -> str:
        """
        Get required secret (raises if not found)

        Args:
            key: Secret key

        Returns:
            str: Secret value

        Raises:
            ConfigurationError: If secret not found
        """
        secret = self.get_secret(key)
        if secret is None:
            raise ConfigurationError(
                f"Required secret not found: {key}. "
                f"Please set it via environment variable or Docker secret."
            )
        return secret

    def _get_from_docker(self, key: str) -> Optional[str]:
        """
        Get secret from Docker secrets

        Docker secrets are stored in /run/secrets/<secret_name>

        Args:
            key: Secret key

        Returns:
            Optional[str]: Secret value or None
        """
        secret_file = self.docker_secrets_dir / key.lower()

        if secret_file.exists():
            try:
                with open(secret_file, "r") as f:
                    secret = f.read().strip()
                logger.debug(f"Retrieved secret from Docker: {key}")
                return secret
            except Exception as e:
                logger.error(f"Failed to read Docker secret {key}: {e}")
                return None

        return None

    def _get_from_environment(self, key: str) -> Optional[str]:
        """
        Get secret from environment variable

        Args:
            key: Secret key (will be uppercased)

        Returns:
            Optional[str]: Secret value or None
        """
        env_key = key.upper()
        secret = os.getenv(env_key)

        if secret:
            logger.debug(f"Retrieved secret from environment: {key}")
            return secret

        return None

    def _is_vault_enabled(self) -> bool:
        """Check if Vault backend is configured"""
        return hasattr(self.settings, "vault_enabled") and self.settings.vault_enabled

    def _get_from_vault(self, key: str) -> Optional[str]:
        """
        Get secret from HashiCorp Vault

        TODO: Implement Vault integration

        Args:
            key: Secret key

        Returns:
            Optional[str]: Secret value or None
        """
        logger.warning("Vault backend not yet implemented")
        return None

    def _is_aws_enabled(self) -> bool:
        """Check if AWS Secrets Manager is configured"""
        return hasattr(self.settings, "aws_secrets_enabled") and self.settings.aws_secrets_enabled

    def _get_from_aws(self, key: str) -> Optional[str]:
        """
        Get secret from AWS Secrets Manager

        TODO: Implement AWS Secrets Manager integration

        Args:
            key: Secret key

        Returns:
            Optional[str]: Secret value or None
        """
        logger.warning("AWS Secrets Manager not yet implemented")
        return None

    def get_huawei_credentials(self) -> Dict[str, str]:
        """
        Get Huawei API credentials

        Returns:
            Dict[str, str]: Credentials dict with 'username' and 'password'

        Raises:
            ConfigurationError: If credentials not found
        """
        # Try secrets first, then fall back to configuration
        username = self.get_secret("HUAWEI_USERNAME")
        if not username:
            username = self.settings.huawei_username
            
        password = self.get_secret("HUAWEI_PASSWORD")
        if not password:
            password = self.settings.huawei_password

        if not username:
            raise ConfigurationError("Huawei username not found in secrets or configuration")
        if not password:
            raise ConfigurationError("Huawei password not found in secrets or configuration")

        return {"username": username, "password": password}

    def get_llm_api_key(self, provider: str) -> Optional[str]:
        """
        Get LLM API key for a provider

        Args:
            provider: LLM provider (openai/anthropic/local)

        Returns:
            Optional[str]: API key or None
        """
        if provider == "openai":
            return self.get_secret("OPENAI_API_KEY")
        elif provider == "anthropic":
            return self.get_secret("ANTHROPIC_API_KEY")
        else:
            # Local LLM doesn't need API key
            return None

    def clear_cache(self):
        """Clear the secrets cache"""
        self._cache.clear()
        logger.debug("Secrets cache cleared")


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """
    Get global secrets manager instance

    Returns:
        SecretsManager: Singleton secrets manager
    """
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager
