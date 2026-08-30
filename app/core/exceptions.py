from __future__ import annotations

from typing import Any


class CommerceAgentError(Exception):
    """Base exception for all Transact AI errors."""
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the base exception.
        
        Args:
            message: Human-readable error message.
            details: Optional dictionary with additional error details.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        return self.message


class ConfigurationError(CommerceAgentError):
    """Exception raised for configuration errors."""
    code = "CONFIGURATION_ERROR"


class ValidationError(CommerceAgentError):
    """Exception raised for data validation errors."""
    code = "VALIDATION_ERROR"


class NotFoundError(CommerceAgentError):
    """Exception raised when a resource is not found."""
    code = "NOT_FOUND"


class PolicyViolationError(CommerceAgentError):
    """Exception raised when an action violates business policy."""
    code = "POLICY_VIOLATION"


class PaymentError(CommerceAgentError):
    """Exception raised for payment processing errors."""
    code = "PAYMENT_ERROR"


class PaymentVerificationError(PaymentError):
    """Exception raised when payment signature or webhook signature verification fails."""
    code = "PAYMENT_VERIFICATION_FAILED"


class StaleDataError(CommerceAgentError):
    """Exception raised when operating on stale data."""
    code = "STALE_DATA"


class AuthorizationError(CommerceAgentError):
    """Exception raised for authorization failures."""
    code = "AUTHORIZATION_ERROR"
