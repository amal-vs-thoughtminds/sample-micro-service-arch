from typing import Any, Dict, Optional, Union
from ..config.models import ServiceConfig
from ..config.service_registry import get_service_registry, initialize_registry
from .client import ServiceClient
from ..exceptions import ServiceCommunicationError
import logging

logger = logging.getLogger(__name__)

class MicroServiceClient:
    """A robust client for microservice-to-microservice communication"""
    _instances: Dict[str, 'MicroServiceClient'] = {}
    
    def __new__(cls, service_name: str):
        """Get or create a singleton instance for the service"""
        try:
            if service_name not in cls._instances:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instances[service_name] = instance
                instance._initialize(service_name)
            return cls._instances[service_name]
        except Exception as e:
            logger.error(f"Failed to create MicroServiceClient for {service_name}: {str(e)}")
            raise ServiceCommunicationError(f"Failed to initialize client: {str(e)}")
    
    def _initialize(self, service_name: str):
        """Initialize the client with service-specific configuration"""
        if self._initialized:
            return
            
        try:
            # Initialize the registry if not already done
            initialize_registry()
            
            # Create service configuration with robust defaults
            self.config = ServiceConfig(
                service_name=service_name,
                retry_attempts=3,
                retry_delay=1.0,
                timeout=5.0,
                circuit_breaker_threshold=5,
                circuit_breaker_timeout=30.0
            )
            
            # Initialize the client with registry
            self.client = ServiceClient(
                config=self.config,
                service_registry=get_service_registry()
            )
            
            self._initialized = True
            logger.info(f"MicroServiceClient initialized for {service_name}")
        except Exception as e:
            logger.error(f"Failed to initialize MicroServiceClient for {service_name}: {str(e)}")
            raise ServiceCommunicationError(f"Failed to initialize client: {str(e)}")
    
    async def request(
        self,
        target_service: str,
        endpoint: str,
        method: str = "GET",
        payload: Optional[Union[Dict[str, Any], Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Make a secure request to another microservice
        
        Args:
            target_service: Name of the target service
            endpoint: API endpoint to call
            method: HTTP method (GET, POST, etc.)
            payload: Request payload
            headers: Additional headers
            timeout: Request timeout in seconds
            
        Returns:
            Decrypted response from the target service
            
        Raises:
            ServiceCommunicationError: If the request fails
            ServiceNotFoundError: If the target service is not found
            ServiceUnavailableError: If the target service is unavailable
        """
        if not self._initialized:
            raise ServiceCommunicationError("Client not properly initialized")
            
        try:
            return await self.client.request(
                target_service=target_service,
                endpoint=endpoint,
                method=method,
                payload=payload,
                headers=headers,
                timeout=timeout
            )
        except Exception as e:
            logger.error(f"Request to {target_service} failed: {str(e)}")
            raise ServiceCommunicationError(f"Request failed: {str(e)}")
    
    async def health_check(self, target_service: str) -> bool:
        """
        Check if a target service is healthy
        
        Args:
            target_service: Name of the service to check
            
        Returns:
            True if service is healthy, False otherwise
        """
        if not self._initialized:
            raise ServiceCommunicationError("Client not properly initialized")
            
        try:
            return await self.client.health_check(target_service)
        except Exception as e:
            logger.error(f"Health check for {target_service} failed: {str(e)}")
            return False
    
    def list_available_services(self) -> Dict[str, str]:
        """
        List all registered services and their base URLs
        
        Returns:
            Dictionary mapping service names to their base URLs
        """
        if not self._initialized:
            raise ServiceCommunicationError("Client not properly initialized")
            
        try:
            return get_service_registry().list_services()
        except Exception as e:
            logger.error(f"Failed to list services: {str(e)}")
            raise ServiceCommunicationError(f"Failed to list services: {str(e)}")
    
    @classmethod
    def get_instance(cls, service_name: str) -> 'MicroServiceClient':
        """
        Get an existing instance or create a new one
        
        Args:
            service_name: Name of the service
            
        Returns:
            MicroServiceClient instance for the service
            
        Raises:
            ServiceCommunicationError: If initialization fails
        """
        return cls(service_name)
    
    @classmethod
    def clear_instances(cls) -> None:
        """Clear all client instances (useful for testing)"""
        cls._instances.clear()
        logger.info("Cleared all MicroServiceClient instances") 