"""
Custom exceptions for fail-fast error handling.

All exceptions provide clear, actionable error messages for troubleshooting.
No silent failures or fallback to dummy data.
"""

from typing import Any


class CassavaOptimiserError(Exception):
    """Base exception for all Cassava Optimiser errors."""
    
    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        self.cause = cause
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Format the full error message with details."""
        msg = self.message
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            msg = f"{msg} [{details_str}]"
        if self.cause:
            msg = f"{msg} (caused by: {self.cause})"
        return msg


class ConfigurationError(CassavaOptimiserError):
    """
    Raised when configuration is missing or invalid.
    
    Examples:
        - Missing required environment variables
        - Invalid YAML configuration files
        - Incompatible settings combinations
    """
    pass


class NetworkError(CassavaOptimiserError):
    """
    Base class for network-related errors.
    
    Examples:
        - Connection timeouts
        - DNS resolution failures
        - SSL/TLS errors
    """
    pass


class TimeoutError(CassavaOptimiserError):
    """
    Raised when an operation times out.
    
    Used for LLM calls, API requests, and database operations
    that exceed their configured timeout duration.
    """
    
    def __init__(
        self,
        message: str,
        *,
        timeout_seconds: int | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        super().__init__(message, details=details, **kwargs)
        self.timeout_seconds = timeout_seconds
        self.operation = operation


class HuaweiAPIError(NetworkError):
    """
    Raised when Huawei iMaster MAE API calls fail.
    
    Includes HTTP status code and response details for debugging.
    """
    
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: str | None = None,
        endpoint: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if status_code is not None:
            details["status_code"] = status_code
        if endpoint:
            details["endpoint"] = endpoint
        if response_body:
            # Truncate large responses
            details["response"] = response_body[:500] if len(response_body) > 500 else response_body
        super().__init__(message, details=details, **kwargs)
        self.status_code = status_code
        self.response_body = response_body
        self.endpoint = endpoint

    @classmethod
    def connection_failed(cls, host: str, cause: Exception | None = None) -> "HuaweiAPIError":
        """Create an error for connection failures."""
        return cls(
            f"Failed to connect to Huawei MAE at {host}. "
            "Verify the host is reachable and credentials are correct.",
            endpoint=host,
            cause=cause,
        )
    
    @classmethod
    def authentication_failed(cls, username: str) -> "HuaweiAPIError":
        """Create an error for authentication failures."""
        return cls(
            f"Authentication failed for user '{username}'. "
            "Check HUAWEI_MAE_USERNAME and HUAWEI_MAE_PASSWORD environment variables.",
            status_code=401,
            details={"username": username},
        )
    
    @classmethod
    def rate_limited(cls, retry_after: int | None = None) -> "HuaweiAPIError":
        """Create an error for rate limiting."""
        msg = "Huawei MAE API rate limit exceeded."
        if retry_after:
            msg += f" Retry after {retry_after} seconds."
        return cls(msg, status_code=429, details={"retry_after": retry_after})


class LLMError(NetworkError):
    """
    Raised when NVIDIA NIM LLM calls fail.
    
    Includes model and prompt context for debugging.
    """
    
    def __init__(
        self,
        message: str,
        *,
        model: str | None = None,
        prompt_length: int | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if model:
            details["model"] = model
        if prompt_length:
            details["prompt_length"] = prompt_length
        super().__init__(message, details=details, **kwargs)
        self.model = model
        self.prompt_length = prompt_length

    @classmethod
    def api_key_invalid(cls) -> "LLMError":
        """Create an error for invalid API key."""
        return cls(
            "NVIDIA NIM API key is invalid or expired. "
            "Check NVIDIA_API_KEY environment variable.",
            details={"action": "Verify API key at build.nvidia.com"},
        )
    
    @classmethod
    def model_unavailable(cls, model: str) -> "LLMError":
        """Create an error for unavailable model."""
        return cls(
            f"Model '{model}' is not available. "
            "Check NVIDIA_MODEL environment variable or model availability.",
            model=model,
        )
    
    @classmethod
    def context_too_long(cls, model: str, prompt_length: int) -> "LLMError":
        """Create an error for context length exceeded."""
        return cls(
            f"Prompt exceeds model context window. Consider reducing input size.",
            model=model,
            prompt_length=prompt_length,
        )


class DatabaseError(CassavaOptimiserError):
    """
    Raised when database operations fail.
    
    Examples:
        - Connection failures
        - Query errors
        - Migration failures
    """
    
    def __init__(
        self,
        message: str,
        *,
        table: str | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if table:
            details["table"] = table
        if operation:
            details["operation"] = operation
        super().__init__(message, details=details, **kwargs)

    @classmethod
    def not_initialized(cls) -> "DatabaseError":
        """Create an error for uninitialized database."""
        return cls(
            "Database not initialized. Run 'python -m cassava_optimizer.scripts.init_db' first.",
            operation="connection",
        )
    
    @classmethod
    def table_not_found(cls, table: str) -> "DatabaseError":
        """Create an error for missing table."""
        return cls(
            f"Table '{table}' not found. Database may need reinitialization.",
            table=table,
            operation="query",
        )


class KPIAnalysisError(CassavaOptimiserError):
    """
    Raised when KPI analysis fails.
    
    Examples:
        - Missing KPI data
        - Invalid threshold configuration
        - Calculation errors
    """
    
    def __init__(
        self,
        message: str,
        *,
        kpi_name: str | None = None,
        site_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if kpi_name:
            details["kpi"] = kpi_name
        if site_id:
            details["site_id"] = site_id
        super().__init__(message, details=details, **kwargs)


class MMLCommandError(CassavaOptimiserError):
    """
    Raised when MML command generation or execution fails.
    
    Examples:
        - Invalid parameter values
        - Command syntax errors
        - Execution failures
    """
    
    def __init__(
        self,
        message: str,
        *,
        command: str | None = None,
        cell_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if command:
            # Truncate long commands
            details["command"] = command[:200] if len(command) > 200 else command
        if cell_id:
            details["cell_id"] = cell_id
        super().__init__(message, details=details, **kwargs)

    @classmethod
    def validation_failed(cls, command: str, reason: str) -> "MMLCommandError":
        """Create an error for command validation failure."""
        return cls(
            f"MML command validation failed: {reason}",
            command=command,
        )
    
    @classmethod
    def execution_failed(cls, command: str, error_response: str) -> "MMLCommandError":
        """Create an error for command execution failure."""
        return cls(
            f"MML command execution failed: {error_response}",
            command=command,
        )


class ValidationError(CassavaOptimiserError):
    """
    Raised when input validation fails.
    
    Examples:
        - Invalid site ID format
        - Out-of-range parameter values
        - Missing required fields
    """
    
    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        value: Any = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, details=details, **kwargs)

    @classmethod
    def invalid_site_id(cls, site_id: str) -> "ValidationError":
        """Create an error for invalid site ID."""
        return cls(
            f"Invalid site ID format: '{site_id}'. Expected format: XXXX-XXXX or alphanumeric.",
            field="site_id",
            value=site_id,
        )
    
    @classmethod
    def parameter_out_of_range(
        cls, param: str, value: float, min_val: float, max_val: float
    ) -> "ValidationError":
        """Create an error for out-of-range parameter."""
        return cls(
            f"Parameter '{param}' value {value} is out of range [{min_val}, {max_val}].",
            field=param,
            value=value,
            details={"min": min_val, "max": max_val},
        )


class AgentExecutionError(CassavaOptimiserError):
    """
    Raised when an agent fails to execute its task.
    
    Examples:
        - LLM call failures
        - Tool execution errors
        - Timeout during agent processing
    """
    
    def __init__(
        self,
        message: str,
        *,
        agent_type: str | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if agent_type:
            details["agent_type"] = agent_type
        if operation:
            details["operation"] = operation
        super().__init__(message, details=details, **kwargs)
        self.agent_type = agent_type
        self.operation = operation


class WorkflowError(CassavaOptimiserError):
    """
    Raised when workflow orchestration fails.
    
    Examples:
        - Agent execution failures
        - State transition errors
        - Timeout conditions
    """
    
    def __init__(
        self,
        message: str,
        *,
        agent: str | None = None,
        state: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if agent:
            details["agent"] = agent
        if state:
            details["state"] = state
        super().__init__(message, details=details, **kwargs)


class SiteNotFoundError(CassavaOptimiserError):
    """Raised when a requested site cannot be found."""
    
    def __init__(self, site_id: str) -> None:
        super().__init__(
            f"Site '{site_id}' not found in the network inventory.",
            details={"site_id": site_id, "action": "Verify site ID or refresh network data"},
        )
        self.site_id = site_id


class CellNotFoundError(CassavaOptimiserError):
    """Raised when a requested cell cannot be found."""
    
    def __init__(self, cell_id: str, site_id: str | None = None) -> None:
        details = {"cell_id": cell_id}
        if site_id:
            details["site_id"] = site_id
        super().__init__(
            f"Cell '{cell_id}' not found.",
            details=details,
        )
        self.cell_id = cell_id
        self.site_id = site_id
