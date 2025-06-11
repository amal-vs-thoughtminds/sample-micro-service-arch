from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict

from ....models.user import User


async def get_user_stats(db: AsyncSession) -> Dict:
    """Get user statistics"""
    # Get total users count
    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar()
    
    # Get active users count
    active_result = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    active_users = active_result.scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users
    } 