from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ...core.db import get_db as get_postgres_db  # Alias the new function to maintain compatibility
from ...schemas.user import User, UserCreate, UserResponse
from ...models.user import User as UserModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/users", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_postgres_db)
):
    """Create a new user"""
    try:
        db_user = UserModel(**user.model_dump())
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return {"status": "success", "user_id": db_user.id}
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.get("/users", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_postgres_db)
):
    """Get users with pagination"""
    try:
        result = await db.execute(
            select(UserModel)
            .offset(skip)
            .limit(limit)
            .order_by(UserModel.created_at.desc())
        )
        users = result.scalars().all()
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch users") 