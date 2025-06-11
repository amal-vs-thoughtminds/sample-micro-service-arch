from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ....schemas.mongodb import UserActivity, UserActivityResponse, ActivityQuery
from ....core.mongodb import get_mongo_collection

logger = logging.getLogger(__name__)


async def create_user_activity(
    db: AsyncIOMotorDatabase,
    activity_data: UserActivity
) -> UserActivityResponse:
    """Create a new user activity record in MongoDB"""
    try:
        collection = db.user_activities
        
        activity_dict = activity_data.dict()
        if activity_dict.get('timestamp') is None:
            activity_dict['timestamp'] = datetime.utcnow()
            
        result = await collection.insert_one(activity_dict)
        
        # Retrieve the created document
        created_activity = await collection.find_one({"_id": result.inserted_id})
        created_activity["_id"] = str(created_activity["_id"])
        
        logger.info(f"Created user activity for user {activity_data.user_id}: {activity_data.activity_type}")
        return UserActivityResponse(**created_activity)
        
    except Exception as e:
        logger.error(f"Failed to create user activity: {e}")
        raise


async def get_user_activities(
    db: AsyncIOMotorDatabase,
    query: ActivityQuery
) -> List[UserActivityResponse]:
    """Get user activities with filtering"""
    try:
        collection = db.user_activities
        
        # Build MongoDB filter
        filter_dict = {}
        
        if query.user_id:
            filter_dict["user_id"] = query.user_id
            
        if query.activity_type:
            filter_dict["activity_type"] = query.activity_type.value
            
        if query.start_date:
            filter_dict.setdefault("timestamp", {})["$gte"] = query.start_date
            
        if query.end_date:
            filter_dict.setdefault("timestamp", {})["$lte"] = query.end_date
        
        # Execute query with pagination
        cursor = collection.find(filter_dict).sort("timestamp", -1).skip(query.skip).limit(query.limit)
        
        activities = []
        async for activity in cursor:
            activity["_id"] = str(activity["_id"])
            activities.append(UserActivityResponse(**activity))
        
        logger.info(f"Retrieved {len(activities)} user activities")
        return activities
        
    except Exception as e:
        logger.error(f"Failed to get user activities: {e}")
        raise


async def get_user_activity_stats(
    db: AsyncIOMotorDatabase,
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Get user activity statistics"""
    try:
        collection = db.user_activities
        
        # Build match stage
        match_stage = {}
        if user_id:
            match_stage["user_id"] = user_id
        if start_date:
            match_stage.setdefault("timestamp", {})["$gte"] = start_date
        if end_date:
            match_stage.setdefault("timestamp", {})["$lte"] = end_date
        
        # Aggregation pipeline
        pipeline = []
        
        if match_stage:
            pipeline.append({"$match": match_stage})
        
        pipeline.extend([
            {
                "$group": {
                    "_id": "$activity_type",
                    "count": {"$sum": 1},
                    "latest": {"$max": "$timestamp"}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_activities": {"$sum": "$count"},
                    "activities_by_type": {
                        "$push": {
                            "activity_type": "$_id",
                            "count": "$count",
                            "latest": "$latest"
                        }
                    }
                }
            }
        ])
        
        result = await collection.aggregate(pipeline).to_list(length=1)
        
        if result:
            stats = result[0]
            stats.pop("_id", None)
            logger.info(f"Generated activity stats for user {user_id}")
            return stats
        else:
            return {
                "total_activities": 0,
                "activities_by_type": []
            }
            
    except Exception as e:
        logger.error(f"Failed to get user activity stats: {e}")
        raise


async def delete_old_activities(
    db: AsyncIOMotorDatabase,
    days_old: int = 90
) -> int:
    """Delete activities older than specified days"""
    try:
        collection = db.user_activities
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        result = await collection.delete_many({"timestamp": {"$lt": cutoff_date}})
        
        logger.info(f"Deleted {result.deleted_count} old activities (older than {days_old} days)")
        return result.deleted_count
        
    except Exception as e:
        logger.error(f"Failed to delete old activities: {e}")
        raise 