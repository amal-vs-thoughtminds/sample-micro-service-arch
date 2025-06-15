import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from ms_communicator import EncryptionMiddleware

from .core.config import settings
from .core.db import create_tables, close_db_connections
from .core.mongodb import mongo_instance, mongodb_lifespan
from .core.middleware import ProcessTimeMiddleware, LoggingMiddleware, SecurityHeadersMiddleware
from .api.analytics.routes import router as analytics_router
from .api.mongodb.routes import router as mongodb_router
from .core.logger import setup_logging
from .schemas.common import HealthCheck
from datetime import datetime

# Setup logging first, before any other imports
setup_logging(
    service_name=settings.SERVICE_NAME,
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.VERSION}")
    
    # Initialize databases
    await create_tables()
    
    # Use MongoDB lifespan handler
    async with mongodb_lifespan(app):
        yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}")
    await close_db_connections()
    logger.info("Database connections closed")

# Create FastAPI application
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.VERSION,
    docs_url=settings.DOCS_URL if not settings.PRODUCTION else None,
    redoc_url=settings.REDOC_URL if not settings.PRODUCTION else None,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ProcessTimeMiddleware)
app.add_middleware(LoggingMiddleware)

# Add encryption middleware with service name
app.add_middleware(
    EncryptionMiddleware,
    service_name=settings.SERVICE_NAME,
    encrypt_responses=True
)

# Include routers
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(mongodb_router, prefix=f"{settings.API_V1_PREFIX}/mongodb", tags=["mongodb"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info(f"Starting {settings.SERVICE_NAME} v{settings.VERSION}")
        # Add any additional startup initialization here
        logger.info(f"{settings.SERVICE_NAME} startup complete")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info(f"Shutting down {settings.SERVICE_NAME}")
        # Add any cleanup code here
        logger.info(f"{settings.SERVICE_NAME} shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

@app.get("/health", response_model=HealthCheck, tags=["health"])
async def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB connection
        mongo_status = "healthy" if mongo_instance._initialized else "unhealthy"
        
        return HealthCheck(
            status="healthy",
            version=settings.VERSION,
            service=settings.SERVICE_NAME,
            details={
                "mongodb": mongo_status,
                "postgres": "healthy"  # Assuming Postgres is healthy if we got this far
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheck(
            status="unhealthy",
            version=settings.VERSION,
            service=settings.SERVICE_NAME,
            details={"error": str(e)}
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "service": settings.SERVICE_NAME
        }
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