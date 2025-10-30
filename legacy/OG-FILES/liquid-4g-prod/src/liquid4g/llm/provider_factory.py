"""
LLM Provider Factory

Creates LangChain LLM instances for different providers (OpenAI, Anthropic, Local).
"""

from typing import Optional, Any
from enum import Enum

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    ChatOpenAI = None  # type: ignore

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    ChatAnthropic = None  # type: ignore

try:
    from langchain_community.llms import Ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    Ollama = None  # type: ignore

from liquid4g.core.config import get_settings
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import ConfigurationError, LLMError
from liquid4g.infrastructure.secrets import get_secrets_manager

logger = get_logger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class LLMProviderFactory:
    """
    Factory for creating LangChain LLM instances

    Supports:
    - OpenAI (GPT-4, GPT-3.5, etc.)
    - Anthropic (Claude 3.5, Claude 3, etc.)
    - Local (Ollama)
    """

    def __init__(self):
        """Initialize LLM provider factory"""
        self.settings = get_settings()
        self.secrets = get_secrets_manager()

    def create_llm(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Create LLM instance

        Args:
            provider: LLM provider (openai/anthropic/local) - uses config if None
            model: Model name - uses config if None
            temperature: Temperature for generation - uses config if None
            **kwargs: Additional provider-specific arguments

        Returns:
            LangChain LLM instance

        Raises:
            ConfigurationError: If provider not configured
            LLMError: If LLM creation fails
        """
        # Get provider from config if not specified
        if provider is None:
            provider = self.settings.llm_provider

        # Validate provider
        try:
            provider_enum = LLMProvider(provider)
        except ValueError:
            raise ConfigurationError(
                f"Invalid LLM provider: {provider}. "
                f"Must be one of: {[p.value for p in LLMProvider]}"
            )

        # Create LLM based on provider
        if provider_enum == LLMProvider.OPENAI:
            return self._create_openai(model, temperature, **kwargs)
        elif provider_enum == LLMProvider.ANTHROPIC:
            return self._create_anthropic(model, temperature, **kwargs)
        elif provider_enum == LLMProvider.LOCAL:
            return self._create_local(model, temperature, **kwargs)
        else:
            raise ConfigurationError(f"Unsupported provider: {provider}")

    def _create_openai(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Create OpenAI LLM instance

        Args:
            model: Model name (default: gpt-4o-mini)
            temperature: Temperature (default: 0.7)
            **kwargs: Additional arguments

        Returns:
            ChatOpenAI instance
        """
        if not OPENAI_AVAILABLE:
            raise LLMError(
                "OpenAI provider not available. Install with: pip install langchain-openai"
            )

        # Get API key
        api_key = self.secrets.get_llm_api_key("openai")
        if not api_key:
            raise ConfigurationError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or Docker secret."
            )

        # Get model and temperature from config if not specified
        if model is None:
            model = getattr(self.settings, "openai_model", "gpt-4o-mini")
        if temperature is None:
            temperature = getattr(self.settings, "llm_temperature", 0.7)

        try:
            llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=api_key,
                **kwargs
            )

            logger.info(f"Created OpenAI LLM: {model} (temp={temperature})")
            return llm

        except Exception as e:
            raise LLMError(f"Failed to create OpenAI LLM: {e}")

    def _create_anthropic(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Create Anthropic LLM instance

        Args:
            model: Model name (default: claude-3-5-sonnet-20241022)
            temperature: Temperature (default: 0.7)
            **kwargs: Additional arguments

        Returns:
            ChatAnthropic instance
        """
        if not ANTHROPIC_AVAILABLE:
            raise LLMError(
                "Anthropic provider not available. Install with: pip install langchain-anthropic"
            )

        # Get API key
        api_key = self.secrets.get_llm_api_key("anthropic")
        if not api_key:
            raise ConfigurationError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable "
                "or Docker secret."
            )

        # Get model and temperature from config if not specified
        if model is None:
            model = getattr(self.settings, "anthropic_model", "claude-3-5-sonnet-20241022")
        if temperature is None:
            temperature = getattr(self.settings, "llm_temperature", 0.7)

        try:
            llm = ChatAnthropic(
                model=model,
                temperature=temperature,
                api_key=api_key,
                **kwargs
            )

            logger.info(f"Created Anthropic LLM: {model} (temp={temperature})")
            return llm

        except Exception as e:
            raise LLMError(f"Failed to create Anthropic LLM: {e}")

    def _create_local(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Create local LLM instance (Ollama)

        Args:
            model: Model name (default: llama3.1)
            temperature: Temperature (default: 0.7)
            **kwargs: Additional arguments

        Returns:
            Ollama instance
        """
        if not OLLAMA_AVAILABLE:
            raise LLMError(
                "Ollama provider not available. Install with: pip install langchain-community"
            )

        # Get model and temperature from config if not specified
        if model is None:
            model = getattr(self.settings, "local_model", "llama3.1")
        if temperature is None:
            temperature = getattr(self.settings, "llm_temperature", 0.7)

        # Get Ollama base URL
        base_url = getattr(self.settings, "ollama_base_url", "http://localhost:11434")

        try:
            llm = Ollama(
                model=model,
                temperature=temperature,
                base_url=base_url,
                **kwargs
            )

            logger.info(f"Created Ollama LLM: {model} (temp={temperature})")
            return llm

        except Exception as e:
            raise LLMError(f"Failed to create Ollama LLM: {e}")

    def is_provider_available(self, provider: str) -> bool:
        """
        Check if a provider is available

        Args:
            provider: Provider name (openai/anthropic/local)

        Returns:
            bool: True if provider is available
        """
        if provider == "openai":
            return OPENAI_AVAILABLE and self.secrets.get_llm_api_key("openai") is not None
        elif provider == "anthropic":
            return ANTHROPIC_AVAILABLE and self.secrets.get_llm_api_key("anthropic") is not None
        elif provider == "local":
            return OLLAMA_AVAILABLE
        else:
            return False

    def get_available_providers(self) -> list[str]:
        """
        Get list of available providers

        Returns:
            list[str]: List of available provider names
        """
        available = []
        for provider in LLMProvider:
            if self.is_provider_available(provider.value):
                available.append(provider.value)
        return available


# Global factory instance
_llm_factory: Optional[LLMProviderFactory] = None


def get_llm_provider() -> LLMProviderFactory:
    """
    Get global LLM provider factory instance

    Returns:
        LLMProviderFactory: Singleton factory
    """
    global _llm_factory
    if _llm_factory is None:
        _llm_factory = LLMProviderFactory()
    return _llm_factory
