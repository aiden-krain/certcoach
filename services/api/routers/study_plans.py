"""Study plan management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import List, Optional

from packages.database.connection import get_db_session
from packages.database.models import StudyPlan, ExamBlueprint, User
from ..core.planner import StudyPlanGenerator
from ..dependencies import get_current_user
from ..models.study_plans import StudyPlanCreate, StudyPlanResponse, StudyPlanUpdate
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/", response_model=StudyPlanResponse)
async def create_study_plan(
    plan_data: StudyPlanCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new study plan for the user."""
    try:
        # Verify blueprint exists
        blueprint = await db.get(ExamBlueprint, plan_data.blueprint_id)
        if not blueprint:
            raise HTTPException(
                status_code=404,
                detail="Exam blueprint not found"
            )
        
        # Create study plan
        study_plan = StudyPlan(
            user_id=current_user["id"],
            blueprint_id=plan_data.blueprint_id,
            title=plan_data.title or f"{blueprint.title} Study Plan",
            target_date=plan_data.target_date,
            daily_hours=plan_data.daily_hours,
            status="active"
        )
        
        db.add(study_plan)
        await db.commit()
        await db.refresh(study_plan)
        
        # Generate initial schedule
        planner = StudyPlanGenerator()
        await planner.generate_schedule(study_plan.id, db)
        
        logger.info("Study plan created", plan_id=study_plan.id, user_id=current_user["id"])
        
        return StudyPlanResponse.from_orm(study_plan)
        
    except Exception as e:
        logger.error("Failed to create study plan", user_id=current_user["id"], error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to create study plan"
        )


@router.get("/", response_model=List[StudyPlanResponse])
async def get_user_study_plans(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    status: Optional[str] = None
):
    """Get all study plans for the current user."""
    try:
        query = select(StudyPlan).where(StudyPlan.user_id == current_user["id"])
        
        if status:
            query = query.where(StudyPlan.status == status)
        
        result = await db.execute(query.order_by(StudyPlan.created_at.desc()))
        plans = result.scalars().all()
        
        return [StudyPlanResponse.from_orm(plan) for plan in plans]
        
    except Exception as e:
        logger.error("Failed to get study plans", user_id=current_user["id"], error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve study plans"
        )


@router.get("/{plan_id}", response_model=StudyPlanResponse)
async def get_study_plan(
    plan_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific study plan."""
    try:
        result = await db.execute(
            select(StudyPlan).where(
                and_(
                    StudyPlan.id == plan_id,
                    StudyPlan.user_id == current_user["id"]
                )
            )
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(
                status_code=404,
                detail="Study plan not found"
            )
        
        return StudyPlanResponse.from_orm(plan)
        
    except Exception as e:
        logger.error("Failed to get study plan", plan_id=plan_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve study plan"
        )


@router.put("/{plan_id}", response_model=StudyPlanResponse)
async def update_study_plan(
    plan_id: int,
    plan_update: StudyPlanUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update a study plan."""
    try:
        result = await db.execute(
            select(StudyPlan).where(
                and_(
                    StudyPlan.id == plan_id,
                    StudyPlan.user_id == current_user["id"]
                )
            )
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(
                status_code=404,
                detail="Study plan not found"
            )
        
        # Update fields
        if plan_update.title is not None:
            plan.title = plan_update.title
        if plan_update.target_date is not None:
            plan.target_date = plan_update.target_date
        if plan_update.daily_hours is not None:
            plan.daily_hours = plan_update.daily_hours
        if plan_update.status is not None:
            plan.status = plan_update.status
        
        plan.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(plan)
        
        logger.info("Study plan updated", plan_id=plan_id, user_id=current_user["id"])
        
        return StudyPlanResponse.from_orm(plan)
        
    except Exception as e:
        logger.error("Failed to update study plan", plan_id=plan_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to update study plan"
        )


@router.get("/{plan_id}/calendar")
async def export_calendar(
    plan_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Export study plan as iCal calendar file."""
    try:
        # Verify plan ownership
        result = await db.execute(
            select(StudyPlan).where(
                and_(
                    StudyPlan.id == plan_id,
                    StudyPlan.user_id == current_user["id"]
                )
            )
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(
                status_code=404,
                detail="Study plan not found"
            )
        
        # Generate iCal content
        from ..core.calendar_export import generate_ical
        ical_content = await generate_ical(plan, db)
        
        from fastapi.responses import Response
        return Response(
            content=ical_content,
            media_type="text/calendar",
            headers={
                "Content-Disposition": f"attachment; filename=study-plan-{plan_id}.ics"
            }
        )
        
    except Exception as e:
        logger.error("Failed to export calendar", plan_id=plan_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to generate calendar export"
        )
