"""
LLM Factory - NVIDIA LLM Initialization
Purpose: Centralized NVIDIA LLM client initialization for Liquid Zimbabwe 4G Network Optimizer
Created: 2026-01-12
"""

import os
import yaml
import logging
from typing import Optional
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def get_llm_client(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None
):
    """
    Factory function to create NVIDIA LLM client based on configuration.
    
    Args:
        model: Model name. If None, uses config.yaml default.
        temperature: Model temperature. If None, uses config.yaml default.
        max_tokens: Maximum tokens. If None, uses config.yaml default.
        timeout: Request timeout. If None, uses config.yaml default.
    
    Returns:
        ChatNVIDIA instance
    
    Raises:
        ValueError: If required API key is missing or configuration is invalid
    """
    # Load config
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "config.yaml"
    )
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    llm_config = config.get('llm', {})
    nvidia_config = llm_config.get('nvidia', {})
    
    # Use overrides or fall back to config
    model = model or nvidia_config.get('model', 'nvidia/nemotron-3-super-120b-a12b')
    temperature = temperature if temperature is not None else nvidia_config.get('temperature', 0.7)
    max_tokens = max_tokens or nvidia_config.get('max_tokens', 4096)
    timeout = timeout or nvidia_config.get('timeout', 120)
    base_url = nvidia_config.get('base_url', 'https://integrate.api.nvidia.com/v1')
    
    # Get API key
    api_key = os.getenv('NVIDIA_API_KEY')
    if not api_key:
        raise ValueError(
            "NVIDIA_API_KEY not found in environment variables. "
            "Please set it in your .env file or Docker environment."
        )
    
    if not model:
        raise ValueError("NVIDIA model must be specified in config.yaml")
    
    logger.info(f"🤖 Initializing NVIDIA LLM with model: {model}")
    
    # Create and return NVIDIA LLM client
    return ChatNVIDIA(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )


def get_llm_config():
    """
    Get the current LLM configuration from config.yaml.
    
    Returns:
        dict: LLM configuration dictionary
    """
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "config.yaml"
    )
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get('llm', {})


def is_llm_available():
    """
    Check if NVIDIA LLM is available (API key is set).
    
    Returns:
        bool: True if NVIDIA_API_KEY is set
    """
    return bool(os.getenv('NVIDIA_API_KEY'))


# Backward compatibility alias
def get_nvidia_llm(**kwargs):
    """
    Get NVIDIA LLM client (backward compatibility alias).
    
    Args:
        **kwargs: Additional parameters to pass to get_llm_client
    
    Returns:
        ChatNVIDIA instance
    """
    return get_llm_client(**kwargs)
