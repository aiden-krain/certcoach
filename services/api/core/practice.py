"""
Practice engine for generating and managing study sessions.

Handles adaptive question selection, FSRS scheduling, and session assembly.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import random
import structlog

from packages.database.models import (
    PracticeItem, Attempt, MasteryRecord, StudyPlan, Objective
)

logger = structlog.get_logger(__name__)


class PracticeEngine:
    """Generates adaptive practice sessions with FSRS scheduling."""
    
    def __init__(self):
        self.target_session_size = 12  # 8-12 focus + 2-3 reviews
        self.review_ratio = 0.25  # 25% reviews, 75% new/focus
        self.difficulty_variance = 0.3  # Difficulty range around user level
    
    async def generate_session(
        self, 
        user_id: str, 
        plan_id: int, 
        db: AsyncSession
    ) -> Dict:
        """Generate a complete practice session."""
        try:
            # Get due reviews
            review_items = await self._get_due_reviews(user_id, db)
            
            # Get focus items based on mastery gaps
            focus_items = await self._get_focus_items(user_id, plan_id, db)
            
            # Combine and limit session size
            session_reviews = review_items[:3]  # Max 3 reviews
            remaining_slots = self.target_session_size - len(session_reviews)
            session_focus = focus_items[:remaining_slots]
            
            # Shuffle for better experience
            all_items = session_reviews + session_focus
            random.shuffle(all_items)
            
            session_data = {
                "session_id": f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "user_id": user_id,
                "plan_id": plan_id,
                "items": [self._format_item_for_session(item) for item in all_items],
                "review_count": len(session_reviews),
                "focus_count": len(session_focus),
                "estimated_duration": len(all_items) * 2.5,  # 2.5 min per item
                "created_at": datetime.utcnow()
            }
            
            logger.info(
                "Session generated", 
                user_id=user_id, 
                total_items=len(all_items),
                reviews=len(session_reviews),
                focus=len(session_focus)
            )
            
            return session_data
            
        except Exception as e:
            logger.error("Failed to generate session", user_id=user_id, error=str(e))
            raise
    
    async def _get_due_reviews(self, user_id: str, db: AsyncSession) -> List[PracticeItem]:
        """Get items due for review based on FSRS scheduling."""
        try:
            # Find attempts with next_review <= now
            result = await db.execute(
                select(PracticeItem)
                .join(Attempt, PracticeItem.id == Attempt.item_id)
                .where(
                    and_(
                        Attempt.user_id == user_id,
                        Attempt.next_review <= datetime.utcnow()
                    )
                )
                .order_by(Attempt.next_review)
                .limit(10)
            )
            
            items = result.scalars().all()
            logger.info("Due reviews found", user_id=user_id, count=len(items))
            return items
            
        except Exception as e:
            logger.error("Failed to get due reviews", user_id=user_id, error=str(e))
            return []
    
    async def _get_focus_items(
        self, 
        user_id: str, 
        plan_id: int, 
        db: AsyncSession
    ) -> List[PracticeItem]:
        """Get focus items based on mastery gaps and study plan."""
        try:
            # Get study plan and objectives
            plan = await db.get(StudyPlan, plan_id)
            if not plan:
                return []
            
            # Get objectives with low mastery
            result = await db.execute(
                select(Objective, MasteryRecord.probability)
                .outerjoin(
                    MasteryRecord, 
                    and_(
                        MasteryRecord.objective_id == Objective.id,
                        MasteryRecord.user_id == user_id
                    )
                )
                .where(Objective.blueprint_id == plan.blueprint_id)
                .order_by(func.coalesce(MasteryRecord.probability, 0.0))
            )
            
            objective_priorities = result.all()
            
            # Get items for low-mastery objectives
            focus_items = []
            for objective, mastery_prob in objective_priorities:
                if len(focus_items) >= 15:  # Limit pool size
                    break
                
                # Get items for this objective that user hasn't seen recently
                result = await db.execute(
                    select(PracticeItem)
                    .outerjoin(
                        Attempt,
                        and_(
                            Attempt.item_id == PracticeItem.id,
                            Attempt.user_id == user_id
                        )
                    )
                    .where(
                        and_(
                            PracticeItem.objective_id == objective.id,
                            # Either never attempted or not attempted recently
                            func.coalesce(Attempt.created_at, datetime.min) < 
                            datetime.utcnow() - timedelta(days=3)
                        )
                    )
                    .order_by(func.random())
                    .limit(3)
                )
                
                items = result.scalars().all()
                focus_items.extend(items)
            
            # Shuffle and limit
            random.shuffle(focus_items)
            logger.info("Focus items selected", user_id=user_id, count=len(focus_items))
            return focus_items
            
        except Exception as e:
            logger.error("Failed to get focus items", user_id=user_id, error=str(e))
            return []
    
    def _format_item_for_session(self, item: PracticeItem) -> Dict:
        """Format a practice item for session delivery."""
        return {
            "item_id": item.id,
            "type": item.item_type,
            "difficulty": item.difficulty,
            "content": item.content,
            "objective_id": item.objective_id,
            # Don't include solution - that's returned after attempt
        }
    
    async def submit_attempt(
        self,
        user_id: str,
        item_id: int,
        response: Dict,
        time_spent: int,
        db: AsyncSession
    ) -> Dict:
        """Process a user's attempt and update FSRS scheduling."""
        try:
            item = await db.get(PracticeItem, item_id)
            if not item:
                raise ValueError("Item not found")
            
            # Evaluate correctness
            is_correct = self._evaluate_response(item, response)
            
            # Get or create previous attempt for FSRS calculation
            result = await db.execute(
                select(Attempt)
                .where(
                    and_(
                        Attempt.user_id == user_id,
                        Attempt.item_id == item_id
                    )
                )
                .order_by(Attempt.created_at.desc())
                .limit(1)
            )
            previous_attempt = result.scalar_one_or_none()
            
            # Calculate FSRS parameters
            fsrs_params = self._calculate_fsrs_parameters(
                is_correct, previous_attempt, time_spent
            )
            
            # Create new attempt record
            attempt = Attempt(
                user_id=user_id,
                item_id=item_id,
                response=response,
                is_correct=is_correct,
                time_spent=time_spent,
                difficulty=fsrs_params["difficulty"],
                stability=fsrs_params["stability"],
                last_review=datetime.utcnow(),
                next_review=fsrs_params["next_review"]
            )
            
            db.add(attempt)
            
            # Update mastery record
            await self._update_mastery_record(user_id, item.objective_id, is_correct, db)
            
            await db.commit()
            
            logger.info(
                "Attempt processed",
                user_id=user_id,
                item_id=item_id,
                correct=is_correct,
                next_review=fsrs_params["next_review"]
            )
            
            return {
                "correct": is_correct,
                "solution": item.solution,
                "explanation": item.solution.get("explanation", ""),
                "next_review": fsrs_params["next_review"],
                "stability_days": fsrs_params["stability"]
            }
            
        except Exception as e:
            logger.error("Failed to process attempt", user_id=user_id, item_id=item_id, error=str(e))
            raise
    
    def _evaluate_response(self, item: PracticeItem, response: Dict) -> bool:
        """Evaluate if the user's response is correct."""
        solution = item.solution
        
        if item.item_type == "mcq":
            return response.get("selected_option") == solution.get("correct_option")
        elif item.item_type == "scenario":
            # Multiple correct answers possible
            correct_options = solution.get("correct_options", [])
            selected = response.get("selected_options", [])
            return set(selected) == set(correct_options)
        elif item.item_type == "code":
            # Simple string comparison for now
            return response.get("code_output", "").strip() == solution.get("expected_output", "").strip()
        
        return False
    
    def _calculate_fsrs_parameters(
        self, 
        is_correct: bool, 
        previous_attempt: Optional[Attempt],
        time_spent: int
    ) -> Dict:
        """Calculate FSRS scheduling parameters."""
        if previous_attempt is None:
            # First attempt
            difficulty = 0.5
            stability = 2.0 if is_correct else 0.5
        else:
            # Subsequent attempt - simplified FSRS
            difficulty = max(0.1, min(0.9, 
                previous_attempt.difficulty + (0.1 if not is_correct else -0.05)
            ))
            
            if is_correct:
                stability = previous_attempt.stability * 2.5
            else:
                stability = max(0.5, previous_attempt.stability * 0.3)
        
        # Calculate next review time
        next_review = datetime.utcnow() + timedelta(days=stability)
        
        return {
            "difficulty": difficulty,
            "stability": stability,
            "next_review": next_review
        }
    
    async def _update_mastery_record(
        self,
        user_id: str,
        objective_id: int,
        is_correct: bool,
        db: AsyncSession
    ):
        """Update mastery probability using simple Bayesian update."""
        try:
            # Get existing mastery record
            result = await db.execute(
                select(MasteryRecord).where(
                    and_(
                        MasteryRecord.user_id == user_id,
                        MasteryRecord.objective_id == objective_id
                    )
                )
            )
            mastery = result.scalar_one_or_none()
            
            if mastery is None:
                # Create new record
                mastery = MasteryRecord(
                    user_id=user_id,
                    objective_id=objective_id,
                    probability=0.1,
                    total_attempts=0,
                    correct_attempts=0
                )
                db.add(mastery)
            
            # Update attempt counts
            mastery.total_attempts += 1
            if is_correct:
                mastery.correct_attempts += 1
            
            # Simple Bayesian update
            prior = mastery.probability
            likelihood = 0.9 if is_correct else 0.1
            
            # Weighted update based on evidence strength
            evidence_weight = min(0.2, 1.0 / (mastery.total_attempts + 1))
            mastery.probability = prior * (1 - evidence_weight) + likelihood * evidence_weight
            
            mastery.last_attempt = datetime.utcnow()
            
            if mastery.first_attempt is None:
                mastery.first_attempt = datetime.utcnow()
            
            logger.info(
                "Mastery updated",
                user_id=user_id,
                objective_id=objective_id,
                new_probability=mastery.probability
            )
            
        except Exception as e:
            logger.error("Failed to update mastery", user_id=user_id, error=str(e))
            raise
