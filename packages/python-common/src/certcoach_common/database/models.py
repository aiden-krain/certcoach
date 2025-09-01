"""
Database models for CertCoach
SQLAlchemy models with Supabase integration
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
from typing import Dict, List, Optional

Base = declarative_base()

class ExamBlueprint(Base):
    """Exam blueprint definitions (DP-700, DBX-DEA, etc.)"""
    __tablename__ = "exam_blueprints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)  # "DP-700 Microsoft Fabric Data Engineer"
    exam_code = Column(String(50), nullable=False, unique=True)  # "dp-700"
    version = Column(String(20), nullable=False)  # "2024-12"
    status = Column(String(20), nullable=False, default="active")  # active, deprecated
    description = Column(Text)
    target_duration_hours = Column(Integer)  # Recommended study hours
    difficulty_level = Column(String(20))  # beginner, intermediate, advanced
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    objectives = relationship("Objective", back_populates="exam_blueprint", cascade="all, delete-orphan")
    study_plans = relationship("StudyPlan", back_populates="exam_blueprint")
    items = relationship("Item", back_populates="exam_blueprint")
    
    __table_args__ = (
        Index("idx_exam_blueprints_code_version", "exam_code", "version"),
        Index("idx_exam_blueprints_status", "status"),
    )

class Objective(Base):
    """Learning objectives within exam blueprints"""
    __tablename__ = "objectives"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_blueprint_id = Column(UUID(as_uuid=True), ForeignKey("exam_blueprints.id"), nullable=False)
    objective_id = Column(String(100), nullable=False)  # "impl_manage_analytics.security_governance"
    name = Column(String(300), nullable=False)
    description = Column(Text)
    weight = Column(Float, nullable=False)  # Decimal weight (0.0-1.0)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("objectives.id"), nullable=True)
    level = Column(Integer, default=0)  # 0=top-level, 1=sub-objective, etc.
    tasks = Column(JSON)  # List of specific tasks/skills
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    exam_blueprint = relationship("ExamBlueprint", back_populates="objectives")
    parent = relationship("Objective", remote_side=[id], backref="children")
    items = relationship("Item", back_populates="objective")
    mastery_records = relationship("MasteryRecord", back_populates="objective")
    
    __table_args__ = (
        Index("idx_objectives_exam_blueprint", "exam_blueprint_id"),
        Index("idx_objectives_objective_id", "objective_id"),
        Index("idx_objectives_parent", "parent_id"),
        CheckConstraint("weight >= 0 AND weight <= 1", name="check_weight_range"),
        UniqueConstraint("exam_blueprint_id", "objective_id", name="unique_exam_objective"),
    )

class User(Base):
    """User accounts with Supabase auth integration"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True)  # Matches Supabase auth.users.id
    email = Column(String(255), nullable=False, unique=True)
    full_name = Column(String(200))
    avatar_url = Column(String(500))
    oauth_provider = Column(String(50))  # github, microsoft, google
    subscription_tier = Column(String(20), default="free")  # free, premium, enterprise
    timezone = Column(String(50), default="UTC")
    preferences = Column(JSON, default=dict)  # UI preferences, notifications, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    study_plans = relationship("StudyPlan", back_populates="user", cascade="all, delete-orphan")
    attempts = relationship("Attempt", back_populates="user", cascade="all, delete-orphan")
    mastery_records = relationship("MasteryRecord", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_subscription", "subscription_tier"),
        Index("idx_users_last_active", "last_active_at"),
    )

