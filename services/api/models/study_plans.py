"""Pydantic models for study plan API requests and responses."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class StudyPlanCreate(BaseModel):
    """Request model for creating a study plan."""
    blueprint_id: int = Field(..., description="ID of the exam blueprint")
    title: Optional[str] = Field(None, description="Custom title for the study plan")
    target_date: datetime = Field(..., description="Target exam date")
    daily_hours: float = Field(1.0, ge=0.5, le=8.0, description="Daily study hours")


class StudyPlanUpdate(BaseModel):
    """Request model for updating a study plan."""
    title: Optional[str] = None
    target_date: Optional[datetime] = None
    daily_hours: Optional[float] = Field(None, ge=0.5, le=8.0)
    status: Optional[str] = Field(None, regex="^(active|paused|completed|cancelled)$")


class StudyPlanResponse(BaseModel):
    """Response model for study plan data."""
    id: int
    user_id: str
    blueprint_id: int
    title: str
    target_date: datetime
    daily_hours: float
    status: str
    progress: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
