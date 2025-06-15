import base64
import json
import os
from typing import Any, Dict, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class EncryptionError(Exception):
    """Base exception for encryption related errors"""
    pass

class EncryptionManager:
    def __init__(self, key: str):
        """Initialize encryption manager with a key"""
        # Derive a 256-bit (32 bytes) key for AESGCM
        self.key = self._derive_key(key)
        # Create Fernet instance for signing (using a different key)
        self.fernet = Fernet(Fernet.generate_key())
        # Create AESGCM instance with the derived key
        self.aesgcm = AESGCM(self.key)

    def _derive_key(self, key: str) -> bytes:
        """Derive a secure 256-bit key from the input key"""
        salt = b'priscope_salt'  # In production, use a secure random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for AESGCM
            salt=salt,
            iterations=100000,
        )
        # Use the raw derived key for AESGCM
        return kdf.derive(key.encode())

    def encrypt_payload(self, payload: Union[Dict[str, Any], Any]) -> str:
        """Encrypt a payload and return it as a base64 string"""
        try:
            # Convert payload to JSON string if it's a dict
            if isinstance(payload, dict):
                payload_str = json.dumps(payload)
            else:
                payload_str = str(payload)

            # Generate a random nonce (12 bytes for AESGCM)
            nonce = os.urandom(12)
            
            # Encrypt the payload
            ciphertext = self.aesgcm.encrypt(
                nonce,
                payload_str.encode(),
                None  # No associated data
            )
            
            # Combine nonce and ciphertext
            encrypted_data = nonce + ciphertext
            
            # Return as base64 string
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt payload: {str(e)}")

    def decrypt_payload(self, encrypted_data: str) -> Union[Dict[str, Any], str]:
        """Decrypt a base64 encoded encrypted payload"""
        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Extract nonce (12 bytes) and ciphertext
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]
            
            # Decrypt
            decrypted_bytes = self.aesgcm.decrypt(
                nonce,
                ciphertext,
                None  # No associated data
            )
            
            # Try to parse as JSON, return as string if not JSON
            try:
                return json.loads(decrypted_bytes.decode())
            except json.JSONDecodeError:
                return decrypted_bytes.decode()
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt payload: {str(e)}")

    def sign_payload(self, payload: str) -> str:
        """Sign a payload to ensure integrity"""
        return self.fernet.sign(payload.encode()).decode()

    def verify_signature(self, signed_payload: str) -> str:
        """Verify and extract the original payload from a signed payload"""
        try:
            return self.fernet.verify(signed_payload.encode()).decode()
        except Exception as e:
            raise EncryptionError(f"Failed to verify signature: {str(e)}") 