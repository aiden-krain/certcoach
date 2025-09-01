"""
Database models for CertCoach platform.

This module defines SQLAlchemy models for all database tables including
exam blueprints, study plans, mastery tracking, and vector embeddings.
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
    study_sessions: Mapped[List["StudySession"]] = relationship("StudySession", back_populates="user")
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
    study_sessions: Mapped[List["StudySession"]] = relationship("StudySession", back_populates="study_plan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("daily_hours > 0 AND daily_hours <= 24", name="valid_daily_hours"),
        CheckConstraint("progress >= 0 AND progress <= 1", name="valid_progress"),
        Index("idx_study_plans_user_status", "user_id", "status"),
    )


class StudySession(Base):
    """Individual study sessions with items and outcomes."""
    
    __tablename__ = "study_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    study_plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("study_plans.id"), nullable=False)
    session_type: Mapped[str] = mapped_column(String(20), default="practice")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    items_planned: Mapped[int] = mapped_column(Integer, default=0)
    items_completed: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    total_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="study_sessions")
    study_plan: Mapped["StudyPlan"] = relationship("StudyPlan", back_populates="study_sessions")
    attempts: Mapped[List["Attempt"]] = relationship("Attempt", back_populates="session")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("items_completed <= items_planned", name="valid_completion_count"),
        CheckConstraint("correct_answers <= items_completed", name="valid_correct_count"),
        Index("idx_study_sessions_user_date", "user_id", "scheduled_at"),
    )


class Item(Base):
    """Practice questions and learning items with metadata."""
    
    __tablename__ = "items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    blueprint_id: Mapped[int] = mapped_column(Integer, ForeignKey("exam_blueprints.id"), nullable=False)
    objective_id: Mapped[int] = mapped_column(Integer, ForeignKey("objectives.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)  # mcq, scenario, code, etc.
    difficulty: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0-1.0
    content: Mapped[dict] = mapped_column(JSON, nullable=False)  # Question data
    solution: Mapped[dict] = mapped_column(JSON, nullable=False)  # Answer and explanation
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    source_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("content_sources.id"))
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    review_status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    blueprint: Mapped["ExamBlueprint"] = relationship("ExamBlueprint")
    objective: Mapped["Objective"] = relationship("Objective")
    source: Mapped[Optional["ContentSource"]] = relationship("ContentSource", back_populates="items")
    attempts: Mapped[List["Attempt"]] = relationship("Attempt", back_populates="item")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("difficulty >= 0 AND difficulty <= 1", name="valid_difficulty"),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)", name="valid_quality"),
        Index("idx_items_objective_difficulty", "objective_id", "difficulty"),
        Index("idx_items_review_status", "review_status"),
    )


class Attempt(Base):
    """User attempts on practice items with SRS data."""
    
    __tablename__ = "attempts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    session_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("study_sessions.id"))
    response: Mapped[dict] = mapped_column(JSON, nullable=False)  # User's answer
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float)  # Self-reported confidence
    time_spent: Mapped[Optional[int]] = mapped_column(Integer)  # Seconds
    hint_used: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # FSRS spaced repetition data
    difficulty: Mapped[float] = mapped_column(Float, default=0.5)
    stability: Mapped[float] = mapped_column(Float, default=2.0)
    retrievability: Mapped[float] = mapped_column(Float, default=0.9)
    last_review: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    next_review: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="attempts")
    item: Mapped["Item"] = relationship("Item", back_populates="attempts")
    session: Mapped[Optional["StudySession"]] = relationship("StudySession", back_populates="attempts")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="valid_confidence"),
        CheckConstraint("difficulty >= 0 AND difficulty <= 1", name="valid_srs_difficulty"),
        CheckConstraint("stability > 0", name="positive_stability"),
        CheckConstraint("retrievability >= 0 AND retrievability <= 1", name="valid_retrievability"),
        Index("idx_attempts_user_item", "user_id", "item_id"),
        Index("idx_attempts_next_review", "next_review"),
    )


class MasteryRecord(Base):
    """Bayesian mastery tracking per user-objective."""
    
    __tablename__ = "mastery_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    objective_id: Mapped[int] = mapped_column(Integer, ForeignKey("objectives.id"), nullable=False)
    
    # Bayesian mastery tracking
    mastery_probability: Mapped[float] = mapped_column(Float, default=0.1)
    confidence_interval: Mapped[float] = mapped_column(Float, default=0.9)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_attempts: Mapped[int] = mapped_column(Integer, default=0)
    recent_velocity: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Time tracking
    first_attempt: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_attempt: Mapped[Optional[datetime]] = mapped_column(DateTime)
    mastery_achieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="mastery_records")
    objective: Mapped["Objective"] = relationship("Objective", back_populates="mastery_records")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "objective_id", name="unique_user_objective_mastery"),
        CheckConstraint("mastery_probability >= 0 AND mastery_probability <= 1", name="valid_mastery_prob"),
        CheckConstraint("confidence_interval >= 0 AND confidence_interval <= 1", name="valid_confidence_interval"),
        CheckConstraint("correct_attempts <= total_attempts", name="valid_attempt_counts"),
        Index("idx_mastery_records_user", "user_id"),
        Index("idx_mastery_records_mastery_prob", "mastery_probability"),
    )


class Note(Base):
    """User notes with vector embeddings for semantic search."""
    
    __tablename__ = "notes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    objective_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("objectives.id"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), default="markdown")
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Vector embeddings for semantic search
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(384))  # all-MiniLM-L6-v2 dimensions
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notes")
    objective: Mapped[Optional["Objective"]] = relationship("Objective")
    
    # Constraints
    __table_args__ = (
        Index("idx_notes_user_objective", "user_id", "objective_id"),
        Index("idx_notes_embedding", "embedding", postgresql_using="ivfflat", postgresql_ops={"embedding": "vector_cosine_ops"}),
    )


class ContentSource(Base):
    """Source attribution and compliance tracking."""
    
    __tablename__ = "content_sources"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # official_docs, community, generated
    url: Mapped[Optional[str]] = mapped_column(String(500))
    license_type: Mapped[Optional[str]] = mapped_column(String(100))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    items: Mapped[List["Item"]] = relationship("Item", back_populates="source")
    
    # Constraints
    __table_args__ = (
        Index("idx_content_sources_type_verified", "source_type", "verified"),
    )


class AuditLog(Base):
    """Security and compliance audit logging."""
    
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")
    
    # Constraints
    __table_args__ = (
        Index("idx_audit_logs_user_action", "user_id", "action"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
        Index("idx_audit_logs_created_at", "created_at"),
    )


# Create indexes for performance optimization
def create_performance_indexes(engine):
    """Create additional performance indexes after table creation."""
    from sqlalchemy import text
    
    with engine.connect() as conn:
        # Create GIN index for JSON columns
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_items_content_gin 
            ON items USING gin (content);
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
