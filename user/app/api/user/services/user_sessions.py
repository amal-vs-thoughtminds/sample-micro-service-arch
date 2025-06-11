from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ....schemas.mongodb import UserSession, UserSessionResponse, SessionQuery

logger = logging.getLogger(__name__)


async def create_user_session(
    db: AsyncIOMotorDatabase,
    session_data: UserSession
) -> UserSessionResponse:
    """Create a new user session record in MongoDB"""
    try:
        collection = db.user_sessions
        
        session_dict = session_data.dict()
        if session_dict.get('login_time') is None:
            session_dict['login_time'] = datetime.utcnow()
        if session_dict.get('last_activity') is None:
            session_dict['last_activity'] = datetime.utcnow()
            
        result = await collection.insert_one(session_dict)
        
        # Retrieve the created document
        created_session = await collection.find_one({"_id": result.inserted_id})
        created_session["_id"] = str(created_session["_id"])
        
        logger.info(f"Created user session for user {session_data.user_id}: {session_data.session_id}")
        return UserSessionResponse(**created_session)
        
    except Exception as e:
        logger.error(f"Failed to create user session: {e}")
        raise


async def get_user_sessions(
    db: AsyncIOMotorDatabase,
    query: SessionQuery
) -> List[UserSessionResponse]:
    """Get user sessions with filtering"""
    try:
        collection = db.user_sessions
        
        # Build MongoDB filter
        filter_dict = {}
        
        if query.user_id:
            filter_dict["user_id"] = query.user_id
            
        if query.is_active is not None:
            filter_dict["is_active"] = query.is_active
            
        if query.start_date:
            filter_dict.setdefault("login_time", {})["$gte"] = query.start_date
            
        if query.end_date:
            filter_dict.setdefault("login_time", {})["$lte"] = query.end_date
        
        # Execute query with pagination
        cursor = collection.find(filter_dict).sort("login_time", -1).skip(query.skip).limit(query.limit)
        
        sessions = []
        async for session in cursor:
            session["_id"] = str(session["_id"])
            sessions.append(UserSessionResponse(**session))
        
        logger.info(f"Retrieved {len(sessions)} user sessions")
        return sessions
        
    except Exception as e:
        logger.error(f"Failed to get user sessions: {e}")
        raise


async def update_session_activity(
    db: AsyncIOMotorDatabase,
    session_id: str
) -> bool:
    """Update session last activity timestamp"""
    try:
        collection = db.user_sessions
        
        result = await collection.update_one(
            {"session_id": session_id},
            {"$set": {"last_activity": datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            logger.debug(f"Updated activity for session {session_id}")
            return True
        else:
            logger.warning(f"Session {session_id} not found for activity update")
            return False
        
    except Exception as e:
        logger.error(f"Failed to update session activity: {e}")
        raise


async def end_user_session(
    db: AsyncIOMotorDatabase,
    session_id: str
) -> bool:
    """End a user session by marking it as inactive"""
    try:
        collection = db.user_sessions
        
        result = await collection.update_one(
            {"session_id": session_id},
            {"$set": {"is_active": False, "last_activity": datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Ended session {session_id}")
            return True
        else:
            logger.warning(f"Session {session_id} not found")
            return False
        
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        raise


async def get_active_sessions_count(
    db: AsyncIOMotorDatabase,
    user_id: Optional[int] = None
) -> int:
    """Get count of active sessions"""
    try:
        collection = db.user_sessions
        
        filter_dict = {"is_active": True}
        if user_id:
            filter_dict["user_id"] = user_id
        
        count = await collection.count_documents(filter_dict)
        
        logger.info(f"Active sessions count: {count}")
        return count
        
    except Exception as e:
        logger.error(f"Failed to get active sessions count: {e}")
        raise 