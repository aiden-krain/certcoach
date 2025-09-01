"""
FSRS (Free Spaced Repetition Scheduler) Implementation
Based on the open-source FSRS algorithm for optimized spaced repetition
https://github.com/open-spaced-repetition/fsrs4anki
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Tuple


class ReviewGrade(Enum):
    """Review grades for FSRS scheduling"""
    AGAIN = 1      # Failed, need to review again soon
    HARD = 2       # Difficult, longer interval than Again but shorter than Good  
    GOOD = 3       # Standard success, normal interval progression
    EASY = 4       # Very easy, longer interval than Good


@dataclass
class FSRSParameters:
    """FSRS algorithm parameters - can be optimized per user"""
    # Default parameters from FSRS research
    w: List[float] = None
    
    def __post_init__(self):
        if self.w is None:
            # Default FSRS parameters (optimized on Anki data)
            self.w = [
                0.4072,    # w0: initial stability for Good grade
                1.1829,    # w1: initial stability for Easy grade  
                3.1262,    # w2: initial difficulty decay
                15.4722,   # w3: difficulty multiplier
                7.2102,    # w4: difficulty offset
                0.5316,    # w5: factor for Again grade
                1.0651,    # w6: factor for Hard grade
                0.0234,    # w7: factor for Easy grade
                1.616,     # w8: stability multiplier for successful reviews
                0.1544,    # w9: stability multiplier for failed reviews
                1.0824,    # w10: retrievability threshold adjustment
                1.9813,    # w11: difficulty adjustment for failed reviews
                0.0953,    # w12: difficulty adjustment for successful reviews
                0.2975,    # w13: initial retrievability
                2.2042,    # w14: difficulty weight in scheduling
                0.2407,    # w15: easy bonus multiplier
                2.9466,    # w16: hard penalty multiplier
                0.5034,    # w17: lapse multiplier
            ]


@dataclass 
class FSRSCard:
    """Represents a card/item in the FSRS system"""
    # Core FSRS state
    difficulty: float = 0.0       # How hard this card is (0-10+ scale)
    stability: float = 0.0        # Days until retrievability drops to 90%
    retrievability: float = 0.0   # Current probability of successful recall
    
    # Scheduling info
    last_review: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    # Learning state
    state: str = "new"            # new, learning, review, relearning
    elapsed_days: float = 0.0     # Days since last review
    scheduled_days: float = 0.0   # Days scheduled for this review
    reps: int = 0                 # Total number of reviews
    lapses: int = 0              # Number of times failed after being learned


class FSRSScheduler:
    """FSRS spaced repetition scheduler"""
    
    def __init__(self, parameters: Optional[FSRSParameters] = None):
        self.params = parameters or FSRSParameters()
    
    def schedule_card(
        self, 
        card: FSRSCard, 
        grade: ReviewGrade, 
        review_time: Optional[datetime] = None
    ) -> Tuple[FSRSCard, List[Tuple[ReviewGrade, datetime, float]]]:
        """
        Schedule a card after review and return next review options
        
        Returns:
            Updated card and list of (grade, due_date, interval) options
        """
        if review_time is None:
            review_time = datetime.now()
        
        # Calculate elapsed days if this isn't the first review
        if card.last_review:
            elapsed = (review_time - card.last_review).total_seconds() / 86400
            card.elapsed_days = elapsed
        
        # Update card based on review grade
        updated_card = self._update_card(card, grade, review_time)
        
        # Generate scheduling options for next review
        options = self._generate_scheduling_options(updated_card, review_time)
        
        return updated_card, options
    
    def _update_card(self, card: FSRSCard, grade: ReviewGrade, review_time: datetime) -> FSRSCard:
        """Update card state after review"""
        new_card = FSRSCard(
            difficulty=card.difficulty,
            stability=card.stability, 
            retrievability=card.retrievability,
            last_review=review_time,
            elapsed_days=card.elapsed_days,
            scheduled_days=card.scheduled_days,
            reps=card.reps + 1,
            lapses=card.lapses,
            state=card.state
        )
        
        if card.state == "new":
            # First review - initialize parameters
            new_card = self._init_card(new_card, grade)
        else:
            # Update existing card
            new_card = self._update_existing_card(new_card, grade)
        
        return new_card
    
    def _init_card(self, card: FSRSCard, grade: ReviewGrade) -> FSRSCard:
        """Initialize a new card after first review"""
        w = self.params.w
        
        # Set initial difficulty based on grade
        if grade == ReviewGrade.AGAIN:
            card.difficulty = w[4]
        elif grade == ReviewGrade.HARD:
            card.difficulty = w[4] - w[5]
        elif grade == ReviewGrade.GOOD:
            card.difficulty = w[4] - w[5] * 2
        else:  # EASY
            card.difficulty = w[4] - w[5] * 3
        
        # Constrain difficulty to reasonable range
        card.difficulty = max(1, min(10, card.difficulty))
        
        # Set initial stability based on grade
        if grade == ReviewGrade.AGAIN:
            card.stability = w[0]
        elif grade == ReviewGrade.HARD:
            card.stability = w[0] * w[6]
        elif grade == ReviewGrade.GOOD:
            card.stability = w[0] * w[7]
        else:  # EASY
            card.stability = w[0] * w[8]
        
        # Set state based on performance
        if grade == ReviewGrade.AGAIN:
            card.state = "learning"
        else:
            card.state = "review"
        
        return card
    
    def _update_existing_card(self, card: FSRSCard, grade: ReviewGrade) -> FSRSCard:
        """Update an existing card after review"""
        w = self.params.w
        
        # Calculate current retrievability
        if card.elapsed_days > 0 and card.stability > 0:
            card.retrievability = math.exp(-card.elapsed_days / card.stability)
        else:
            card.retrievability = 1.0
        
        # Update difficulty
        new_difficulty = card.difficulty
        if grade == ReviewGrade.AGAIN:
            new_difficulty += w[11] * (1 - card.retrievability)
            card.lapses += 1
            card.state = "relearning"
        else:
            new_difficulty -= w[12] * card.retrievability
            if card.state in ["learning", "relearning"]:
                card.state = "review"
        
        card.difficulty = max(1, min(10, new_difficulty))
        
        # Update stability
        if grade == ReviewGrade.AGAIN:
            # Failed review - reduce stability
            card.stability = max(0.1, card.stability * w[9])
        else:
            # Successful review - increase stability
            success_factor = (
                1 + (math.exp(w[13]) - 1) * (11 - card.difficulty) / 10 *
                math.exp(-0.5 * (card.difficulty - 4) ** 2 / (w[14] ** 2))
            )
            
            if grade == ReviewGrade.HARD:
                success_factor *= w[16]
            elif grade == ReviewGrade.EASY:
                success_factor *= w[15]
            
            card.stability *= success_factor
        
        return card
    
    def _generate_scheduling_options(
        self, 
        card: FSRSCard, 
        review_time: datetime
    ) -> List[Tuple[ReviewGrade, datetime, float]]:
        """Generate scheduling options for the next review"""
        options = []
        
        for grade in ReviewGrade:
            interval = self._calculate_interval(card, grade)
            due_date = review_time + timedelta(days=interval)
            options.append((grade, due_date, interval))
        
        return options
    
    def _calculate_interval(self, card: FSRSCard, grade: ReviewGrade) -> float:
        """Calculate interval for a given grade"""
        w = self.params.w
        
        if card.state == "new":
            # First review intervals
            if grade == ReviewGrade.AGAIN:
                return 0.0416  # 1 hour
            elif grade == ReviewGrade.HARD:
                return 0.25    # 6 hours  
            elif grade == ReviewGrade.GOOD:
                return 1.0     # 1 day
            else:  # EASY
                return 4.0     # 4 days
        
        elif card.state in ["learning", "relearning"]:
            # Learning intervals
            if grade == ReviewGrade.AGAIN:
                return 0.0416  # 1 hour
            elif grade == ReviewGrade.HARD:
                return 0.25    # 6 hours
            else:  # GOOD or EASY
                return 1.0     # 1 day
        
        else:  # review state
            # Use stability-based intervals
            if grade == ReviewGrade.AGAIN:
                return max(0.0416, card.stability * w[9])
            elif grade == ReviewGrade.HARD:
                return max(1.0, card.stability * w[16])
            elif grade == ReviewGrade.GOOD:
                return card.stability
            else:  # EASY
                return card.stability * w[15]
    
    def get_due_cards(
        self, 
        cards: List[FSRSCard], 
        current_time: Optional[datetime] = None
    ) -> List[FSRSCard]:
        """Get cards that are due for review"""
        if current_time is None:
            current_time = datetime.now()
        
        due_cards = []
        for card in cards:
            if card.due_date and card.due_date <= current_time:
                due_cards.append(card)
        
        return due_cards
    
    def optimize_parameters(
        self, 
        review_history: List[Tuple[FSRSCard, ReviewGrade, datetime]]
    ) -> FSRSParameters:
        """
        Optimize FSRS parameters based on user's review history
        This is a placeholder - real implementation would use optimization algorithms
        """
        # TODO: Implement parameter optimization using review log
        # This would analyze the user's actual performance vs predicted performance
        # and adjust parameters to minimize prediction error
        return self.params


# Example usage and testing
def test_fsrs_scheduler():
    """Test the FSRS scheduler with sample data"""
    scheduler = FSRSScheduler()
    
    # Create a new card
    card = FSRSCard()
    
    # First review - user found it Good
    updated_card, options = scheduler.schedule_card(card, ReviewGrade.GOOD)
    print(f"After first review (GOOD): stability={updated_card.stability:.2f}, difficulty={updated_card.difficulty:.2f}")
    
    # Simulate the next review after the scheduled interval
    next_review_time = datetime.now() + timedelta(days=1)
    updated_card.due_date = next_review_time
    updated_card.scheduled_days = 1.0
    
    # Second review - user found it Hard
    final_card, final_options = scheduler.schedule_card(updated_card, ReviewGrade.HARD, next_review_time)
    print(f"After second review (HARD): stability={final_card.stability:.2f}, difficulty={final_card.difficulty:.2f}")
    
    # Show scheduling options
    print("\nNext review options:")
    for grade, due_date, interval in final_options:
        print(f"  {grade.name}: {interval:.1f} days ({due_date.strftime('%Y-%m-%d %H:%M')})")


if __name__ == "__main__":
    test_fsrs_scheduler()
