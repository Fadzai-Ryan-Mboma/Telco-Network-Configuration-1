"""
Async client for NVIDIA NIM LLM API.

Provides async methods for text generation with proper error handling,
retries, and response parsing for network optimization tasks.
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator

import httpx
import structlog

from cassava_optimizer.domain.exceptions import LLMError

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    """Container for LLM response with metadata."""
    
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str
    created_at: datetime
    latency_ms: float
    
    @property
    def cost_estimate(self) -> float:
        """Estimate cost based on token usage (NVIDIA NIM pricing)."""
        # Approximate cost per 1M tokens
        input_cost = (self.prompt_tokens / 1_000_000) * 0.50
        output_cost = (self.completion_tokens / 1_000_000) * 1.50
        return input_cost + output_cost


class NVIDIANIMClient:
    """
    Async client for NVIDIA NIM LLM API.
    
    Designed for network optimization tasks with:
    - Async streaming support
    - Automatic retries with backoff
    - Token usage tracking
    - Structured output parsing
    """
    
    DEFAULT_MODEL = "meta/llama-3.1-70b-instruct"
    BASE_URL = "https://integrate.api.nvidia.com/v1"
    
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        timeout: int = 120,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the NVIDIA NIM client.
        
        Args:
            api_key: NVIDIA NIM API key
            model: Model identifier
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=httpx.Timeout(timeout, connect=10.0),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        
        self._log = logger.bind(component="llm_client", model=model)
        self._total_tokens_used = 0
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def __aenter__(self) -> "NVIDIANIMClient":
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        await self.close()
    
    @property
    def total_tokens_used(self) -> int:
        """Total tokens used across all requests."""
        return self._total_tokens_used
    
    # =========================================================================
    # Core API Methods
    # =========================================================================
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> LLMResponse:
        """
        Generate text from a prompt.
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            json_mode: Whether to request JSON output
            
        Returns:
            LLMResponse with generated content
            
        Raises:
            LLMError: If generation fails
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        return await self._complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )
    
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> LLMResponse:
        """
        Generate response from conversation history.
        
        Args:
            messages: List of messages with role and content
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            json_mode: Whether to request JSON output
            
        Returns:
            LLMResponse with generated content
        """
        return await self._complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )
    
    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """
        Stream text generation with async iteration.
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Text chunks as they are generated
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        
        self._log.info("Starting streaming generation", prompt_length=len(prompt))
        
        try:
            async with self._client.stream(
                "POST",
                "/chat/completions",
                json=payload,
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise LLMError(
                        f"Streaming request failed: {response.status_code}",
                        response_body=body.decode(),
                    )
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.TimeoutException as e:
            raise LLMError.timeout(self.timeout, e)
        except httpx.ConnectError as e:
            raise LLMError.connection_failed(self.BASE_URL, e)
    
    # =========================================================================
    # Specialized Methods for Network Optimization
    # =========================================================================
    
    async def analyze_kpis(
        self,
        kpi_data: dict[str, Any],
        site_context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze KPI data and identify issues.
        
        Args:
            kpi_data: Dictionary of KPI names to values
            site_context: Site information for context
            
        Returns:
            Analysis results with identified issues
        """
        prompt = f"""Analyze the following 4G LTE network KPI data and identify performance issues.

Site Information:
{json.dumps(site_context, indent=2)}

Current KPIs:
{json.dumps(kpi_data, indent=2)}

Provide your analysis in the following JSON format:
{{
    "overall_health_score": <0-100>,
    "critical_issues": [
        {{"kpi": "<kpi_name>", "value": <current_value>, "threshold": <expected>, "severity": "critical|warning|info", "impact": "<description>"}}
    ],
    "correlations": [
        {{"kpis": ["<kpi1>", "<kpi2>"], "relationship": "<description>"}}
    ],
    "root_causes": ["<potential root cause>"],
    "recommended_focus_areas": ["<area>"]
}}"""
        
        response = await self.generate(
            prompt=prompt,
            system_prompt=self._get_system_prompt("analyzer"),
            temperature=0.2,
            json_mode=True,
        )
        
        return self._parse_json_response(response.content)
    
    async def generate_recommendations(
        self,
        analysis: dict[str, Any],
        site_context: dict[str, Any],
        available_parameters: list[str],
    ) -> list[dict[str, Any]]:
        """
        Generate optimization recommendations based on analysis.
        
        Args:
            analysis: KPI analysis results
            site_context: Site information
            available_parameters: List of adjustable parameters
            
        Returns:
            List of recommendations with parameters
        """
        prompt = f"""Based on the network analysis, generate optimization recommendations.

Analysis Results:
{json.dumps(analysis, indent=2)}

Site Context:
{json.dumps(site_context, indent=2)}

Available Parameters for Adjustment:
{json.dumps(available_parameters, indent=2)}

Generate recommendations in this JSON format:
{{
    "recommendations": [
        {{
            "id": "<unique_id>",
            "priority": <1-10>,
            "title": "<short title>",
            "description": "<detailed description>",
            "target_kpis": ["<affected kpi names>"],
            "expected_improvement": {{"<kpi>": "<% or absolute improvement>"}},
            "risk_level": "low|medium|high",
            "parameters": [
                {{"name": "<param>", "current": "<value>", "recommended": "<value>", "unit": "<unit>"}}
            ],
            "mml_commands": ["<command>"],
            "validation_criteria": "<how to verify success>"
        }}
    ]
}}"""
        
        response = await self.generate(
            prompt=prompt,
            system_prompt=self._get_system_prompt("strategy_planner"),
            temperature=0.3,
            json_mode=True,
        )
        
        result = self._parse_json_response(response.content)
        return result.get("recommendations", [])
    
    async def validate_changes(
        self,
        before_kpis: dict[str, Any],
        after_kpis: dict[str, Any],
        applied_changes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Validate optimization results by comparing KPIs.
        
        Args:
            before_kpis: KPI values before optimization
            after_kpis: KPI values after optimization
            applied_changes: List of changes that were applied
            
        Returns:
            Validation results with effectiveness assessment
        """
        prompt = f"""Validate the effectiveness of the applied network optimizations.

KPIs Before Optimization:
{json.dumps(before_kpis, indent=2)}

KPIs After Optimization:
{json.dumps(after_kpis, indent=2)}

Applied Changes:
{json.dumps(applied_changes, indent=2)}

Provide validation results in this JSON format:
{{
    "overall_success": true|false,
    "effectiveness_score": <0-100>,
    "kpi_changes": [
        {{"kpi": "<name>", "before": <value>, "after": <value>, "change_percent": <percent>, "improved": true|false}}
    ],
    "successful_changes": ["<change descriptions>"],
    "ineffective_changes": ["<change descriptions>"],
    "unexpected_effects": ["<any unexpected changes>"],
    "rollback_recommended": true|false,
    "next_steps": ["<recommendations>"]
}}"""
        
        response = await self.generate(
            prompt=prompt,
            system_prompt=self._get_system_prompt("validator"),
            temperature=0.2,
            json_mode=True,
        )
        
        return self._parse_json_response(response.content)
    
    # =========================================================================
    # Internal Methods
    # =========================================================================
    
    async def _complete(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        json_mode: bool,
    ) -> LLMResponse:
        """Make a completion request with retry logic."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        prompt_length = sum(len(m.get("content", "")) for m in messages)
        self._log.info("Starting generation", prompt_length=prompt_length)
        
        start_time = datetime.utcnow()
        last_error: Exception | None = None
        
        for attempt in range(self.max_retries):
            try:
                response = await self._client.post(
                    "/chat/completions",
                    json=payload,
                )
                
                if response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get("Retry-After", "5"))
                    self._log.warning("Rate limited", retry_after=retry_after)
                    await asyncio.sleep(retry_after)
                    continue
                
                if response.status_code >= 500:
                    # Server error
                    wait = 2 ** attempt
                    self._log.warning(
                        "Server error, retrying",
                        status=response.status_code,
                        wait=wait,
                    )
                    await asyncio.sleep(wait)
                    continue
                
                if response.status_code != 200:
                    raise LLMError(
                        f"LLM request failed: {response.status_code}",
                        response_body=response.text,
                    )
                
                data = response.json()
                latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                choice = data.get("choices", [{}])[0]
                usage = data.get("usage", {})
                
                self._total_tokens_used += usage.get("total_tokens", 0)
                
                llm_response = LLMResponse(
                    content=choice.get("message", {}).get("content", ""),
                    model=data.get("model", self.model),
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                    finish_reason=choice.get("finish_reason", ""),
                    created_at=datetime.utcnow(),
                    latency_ms=latency_ms,
                )
                
                self._log.info(
                    "Generation complete",
                    tokens=llm_response.total_tokens,
                    latency_ms=latency_ms,
                )
                
                return llm_response
                
            except httpx.TimeoutException as e:
                last_error = e
                self._log.warning("Request timeout", attempt=attempt + 1)
                await asyncio.sleep(2 ** attempt)
            
            except httpx.ConnectError as e:
                raise LLMError.connection_failed(self.BASE_URL, e)
        
        raise LLMError.timeout(self.timeout, last_error)
    
    def _get_system_prompt(self, agent_type: str) -> str:
        """Get system prompt for specific agent type."""
        prompts = {
            "analyzer": """You are an expert 4G LTE network performance analyst. Your role is to:
- Analyze KPI data to identify performance degradation
- Correlate related KPIs to find root causes
- Prioritize issues by their impact on user experience and revenue
- Provide actionable insights based on network engineering best practices

Always respond with valid JSON. Be precise with numerical thresholds and specific in your analysis.""",
            
            "strategy_planner": """You are an expert 4G LTE network optimization strategist. Your role is to:
- Generate optimization recommendations based on analysis
- Propose specific parameter changes with safe values
- Consider the risk and impact of each change
- Provide MML commands for Huawei eNodeB configuration

Always respond with valid JSON. Ensure recommendations are safe and follow Huawei best practices.""",
            
            "validator": """You are an expert at validating network optimization results. Your role is to:
- Compare before/after KPI metrics objectively
- Assess the effectiveness of applied changes
- Identify any negative side effects
- Recommend rollback if changes caused degradation

Always respond with valid JSON. Be objective and data-driven in your assessment.""",
        }
        
        return prompts.get(agent_type, "You are a helpful assistant. Always respond with valid JSON.")
    
    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Parse JSON from LLM response."""
        # Clean up the response
        content = content.strip()
        
        # Handle markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            self._log.error("Failed to parse JSON response", error=str(e))
            raise LLMError(
                f"Failed to parse LLM response as JSON: {e}",
                response_body=content,
            )
