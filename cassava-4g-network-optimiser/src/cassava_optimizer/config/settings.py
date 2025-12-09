"""
Application settings using Pydantic Settings.

Loads configuration from environment variables and .env file.
Fail-fast pattern: raises clear errors if required settings are missing.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class NvidiaSettings(BaseSettings):
    """NVIDIA NIM API configuration."""

    model_config = SettingsConfigDict(env_prefix="NVIDIA_")

    api_key: SecretStr = Field(..., description="NVIDIA NIM API key")
    model: str = Field(
        default="meta/llama-3.1-70b-instruct",
        description="Model identifier for NVIDIA NIM",
    )
    base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="NVIDIA NIM API base URL",
    )
    rate_limit: int = Field(default=5, ge=1, le=100, alias="NVIDIA_API_RATE_LIMIT")
    timeout: int = Field(default=60, ge=10, le=300, alias="NVIDIA_API_TIMEOUT")


class HuaweiSettings(BaseSettings):
    """Huawei iMaster MAE API configuration."""

    model_config = SettingsConfigDict(env_prefix="HUAWEI_MAE_")

    host: str = Field(..., description="Huawei MAE server hostname")
    port: int = Field(default=32102, ge=1, le=65535, description="MAE API port")
    username: str = Field(..., description="MAE API username")
    password: SecretStr = Field(..., description="MAE API password")
    use_ssl: bool = Field(default=True, description="Use HTTPS for MAE API")
    rate_limit: int = Field(default=10, ge=1, le=100, alias="HUAWEI_API_RATE_LIMIT")
    timeout: int = Field(default=30, ge=5, le=120, alias="HUAWEI_API_TIMEOUT")

    @property
    def base_url(self) -> str:
        """Construct the base URL for Huawei MAE API."""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.host}:{self.port}"


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: str = Field(
        default="sqlite+aiosqlite:///./data/cassava_network.db",
        description="Database connection URL",
    )
    echo: bool = Field(default=False, description="Echo SQL statements to log")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure SQLite URLs use aiosqlite for async support."""
        if v.startswith("sqlite:") and "aiosqlite" not in v:
            return v.replace("sqlite:", "sqlite+aiosqlite:")
        return v


class UISettings(BaseSettings):
    """UI configuration."""

    model_config = SettingsConfigDict(env_prefix="UI_")

    default_theme: Literal["light", "dark"] = Field(
        default="light", description="Default UI theme"
    )
    show_debug_info: bool = Field(
        default=False, description="Show debug information in UI"
    )
    auto_refresh_interval: int = Field(
        default=30, ge=5, le=300, description="Auto-refresh interval in seconds"
    )


class FeatureFlags(BaseSettings):
    """Feature flags for enabling/disabling functionality."""

    model_config = SettingsConfigDict(env_prefix="ENABLE_")

    command_execution: bool = Field(
        default=False,
        alias="ENABLE_COMMAND_EXECUTION",
        description="Enable actual command execution on network equipment",
    )
    auto_rollback: bool = Field(
        default=True,
        alias="ENABLE_AUTO_ROLLBACK",
        description="Enable automatic rollback on failed commands",
    )
    historical_correlation: bool = Field(
        default=True,
        alias="ENABLE_HISTORICAL_CORRELATION",
        description="Enable historical data correlation in analysis",
    )


class Settings(BaseSettings):
    """Main application settings aggregating all sub-settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application metadata
    app_name: str = Field(default="Cassava 4G Network Optimiser")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    debug: bool = Field(default=False, alias="APP_DEBUG")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", alias="LOG_LEVEL"
    )
    log_format: Literal["json", "console"] = Field(default="json", alias="LOG_FORMAT")

    # Sub-settings (loaded separately to handle prefixes correctly)
    # We'll load these via properties to ensure proper prefix handling

    # Direct fields for required env vars (to ensure fail-fast)
    nvidia_api_key: SecretStr = Field(..., alias="NVIDIA_API_KEY")
    huawei_mae_host: str = Field(..., alias="HUAWEI_MAE_HOST")
    huawei_mae_username: str = Field(..., alias="HUAWEI_MAE_USERNAME")
    huawei_mae_password: SecretStr = Field(..., alias="HUAWEI_MAE_PASSWORD")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent.parent

    @property
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return self.project_root / "data"

    @property
    def logs_dir(self) -> Path:
        """Get the logs directory path."""
        return self.project_root / "logs"


class DevelopmentSettings(Settings):
    """Development-specific settings with relaxed defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Override with optional for development
    nvidia_api_key: SecretStr = Field(
        default=SecretStr("dev-key-not-set"), alias="NVIDIA_API_KEY"
    )
    huawei_mae_host: str = Field(default="localhost", alias="HUAWEI_MAE_HOST")
    huawei_mae_username: str = Field(default="dev_user", alias="HUAWEI_MAE_USERNAME")
    huawei_mae_password: SecretStr = Field(
        default=SecretStr("dev_pass"), alias="HUAWEI_MAE_PASSWORD"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses fail-fast pattern: raises ValidationError with clear messages
    if required environment variables are missing.
    
    Returns:
        Settings: Validated application settings
        
    Raises:
        pydantic.ValidationError: If required settings are missing or invalid
    """
    return Settings()


def get_nvidia_settings() -> NvidiaSettings:
    """Get NVIDIA-specific settings."""
    return NvidiaSettings()


def get_huawei_settings() -> HuaweiSettings:
    """Get Huawei-specific settings."""
    return HuaweiSettings()


def get_database_settings() -> DatabaseSettings:
    """Get database settings."""
    return DatabaseSettings()


def get_ui_settings() -> UISettings:
    """Get UI settings."""
    return UISettings()


def get_feature_flags() -> FeatureFlags:
    """Get feature flags."""
    return FeatureFlags()
