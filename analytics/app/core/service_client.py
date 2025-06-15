from ms_communicator import ServiceClient, ServiceConfig, ServiceRegistry, ServiceEndpoint
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)

class AnalyticsServiceClient:
    _instance: Optional['AnalyticsServiceClient'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the service client with configuration"""
        # Initialize service registry
        self.registry = ServiceRegistry()
        
        # Register user service
        self.registry.register_service(ServiceEndpoint(
            service_name="user-service",
            base_url="http://user-service:8002",
            health_check_endpoint="/health"
        ))
        
        # Create service configuration
        self.config = ServiceConfig(
            service_name="analytics-service",
            retry_attempts=3,
            retry_delay=1.0,
            timeout=5.0
        )
        
        # Initialize client
        self.client = ServiceClient(self.config, self.registry)
        logger.info("Analytics service client initialized")
    
    async def get_user_details(self, user_id: str) -> Dict[str, Any]:
        """
        Get user details from the user service
        
        Args:
            user_id: The ID of the user
            
        Returns:
            The user details from the user service
        """
        try:
            response = await self.client.request(
                target_service="user-service",
                endpoint=f"/api/v1/users/{user_id}",
                method="GET"
            )
            
            logger.info(f"Successfully retrieved user details for user {user_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to get user details: {str(e)}")
            raise
    
    async def check_user_health(self) -> bool:
        """Check if the user service is healthy"""
        try:
            return await self.client.health_check("user-service")
        except Exception as e:
            logger.error(f"User service health check failed: {str(e)}")
            return False 