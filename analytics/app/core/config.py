from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Service settings
    SERVICE_NAME: str = "analytics-service"
    VERSION: str = "1.0.0"
    PRODUCTION: bool = Field(default=False, env="PRODUCTION")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    
    # CORS settings
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS",
        description="List of allowed CORS origins"
    )
    
    # Database settings
    POSTGRES_HOST: str = Field(default="postgres", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="postgres123", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(default="microservices_db", env="POSTGRES_DB")
    
    # MongoDB settings
    MONGODB_HOST: str = Field(default="mongodb", env="MONGODB_HOST")
    MONGODB_PORT: int = Field(default=27017, env="MONGODB_PORT")
    MONGODB_USER: str = Field(default="admin", env="MONGODB_USER")
    MONGODB_PASSWORD: str = Field(default="admin123", env="MONGODB_PASSWORD")
    MONGODB_DB: str = Field(default="analytics_db", env="MONGODB_DB")
    MONGODB_COLLECTION: str = Field(default="analytics_events", env="MONGODB_COLLECTION")
    
    # Security settings
    ENCRYPTION_KEY: str = Field(
        default="analytics-service-secret-key-456",
        env="ANALYTICS_SERVICE_ENCRYPTION_KEY"
    )
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_DIR: str = Field(default="/app/logs", env="LOG_DIR")
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from environment variable"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def mongodb_url(self) -> str:
        """Get MongoDB connection URL"""
        return f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB}"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

# Create global settings instance
settings = Settings() 