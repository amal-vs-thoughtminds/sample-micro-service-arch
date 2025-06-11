from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging

from .config import settings

logger = logging.getLogger(__name__)


class MongoInstance:
    """MongoDB instance for managing async database connections"""
    
    _instance = None
    _client: Optional[AsyncIOMotorClient] = None
    _db = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoInstance, cls).__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """Initialize MongoDB async connection"""
        if not self._initialized:
            try:
                self._client = AsyncIOMotorClient(settings.mongodb_url)
                self._db = self._client[settings.mongodb_db]
                
                # Test the connection
                await self._client.admin.command('ping')
                self._initialized = True
                logger.info(f"MongoDB async client initialized - Database: {settings.mongodb_db}")
                
            except Exception as e:
                logger.error(f"Failed to initialize MongoDB: {e}")
                raise
    
    async def get_database(self):
        """Get asynchronous MongoDB database"""
        if not self._initialized:
            await self.initialize()
        return self._db
    
    async def get_collection(self, collection_name: str):
        """Get a specific collection from the database"""
        db = await self.get_database()
        return db[collection_name]
    
    async def close_connections(self):
        """Close MongoDB connections"""
        if self._client and self._initialized:
            await self._client.close()
            self._initialized = False
            logger.info("MongoDB async client closed")
    
    async def ping(self) -> bool:
        """Test MongoDB connection"""
        try:
            if self._client:
                await self._client.admin.command('ping')
                return True
            return False
        except Exception as e:
            logger.error(f"MongoDB ping failed: {e}")
            return False
    
    async def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            db = await self.get_database()
            
            # Analytics events collection indexes
            analytics_events = db.analytics_events
            await analytics_events.create_index("event_type")
            await analytics_events.create_index("user_id")
            await analytics_events.create_index("timestamp")
            await analytics_events.create_index([("event_type", 1), ("timestamp", -1)])
            await analytics_events.create_index([("user_id", 1), ("timestamp", -1)])
            
            # Analytics sessions collection indexes
            analytics_sessions = db.analytics_sessions
            await analytics_sessions.create_index("session_id")
            await analytics_sessions.create_index("user_id")
            await analytics_sessions.create_index("created_at")
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes: {e}")


# Global MongoDB instance
mongo_instance = MongoInstance()


async def get_mongodb():
    """Get MongoDB database (asynchronous dependency)"""
    return await mongo_instance.get_database()


async def get_mongo_collection(collection_name: str):
    """Get specific MongoDB collection (asynchronous)"""
    return await mongo_instance.get_collection(collection_name) 