from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ....models.analytics import AnalyticsEvent
from ..schemas import AnalyticsEventCreate


async def create_analytics_event(db: AsyncSession, event_data: AnalyticsEventCreate) -> AnalyticsEvent:
    """Create a new analytics event"""
    db_event = AnalyticsEvent(
        event_type=event_data.event_type.value,
        event_name=event_data.event_name,
        user_id=event_data.user_id,
        properties=event_data.properties,
        timestamp=datetime.utcnow()
    )
    
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    
    return db_event 