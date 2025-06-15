from typing import Dict, Optional
from pydantic import BaseModel, Field
from .models import ServiceEndpoint

class ServiceRegistryConfig(BaseModel):
    """Central configuration for all microservices"""
    services: Dict[str, ServiceEndpoint] = Field(default_factory=dict)
    
    def register_service(self, service: ServiceEndpoint) -> None:
        """Register a new service"""
        self.services[service.service_name] = service
    
    def get_service(self, service_name: str) -> ServiceEndpoint:
        """Get a registered service"""
        if service_name not in self.services:
            raise KeyError(f"Service {service_name} not found in registry")
        return self.services[service_name]
    
    def get_service_url(self, service_name: str, endpoint: str = "") -> str:
        """Get the full URL for a service endpoint"""
        service = self.get_service(service_name)
        return f"{service.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    def list_services(self) -> Dict[str, str]:
        """List all registered services and their base URLs"""
        return {name: service.base_url for name, service in self.services.items()}

# Create a singleton instance
_registry: Optional[ServiceRegistryConfig] = None

def get_service_registry() -> ServiceRegistryConfig:
    """Get or create the service registry singleton"""
    global _registry
    if _registry is None:
        _registry = ServiceRegistryConfig()
    return _registry

# Pre-register common services
def initialize_registry() -> ServiceRegistryConfig:
    """Initialize the registry with common services"""
    registry = get_service_registry()
    
    # Register user service
    registry.register_service(ServiceEndpoint(
        service_name="user-service",
        base_url="http://user-service:8002",
        health_check_endpoint="/health",
        version="v1"
    ))
    
    # Register analytics service
    registry.register_service(ServiceEndpoint(
        service_name="analytics-service",
        base_url="http://analytics-service:8000",
        health_check_endpoint="/health",
        version="v1"
    ))
    
    
    return registry 