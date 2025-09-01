"""
Study plan generation and scheduling logic.

Handles blueprint-weighted session planning, automatic rescheduling,
and adaptive timeline management.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import structlog

from packages.database.models import (
    StudyPlan, ExamBlueprint, Objective, StudySession, MasteryRecord
)

logger = structlog.get_logger(__name__)


class StudyPlanGenerator:
    """Generates and manages study plans based on exam blueprints."""
    
    def __init__(self):
        self.default_session_duration = 45  # minutes
        self.min_daily_sessions = 1
        self.max_daily_sessions = 4
    
    async def generate_schedule(self, plan_id: int, db: AsyncSession) -> bool:
        """Generate initial study schedule for a plan."""
        try:
            # Get study plan and blueprint
            plan = await db.get(StudyPlan, plan_id)
            if not plan:
                logger.error("Study plan not found", plan_id=plan_id)
                return False
            
            blueprint = await db.get(ExamBlueprint, plan.blueprint_id)
            if not blueprint:
                logger.error("Blueprint not found", blueprint_id=plan.blueprint_id)
                return False
            
            # Get all objectives for the blueprint
            result = await db.execute(
                select(Objective).where(Objective.blueprint_id == blueprint.id)
            )
            objectives = result.scalars().all()
            
            # Calculate total study time needed
            days_until_exam = (plan.target_date - datetime.utcnow()).days
            total_study_hours = days_until_exam * plan.daily_hours
            
            # Distribute study time across objectives based on weights
            objective_hours = self._distribute_study_time(objectives, total_study_hours)
            
            # Generate daily sessions
            sessions = self._generate_daily_sessions(
                plan, objective_hours, days_until_exam
            )
            
            # Save sessions to database
            for session_data in sessions:
                session = StudySession(
                    user_id=plan.user_id,
                    study_plan_id=plan.id,
                    session_type=session_data["type"],
                    started_at=session_data["scheduled_time"],
                    items_completed=0
                )
                db.add(session)
            
            await db.commit()
            logger.info("Schedule generated", plan_id=plan_id, sessions_count=len(sessions))
            return True
            
        except Exception as e:
            logger.error("Failed to generate schedule", plan_id=plan_id, error=str(e))
            return False
    
    def _distribute_study_time(self, objectives: List[Objective], total_hours: float) -> Dict[int, float]:
        """Distribute study time across objectives based on weights."""
        total_weight = sum(obj.weight for obj in objectives)
        distribution = {}
        
        for objective in objectives:
            weight_ratio = objective.weight / total_weight
            hours = total_hours * weight_ratio
            distribution[objective.id] = hours
        
        return distribution
    
    def _generate_daily_sessions(
        self, 
        plan: StudyPlan, 
        objective_hours: Dict[int, float],
        days_available: int
    ) -> List[Dict]:
        """Generate daily study sessions."""
        sessions = []
        current_date = datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Calculate sessions per day
        sessions_per_day = min(
            self.max_daily_sessions,
            max(1, int(plan.daily_hours / (self.default_session_duration / 60)))
        )
        
        for day in range(days_available):
            session_date = current_date + timedelta(days=day)
            
            # Skip weekends (optional - could be configurable)
            if session_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                continue
            
            # Generate sessions for this day
            for session_num in range(sessions_per_day):
                session_time = session_date + timedelta(
                    hours=session_num * (self.default_session_duration / 60 + 0.25)  # 15 min break
                )
                
                sessions.append({
                    "type": "practice",
                    "scheduled_time": session_time,
                    "duration_minutes": self.default_session_duration,
                    "objectives": self._select_session_objectives(objective_hours, day, session_num)
                })
        
        return sessions
    
    def _select_session_objectives(
        self, 
        objective_hours: Dict[int, float],
        day: int, 
        session: int
    ) -> List[int]:
        """Select which objectives to focus on for a session."""
        # Simple round-robin distribution for now
        # In production, this would consider mastery levels and priorities
        objectives = list(objective_hours.keys())
        session_index = day * 4 + session  # Assuming max 4 sessions per day
        
        # Return 1-3 objectives per session
        selected = []
        for i in range(min(3, len(objectives))):
            obj_index = (session_index + i) % len(objectives)
            selected.append(objectives[obj_index])
        
        return selected


class ScheduleManager:
    """Manages schedule adjustments and rescheduling."""
    
    async def handle_missed_session(self, session_id: int, db: AsyncSession) -> bool:
        """Handle a missed session by rescheduling."""
        try:
            session = await db.get(StudySession, session_id)
            if not session:
                return False
            
            # Find next available slot
            next_slot = await self._find_next_available_slot(session.user_id, db)
            if next_slot:
                session.started_at = next_slot
                await db.commit()
                
                logger.info("Session rescheduled", session_id=session_id, new_time=next_slot)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to reschedule session", session_id=session_id, error=str(e))
            return False
    
    async def _find_next_available_slot(self, user_id: str, db: AsyncSession) -> Optional[datetime]:
        """Find the next available time slot for a session."""
        # Get existing sessions for the user
        result = await db.execute(
            select(StudySession).where(
                and_(
                    StudySession.user_id == user_id,
                    StudySession.started_at > datetime.utcnow()
                )
            ).order_by(StudySession.started_at)
        )
        existing_sessions = result.scalars().all()
        
        # Find first gap in schedule
        current_time = datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0)
        
        for i in range(30):  # Look ahead 30 days
            candidate_time = current_time + timedelta(days=i)
            
            # Skip weekends
            if candidate_time.weekday() >= 5:
                continue
            
            # Check if slot is available
            slot_available = True
            for session in existing_sessions:
                if abs((session.started_at - candidate_time).total_seconds()) < 3600:  # 1 hour buffer
                    slot_available = False
                    break
            
            if slot_available:
                return candidate_time
        
        return None


class ProgressTracker:
    """Tracks study progress and updates plans accordingly."""
    
    async def update_plan_progress(self, plan_id: int, db: AsyncSession) -> float:
        """Calculate and update study plan progress."""
        try:
            plan = await db.get(StudyPlan, plan_id)
            if not plan:
                return 0.0
            
            # Get completed sessions
            result = await db.execute(
                select(StudySession).where(
                    and_(
                        StudySession.study_plan_id == plan_id,
                        StudySession.completed_at.is_not(None)
                    )
                )
            )
            completed_sessions = result.scalars().all()
            
            # Get total planned sessions
            result = await db.execute(
                select(StudySession).where(StudySession.study_plan_id == plan_id)
            )
            total_sessions = result.scalars().all()
            
            if not total_sessions:
                progress = 0.0
            else:
                progress = len(completed_sessions) / len(total_sessions)
            
            # Update plan progress
            plan.progress = progress
            await db.commit()
            
            logger.info("Progress updated", plan_id=plan_id, progress=progress)
            return progress
            
        except Exception as e:
            logger.error("Failed to update progress", plan_id=plan_id, error=str(e))
            return 0.0
