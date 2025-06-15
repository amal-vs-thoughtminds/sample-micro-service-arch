from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class RetryStrategy(str, Enum):
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"

class ServiceConfig(BaseModel):
    service_name: str = Field(..., description="Name of the current service")
    retry_attempts: int = Field(default=3, ge=1, le=10, description="Number of retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.1, description="Base delay between retries in seconds")
    retry_strategy: RetryStrategy = Field(default=RetryStrategy.EXPONENTIAL, description="Retry strategy to use")
    timeout: float = Field(default=5.0, ge=0.1, description="Request timeout in seconds")
    circuit_breaker_threshold: int = Field(default=5, ge=1, description="Number of failures before circuit breaker trips")
    circuit_breaker_timeout: float = Field(default=30.0, ge=1.0, description="Circuit breaker reset timeout in seconds")
    
    class Config:
        env_prefix = "MS_COMMUNICATOR_"
        case_sensitive = False

class ServiceEndpoint(BaseModel):
    service_name: str
    base_url: str
    health_check_endpoint: str = "/health"
    version: str = "v1"
    timeout: Optional[float] = None

class ServiceRegistry(BaseModel):
    services: dict[str, ServiceEndpoint] = Field(default_factory=dict)

    def register_service(self, service: ServiceEndpoint) -> None:
        self.services[service.service_name] = service

    def get_service(self, service_name: str) -> ServiceEndpoint:
        if service_name not in self.services:
            raise KeyError(f"Service {service_name} not found in registry")
        return self.services[service_name] 