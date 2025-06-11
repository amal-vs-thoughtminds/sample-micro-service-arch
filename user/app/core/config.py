from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # App Settings
    app_name: str = "User Service"
    version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    
    # Database Settings - PostgreSQL
    postgres_user: str = "postgres"
    postgres_password: str = "postgres123"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "microservices_db"
    
    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    # MongoDB Settings
    mongodb_user: str = "admin"
    mongodb_password: str = "admin123"
    mongodb_host: str = "mongodb"
    mongodb_port: int = 27017
    mongodb_db: str = "user_db"
    
    @property
    def mongodb_url(self) -> str:
        return f"mongodb://{self.mongodb_user}:{self.mongodb_password}@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_db}?authSource=admin"
    
    # Service Communication Settings
    user_service_url: str = "http://user-service:8000"
    analytics_service_url: str = "http://analytics-service:8000"
    
    # Security Settings
    encryption_key: str = "your-secret-encryption-key-32-chars!!"
    jwt_secret_key: str = "your-jwt-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Password Settings
    pwd_context_schemes: list = ["bcrypt"]
    pwd_context_deprecated: str = "auto"
    
    # Communication Settings
    communication_method: str = "http"
    
    # CORS Settings
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    # Whitelisted hosts for production
    cors_whitelist: list = [
        "https://yourdomain.com",
        "https://api.yourdomain.com",
        "https://admin.yourdomain.com"
    ]
    
    @property
    def cors_origins(self) -> list:
        """Get CORS origins based on environment"""
        if self.environment == "development" or self.debug:
            return ["*"]  # Allow all in development
        else:
            return self.cors_whitelist  # Use whitelist in production
    
    # Logging Settings
    log_level: str = "INFO"
    
    # Production Settings
    production: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 