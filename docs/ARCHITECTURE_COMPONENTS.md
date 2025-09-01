# 📋 **CertCoach Component Documentation**

This document provides comprehensive documentation for each component of the CertCoach simplified architecture, explaining their purpose, functionality, and interactions.

## 🏗️ **Architecture Components Overview**

CertCoach uses a simplified microservices architecture with a single FastAPI backend service, Supabase for database and authentication, and optional Redis for caching. Here's how each component works:

---

## 📱 **Services Layer**

### **`services/api/`** - Main FastAPI Backend Service

The core backend service that handles all business logic, API endpoints, and data processing.

#### **`main.py`** - Application Entry Point
**Purpose**: FastAPI application initialization and configuration
```python
# Key responsibilities:
- Application factory pattern for FastAPI app creation
- Middleware registration (CORS, logging, authentication)
- Router registration for all API endpoints
- Health check endpoints
- Environment-based configuration
- Database connection initialization
```

#### **`routers/`** - API Route Handlers
Organized by domain for clean separation of concerns.

##### **`health.py`** - Health Checks and Monitoring
**Purpose**: System health monitoring and service status
```python
# Endpoints:
GET /health        # Basic health check
GET /health/deep   # Database and external service checks
GET /metrics       # Prometheus-style metrics

# Features:
- Database connection health
- Redis connection status (if enabled)
- Memory and CPU usage
- Response time tracking
```

##### **`auth.py`** - Authentication Endpoints
**Purpose**: User authentication and session management
```python
# Endpoints:
POST /api/v1/auth/register    # User registration
POST /api/v1/auth/login       # User login
POST /api/v1/auth/logout      # User logout
GET  /api/v1/auth/profile     # Get user profile
PUT  /api/v1/auth/profile     # Update user profile

# Features:
- Supabase Auth integration
- JWT token handling
- Password reset functionality
- Profile management
```

##### **`study_plans.py`** - Study Plan Management
**Purpose**: Study plan creation, management, and scheduling
```python
# Endpoints:
POST /api/v1/study-plans            # Create new study plan
GET  /api/v1/study-plans            # List user's plans
GET  /api/v1/study-plans/{id}       # Get specific plan
PUT  /api/v1/study-plans/{id}       # Update plan
DELETE /api/v1/study-plans/{id}     # Delete plan
GET  /api/v1/study-plans/{id}/calendar # Export iCal

# Features:
- Blueprint-based plan generation
- Adaptive scheduling algorithms
- Progress tracking integration
- Calendar export (iCal format)
```

##### **`practice.py`** - Practice Session API
**Purpose**: Practice session generation and response handling
```python
# Endpoints:
POST /api/v1/practice/sessions      # Generate practice session
POST /api/v1/practice/attempts      # Submit answer attempt
GET  /api/v1/practice/review-queue  # Get items due for review
GET  /api/v1/practice/mock-exam     # Generate mock exam

# Features:
- Smart session assembly (2-3 reviews + 8-12 focus items)
- FSRS spaced repetition scheduling
- Performance tracking
- Adaptive difficulty adjustment
```

##### **`mastery.py`** - Mastery Tracking
**Purpose**: Learning progress and mastery probability tracking
```python
# Endpoints:
GET /api/v1/mastery/{user_id}       # Overall mastery overview
GET /api/v1/mastery/objectives/{id} # Per-objective mastery
GET /api/v1/mastery/gaps           # Gap analysis report
POST /api/v1/mastery/update        # Update mastery scores

# Features:
- Bayesian mastery probability calculation
- Learning objective tracking
- Gap analysis and recommendations
- Progress visualization data
```

##### **`notes.py`** - Notes and Flashcards
**Purpose**: Note management and flashcard generation
```python
# Endpoints:
POST /api/v1/notes                  # Create note
GET  /api/v1/notes                  # List user's notes
PUT  /api/v1/notes/{id}            # Update note
DELETE /api/v1/notes/{id}          # Delete note
GET  /api/v1/notes/search          # Semantic search
POST /api/v1/notes/{id}/flashcards # Generate flashcards
GET  /api/v1/notes/flashcards/due  # Get due flashcards

# Features:
- Vector semantic search (pgvector)
- Automatic flashcard generation
- SRS integration for flashcards
- Markdown note support
```

#### **`core/`** - Business Logic Modules
The heart of CertCoach's intelligence, containing all business rules and algorithms.

##### **`planner.py`** - Study Plan Generation
**Purpose**: Intelligent study plan creation and management
```python
# Core Functions:
- Blueprint weight analysis
- Timeline generation based on exam date
- Session scheduling with gap handling
- Progress-based plan adjustments

# Key Algorithms:
- Weighted objective prioritization
- Adaptive timeline compression/expansion
- Missed session rescheduling
- Calendar conflict resolution
```

