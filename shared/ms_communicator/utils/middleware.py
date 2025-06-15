from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import json
import logging
from .dependencies import get_encryption_manager

logger = logging.getLogger(__name__)

class EncryptionMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        service_name: str,
        encrypt_responses: bool = True
    ):
        super().__init__(app)
        self.service_name = service_name
        self.encrypt_responses = encrypt_responses
        self.encryption_manager = get_encryption_manager(service_name)
        
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Store whether the request was encrypted
        request.state.was_encrypted = request.headers.get("X-Encrypted-Payload") == "true"
        
        # Get the original response
        response = await call_next(request)
        
        # If the request was encrypted and we should encrypt responses
        if request.state.was_encrypted and self.encrypt_responses:
            try:
                # Get the response body
                response_body = [chunk async for chunk in response.body_iterator]
                response.body_iterator = iterate_in_threadpool(response_body)
                
                # Parse the response body
                try:
                    body = json.loads(response_body[0].decode())
                except json.JSONDecodeError:
                    # If response is not JSON, return as is
                    return response
                
                # Encrypt the response
                encrypted_data = self.encryption_manager.encrypt_payload(body)
                
                # Create new response with encrypted data
                new_response = Response(
                    content=json.dumps({"encrypted_data": encrypted_data}),
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
                # Add encryption headers
                new_response.headers["X-Encrypted-Payload"] = "true"
                new_response.headers["X-Encryption-Service"] = self.service_name
                
                logger.debug(f"Encrypted response for {request.url.path}")
                return new_response
                
            except Exception as e:
                logger.error(f"Failed to encrypt response: {str(e)}")
                # Return original response if encryption fails
                return response
        
        return response

def iterate_in_threadpool(iterator):
    """Helper function to iterate over response body chunks"""
    for chunk in iterator:
        yield chunk 