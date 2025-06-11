import json
import base64
from typing import Dict, Any
from cryptography.fernet import Fernet
import logging

from .config import settings

logger = logging.getLogger(__name__)


class EncryptionManager:
    def __init__(self, encryption_key: str):
        # Ensure key is 32 bytes for Fernet
        key_bytes = encryption_key.encode()[:32]
        key_bytes = key_bytes.ljust(32, b'0')  # Pad to 32 bytes if shorter
        self.fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
    
    def encrypt_data(self, data: Dict[str, Any]) -> str:
        """Encrypt data for transmission"""
        try:
            json_data = json.dumps(data, default=str)
            encrypted_data = self.fernet.encrypt(json_data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt received data"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise


# Global encryption manager instance
encryption_manager = EncryptionManager(settings.encryption_key)


def encrypt_response_data(data: Dict[str, Any]) -> Dict[str, str]:
    """Encrypt response data to send to other services"""
    return {
        "encrypted_data": encryption_manager.encrypt_data(data)
    }


def decrypt_request_data(encrypted_data: str) -> Dict[str, Any]:
    """Decrypt incoming data from other services"""
    return encryption_manager.decrypt_data(encrypted_data)


def is_encrypted_request(headers: dict) -> bool:
    """Check if request is encrypted"""
    return headers.get("X-Service-Communication") == "encrypted" 