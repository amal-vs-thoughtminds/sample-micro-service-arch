from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ....models.analytics import AnalyticsEvent


async def get_events_count(db: AsyncSession) -> int:
    """Get total events count"""
    result = await db.execute(select(func.count(AnalyticsEvent.id)))
    return result.scalar()


async def get_events_by_type(db: AsyncSession, event_type: str) -> int:
    """Get events count by type"""
    result = await db.execute(
        select(func.count(AnalyticsEvent.id)).where(AnalyticsEvent.event_type == event_type)
    )
    return result.scalar() 