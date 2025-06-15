from fastapi import Request, HTTPException
from typing import Optional, Dict, Any
from .encryption import EncryptionManager
from .key_manager import KeyManager
import logging

logger = logging.getLogger(__name__)

async def get_encrypted_payload(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency to automatically decrypt incoming encrypted payloads.
    Expects the payload to be in the format: {"encrypted_data": "encrypted_string"}
    """
    try:
        # Get the service name from headers
        encryption_service = request.headers.get("X-Encryption-Service")
        if not encryption_service:
            # If no encryption service specified, return raw payload
            return await request.json()

        # Get the raw payload
        payload = await request.json()
        if not isinstance(payload, dict) or "encrypted_data" not in payload:
            return payload

        # Initialize key manager for the current service
        service_name = request.headers.get("X-Service-Name", "unknown-service")
        key_manager = KeyManager(service_name)

        # Get the encryption key for the service that encrypted the payload
        encryption_key = key_manager.get_service_key(encryption_service)
        if not encryption_key:
            raise HTTPException(
                status_code=400,
                detail=f"Encryption key not found for service: {encryption_service}"
            )

        # Decrypt the payload
        encryption_manager = EncryptionManager(encryption_key)
        decrypted_data = encryption_manager.decrypt_payload(payload["encrypted_data"])
        
        logger.info(f"Successfully decrypted payload from {encryption_service}")
        return decrypted_data

    except Exception as e:
        logger.error(f"Error decrypting payload: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Error processing encrypted payload: {str(e)}"
        )

def get_encryption_manager(service_name: str) -> EncryptionManager:
    """
    FastAPI dependency to get an encryption manager for the current service.
    Use this when you need to encrypt responses.
    """
    try:
        key_manager = KeyManager(service_name)
        encryption_key = key_manager.get_own_key()
        return EncryptionManager(encryption_key)
    except Exception as e:
        logger.error(f"Error initializing encryption manager: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error initializing encryption: {str(e)}"
        ) 