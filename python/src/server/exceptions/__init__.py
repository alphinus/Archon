"""
Custom exceptions for Archon server.
Provides structured error handling across the application.
"""

from typing import Optional, Dict, Any


class ArchonException(Exception):
    """Base exception for all Archon errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(ArchonException):
    """Database connection or query errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=503,
            details=details
        )


class ValidationError(ArchonException):
    """Input validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=error_details
        )


class AuthenticationError(ArchonException):
    """Authentication failures."""
    
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            status_code=401,
            details=details
        )


class AuthorizationError(ArchonException):
    """Authorization failures."""
    
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details
        )


class NotFoundError(ArchonException):
    """Resource not found."""
    
    def __init__(self, resource: str, identifier: str, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        error_details.update({"resource": resource, "identifier": identifier})
        super().__init__(
            message=f"{resource} not found: {identifier}",
            error_code="NOT_FOUND",
            status_code=404,
            details=error_details
        )


class RateLimitError(ArchonException):
    """Rate limit exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )


class ExternalServiceError(ArchonException):
    """External service (Supabase, Redis, etc.) errors."""
    
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        error_details["service"] = service
        super().__init__(
            message=f"{service} error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=503,
            details=error_details
        )


class CircuitBreakerOpenError(ArchonException):
    """Circuit breaker is open, service unavailable."""
    
    def __init__(self, service: str, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        error_details["service"] = service
        super().__init__(
            message=f"Service temporarily unavailable: {service}",
            error_code="CIRCUIT_BREAKER_OPEN",
            status_code=503,
            details=error_details
        )
