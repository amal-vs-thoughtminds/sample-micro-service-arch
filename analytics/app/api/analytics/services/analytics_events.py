from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ....schemas.mongodb import AnalyticsEvent, AnalyticsEventResponse, EventQuery

logger = logging.getLogger(__name__)


async def create_analytics_event(
    db: AsyncIOMotorDatabase,
    event_data: AnalyticsEvent
) -> AnalyticsEventResponse:
    """Create a new analytics event record in MongoDB"""
    try:
        collection = db.analytics_events
        
        event_dict = event_data.dict()
        if event_dict.get('timestamp') is None:
            event_dict['timestamp'] = datetime.utcnow()
            
        result = await collection.insert_one(event_dict)
        
        # Retrieve the created document
        created_event = await collection.find_one({"_id": result.inserted_id})
        created_event["_id"] = str(created_event["_id"])
        
        logger.info(f"Created analytics event: {event_data.event_type} - {event_data.event_name}")
        return AnalyticsEventResponse(**created_event)
        
    except Exception as e:
        logger.error(f"Failed to create analytics event: {e}")
        raise


async def get_analytics_events(
    db: AsyncIOMotorDatabase,
    query: EventQuery
) -> List[AnalyticsEventResponse]:
    """Get analytics events with filtering"""
    try:
        collection = db.analytics_events
        
        # Build MongoDB filter
        filter_dict = {}
        
        if query.event_type:
            filter_dict["event_type"] = query.event_type.value
            
        if query.user_id:
            filter_dict["user_id"] = query.user_id
            
        if query.session_id:
            filter_dict["session_id"] = query.session_id
            
        if query.start_date:
            filter_dict.setdefault("timestamp", {})["$gte"] = query.start_date
            
        if query.end_date:
            filter_dict.setdefault("timestamp", {})["$lte"] = query.end_date
        
        # Execute query with pagination
        cursor = collection.find(filter_dict).sort("timestamp", -1).skip(query.skip).limit(query.limit)
        
        events = []
        async for event in cursor:
            event["_id"] = str(event["_id"])
            events.append(AnalyticsEventResponse(**event))
        
        logger.info(f"Retrieved {len(events)} analytics events")
        return events
        
    except Exception as e:
        logger.error(f"Failed to get analytics events: {e}")
        raise 