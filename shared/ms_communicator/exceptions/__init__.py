"""
Exception classes for microservice communication.
"""

class ServiceCommunicationError(Exception):
    """Base exception for service communication errors"""
    pass

class ServiceNotFoundError(ServiceCommunicationError):
    """Raised when a service is not found in the registry"""
    pass

class ServiceUnavailableError(ServiceCommunicationError):
    """Raised when a service is unavailable or not responding"""
    pass

class InvalidPayloadError(ServiceCommunicationError):
    """Raised when the payload is invalid or cannot be processed"""
    pass

class ConfigurationError(ServiceCommunicationError):
    """Raised when there is a configuration error"""
    pass

class AuthenticationError(ServiceCommunicationError):
    """Raised when there is an authentication error"""
    pass

class AuthorizationError(ServiceCommunicationError):
    """Raised when there is an authorization error"""
    pass

__all__ = [
    "ServiceCommunicationError",
    "ServiceNotFoundError",
    "ServiceUnavailableError",
    "InvalidPayloadError",
    "ConfigurationError",
    "AuthenticationError",
    "AuthorizationError",
]