class StudyPlan(Base):
    """User study plans for specific exams"""
    __tablename__ = "study_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exam_blueprint_id = Column(UUID(as_uuid=True), ForeignKey("exam_blueprints.id"), nullable=False)
    name = Column(String(200), nullable=False)
    target_exam_date = Column(DateTime)
    hours_per_week = Column(Integer, default=10)
    preferred_study_days = Column(JSON, default=list)  # [1,2,3,4,5] for Mon-Fri
    status = Column(String(20), default="active")  # active, paused, completed
    current_phase = Column(String(50), default="initial_learning")  # initial_learning, review, intensive
    progress_percentage = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="study_plans")
    exam_blueprint = relationship("ExamBlueprint", back_populates="study_plans")
    sessions = relationship("StudySession", back_populates="study_plan", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_study_plans_user", "user_id"),
        Index("idx_study_plans_exam", "exam_blueprint_id"), 
        Index("idx_study_plans_status", "status"),
        CheckConstraint("hours_per_week > 0 AND hours_per_week <= 168", name="check_hours_per_week"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100", name="check_progress_range"),
    )

class StudySession(Base):
    """Individual study sessions (daily practice, weekly mocks, etc.)"""
    __tablename__ = "study_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_plan_id = Column(UUID(as_uuid=True), ForeignKey("study_plans.id"), nullable=False)
    session_type = Column(String(30), nullable=False)  # daily_practice, weekly_mock, review_session
    scheduled_date = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    status = Column(String(20), default="scheduled")  # scheduled, in_progress, completed, skipped
    objective_mix = Column(JSON)  # {"objective_id": weight, ...} for this session
    target_duration_minutes = Column(Integer, default=25)
    actual_duration_minutes = Column(Integer)
    score_percentage = Column(Float)
    items_attempted = Column(Integer, default=0)
    items_correct = Column(Integer, default=0)
    session_notes = Column(Text)
    
    # Relationships
    study_plan = relationship("StudyPlan", back_populates="sessions")
    attempts = relationship("Attempt", back_populates="study_session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_study_sessions_plan", "study_plan_id"),
        Index("idx_study_sessions_scheduled", "scheduled_date"),
        Index("idx_study_sessions_type_status", "session_type", "status"),
        CheckConstraint("target_duration_minutes > 0", name="check_target_duration"),
        CheckConstraint("score_percentage IS NULL OR (score_percentage >= 0 AND score_percentage <= 100)", name="check_score_range"),
    )

class Item(Base):
    """Practice questions and content items"""
    __tablename__ = "items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_blueprint_id = Column(UUID(as_uuid=True), ForeignKey("exam_blueprints.id"), nullable=False)
    objective_id = Column(UUID(as_uuid=True), ForeignKey("objectives.id"), nullable=False)
    item_type = Column(String(30), nullable=False)  # scenario_mcq, code_outcome, troubleshooting
    title = Column(String(300))
    prompt = Column(Text, nullable=False)  # Question text
    content = Column(JSON, nullable=False)  # Full content including options, code, etc.
    correct_answer = Column(JSON, nullable=False)  # Correct answer(s)
    rationale = Column(Text, nullable=False)  # Detailed explanation
    difficulty_score = Column(Float, default=0.5)  # 0.0-1.0 difficulty rating
    cognitive_level = Column(String(20))  # remember, understand, apply, analyze, evaluate, create
    estimated_time_seconds = Column(Integer, default=120)
    source_materials = Column(JSON, default=list)  # List of source references
    tags = Column(ARRAY(String), default=list)  # Searchable tags
    status = Column(String(20), default="active")  # active, under_review, archived
    quality_score = Column(Float)  # Human/AI quality rating
    usage_count = Column(Integer, default=0)  # How many times used
    success_rate = Column(Float)  # Overall success rate
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    exam_blueprint = relationship("ExamBlueprint", back_populates="items")
    objective = relationship("Objective", back_populates="items")
    attempts = relationship("Attempt", back_populates="item", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_items_exam_blueprint", "exam_blueprint_id"),
        Index("idx_items_objective", "objective_id"),
        Index("idx_items_type", "item_type"),
        Index("idx_items_difficulty", "difficulty_score"),
        Index("idx_items_status", "status"),
        Index("idx_items_tags", "tags", postgresql_using="gin"),
        CheckConstraint("difficulty_score >= 0 AND difficulty_score <= 1", name="check_difficulty_range"),
        CheckConstraint("estimated_time_seconds > 0", name="check_time_positive"),
    )

