"""
Configuration Management for Liquid4G

Handles loading configuration from:
- Environment variables
- .env files
- YAML configuration files
- Secrets managers
"""

from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    # Environment
    env: str = Field(default="development", description="Environment: development|production|testing")

    # Huawei API
    huawei_api_url: str = Field(default="", description="Huawei iMaster MAE API URL")
    huawei_username: str = Field(default="", description="API username")
    huawei_password: str = Field(default="", description="API password")
    huawei_ssl_verify: bool = Field(default=True, description="Verify SSL certificates")

    # LLM Configuration
    llm_provider: str = Field(default="openai", description="LLM provider: openai|anthropic|local")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model")
    openai_temperature: float = Field(default=0.0, description="LLM temperature")

    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", description="Claude model")

    local_llm_url: str = Field(default="http://localhost:11434", description="Local LLM URL")
    local_llm_model: str = Field(default="llama3:8b", description="Local LLM model")

    llm_timeout: int = Field(default=30, description="LLM request timeout")
    llm_max_retries: int = Field(default=2, description="Max LLM retries")
    llm_max_tokens: int = Field(default=4000, description="Max tokens per request")

    # Database
    db_path: str = Field(default="data/database/liquid4g.db", description="Database file path")
    db_pool_size: int = Field(default=5, description="Connection pool size")
    db_timeout: int = Field(default=30, description="Query timeout")
    db_enable_wal: bool = Field(default=True, description="Enable WAL mode")

    # Redis
    redis_enabled: bool = Field(default=False, description="Enable Redis cache")
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: str = Field(default="", description="Redis password")
    redis_db: int = Field(default=0, description="Redis database")

    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format: json|text")
    log_file: str = Field(default="data/logs/liquid4g.log", description="Log file path")

    # API
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=4, description="API workers")

    # Streamlit
    streamlit_port: int = Field(default=8501, description="Streamlit port")
    streamlit_server_address: str = Field(default="0.0.0.0", description="Streamlit address")

    # Monitoring
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus")
    prometheus_port: int = Field(default=9090, description="Prometheus port")
    metrics_enabled: bool = Field(default=True, description="Enable metrics")

    # Circuit Breaker
    circuit_breaker_enabled: bool = Field(default=True, description="Enable circuit breaker")
    circuit_breaker_threshold: int = Field(default=5, description="Failure threshold")
    circuit_breaker_timeout: int = Field(default=60, description="Timeout in seconds")

    # Agent Configuration
    agent_llm_enabled: bool = Field(default=True, description="Enable LLM for agents")
    agent_fallback_enabled: bool = Field(default=True, description="Enable rule-based fallback")
    agent_timeout: int = Field(default=120, description="Agent timeout in seconds")

    # Security
    jwt_secret_key: str = Field(default="", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expires_minutes: int = Field(default=30, description="JWT expiration")

    # Docker
    docker_deployment: bool = Field(default=False, description="Running in Docker")
    tz: str = Field(default="Africa/Harare", description="Timezone")

    # Secrets
    secrets_backend: str = Field(
        default="environment",
        description="Secrets backend: environment|docker|vault|aws",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.env == "development"

    @property
    def config_dir(self) -> Path:
        """Get config directory path"""
        return Path(__file__).parent.parent.parent.parent / "config"

    def load_yaml_config(self, config_file: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        config_path = self.config_dir / config_file

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for specific agent"""
        try:
            agent_config = self.load_yaml_config(f"agents/{agent_name}.yaml")
            return agent_config
        except FileNotFoundError:
            # Return default config
            return {
                "llm_enabled": self.agent_llm_enabled,
                "fallback_enabled": self.agent_fallback_enabled,
                "timeout": self.agent_timeout,
            }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
