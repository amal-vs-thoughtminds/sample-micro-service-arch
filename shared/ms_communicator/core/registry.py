"""
Service Registry Module

Provides service registration and discovery functionality.
"""

from typing import Dict, List, Optional
import logging
from ..exceptions import ServiceNotFoundError, ServiceUnavailableError

logger = logging.getLogger(__name__)

class ServiceRegistry:
    """Singleton service registry for managing microservice endpoints."""
    
    _instance = None
    _services: Dict[str, dict] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceRegistry, cls).__new__(cls)
            logger.info("Initializing service registry")
        return cls._instance
    
    def register(self, service_name: str, service_url: str, metadata: Optional[dict] = None) -> None:
        """
        Register a service in the registry.
        
        Args:
            service_name: Name of the service
            service_url: URL where the service can be reached
            metadata: Optional metadata about the service
        """
        if service_name in self._services:
            logger.warning(f"Service {service_name} already registered, updating...")
        
        self._services[service_name] = {
            "url": service_url,
            "metadata": metadata or {},
            "status": "active"
        }
        logger.info(f"Service {service_name} registered at {service_url}")
    
    def get(self, service_name: str) -> dict:
        """
        Get service information from the registry.
        
        Args:
            service_name: Name of the service to look up
            
        Returns:
            dict: Service information including URL and metadata
            
        Raises:
            ServiceNotFoundError: If the service is not registered
            ServiceUnavailableError: If the service is registered but marked as unavailable
        """
        if service_name not in self._services:
            raise ServiceNotFoundError(f"Service {service_name} not found in registry")
        
        service = self._services[service_name]
        if service["status"] != "active":
            raise ServiceUnavailableError(f"Service {service_name} is not available")
        
        return service
    
    def list_services(self) -> List[str]:
        """
        List all registered services.
        
        Returns:
            List[str]: List of service names
        """
        return list(self._services.keys())
    
    def update_status(self, service_name: str, status: str) -> None:
        """
        Update the status of a registered service.
        
        Args:
            service_name: Name of the service
            status: New status (e.g., "active", "unavailable")
            
        Raises:
            ServiceNotFoundError: If the service is not registered
        """
        if service_name not in self._services:
            raise ServiceNotFoundError(f"Service {service_name} not found in registry")
        
        self._services[service_name]["status"] = status
        logger.info(f"Service {service_name} status updated to {status}")
    
    def remove(self, service_name: str) -> None:
        """
        Remove a service from the registry.
        
        Args:
            service_name: Name of the service to remove
            
        Raises:
            ServiceNotFoundError: If the service is not registered
        """
        if service_name not in self._services:
            raise ServiceNotFoundError(f"Service {service_name} not found in registry")
        
        del self._services[service_name]
        logger.info(f"Service {service_name} removed from registry")

# Convenience functions for the singleton instance
def register_service(service_name: str, service_url: str, metadata: Optional[dict] = None) -> None:
    """Register a service in the registry."""
    ServiceRegistry().register(service_name, service_url, metadata)

def get_service(service_name: str) -> dict:
    """Get service information from the registry."""
    return ServiceRegistry().get(service_name)

def list_services() -> List[str]:
    """List all registered services."""
    return ServiceRegistry().list_services()

def update_service_status(service_name: str, status: str) -> None:
    """Update the status of a registered service."""
    ServiceRegistry().update_status(service_name, status)

def remove_service(service_name: str) -> None:
    """Remove a service from the registry."""
    ServiceRegistry().remove(service_name) 