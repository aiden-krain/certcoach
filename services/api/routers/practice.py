"""Practice session management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List

from packages.database.connection import get_db_session
from ..core.practice import PracticeEngine
from ..dependencies import get_current_user
from ..models.practice import SessionResponse, AttemptRequest, AttemptResponse
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/sessions", response_model=SessionResponse)
async def generate_practice_session(
    plan_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate a new practice session for the user."""
    try:
        engine = PracticeEngine()
        session_data = await engine.generate_session(
            user_id=current_user["id"],
            plan_id=plan_id,
            db=db
        )
        
        return SessionResponse(**session_data)
        
    except Exception as e:
        logger.error("Failed to generate practice session", user_id=current_user["id"], error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to generate practice session"
        )


@router.post("/attempts", response_model=AttemptResponse)
async def submit_attempt(
    attempt_data: AttemptRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Submit an attempt for a practice item."""
    try:
        engine = PracticeEngine()
        result = await engine.submit_attempt(
            user_id=current_user["id"],
            item_id=attempt_data.item_id,
            response=attempt_data.response,
            time_spent=attempt_data.time_spent,
            db=db
        )
        
        return AttemptResponse(**result)
        
    except Exception as e:
        logger.error("Failed to submit attempt", user_id=current_user["id"], error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to process attempt"
        )


@router.get("/review-queue")
async def get_review_queue(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get items due for review."""
    try:
        engine = PracticeEngine()
        review_items = await engine._get_due_reviews(current_user["id"], db)
        
        return {
            "user_id": current_user["id"],
            "due_count": len(review_items),
            "items": [
                {
                    "item_id": item.id,
                    "type": item.item_type,
                    "difficulty": item.difficulty,
                    "objective_id": item.objective_id
                }
                for item in review_items
            ]
        }
        
    except Exception as e:
        logger.error("Failed to get review queue", user_id=current_user["id"], error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve review queue"
        )
