from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from .core.config import settings
from .core.db import create_tables, close_db_connections
from .core.mongodb import mongo_instance
from .core.middleware import ProcessTimeMiddleware, LoggingMiddleware, SecurityHeadersMiddleware
from .api.user.routes import router as user_router
from .api.mongodb.routes import router as mongodb_router
from .utils.logger import setup_logging
from .schemas.common import HealthCheck
from datetime import datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting User Service...")
    await create_tables()
    await mongo_instance.initialize()
    await mongo_instance.create_indexes()
    logger.info("Database tables created and MongoDB initialized")
    yield
    
    # Shutdown
    logger.info("Shutting down User Service...")
    await close_db_connections()
    await mongo_instance.close_connections()
    # Close dispatcher connections
    from .core.dispatcher import dispatcher
    await dispatcher.close()
    logger.info("Database, MongoDB, and dispatcher connections closed")


# Setup logging
logger = setup_logging()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="User Management Microservice with encrypted inter-service communication",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Add custom middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ProcessTimeMiddleware)
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(user_router, prefix=settings.api_v1_prefix, tags=["users"])
app.include_router(mongodb_router, prefix=f"{settings.api_v1_prefix}/mongodb", tags=["mongodb"])


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        service=settings.app_name,
        version=settings.version,
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    ) 