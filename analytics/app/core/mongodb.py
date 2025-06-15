from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging
from .config import settings
from contextlib import asynccontextmanager
from fastapi import FastAPI

logger = logging.getLogger(__name__)

class MongoDBInstance:
    """ASGI-compatible MongoDB singleton instance"""
    _instance: Optional['MongoDBInstance'] = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self) -> None:
        """Initialize MongoDB connection"""
        if self._initialized:
            return
            
        try:
            # Create MongoDB connection URL
            mongo_url = f"mongodb://{settings.MONGODB_USER}:{settings.MONGODB_PASSWORD}@{settings.MONGODB_HOST}:{settings.MONGODB_PORT}"
            
            # Initialize client
            self._client = AsyncIOMotorClient(mongo_url)
            
            # Get database
            self._db = self._client[settings.MONGODB_DB]
            
            # Verify connection
            await self._client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            # Create indexes
            await self.create_indexes()
            
            self._initialized = True
            logger.info("MongoDB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {str(e)}")
            raise
    
    async def create_indexes(self) -> None:
        """Create necessary indexes for the analytics collection"""
        try:
            collection = self._db[settings.MONGODB_COLLECTION]
            
            # Create indexes
            await collection.create_index("event_type")
            await collection.create_index("user_id")
            await collection.create_index("timestamp")
            await collection.create_index([("timestamp", -1), ("event_type", 1)])
            
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes: {str(e)}")
            raise
    
    async def close_connections(self) -> None:
        """Close MongoDB connections"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self._initialized = False
            logger.info("MongoDB connections closed")
    
    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        return self._db
    
    @property
    def client(self) -> AsyncIOMotorClient:
        """Get client instance"""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        return self._client

# Create global MongoDB instance
mongo_instance = MongoDBInstance()

# ASGI lifespan handler
@asynccontextmanager
async def mongodb_lifespan(app: FastAPI):
    """MongoDB lifespan handler for ASGI applications"""
    try:
        # Initialize MongoDB on startup
        await mongo_instance.initialize()
        yield
    finally:
        # Close MongoDB connections on shutdown
        await mongo_instance.close_connections()

# Dependency for getting MongoDB collection
async def get_mongodb():
    """FastAPI dependency for getting MongoDB database"""
    if not mongo_instance._initialized:
        await mongo_instance.initialize()
    return mongo_instance.db

async def get_mongo_collection(collection_name: str | None = None):
    """FastAPI dependency for getting MongoDB collection"""
    if not mongo_instance._initialized:
        await mongo_instance.initialize()
    
    # Use default collection if none provided
    if collection_name is None:
        collection_name = settings.MONGODB_COLLECTION
        
    return mongo_instance.db[collection_name] 