class Attempt(Base):
    """User attempts at practice items"""
    __tablename__ = "attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False)
    study_session_id = Column(UUID(as_uuid=True), ForeignKey("study_sessions.id"), nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    submitted_at = Column(DateTime)
    user_answer = Column(JSON)  # User's selected answer(s)
    is_correct = Column(Boolean)
    time_spent_seconds = Column(Integer)
    confidence_level = Column(Integer)  # 1-5 how confident user feels
    difficulty_rating = Column(Integer)  # 1-5 how difficult user found it
    user_notes = Column(Text)  # User's notes on this question
    
    # Relationships
    user = relationship("User", back_populates="attempts")
    item = relationship("Item", back_populates="attempts")
    study_session = relationship("StudySession", back_populates="attempts")
    
    __table_args__ = (
        Index("idx_attempts_user", "user_id"),
        Index("idx_attempts_item", "item_id"),
        Index("idx_attempts_session", "study_session_id"),
        Index("idx_attempts_submitted", "submitted_at"),
        Index("idx_attempts_user_item", "user_id", "item_id"),
        CheckConstraint("confidence_level IS NULL OR (confidence_level >= 1 AND confidence_level <= 5)", name="check_confidence_range"),
        CheckConstraint("difficulty_rating IS NULL OR (difficulty_rating >= 1 AND difficulty_rating <= 5)", name="check_difficulty_rating_range"),
        CheckConstraint("time_spent_seconds IS NULL OR time_spent_seconds >= 0", name="check_time_non_negative"),
    )

class MasteryRecord(Base):
    """User mastery tracking per objective using Bayesian inference"""
    __tablename__ = "mastery_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    objective_id = Column(UUID(as_uuid=True), ForeignKey("objectives.id"), nullable=False)
    probability_correct = Column(Float, nullable=False, default=0.5)  # Bayesian probability
    confidence_interval = Column(Float, default=0.2)  # Width of confidence interval
    attempts_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime)
    last_review_at = Column(DateTime)
    next_review_due = Column(DateTime)
    mastery_level = Column(String(20), default="novice")  # novice, developing, proficient, expert
    learning_velocity = Column(Float, default=0.0)  # Rate of improvement
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="mastery_records")
    objective = relationship("Objective", back_populates="mastery_records")
    
    __table_args__ = (
        Index("idx_mastery_user", "user_id"),
        Index("idx_mastery_objective", "objective_id"),
        Index("idx_mastery_due", "next_review_due"),
        Index("idx_mastery_level", "mastery_level"),
        UniqueConstraint("user_id", "objective_id", name="unique_user_objective_mastery"),
        CheckConstraint("probability_correct >= 0 AND probability_correct <= 1", name="check_probability_range"),
        CheckConstraint("attempts_count >= 0", name="check_attempts_non_negative"),
        CheckConstraint("correct_count >= 0 AND correct_count <= attempts_count", name="check_correct_count"),
    )

class Note(Base):
    """User study notes with vector embeddings for search"""
    __tablename__ = "notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exam_blueprint_id = Column(UUID(as_uuid=True), ForeignKey("exam_blueprints.id"), nullable=True)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default="markdown")  # markdown, plain_text
    tags = Column(ARRAY(String), default=list)
    is_public = Column(Boolean, default=False)  # Allow sharing with other users
    flashcards = Column(JSON, default=list)  # Generated flashcards from content
    embedding = Column(Vector(384))  # Vector embedding for semantic search
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notes")
    exam_blueprint = relationship("ExamBlueprint")
    
    __table_args__ = (
        Index("idx_notes_user", "user_id"),
        Index("idx_notes_exam", "exam_blueprint_id"),
        Index("idx_notes_tags", "tags", postgresql_using="gin"),
        Index("idx_notes_public", "is_public"),
        Index("idx_notes_embedding", "embedding", postgresql_using="ivfflat", postgresql_ops={"embedding": "vector_cosine_ops"}),
    )

class AuditLog(Base):
    """Comprehensive audit trail for security and compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # login, create_item, submit_answer, etc.
    resource_type = Column(String(50))  # user, item, study_plan, etc.
    resource_id = Column(String(100))  # ID of affected resource
    details = Column(JSON, default=dict)  # Additional context
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    session_id = Column(String(100))
    risk_score = Column(Float, default=0.0)  # Automated risk assessment
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index("idx_audit_logs_user", "user_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_timestamp", "timestamp"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
        Index("idx_audit_logs_risk", "risk_score"),
    )

class ContentSource(Base):
    """Tracking of official documentation sources for compliance"""
    __tablename__ = "content_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(1000), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    domain = Column(String(200), nullable=False)
    license_type = Column(String(100), nullable=False)
    content_hash = Column(String(64))  # SHA-256 of content for change detection
    last_verified_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    verification_status = Column(String(20), default="verified")  # verified, broken, quarantined
    content_excerpt = Column(Text)  # Small excerpt for verification
    metadata = Column(JSON, default=dict)  # Additional source metadata
    
    __table_args__ = (
        Index("idx_content_sources_domain", "domain"),
        Index("idx_content_sources_verified", "last_verified_at"),
        Index("idx_content_sources_status", "verification_status"),
        Index("idx_content_sources_hash", "content_hash"),
    )
