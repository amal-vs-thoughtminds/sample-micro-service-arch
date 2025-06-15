from typing import Optional, Dict, Any, AsyncGenerator, Annotated
from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from .db import get_postgres_db
from ms_communicator.utils.encryption import EncryptionManager, EncryptionError
import logging
from app.core.config import settings

from .mongodb import get_mongo_collection

logger = logging.getLogger(__name__)

# Initialize encryption manager with service-specific key
encryption_manager = EncryptionManager(settings.ENCRYPTION_KEY)

# Database dependencies
PostgresDB = Annotated[AsyncSession, Depends(get_postgres_db)]
MongoDB = Annotated[AsyncGenerator, Depends(get_mongo_collection)]

# Encryption manager dependency
def get_encryption_manager() -> EncryptionManager:
    """Get encryption manager instance"""
    try:
        logger.debug(f"USER_SERVICE_ENCRYPTION_KEY value: {settings.USER_SERVICE_ENCRYPTION_KEY} (type: {type(settings.USER_SERVICE_ENCRYPTION_KEY)})")
        return EncryptionManager(settings.USER_SERVICE_ENCRYPTION_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize encryption manager: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize encryption service"
        )

# Decrypted payload dependency
async def get_decrypted_payload(encryption_manager: Annotated[EncryptionManager, Depends(get_encryption_manager)], encrypted_payload: Optional[str] = None) -> Optional[dict]:
    """Decrypt and validate payload (if provided) or return None if not provided"""
    if encrypted_payload is None:
        return None
    try:
        return await encryption_manager.decrypt_payload(encrypted_payload)
    except EncryptionError as e:
        logger.error(f"Decryption error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during decryption: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process encrypted payload"
        )

async def get_optional_decrypted_payload(request: Request) -> Optional[Dict[str, Any]]:
    """Get and decrypt the request payload if it exists"""
    try:
        if not request.headers.get('content-type') == 'application/json':
            return None
            
        encrypted_data = await request.json()
        
        if not isinstance(encrypted_data, dict) or 'encrypted_data' not in encrypted_data:
            return None
            
        decrypted_data = encryption_manager.decrypt_payload(encrypted_data['encrypted_data'])
        return decrypted_data
    except EncryptionError as e:
        logger.error(f"Decryption error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error processing encrypted payload: {str(e)}")
        return None

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async for session in get_postgres_db():
        yield session

async def get_mongo_db():
    """Get MongoDB dependency"""
    return await get_mongo_collection()

async def get_mongo_db_collection(collection_name: str):
    """Get MongoDB collection dependency"""
    return await get_mongo_collection(collection_name) 