"""
Core Module

Provides core functionality for microservice communication.
"""

from .registry import (
    ServiceRegistry,
    register_service,
    get_service,
    list_services,
    update_service_status,
    remove_service,
)

__all__ = [
    "ServiceRegistry",
    "register_service",
    "get_service",
    "list_services",
    "update_service_status",
    "remove_service",
]
