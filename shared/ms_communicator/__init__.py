"""
Microservice Communication Library
=================================

A secure, maintainable library for microservice-to-microservice communication.
Provides encryption, service discovery, and robust error handling.

Version: 1.0.0
"""

__version__ = "1.0.0"

# Initialize service registry on import
from .core.registry import ServiceRegistry
service_registry = ServiceRegistry()

# Core components
from .core.client import ServiceClient
from .core.micro_client import MicroServiceClient
from .utils.encryption import EncryptionManager
from .utils.middleware import EncryptionMiddleware

# Import exceptions
from .exceptions import (
    ServiceCommunicationError,
    ServiceNotFoundError,
    ServiceUnavailableError,
    InvalidPayloadError,
    ConfigurationError,
    AuthenticationError,
    AuthorizationError,
)

# Service registry functions
def register_service(name: str, url: str) -> None:
    """Register a service with the registry"""
    service_registry.register(name, url)

def get_service(name: str) -> dict:
    """Get service information from the registry"""
    return service_registry.get(name)

def list_services() -> list:
    """List all registered services"""
    return service_registry.list_services()

def update_service_status(name: str, status: str) -> None:
    """Update service status in the registry"""
    service_registry.update_status(name, status)

def remove_service(name: str) -> None:
    """Remove a service from the registry"""
    service_registry.remove(name)

__all__ = [
    # Version
    "__version__",
    
    # Core components
    "ServiceClient",
    "MicroServiceClient",
    "EncryptionManager",
    "ServiceRegistry",
    "EncryptionMiddleware",
    "service_registry",
    
    # Service registry functions
    "register_service",
    "get_service",
    "list_services",
    "update_service_status",
    "remove_service",
    
    # Exceptions
    "ServiceCommunicationError",
    "ServiceNotFoundError",
    "ServiceUnavailableError",
    "InvalidPayloadError",
    "ConfigurationError",
    "AuthenticationError",
    "AuthorizationError",
]