##### **`practice.py`** - Practice Engine + FSRS
**Purpose**: Practice session assembly and spaced repetition
```python
# Core Functions:
- Session composition (reviews + new items)
- FSRS algorithm implementation
- Difficulty level adaptation
- Performance analysis

# Key Features:
- Free Spaced Repetition Scheduler (FSRS)
- Smart item selection algorithms
- Contextual hint generation
- Performance-based difficulty scaling
```

##### **`mastery.py`** - Bayesian Mastery Tracking
**Purpose**: Learning progress quantification using Bayesian inference
```python
# Core Functions:
- Mastery probability calculation
- Confidence interval tracking
- Learning velocity analysis
- Gap identification

# Key Algorithms:
- Bayesian updating based on performance
- Multi-objective mastery aggregation
- Time-decay for stale knowledge
- Confidence-based recommendations
```

##### **`calendar.py`** - iCal Export Functionality
**Purpose**: Calendar integration and export capabilities
```python
# Core Functions:
- iCal format generation
- Study session scheduling
- Reminder creation
- External calendar integration

# Features:
- RFC 5545 compliant iCal files
- Time zone handling
- Recurring session support
- Calendar app compatibility
```

#### **`models/`** - Pydantic Request/Response Models
Type-safe API contracts using Pydantic.

##### **`study_plans.py`** - Study Plan Schemas
```python
# Models:
- CreateStudyPlanRequest
- StudyPlanResponse
- UpdateStudyPlanRequest
- StudySessionResponse
- CalendarExportRequest

# Validation:
- Date range validation
- Blueprint compatibility checks
- Session duration constraints
```

##### **`practice.py`** - Practice Session Schemas
```python
# Models:
- PracticeSessionRequest
- PracticeSessionResponse
- AttemptSubmissionRequest
- AttemptResponse
- ReviewQueueResponse

# Validation:
- Answer format validation
- Session type constraints
- Performance metric bounds
```

##### **`notes.py`** - Notes and Flashcard Schemas
```python
# Models:
- CreateNoteRequest
- NoteResponse
- UpdateNoteRequest
- FlashcardGenerationRequest
- SearchRequest

# Validation:
- Markdown content validation
- Search query constraints
- Flashcard format rules
```

#### **`middleware/`** - FastAPI Middleware
Cross-cutting concerns handled at the middleware level.

##### **`auth.py`** - JWT Authentication
```python
# Functions:
- JWT token validation
- User context injection
- Route-based authorization
- Session management

# Features:
- Supabase JWT integration
- Automatic token refresh
- Role-based access control
- Request context enrichment
```

##### **`logging.py`** - Request/Response Logging
```python
# Functions:
- Structured request logging
- Performance monitoring
- Error tracking
- User activity logging

# Features:
- JSON structured logs
- Request/response correlation
- Performance metrics collection
- Error context capture
```

#### **`dependencies.py`** - Shared FastAPI Dependencies
```python
# Dependencies:
- Database session management
- User authentication verification
- Request validation
- Rate limiting

# Injection Points:
- Database connections
- Current user context
- Redis connections
- External API clients
```

---

## 🗄️ **Database Layer**

### **`packages/database/`** - Shared Database Layer

#### **`models.py`** - SQLAlchemy ORM Models
**Purpose**: Database schema definition and relationships
```python
# Core Tables (8 optimized tables):

# User Management
class User(Base):           # Supabase-integrated user accounts
class StudyPlan(Base):      # User study plans with timelines
class StudySession(Base):   # Individual practice sessions

# Content & Assessment
class ExamBlueprint(Base):  # Official exam structure definitions
class Objective(Base):      # Hierarchical learning objectives
class PracticeItem(Base):   # Questions with metadata and solutions

# Learning & Progress
class Attempt(Base):        # User responses with FSRS scheduling
class MasteryRecord(Base):  # Bayesian mastery probability per objective
class Note(Base):          # User notes with vector embeddings + flashcards

# Key Features:
- Foreign key relationships for data integrity
- Vector column support (pgvector)
- JSON columns for flexible metadata
- Timestamps and audit fields
- Row Level Security (RLS) integration
```

#### **`connection.py`** - Database Connection Management
**Purpose**: Database connection pooling and session management
```python
# Core Functions:
- Async database session factory
- Connection pool configuration
- Transaction management
- Error handling and retries

# Features:
- SQLAlchemy async engine
- Connection pool optimization
- Health check queries
- Migration support
```

---

## 📊 **Data Layer**

### **`data/blueprints/`** - Exam Blueprint Definitions
Official exam structure definitions in YAML format.

