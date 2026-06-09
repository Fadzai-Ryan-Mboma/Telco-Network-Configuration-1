"""
LLM client factory for the NetGenix optimizer workflow.

Supports three providers: nvidia, gemini, mistral.
Active provider is set via config.yaml llm.provider (overridable per-call).
All clients return a LangChain-compatible BaseChatModel so agents are provider-agnostic.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


def _load_llm_config() -> dict:
    config_path = Path(__file__).resolve().parents[1] / "config" / "config.yaml"
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as fh:
        return (yaml.safe_load(fh) or {}).get("llm", {})


def _resolve_env(value: str) -> str:
    """Expand ${VAR} placeholders from environment."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.getenv(value[2:-1], "")
    return value


# ── Response helpers ──────────────────────────────────────────────────────────

def normalize_llm_content(content) -> str:
    """Return plain text from provider-specific message content shapes."""
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") in (None, "text"):
                    parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return " ".join(part for part in parts if part).strip()
    return "" if content is None else str(content)


def message_to_text(message) -> str:
    """Extract normalized text from a LangChain message or arbitrary object."""
    return normalize_llm_content(message.content if hasattr(message, "content") else message)


def looks_like_llm_failure(text: str) -> bool:
    """Detect explicit model failures without flagging normal telecom text."""
    normalized = (text or "").strip().upper()
    failure_prefixes = (
        "ERROR:",
        "FATAL:",
        "EXCEPTION:",
        "I CANNOT",
        "I CAN'T",
        "I AM UNABLE",
        "I'M UNABLE",
        "UNABLE TO PROCESS",
        "CANNOT PROVIDE",
        "NO RECOMMENDATIONS POSSIBLE",
    )
    return normalized.startswith(failure_prefixes)


# ── Provider clients ──────────────────────────────────────────────────────────

def get_nvidia_client(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
):
    try:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
    except ImportError as exc:
        raise RuntimeError("langchain-nvidia-ai-endpoints is not installed.") from exc

    cfg = _load_llm_config().get("nvidia", {})
    api_key = os.getenv("NVIDIA_API_KEY") or _resolve_env(cfg.get("api_key", ""))
    if not api_key:
        raise ValueError("NVIDIA_API_KEY is not configured.")

    selected_model = model or cfg.get("model", "nvidia/nemotron-3-super-120b-a12b")
    logger.info("Initializing NVIDIA LLM: %s", selected_model)
    return ChatNVIDIA(
        model=selected_model,
        api_key=api_key,
        base_url=cfg.get("base_url", "https://integrate.api.nvidia.com/v1"),
        temperature=temperature if temperature is not None else cfg.get("temperature", 0.7),
        max_tokens=max_tokens or cfg.get("max_tokens", 4096),
        timeout=timeout or cfg.get("timeout", 120),
    )


def get_gemini_client(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
):
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:
        raise RuntimeError("langchain-google-genai is not installed.") from exc

    cfg = _load_llm_config().get("gemini", {})
    api_key = os.getenv("GEMINI_API_KEY") or _resolve_env(cfg.get("api_key", ""))
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    selected_model = model or cfg.get("model", "gemini-3.1-pro-preview")
    logger.info("Initializing Gemini LLM: %s", selected_model)
    return ChatGoogleGenerativeAI(
        model=selected_model,
        google_api_key=api_key,
        temperature=temperature if temperature is not None else cfg.get("temperature", 0.7),
        max_output_tokens=max_tokens or cfg.get("max_tokens", 4096),
        timeout=timeout or cfg.get("timeout", 120),
    )


def get_mistral_client(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
):
    try:
        from langchain_mistralai import ChatMistralAI
    except ImportError as exc:
        raise RuntimeError("langchain-mistralai is not installed.") from exc

    cfg = _load_llm_config().get("mistral", {})
    api_key = os.getenv("MISTRAL_API_KEY") or _resolve_env(cfg.get("api_key", ""))
    if not api_key:
        raise ValueError("MISTRAL_API_KEY is not configured.")

    selected_model = model or cfg.get("model", "magistral-medium-latest")
    logger.info("Initializing Mistral LLM: %s", selected_model)
    return ChatMistralAI(
        model=selected_model,
        api_key=api_key,
        temperature=temperature if temperature is not None else cfg.get("temperature", 0.7),
        max_tokens=max_tokens or cfg.get("max_tokens", 4096),
        timeout=timeout or cfg.get("timeout", 120),
    )


# ── Router ────────────────────────────────────────────────────────────────────

_PROVIDERS = {
    "nvidia": get_nvidia_client,
    "gemini": get_gemini_client,
    "mistral": get_mistral_client,
}


def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
):
    """
    Return a LangChain-compatible chat client for the active provider.
    provider overrides config.yaml llm.provider if supplied.
    """
    cfg = _load_llm_config()
    active = provider or cfg.get("provider", "nvidia")

    if active not in _PROVIDERS:
        raise ValueError(f"Unknown LLM provider '{active}'. Choose from: {list(_PROVIDERS)}")

    return _PROVIDERS[active](
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )


def get_llm_config() -> dict:
    """Return current LLM config without exposing secrets."""
    cfg = _load_llm_config()
    return {
        "provider": cfg.get("provider", "nvidia"),
        "nvidia": {k: v for k, v in cfg.get("nvidia", {}).items() if k != "api_key"},
        "gemini": {k: v for k, v in cfg.get("gemini", {}).items() if k != "api_key"},
        "mistral": {k: v for k, v in cfg.get("mistral", {}).items() if k != "api_key"},
    }


def is_llm_available() -> bool:
    """Return True when the active provider has a configured API key."""
    cfg = _load_llm_config()
    active = cfg.get("provider", "nvidia")
    key_map = {
        "nvidia": "NVIDIA_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "mistral": "MISTRAL_API_KEY",
    }
    return bool(os.getenv(key_map.get(active, "")))


# Backward-compatible alias
def get_nvidia_llm(**kwargs):
    return get_nvidia_client(**kwargs)
