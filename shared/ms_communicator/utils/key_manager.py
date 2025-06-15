from typing import Dict, Optional
from pydantic import BaseModel, SecretStr
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class ServiceKeys(BaseModel):
    """Model to store encryption keys for different services"""
    own_key: SecretStr
    service_keys: Dict[str, SecretStr] = {}

class KeyManager:
    def __init__(self, service_name: str):
        """
        Initialize key manager for a service
        
        Args:
            service_name: Name of the current service (e.g., 'user-service', 'analytics-service')
        """
        self.service_name = service_name
        self.keys = self._load_keys()
        
    def _load_keys(self) -> ServiceKeys:
        """Load encryption keys from environment variables"""
        load_dotenv()
        
        # Get own service key
        own_key_env = f"{self.service_name.upper().replace('-', '_')}_ENCRYPTION_KEY"
        own_key = os.getenv(own_key_env)
        if not own_key:
            raise ValueError(f"Own encryption key not found in environment variable: {own_key_env}")
        
        # Initialize with own key
        keys = ServiceKeys(own_key=SecretStr(own_key))
        
        # Load other service keys
        for env_var in os.environ:
            if env_var.endswith('_ENCRYPTION_KEY') and env_var != own_key_env:
                service_name = env_var.replace('_ENCRYPTION_KEY', '').lower().replace('_', '-')
                keys.service_keys[service_name] = SecretStr(os.getenv(env_var))
                logger.info(f"Loaded encryption key for service: {service_name}")
        
        return keys
    
    def get_own_key(self) -> str:
        """Get the encryption key for the current service"""
        return self.keys.own_key.get_secret_value()
    
    def get_service_key(self, service_name: str) -> Optional[str]:
        """
        Get the encryption key for a specific service
        
        Args:
            service_name: Name of the service to get the key for
            
        Returns:
            The encryption key for the service, or None if not found
        """
        if service_name == self.service_name:
            return self.get_own_key()
        
        service_key = self.keys.service_keys.get(service_name)
        if not service_key:
            logger.warning(f"Encryption key not found for service: {service_name}")
            return None
            
        return service_key.get_secret_value()
    
    def has_service_key(self, service_name: str) -> bool:
        """Check if we have the encryption key for a specific service"""
        return service_name == self.service_name or service_name in self.keys.service_keys 