#### **`dp-700.yaml`** - Microsoft DP-700 Blueprint
```yaml
# Structure:
exam:
  name: "Microsoft Fabric Analytics Engineer"
  code: "DP-700"
  domains:
    - name: "Implement and manage a solution"
      weight: 35
      objectives:
        - id: "1.1"
          description: "Implement lakehouse architecture"
          sub_objectives: [...]

# Purpose:
- Official exam weight distribution
- Learning objective hierarchy
- Content area definitions
- Assessment criteria mapping
```

#### **`databricks-dea.yaml`** - Databricks DEA Blueprint
```yaml
# Structure:
exam:
  name: "Databricks Certified Data Engineer Associate"
  code: "DBX-DEA"
  domains: [...]

# Features:
- Multi-cloud platform coverage
- Technology-specific objectives
- Practical skill assessments
- Certification pathway alignment
```

### **`data/templates/`** - Question Templates
Reusable question generation templates.

#### **`scenario_mcq.py`** - Multi-Choice Scenarios
```python
# Purpose: Complex scenario-based multiple choice questions
# Features:
- Real-world problem scenarios
- Multiple correct answer formats
- Distractor analysis
- Difficulty scaling parameters
```

#### **`code_output.py`** - Code Execution Questions
```python
# Purpose: Code analysis and output prediction
# Features:
- Syntax highlighting support
- Multi-language code blocks
- Execution trace analysis
- Common error patterns
```

#### **`troubleshoot.py`** - Problem-Solving Scenarios
```python
# Purpose: Diagnostic and troubleshooting scenarios
# Features:
- Step-by-step problem solving
- Multiple solution paths
- Best practice reinforcement
- Real-world error scenarios
```

---

## 🔧 **Scripts Layer**

### **`scripts/`** - Utility Scripts
Database and development utilities.

#### **`setup_database.py`** - Database Initialization
```python
# Purpose: Complete database setup and configuration
# Functions:
- Create database schema
- Set up Row Level Security policies
- Configure pgvector extension
- Create indexes and constraints
- Initialize default data
```

#### **`seed_blueprints.py`** - Blueprint Data Loading
```python
# Purpose: Load exam blueprint definitions into database
# Functions:
- Parse YAML blueprint files
- Validate blueprint structure
- Create hierarchical objectives
- Calculate weight distributions
- Update existing blueprints
```

#### **`seed_sample_data.py`** - Development Sample Data
```python
# Purpose: Generate sample data for development and testing
# Functions:
- Create test users
- Generate practice items
- Create sample study plans
- Populate mastery records
- Generate test notes and flashcards
```

---

## 🔄 **Migration Layer**

### **`migrations/`** - Alembic Database Migrations
Database schema version control using Alembic.

#### **Migration Structure**
```python
# Migration files handle:
- Schema changes over time
- Data migration scripts
- Index creation/deletion
- Constraint modifications
- Function and trigger updates

# Key Files:
- env.py: Alembic environment configuration
- versions/: Individual migration files
- alembic.ini: Alembic configuration
```

---

## 🔗 **Component Interactions**

### **Request Flow Example: Creating a Practice Session**
```
1. Frontend → POST /api/v1/practice/sessions
2. auth.py middleware → Validates JWT token
3. practice.py router → Receives request
4. dependencies.py → Injects database session
5. core/practice.py → Assembles session using FSRS
6. packages/database/models.py → Queries practice items
7. core/mastery.py → Checks mastery levels
8. Response → Returns structured session data
```

### **Data Flow Example: Mastery Update**
```
1. User submits answer → practice.py router
2. Attempt recorded → database/models.py
3. FSRS algorithm updates → core/practice.py
4. Mastery probability recalculated → core/mastery.py
5. Study plan adjusted → core/planner.py
6. Next session scheduled → Updated in database
```

### **Background Process Example: Flashcard Generation**
```
1. User creates note → notes.py router
2. Note saved with content → database/models.py
3. Vector embedding generated → OpenAI API
4. Flashcards extracted → core/notes.py
5. SRS scheduling applied → core/practice.py
6. Flashcards available in review queue
```

---

## 🎯 **Key Design Principles**

### **1. Single Responsibility**
Each component has a clear, focused purpose with minimal coupling to other components.

### **2. Dependency Injection**
FastAPI's dependency injection system manages database connections, authentication, and shared services.

### **3. Type Safety**
Pydantic models ensure type safety across API boundaries with automatic validation.

### **4. Async First**
All database operations and external API calls use async/await for optimal performance.

### **5. Separation of Concerns**
Business logic (core/), API handling (routers/), and data models (packages/database/) are clearly separated.

### **6. Configuration-Driven**
Environment variables and configuration files drive behavior without code changes.

---

This architecture provides a solid foundation for the CertCoach MVP while maintaining simplicity and allowing for future growth. Each component is designed to be testable, maintainable, and scalable as the platform evolves.
