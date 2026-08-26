from __future__ import annotations

from app.core.exceptions import (
    CommerceAgentError,
    ConfigurationError,
    ValidationError,
    NotFoundError,
    PolicyViolationError,
    PaymentError,
    StaleDataError,
    AuthorizationError,
)

def test_base_exception_attributes() -> None:
    """Test the attributes of the base exception."""
    exc = CommerceAgentError("Test error", {"key": "value"})
    assert exc.message == "Test error"
    assert exc.details == {"key": "value"}
    assert exc.code == "INTERNAL_ERROR"

def test_exception_hierarchy() -> None:
    """Test that all specific exceptions subclass the base exception."""
    exceptions = [
        ConfigurationError,
        ValidationError,
        NotFoundError,
        PolicyViolationError,
        PaymentError,
        StaleDataError,
        AuthorizationError,
    ]
    for exc_class in exceptions:
        assert issubclass(exc_class, CommerceAgentError)

def test_policy_violation_error() -> None:
    """Test PolicyViolationError specific code."""
    exc = PolicyViolationError(message="Price exceeds budget", details={"price": 520, "budget": 500})
    assert exc.code == "POLICY_VIOLATION"
    assert exc.message == "Price exceeds budget"
    assert exc.details == {"price": 520, "budget": 500}

def test_exception_str() -> None:
    """Test string representation of exceptions."""
    exc = ValidationError("Invalid data")
    assert str(exc) == "Invalid data"

def test_exception_with_details() -> None:
    """Test exception preserves details dict."""
    details = {"field": "username", "reason": "too short"}
    exc = ValidationError("Validation failed", details=details)
    assert exc.details == details
