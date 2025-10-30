"""
LLM Executor

High-level executor for LLM calls with circuit breaker, retry, and parsing.
"""

import time
from typing import Type, TypeVar, Optional, Any, Dict
from pydantic import BaseModel

from liquid4g.core.config import get_settings
from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import (
    LLMError,
    LLMExecutionError,
    LLMResponseError,
    CircuitBreakerOpenError,
)
from liquid4g.llm.provider_factory import get_llm_provider
from liquid4g.llm.prompt_manager import get_prompt_manager
from liquid4g.llm.response_parser import get_response_parser
from liquid4g.llm.circuit_breaker import CircuitBreaker

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMExecutor:
    """
    High-level LLM executor

    Features:
    - Automatic prompt formatting
    - LLM invocation with circuit breaker
    - Response parsing and validation
    - Retry logic with exponential backoff
    - Comprehensive error handling
    """

    def __init__(self):
        """Initialize LLM executor"""
        self.settings = get_settings()
        self.llm_factory = get_llm_provider()
        self.prompt_manager = get_prompt_manager()
        self.response_parser = get_response_parser()

        # Circuit breaker for resilience
        self.circuit_breaker = CircuitBreaker()

        # Retry configuration
        self.max_retries = getattr(self.settings, "llm_max_retries", 3)
        self.retry_delay = getattr(self.settings, "llm_retry_delay", 2)

        logger.info("LLM executor initialized")

    def execute(
        self,
        agent_type: str,
        task_name: str,
        response_model: Type[T],
        task_variables: Optional[Dict[str, Any]] = None,
        **llm_kwargs
    ) -> T:
        """
        Execute LLM call with full pipeline

        Args:
            agent_type: Agent type for system prompt
            task_name: Task name for user prompt
            response_model: Pydantic model for response validation
            task_variables: Variables for task prompt template
            **llm_kwargs: Additional LLM arguments (temperature, etc.)

        Returns:
            T: Validated response model

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            LLMExecutionError: If execution fails after retries
            LLMResponseError: If response parsing fails
        """
        # Format prompt
        task_vars = task_variables or {}
        prompt_text = self._format_prompt(agent_type, task_name, task_vars)

        # Execute with circuit breaker and retry
        response_text = self._execute_with_retry(prompt_text, **llm_kwargs)

        # Parse and validate response
        try:
            result = self.response_parser.parse_json(response_text, response_model)
            logger.info(f"Successfully executed LLM call: {agent_type}/{task_name}")
            return result

        except LLMResponseError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise

    def execute_raw(
        self,
        agent_type: str,
        task_name: str,
        task_variables: Optional[Dict[str, Any]] = None,
        **llm_kwargs
    ) -> str:
        """
        Execute LLM call and return raw text response

        Args:
            agent_type: Agent type for system prompt
            task_name: Task name for user prompt
            task_variables: Variables for task prompt template
            **llm_kwargs: Additional LLM arguments

        Returns:
            str: Raw LLM response text

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            LLMExecutionError: If execution fails after retries
        """
        # Format prompt
        task_vars = task_variables or {}
        prompt_text = self._format_prompt(agent_type, task_name, task_vars)

        # Execute with circuit breaker and retry
        return self._execute_with_retry(prompt_text, **llm_kwargs)

    def _format_prompt(
        self,
        agent_type: str,
        task_name: str,
        task_variables: Dict[str, Any]
    ) -> str:
        """
        Format complete prompt

        Args:
            agent_type: Agent type
            task_name: Task name
            task_variables: Task variables

        Returns:
            str: Formatted prompt
        """
        system_prompt = self.prompt_manager.get_system_prompt(agent_type)
        task_prompt = self.prompt_manager.get_task_prompt(task_name, **task_variables)

        return f"{system_prompt}\n\n{task_prompt}"

    def _execute_with_retry(
        self,
        prompt_text: str,
        **llm_kwargs
    ) -> str:
        """
        Execute LLM call with retry logic

        Args:
            prompt_text: Formatted prompt
            **llm_kwargs: LLM arguments

        Returns:
            str: LLM response text

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            LLMExecutionError: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Execute through circuit breaker
                response = self.circuit_breaker.call(
                    self._call_llm,
                    prompt_text,
                    **llm_kwargs
                )
                return response

            except CircuitBreakerOpenError:
                # Circuit breaker is open, don't retry
                logger.error("Circuit breaker is OPEN, blocking LLM call")
                raise

            except Exception as e:
                last_error = e
                logger.warning(
                    f"LLM call attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )

                # Don't retry on last attempt
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)

        # All retries failed
        logger.error(f"LLM call failed after {self.max_retries} attempts")
        raise LLMExecutionError(
            f"LLM call failed after {self.max_retries} attempts. Last error: {last_error}"
        )

    def _call_llm(self, prompt_text: str, **llm_kwargs) -> str:
        """
        Call LLM (internal method)

        Args:
            prompt_text: Prompt text
            **llm_kwargs: LLM arguments

        Returns:
            str: LLM response

        Raises:
            LLMError: If LLM call fails
        """
        try:
            # Create LLM instance
            llm = self.llm_factory.create_llm(**llm_kwargs)

            # Invoke LLM
            logger.debug(f"Invoking LLM with prompt length: {len(prompt_text)}")
            start_time = time.time()

            response = llm.invoke(prompt_text)

            duration = time.time() - start_time
            logger.debug(f"LLM call completed in {duration:.2f}s")

            # Extract content from response
            if hasattr(response, "content"):
                return response.content
            elif isinstance(response, str):
                return response
            else:
                logger.warning(f"Unexpected LLM response type: {type(response)}")
                return str(response)

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise LLMError(f"LLM call failed: {e}")

    def get_circuit_breaker_stats(self) -> Dict[str, Any]:
        """
        Get circuit breaker statistics

        Returns:
            Dict[str, Any]: Circuit breaker stats
        """
        return self.circuit_breaker.get_stats()

    def reset_circuit_breaker(self):
        """Reset circuit breaker to closed state"""
        self.circuit_breaker.reset()
        logger.info("Circuit breaker manually reset")

    def is_available(self) -> bool:
        """
        Check if LLM executor is available

        Returns:
            bool: True if executor is available
        """
        # Check if provider is available
        available_providers = self.llm_factory.get_available_providers()
        if not available_providers:
            logger.warning("No LLM providers available")
            return False

        # Check if circuit breaker is closed
        if self.circuit_breaker.is_open():
            logger.warning("Circuit breaker is OPEN")
            return False

        return True


# Global executor instance
_executor: Optional[LLMExecutor] = None


def get_llm_executor() -> LLMExecutor:
    """
    Get global LLM executor instance

    Returns:
        LLMExecutor: Singleton executor
    """
    global _executor
    if _executor is None:
        _executor = LLMExecutor()
    return _executor
