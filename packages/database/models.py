"""
Simplified database models for CertCoach platform.

Core tables focused on essential functionality:
- Users, Blueprints, Study Plans, Practice Items
- Attempts, Mastery Records, Notes with SRS
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, Text, ForeignKey, 
    JSON, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class ExamBlueprint(Base):
    """Exam blueprint definitions with objectives and weights."""
    
    __tablename__ = "exam_blueprints"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    total_weight: Mapped[int] = mapped_column(Integer, default=100)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    objectives: Mapped[List["Objective"]] = relationship("Objective", back_populates="blueprint")
    study_plans: Mapped[List["StudyPlan"]] = relationship("StudyPlan", back_populates="blueprint")


class Objective(Base):
    """Learning objectives with hierarchical structure and weights."""
    
    __tablename__ = "objectives"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    blueprint_id: Mapped[int] = mapped_column(Integer, ForeignKey("exam_blueprints.id"), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("objectives.id"))
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    blueprint: Mapped["ExamBlueprint"] = relationship("ExamBlueprint", back_populates="objectives")
    parent: Mapped[Optional["Objective"]] = relationship("Objective", remote_side=[id])
    children: Mapped[List["Objective"]] = relationship("Objective", back_populates="parent")
    mastery_records: Mapped[List["MasteryRecord"]] = relationship("MasteryRecord", back_populates="objective")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("blueprint_id", "code", name="unique_objective_code_per_blueprint"),
        Index("idx_objectives_blueprint_parent", "blueprint_id", "parent_id"),
    )


class User(Base):
    """User accounts integrated with Supabase authentication."""
    
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # Supabase UUID
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    preferences: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    study_plans: Mapped[List["StudyPlan"]] = relationship("StudyPlan", back_populates="user")
    attempts: Mapped[List["Attempt"]] = relationship("Attempt", back_populates="user")
    notes: Mapped[List["Note"]] = relationship("Note", back_populates="user")
    mastery_records: Mapped[List["MasteryRecord"]] = relationship("MasteryRecord", back_populates="user")


class StudyPlan(Base):
    """User study plans with timeline and scheduling."""
    
    __tablename__ = "study_plans"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    blueprint_id: Mapped[int] = mapped_column(Integer, ForeignKey("exam_blueprints.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    target_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    daily_hours: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="study_plans")
    blueprint: Mapped["ExamBlueprint"] = relationship("ExamBlueprint", back_populates="study_plans")
    sessions: Mapped[List["StudySession"]] = relationship("StudySession", back_populates="study_plan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("daily_hours > 0 AND daily_hours <= 24", name="valid_daily_hours"),
        CheckConstraint("progress >= 0 AND progress <= 1", name="valid_progress"),
        Index("idx_study_plans_user_status", "user_id", "status"),
    )


class PracticeItem(Base):
    """Practice questions and learning scenarios."""
    
    __tablename__ = "practice_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    blueprint_id: Mapped[int] = mapped_column(Integer, ForeignKey("exam_blueprints.id"), nullable=False)
    objective_id: Mapped[int] = mapped_column(Integer, ForeignKey("objectives.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)  # mcq, scenario, code
    difficulty: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0-1.0
    content: Mapped[dict] = mapped_column(JSON, nullable=False)  # Question data
    solution: Mapped[dict] = mapped_column(JSON, nullable=False)  # Answer and explanation
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    blueprint: Mapped["ExamBlueprint"] = relationship("ExamBlueprint")
    objective: Mapped["Objective"] = relationship("Objective")
    attempts: Mapped[List["Attempt"]] = relationship("Attempt", back_populates="item")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("difficulty >= 0 AND difficulty <= 1", name="valid_difficulty"),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)", name="valid_quality"),
        Index("idx_items_objective_difficulty", "objective_id", "difficulty"),
    )


class Attempt(Base):
    """User attempts with simplified SRS data."""
    
    __tablename__ = "attempts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("practice_items.id"), nullable=False)
    response: Mapped[dict] = mapped_column(JSON, nullable=False)  # User's answer
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float)  # Self-reported confidence
    time_spent: Mapped[Optional[int]] = mapped_column(Integer)  # Seconds
    
    # Simplified FSRS data
    difficulty: Mapped[float] = mapped_column(Float, default=0.5)
    stability: Mapped[float] = mapped_column(Float, default=2.0)
    last_review: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    next_review: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="attempts")
    item: Mapped["PracticeItem"] = relationship("PracticeItem", back_populates="attempts")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="valid_confidence"),
        CheckConstraint("difficulty >= 0 AND difficulty <= 1", name="valid_srs_difficulty"),
        CheckConstraint("stability > 0", name="positive_stability"),
        Index("idx_attempts_user_item", "user_id", "item_id"),
        Index("idx_attempts_next_review", "next_review"),
    )


class MasteryRecord(Base):
    """Simplified mastery tracking per user-objective."""
    
    __tablename__ = "mastery_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    objective_id: Mapped[int] = mapped_column(Integer, ForeignKey("objectives.id"), nullable=False)
    
    # Simple mastery tracking
    probability: Mapped[float] = mapped_column(Float, default=0.1)  # P(mastery)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_attempts: Mapped[int] = mapped_column(Integer, default=0)
    
    # Time tracking
    first_attempt: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_attempt: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="mastery_records")
    objective: Mapped["Objective"] = relationship("Objective", back_populates="mastery_records")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "objective_id", name="unique_user_objective_mastery"),
        CheckConstraint("probability >= 0 AND probability <= 1", name="valid_mastery_prob"),
        CheckConstraint("correct_attempts <= total_attempts", name="valid_attempt_counts"),
        Index("idx_mastery_records_user", "user_id"),
    )


class Note(Base):
    """User notes with flashcard generation and vector search."""
    
    __tablename__ = "notes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    objective_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("objectives.id"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    note_type: Mapped[str] = mapped_column(String(20), default="note")  # note, flashcard
    
    # SRS data for flashcards
    is_flashcard: Mapped[bool] = mapped_column(Boolean, default=False)
    front: Mapped[Optional[str]] = mapped_column(Text)  # Question side
    back: Mapped[Optional[str]] = mapped_column(Text)   # Answer side
    difficulty: Mapped[Optional[float]] = mapped_column(Float, default=0.5)
    stability: Mapped[Optional[float]] = mapped_column(Float, default=2.0)
    next_review: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Vector embeddings for semantic search
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(384))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notes")
    objective: Mapped[Optional["Objective"]] = relationship("Objective")
    
    # Constraints
    __table_args__ = (
        Index("idx_notes_user_objective", "user_id", "objective_id"),
        Index("idx_notes_flashcard_review", "is_flashcard", "next_review"),
        Index("idx_notes_embedding", "embedding", postgresql_using="ivfflat", postgresql_ops={"embedding": "vector_cosine_ops"}),
    )


class StudyPlan(Base):
    """User study plans with timeline and scheduling."""
    
    __tablename__ = "study_plans"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    blueprint_id: Mapped[int] = mapped_column(Integer, ForeignKey("exam_blueprints.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    target_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    daily_hours: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="study_plans")
    blueprint: Mapped["ExamBlueprint"] = relationship("ExamBlueprint", back_populates="study_plans")
    study_sessions: Mapped[List["StudySession"]] = relationship("StudySession", back_populates="study_plan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("daily_hours > 0 AND daily_hours <= 24", name="valid_daily_hours"),
        CheckConstraint("progress >= 0 AND progress <= 1", name="valid_progress"),
        Index("idx_study_plans_user_status", "user_id", "status"),
    )


class StudySession(Base):
    """Practice sessions for tracking study activity."""
    
    __tablename__ = "study_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    study_plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("study_plans.id"), nullable=False)
    session_type: Mapped[str] = mapped_column(String(20), default="practice")  # practice, review, mock
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    items_completed: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    study_plan: Mapped["StudyPlan"] = relationship("StudyPlan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("correct_answers <= items_completed", name="valid_correct_count"),
        Index("idx_sessions_user_date", "user_id", "started_at"),
    )


# Create indexes for performance optimization
def create_performance_indexes(engine):
    """Create additional performance indexes after table creation."""
    from sqlalchemy import text
    
    with engine.connect() as conn:
        # Create GIN index for JSON columns
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_items_content_gin 
            ON practice_items USING gin (content);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_attempts_response_gin 
            ON attempts USING gin (response);
        """))
        
        # Create partial indexes for active records
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_exam_blueprints_active 
            ON exam_blueprints (id) WHERE active = true;
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_study_plans_active 
            ON study_plans (user_id, created_at) WHERE status = 'active';
        """))
        
        conn.commit()
