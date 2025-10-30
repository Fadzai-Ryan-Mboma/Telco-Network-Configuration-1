"""
LLM Response Parser

Parses and validates LLM responses using Pydantic models.
"""

import json
from typing import TypeVar, Type, Optional, Any, Dict
from pydantic import BaseModel, ValidationError

from liquid4g.core.logging import get_logger
from liquid4g.core.exceptions import LLMResponseError

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class ResponseParser:
    """
    Parse and validate LLM responses

    Features:
    - JSON extraction from text
    - Pydantic validation
    - Error handling and logging
    - Fallback parsing strategies
    """

    def parse_json(self, text: str, model: Type[T]) -> T:
        """
        Parse JSON response and validate with Pydantic model

        Args:
            text: LLM response text (may contain JSON)
            model: Pydantic model class for validation

        Returns:
            T: Validated model instance

        Raises:
            LLMResponseError: If parsing or validation fails
        """
        # Extract JSON from text
        json_str = self._extract_json(text)

        if not json_str:
            raise LLMResponseError(
                f"No valid JSON found in response. Response preview: {text[:200]}"
            )

        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}\nJSON: {json_str[:500]}")
            raise LLMResponseError(f"Invalid JSON in response: {e}")

        # Validate with Pydantic
        try:
            instance = model.model_validate(data)
            logger.debug(f"Successfully parsed response as {model.__name__}")
            return instance

        except ValidationError as e:
            logger.error(f"Pydantic validation error: {e}\nData: {data}")
            raise LLMResponseError(f"Response validation failed: {e}")

    def parse_dict(self, text: str) -> Dict[str, Any]:
        """
        Parse JSON response as dictionary (no validation)

        Args:
            text: LLM response text

        Returns:
            Dict[str, Any]: Parsed dictionary

        Raises:
            LLMResponseError: If parsing fails
        """
        json_str = self._extract_json(text)

        if not json_str:
            raise LLMResponseError("No valid JSON found in response")

        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                raise LLMResponseError(f"Expected dict, got {type(data)}")
            return data

        except json.JSONDecodeError as e:
            raise LLMResponseError(f"Invalid JSON in response: {e}")

    def _extract_json(self, text: str) -> Optional[str]:
        """
        Extract JSON from text

        Tries multiple strategies:
        1. Entire text is JSON
        2. JSON wrapped in code blocks (```json ... ```)
        3. First {...} or [...] block found

        Args:
            text: Text containing JSON

        Returns:
            Optional[str]: Extracted JSON string or None
        """
        text = text.strip()

        # Strategy 1: Entire text is JSON
        if (text.startswith("{") and text.endswith("}")) or \
           (text.startswith("[") and text.endswith("]")):
            return text

        # Strategy 2: JSON in code blocks
        if "```json" in text or "```" in text:
            json_str = self._extract_from_code_block(text)
            if json_str:
                return json_str

        # Strategy 3: Find first {...} or [...] block
        json_str = self._extract_first_json_object(text)
        if json_str:
            return json_str

        return None

    def _extract_from_code_block(self, text: str) -> Optional[str]:
        """
        Extract JSON from markdown code block

        Args:
            text: Text containing code block

        Returns:
            Optional[str]: Extracted JSON or None
        """
        # Look for ```json ... ``` or ``` ... ```
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        return None

    def _extract_first_json_object(self, text: str) -> Optional[str]:
        """
        Extract first JSON object or array from text

        Args:
            text: Text containing JSON

        Returns:
            Optional[str]: Extracted JSON or None
        """
        # Try to find { ... } block
        brace_start = text.find("{")
        if brace_start >= 0:
            # Find matching closing brace
            brace_count = 0
            for i in range(brace_start, len(text)):
                if text[i] == "{":
                    brace_count += 1
                elif text[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        return text[brace_start:i+1]

        # Try to find [ ... ] block
        bracket_start = text.find("[")
        if bracket_start >= 0:
            # Find matching closing bracket
            bracket_count = 0
            for i in range(bracket_start, len(text)):
                if text[i] == "[":
                    bracket_count += 1
                elif text[i] == "]":
                    bracket_count -= 1
                    if bracket_count == 0:
                        return text[bracket_start:i+1]

        return None

    def safe_parse(
        self,
        text: str,
        model: Type[T],
        default: Optional[T] = None
    ) -> Optional[T]:
        """
        Parse response with fallback to default on error

        Args:
            text: LLM response text
            model: Pydantic model class
            default: Default value if parsing fails

        Returns:
            Optional[T]: Parsed model or default
        """
        try:
            return self.parse_json(text, model)
        except LLMResponseError as e:
            logger.warning(f"Failed to parse response, using default: {e}")
            return default


# Response models for common LLM outputs

class MonitoringIssue(BaseModel):
    """Single monitoring issue"""
    kpi_key: str
    current_value: float
    threshold_value: float
    severity: str  # critical/warning/info
    trend: Optional[str] = None  # increasing/decreasing/stable
    priority: str  # high/medium/low


class MonitoringResponse(BaseModel):
    """Response from monitor agent"""
    issues: list[MonitoringIssue]
    cells_requiring_attention: list[str]
    summary: str


class RootCause(BaseModel):
    """Root cause analysis result"""
    issue: str
    likely_cause: str
    supporting_data: str


class ParameterChange(BaseModel):
    """Recommended parameter change"""
    param_key: str
    current_value: float
    recommended_value: float
    expected_improvement: str
    risk_level: str  # low/medium/high
    justification: str


class AnalysisResponse(BaseModel):
    """Response from analyzer agent"""
    root_causes: list[RootCause]
    recommended_changes: list[ParameterChange]
    summary: str


class CommandSet(BaseModel):
    """MML command set"""
    pre_change_commands: list[str]
    modification_commands: list[str]
    verification_commands: list[str]
    rollback_commands: list[str]
    execution_notes: Optional[str] = None


class ParameterValidation(BaseModel):
    """Single parameter validation result"""
    param_key: str
    proposed_value: float
    is_valid: bool
    within_range: bool
    no_conflicts: bool
    validation_notes: str


class ValidationResponse(BaseModel):
    """Response from validation agent"""
    validation_results: list[ParameterValidation]
    overall_assessment: str  # approved/rejected/conditional
    risk_level: str  # low/medium/high
    approval_decision: str  # approved/rejected
    conditions: list[str] = []
    rejection_reasons: list[str] = []


class CommandExecution(BaseModel):
    """Single command execution result"""
    command: str
    status: str  # success/failed
    timestamp: str
    error_message: Optional[str] = None


class ExecutionResponse(BaseModel):
    """Response from execution agent"""
    execution_status: str  # completed/failed/rolled_back
    commands_executed: list[CommandExecution]
    rollback_required: bool
    post_change_kpis: Dict[str, Any] = {}
    execution_notes: str


# Global parser instance
_parser: Optional[ResponseParser] = None


def get_response_parser() -> ResponseParser:
    """
    Get global response parser instance

    Returns:
        ResponseParser: Singleton parser
    """
    global _parser
    if _parser is None:
        _parser = ResponseParser()
    return _parser
