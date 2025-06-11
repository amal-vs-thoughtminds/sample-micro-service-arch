from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, AsyncGenerator
import json
import logging

from .db import get_postgres_db
from .mongodb import get_mongodb, get_mongo_collection
from .encryption import decrypt_request_data

logger = logging.getLogger(__name__)


async def get_decrypted_payload(request: Request) -> Optional[Dict[str, Any]]:
    """
    Dependency to automatically decrypt request payload if it's encrypted.
    Returns None if not encrypted, or the decrypted data if encrypted.
    """
    if request.headers.get("X-Service-Communication") == "encrypted":
        try:
            body = await request.json()
            if "encrypted_data" in body:
                return decrypt_request_data(body["encrypted_data"])
        except Exception as e:
            logger.error(f"Failed to decrypt request: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to decrypt request data"
            )
    return None


async def get_optional_decrypted_payload(request: Request) -> Optional[Dict[str, Any]]:
    """
    Optional dependency for endpoints that may or may not need encryption.
    Only decrypts if X-Encrypt-Response header is present or service communication.
    """
    # Only decrypt if client specifically requests encrypted communication
    if (request.headers.get("X-Encrypt-Response") == "true" or 
        request.headers.get("X-Service-Communication") == "encrypted"):
        try:
            return await get_decrypted_payload(request)
        except:
            # If decryption fails, just return None (handle as regular request)
            return None
    
    return None


def get_db_session() -> AsyncSession:
    """Get database session dependency"""
    return Depends(get_postgres_db)


async def get_mongo_db():
    """Get MongoDB dependency"""
    return await get_mongodb()


async def get_mongo_db_collection(collection_name: str):
    """Get MongoDB collection dependency"""
    return await get_mongo_collection(collection_name) 