import aiohttp
import logging
from typing import Any, Dict, Optional, Union
from ..config.models import ServiceConfig, ServiceRegistry, ServiceEndpoint
from ..utils.encryption import EncryptionManager, EncryptionError
from ..utils.retry import RetryManager, CircuitBreaker, CircuitBreakerError
from ..utils.key_manager import KeyManager
from ..exceptions import ServiceCommunicationError, ServiceNotFoundError

logger = logging.getLogger(__name__)

class ServiceClient:
    def __init__(
        self,
        config: ServiceConfig,
        service_registry: Optional[ServiceRegistry] = None
    ):
        """Initialize the service client with configuration and registry"""
        try:
            self.config = config
            self.service_registry = service_registry or ServiceRegistry()
            self.key_manager = KeyManager(config.service_name)
            
            # Initialize circuit breaker with safe defaults
            circuit_breaker = CircuitBreaker(
                failure_threshold=config.circuit_breaker_threshold,
                reset_timeout=config.circuit_breaker_timeout
            )
            
            # Initialize retry manager with circuit breaker
            self.retry_manager = RetryManager(
                max_attempts=config.retry_attempts,
                delay=config.retry_delay,
                strategy=config.retry_strategy.value,
                circuit_breaker=circuit_breaker
            )
            
            logger.info(f"ServiceClient initialized for {config.service_name}")
        except Exception as e:
            logger.error(f"Failed to initialize ServiceClient: {str(e)}")
            raise ServiceCommunicationError(f"Failed to initialize client: {str(e)}")

    def _get_encryption_manager(self, service_name: str) -> EncryptionManager:
        """Get encryption manager for a specific service"""
        try:
            key = self.key_manager.get_service_key(service_name)
            if not key:
                raise ServiceNotFoundError(f"Encryption key not found for service: {service_name}")
            return EncryptionManager(key)
        except Exception as e:
            logger.error(f"Failed to get encryption manager: {str(e)}")
            raise ServiceCommunicationError(f"Encryption error: {str(e)}")

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
        Make a secure request to another service
        
        Encryption flow:
        1. Request: Sender encrypts with sender's key, receiver decrypts with sender's key
        2. Response: Receiver encrypts with receiver's key, sender decrypts with receiver's key
        """
        try:
            # Get service info first to fail fast if service not found
            service = self.service_registry.get_service(target_service)
            url = f"{service.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            # Get encryption managers
            sender_encryption = self._get_encryption_manager(self.config.service_name)
            
            # Prepare headers
            request_headers = {
                "Content-Type": "application/json",
                "X-Service-Name": self.config.service_name,
                "X-Target-Service": target_service,
                "X-Encryption-Service": self.config.service_name,  # Indicates which service's key was used
                **(headers or {})
            }

            # Encrypt payload if present
            if payload is not None:
                try:
                    # Encrypt with sender's (own) key
                    encrypted_payload = sender_encryption.encrypt_payload(payload)
                    request_headers["X-Encrypted-Payload"] = "true"
                    payload = {"encrypted_data": encrypted_payload}
                except Exception as e:
                    logger.error(f"Failed to encrypt payload: {str(e)}")
                    raise ServiceCommunicationError(f"Encryption error: {str(e)}")

            # Make the request with retry and circuit breaker
            @self.retry_manager
            async def _make_request() -> Any:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.request(
                            method=method,
                            url=url,
                            json=payload,
                            headers=request_headers,
                            timeout=timeout or self.config.timeout
                        ) as response:
                            response.raise_for_status()
                            response_data = await response.json()
                            
                            # Decrypt response if it's encrypted
                            if response.headers.get("X-Encrypted-Payload") == "true":
                                if isinstance(response_data, dict):
                                    encrypted_data = response_data.get("encrypted_data")
                                    if not encrypted_data:
                                        raise ServiceCommunicationError("Invalid encrypted response format")
                                    
                                    # Get the service that encrypted the response
                                    encryption_service = response.headers.get("X-Encryption-Service")
                                    if not encryption_service:
                                        raise ServiceCommunicationError("Missing encryption service in response")
                                    
                                    try:
                                        # Decrypt using the encryption service's key
                                        return self._get_encryption_manager(encryption_service).decrypt_payload(
                                            encrypted_data
                                        )
                                    except Exception as e:
                                        logger.error(f"Failed to decrypt response: {str(e)}")
                                        raise ServiceCommunicationError(f"Decryption error: {str(e)}")
                            return response_data
                except aiohttp.ClientError as e:
                    logger.error(f"HTTP error occurred: {str(e)}")
                    raise ServiceCommunicationError(f"HTTP error: {str(e)}")
                except Exception as e:
                    logger.error(f"Request failed: {str(e)}")
                    raise ServiceCommunicationError(f"Request failed: {str(e)}")

            return await _make_request()

        except CircuitBreakerError as e:
            logger.error(f"Circuit breaker is open: {str(e)}")
            raise ServiceCommunicationError(f"Circuit breaker is open: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            raise ServiceCommunicationError(f"Unexpected error: {str(e)}")

    async def health_check(self, target_service: str) -> bool:
        """
        Check the health of a target service
        """
        try:
            service = self.service_registry.get_service(target_service)
            response = await self.request(
                target_service=target_service,
                endpoint=service.health_check_endpoint,
                method="GET"
            )
            return response.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Health check failed for {target_service}: {str(e)}")
            return False 