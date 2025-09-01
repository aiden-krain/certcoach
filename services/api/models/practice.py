"""Pydantic models for practice session API requests and responses."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List, Any, Optional


class SessionItem(BaseModel):
    """Individual practice item in a session."""
    item_id: int
    type: str
    difficulty: float
    content: Dict[str, Any]
    objective_id: int


class SessionResponse(BaseModel):
    """Response model for generated practice sessions."""
    session_id: str
    user_id: str
    plan_id: int
    items: List[SessionItem]
    review_count: int
    focus_count: int
    estimated_duration: float = Field(..., description="Estimated duration in minutes")
    created_at: datetime


class AttemptRequest(BaseModel):
    """Request model for submitting an attempt."""
    item_id: int
    response: Dict[str, Any] = Field(..., description="User's response to the item")
    time_spent: int = Field(..., description="Time spent in seconds")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Self-reported confidence")


class AttemptResponse(BaseModel):
    """Response model for attempt results."""
    correct: bool
    solution: Dict[str, Any]
    explanation: str
    next_review: datetime
    stability_days: float = Field(..., description="Days until next review")
