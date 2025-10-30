"""
Custom Exceptions for Liquid4G

Hierarchy:
- Liquid4GException (base)
  ├── ConfigurationError
  ├── DatabaseError
  ├── APIError
  │   ├── HuaweiAPIError
  │   └── AuthenticationError
  ├── AgentError
  │   ├── AgentExecutionError
  │   ├── LLMExecutionError
  │   ├── LLMResponseValidationError
  │   └── CircuitBreakerOpenError
  └── ValidationError
"""


class Liquid4GException(Exception):
    """Base exception for all Liquid4G errors"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# Configuration Errors
class ConfigurationError(Liquid4GException):
    """Configuration-related errors"""

    pass


# Database Errors
class DatabaseError(Liquid4GException):
    """Database operation errors"""

    pass


class MigrationError(DatabaseError):
    """Database migration errors"""

    pass


# API Errors
class APIError(Liquid4GException):
    """External API errors"""

    pass


class HuaweiAPIError(APIError):
    """Huawei iMaster MAE API errors"""

    pass


class AuthenticationError(APIError):
    """Authentication failures"""

    pass


class APITimeoutError(APIError):
    """API request timeout"""

    pass


# Agent Errors
class AgentError(Liquid4GException):
    """Agent execution errors"""

    pass


class AgentExecutionError(AgentError):
    """General agent execution failure"""

    pass


class LLMExecutionError(AgentError):
    """LLM execution failure"""

    pass


class LLMResponseValidationError(AgentError):
    """LLM response validation failure"""

    pass


class LLMResponseError(AgentError):
    """LLM response parsing/validation error"""

    pass


class LLMError(AgentError):
    """General LLM error"""

    pass


class CircuitBreakerOpenError(AgentError):
    """Circuit breaker is open, blocking requests"""

    pass


class AgentTimeoutError(AgentError):
    """Agent execution timeout"""

    pass


# Validation Errors
class ValidationError(Liquid4GException):
    """Input validation errors"""

    pass


class ParameterValidationError(ValidationError):
    """Network parameter validation errors"""

    pass


class SafetyConstraintViolationError(ValidationError):
    """Safety constraint violation"""

    pass


# Domain Errors
class DomainError(Liquid4GException):
    """Domain logic errors"""

    pass


class KPIError(DomainError):
    """KPI-related errors"""

    pass


class ParameterError(DomainError):
    """Parameter-related errors"""

    pass


class OptimizationError(DomainError):
    """Optimization logic errors"""

    pass
