import httpx
import asyncio
from typing import Dict, Any, Optional, Union
import logging
from contextlib import asynccontextmanager
import time

from .config import settings
from .encryption import encrypt_response_data, decrypt_request_data

logger = logging.getLogger(__name__)


class ServiceDispatcher:
    """Advanced dispatcher for encrypted inter-service communication"""
    
    def __init__(self):
        self.service_urls = {
            "user": settings.user_service_url,
            "analytics": settings.analytics_service_url
        }
        self.client_config = {
            "timeout": httpx.Timeout(30.0, connect=5.0),
            "limits": httpx.Limits(max_keepalive_connections=20, max_connections=100),
            "retries": 3
        }
        self._client_pool = None
    
    @asynccontextmanager
    async def _get_client(self):
        """Get HTTP client with connection pooling"""
        if self._client_pool is None:
            self._client_pool = httpx.AsyncClient(
                timeout=self.client_config["timeout"],
                limits=self.client_config["limits"]
            )
        
        try:
            yield self._client_pool
        except Exception as e:
            logger.error(f"Client error: {e}")
            raise
    
    async def close(self):
        """Close the HTTP client pool"""
        if self._client_pool:
            await self._client_pool.aclose()
            self._client_pool = None
    
    async def _retry_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """Execute request with retry logic"""
        max_retries = self.client_config["retries"]
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Attempting request to {url} (attempt {attempt + 1}/{max_retries + 1})")
                
                if method.upper() == "POST":
                    response = await client.post(url, **kwargs)
                elif method.upper() == "GET":
                    response = await client.get(url, **kwargs)
                elif method.upper() == "PUT":
                    response = await client.put(url, **kwargs)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response
                
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Request failed after {max_retries + 1} attempts: {e}")
                    raise
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Server error {e.response.status_code}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"HTTP error {e.response.status_code}: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error during request: {e}")
                raise
    
    async def send_encrypted_request(
        self,
        service: str,
        endpoint: str,
        data: Dict[str, Any],
        method: str = "POST",
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Send encrypted request to another service with enhanced error handling
        """
        start_time = time.time()
        
        if service not in self.service_urls:
            raise ValueError(f"Unknown service: {service}")
        
        try:
            # Encrypt the payload
            encrypted_payload = encrypt_response_data(data)
            
            # Prepare request
            url = f"{self.service_urls[service]}{endpoint}"
            headers = {
                "X-Service-Communication": "encrypted",
                "Content-Type": "application/json",
                "User-Agent": f"ServiceDispatcher/{settings.app_name}",
                "X-Request-ID": f"{int(time.time() * 1000)}"
            }
            
            request_kwargs = {
                "headers": headers,
                "json": encrypted_payload if method.upper() in ["POST", "PUT"] else None,
                "params": encrypted_payload if method.upper() == "GET" else None
            }
            
            if timeout:
                request_kwargs["timeout"] = timeout
            
            # Send request with retry logic
            async with self._get_client() as client:
                response = await self._retry_request(client, method, url, **request_kwargs)
            
            # Parse response
            response_data = response.json()
            
            # Log successful request
            duration = time.time() - start_time
            logger.info(f"Successfully called {service}{endpoint} in {duration:.2f}s")
            
            # Check if response is encrypted
            if "encrypted_data" in response_data:
                # Decrypt the response
                decrypted_data = decrypt_request_data(response_data["encrypted_data"])
                logger.debug(f"Decrypted response from {service}")
                return decrypted_data
            else:
                # Return as-is if not encrypted
                logger.debug(f"Received unencrypted response from {service}")
                return response_data
                
        except httpx.RequestError as e:
            duration = time.time() - start_time
            logger.error(f"Request error when calling {service}{endpoint} after {duration:.2f}s: {e}")
            raise
        except httpx.HTTPStatusError as e:
            duration = time.time() - start_time
            logger.error(f"HTTP {e.response.status_code} error when calling {service}{endpoint} after {duration:.2f}s: {e}")
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Unexpected error when calling {service}{endpoint} after {duration:.2f}s: {e}")
            raise
    
    async def send_unencrypted_request(
        self,
        service: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Send unencrypted request to another service for public endpoints
        """
        start_time = time.time()
        
        if service not in self.service_urls:
            raise ValueError(f"Unknown service: {service}")
        
        try:
            url = f"{self.service_urls[service]}{endpoint}"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": f"ServiceDispatcher/{settings.app_name}",
                "X-Request-ID": f"{int(time.time() * 1000)}"
            }
            
            request_kwargs = {
                "headers": headers,
                "json": data if method.upper() in ["POST", "PUT"] and data else None,
                "params": data if method.upper() == "GET" and data else None
            }
            
            if timeout:
                request_kwargs["timeout"] = timeout
            
            async with self._get_client() as client:
                response = await self._retry_request(client, method, url, **request_kwargs)
            
            duration = time.time() - start_time
            logger.info(f"Successfully called {service}{endpoint} (unencrypted) in {duration:.2f}s")
            
            return response.json()
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error calling {service}{endpoint} (unencrypted) after {duration:.2f}s: {e}")
            raise
    
    async def call_analytics_service(
        self, 
        endpoint: str, 
        data: Dict[str, Any], 
        encrypted: bool = True,
        method: str = "POST"
    ) -> Dict[str, Any]:
        """Enhanced method to call analytics service"""
        if encrypted:
            return await self.send_encrypted_request("analytics", endpoint, data, method)
        else:
            return await self.send_unencrypted_request("analytics", endpoint, data, method)
    
    async def call_user_service(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None, 
        encrypted: bool = False,
        method: str = "GET"
    ) -> Dict[str, Any]:
        """Enhanced method to call user service"""
        if encrypted:
            return await self.send_encrypted_request("user", endpoint, data or {}, method)
        else:
            return await self.send_unencrypted_request("user", endpoint, data, method)
    
    async def health_check(self, service: str) -> Dict[str, Any]:
        """Check health of a service"""
        try:
            return await self.send_unencrypted_request(service, "/health", method="GET", timeout=5.0)
        except Exception as e:
            logger.error(f"Health check failed for {service}: {e}")
            return {"status": "unhealthy", "error": str(e)}


# Global dispatcher instance
dispatcher = ServiceDispatcher() 