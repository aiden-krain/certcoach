# 🚀 **Development Guide**

This guide provides comprehensive instructions for setting up, developing, and contributing to the CertCoach platform.

## 🛠️ **Development Environment Setup**

### **Prerequisites**
Before starting, ensure you have the following installed:

- **Python 3.12+** - Core backend runtime
- **uv** - Fast Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Node.js 18+** - Frontend development (optional for backend-only work)
- **Git** - Version control
- **VS Code** - Recommended IDE with Python and FastAPI extensions
- **Supabase Account** - Database and authentication provider
- **Redis** (optional) - For caching and background jobs

### **1. Repository Setup**
```bash
# Clone the repository
git clone https://github.com/your-org/certcoach.git
cd certcoach

# Install Python dependencies with uv
uv sync --dev

# Verify installation
uv run python --version
uv run python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
```

### **2. Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required variables:
DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
SUPABASE_URL=https://[project].supabase.co
SUPABASE_ANON_KEY=[anon-key]
SUPABASE_SERVICE_ROLE_KEY=[service-key]
OPENAI_API_KEY=[your-openai-key]
```

### **3. Database Setup**
```bash
# Initialize database schema
uv run python scripts/setup_database.py

# Load exam blueprints
uv run python scripts/seed_blueprints.py

# (Optional) Load sample data for development
uv run python scripts/seed_sample_data.py

# Verify setup
uv run python -c "
from packages.database.connection import get_database_engine
import asyncio
async def test():
    engine = get_database_engine()
    print('Database connection successful!')
asyncio.run(test())
"
```

### **4. Start Development Server**
```bash
# Start FastAPI with hot reload
uv run uvicorn services.api.main:app --reload --port 8000

# Server will be available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

---

## 🏗️ **Project Structure & Conventions**

### **Code Organization**
```
services/api/
├── main.py              # FastAPI app factory
├── routers/             # API endpoints (one file per domain)
│   ├── __init__.py
│   ├── health.py        # Health checks
│   ├── auth.py          # Authentication
│   ├── study_plans.py   # Study plan management
│   ├── practice.py      # Practice sessions
│   ├── mastery.py       # Mastery tracking
│   └── notes.py         # Notes and flashcards
├── core/                # Business logic (domain services)
│   ├── __init__.py
│   ├── planner.py       # Study plan generation
│   ├── practice.py      # Practice engine + FSRS
│   ├── mastery.py       # Bayesian mastery tracking
│   └── calendar.py      # iCal export
├── models/              # Pydantic schemas
│   ├── __init__.py
│   ├── study_plans.py   # Study plan schemas
│   ├── practice.py      # Practice session schemas
│   └── notes.py         # Notes schemas
├── middleware/          # FastAPI middleware
│   ├── __init__.py
│   ├── auth.py          # JWT authentication
│   └── logging.py       # Request logging
└── dependencies.py      # Shared dependencies
```

### **Naming Conventions**
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Database Tables**: `snake_case`
- **API Endpoints**: `kebab-case` for URLs, `snake_case` for parameters

### **Import Standards**
```python
# Standard library imports
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

# Local imports
from packages.database.models import User, StudyPlan
from services.api.models.study_plans import CreateStudyPlanRequest
from services.api.core.planner import StudyPlanGenerator
from services.api.dependencies import get_current_user, get_db_session
```

---

## 🧪 **Testing Strategy**

### **Test Structure**
```
tests/
├── unit/                # Fast, isolated unit tests
│   ├── test_core/       # Business logic tests
│   ├── test_models/     # Pydantic model tests
│   └── test_utils/      # Utility function tests
├── integration/         # Database and service integration tests
│   ├── test_database/   # Database operation tests
│   ├── test_api/        # API endpoint tests
│   └── test_external/   # External service tests
└── fixtures/            # Test data and fixtures
    ├── sample_data.py   # Test data factories
    └── conftest.py      # Pytest configuration
```

### **Running Tests**
```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=services --cov=packages --cov-report=html

# Run specific test categories
uv run pytest tests/unit/           # Unit tests only
uv run pytest tests/integration/    # Integration tests only
uv run pytest -k "test_study_plan"  # Tests matching pattern

# Run tests with verbose output
uv run pytest -v --tb=short

# Run tests in parallel (requires pytest-xdist)
uv run pytest -n auto
```

### **Writing Tests**
```python
# Example unit test
import pytest
from services.api.core.planner import StudyPlanGenerator
from services.api.models.study_plans import CreateStudyPlanRequest

class TestStudyPlanGenerator:
    @pytest.fixture
    def generator(self):
        return StudyPlanGenerator()
    
    @pytest.fixture
    def sample_request(self):
        return CreateStudyPlanRequest(
            name="DP-700 Study Plan",
            exam_blueprint_id="123e4567-e89b-12d3-a456-426614174000",
            exam_date="2024-06-01",
            daily_study_hours=2.0
        )
    
    async def test_generate_plan_creates_valid_schedule(self, generator, sample_request):
        # Test business logic without database
        plan = await generator.generate_plan(sample_request)
        
        assert plan.name == sample_request.name
        assert plan.total_sessions > 0
        assert plan.estimated_completion_date <= sample_request.exam_date

# Example integration test
import pytest
from httpx import AsyncClient
from services.api.main import app

@pytest.mark.asyncio
async def test_create_study_plan_endpoint(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/study-plans",
        json={
            "name": "Test Plan",
            "exam_blueprint_id": "123e4567-e89b-12d3-a456-426614174000",
            "exam_date": "2024-06-01",
            "daily_study_hours": 1.5
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Plan"
    assert "id" in data
```

---

## 🔧 **Development Workflow**

### **Daily Development Process**
1. **Start Development Environment**
   ```bash
   # Terminal 1: Start database (if local)
   docker run -d --name certcoach-redis -p 6379:6379 redis:7-alpine
   
   # Terminal 2: Start FastAPI server
   uv run uvicorn services.api.main:app --reload --port 8000
   
   # Terminal 3: Run tests in watch mode (optional)
   uv run pytest --watch
   ```

2. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/study-plan-improvements
   ```

3. **Development Cycle**
   - Write failing tests first (TDD approach)
   - Implement functionality
   - Run tests: `uv run pytest`
   - Check type hints: `uv run mypy services/ packages/`
   - Format code: `uv run ruff format .`
   - Lint code: `uv run ruff check . --fix`

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: improve study plan generation algorithm"
   git push origin feature/study-plan-improvements
   ```

### **Code Quality Tools**
```bash
# Type checking with mypy
uv run mypy services/ packages/

# Code formatting with ruff
uv run ruff format .

# Linting with ruff
uv run ruff check . --fix

# Import sorting
uv run ruff check . --select I --fix

# Check for security issues
uv run bandit -r services/ packages/
```

### **Pre-commit Hooks** (Recommended)
```bash
# Install pre-commit
uv add --dev pre-commit

# Set up git hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

---

## 🗄️ **Database Development**

### **Database Migrations**
```bash
# Create new migration
uv run alembic revision --autogenerate -m "Add practice_items table"

# Apply migrations
uv run alembic upgrade head

# Downgrade migration
uv run alembic downgrade -1

# View migration history
uv run alembic history

# Check current revision
uv run alembic current
```

### **Database Development Patterns**
```python
# Creating a new database model
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class NewModel(Base):
    __tablename__ = "new_models"
    
    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String(255), nullable=False)
    data = Column(JSONB, default={})
    created_at = Column(DateTime, server_default=text("NOW()"))
    
    # Always add indexes for foreign keys and common queries
    __table_args__ = (
        Index('idx_new_models_name', 'name'),
    )

# Database query patterns
async def get_models_by_name(db: AsyncSession, name: str) -> List[NewModel]:
    result = await db.execute(
        select(NewModel).where(NewModel.name.ilike(f"%{name}%"))
    )
    return result.scalars().all()
```

### **Testing with Database**
```python
# Use test database for integration tests
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from packages.database.models import Base

@pytest.fixture
async def test_db():
    # Create test database
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_certcoach")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

---

## 🔌 **API Development Guidelines**

### **Router Structure**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from services.api.models.study_plans import StudyPlanResponse, CreateStudyPlanRequest
from services.api.dependencies import get_current_user, get_db_session

router = APIRouter(prefix="/api/v1/study-plans", tags=["study-plans"])

@router.get("/", response_model=List[StudyPlanResponse])
async def list_study_plans(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = 10,
    offset: int = 0
) -> List[StudyPlanResponse]:
    """List user's study plans with pagination."""
    # Implementation here
    pass

@router.post("/", response_model=StudyPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_study_plan(
    plan_data: CreateStudyPlanRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> StudyPlanResponse:
    """Create a new study plan."""
    # Implementation here
    pass
```

### **Error Handling Patterns**
```python
from fastapi import HTTPException, status

# Custom exceptions
class StudyPlanNotFound(HTTPException):
    def __init__(self, plan_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study plan {plan_id} not found"
        )

class InvalidExamDate(HTTPException):
    def __init__(self, exam_date: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exam date {exam_date} must be in the future"
        )

# Usage in endpoints
@router.get("/{plan_id}")
async def get_study_plan(plan_id: str, db: AsyncSession = Depends(get_db_session)):
    plan = await get_plan_by_id(db, plan_id)
    if not plan:
        raise StudyPlanNotFound(plan_id)
    return plan
```

### **Response Models**
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class StudyPlanResponse(BaseModel):
    id: str = Field(..., description="Unique plan identifier")
    name: str = Field(..., description="Plan name")
    exam_date: Optional[datetime] = Field(None, description="Target exam date")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True  # For SQLAlchemy model conversion
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

---

## 🚀 **Deployment & Production**

### **Environment Preparation**
```bash
# Production dependencies only
uv sync --no-dev

# Environment variables for production
export ENVIRONMENT=production
export DATABASE_URL=postgresql://...
export REDIS_URL=redis://...
export OPENAI_API_KEY=...
```

### **Production Server**
```bash
# Using Gunicorn with uvicorn workers
uv run gunicorn services.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
```

### **Docker Deployment**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependencies
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev --no-cache

# Copy application
COPY . .

# Run application
CMD ["uv", "run", "gunicorn", "services.api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

---

## 🤝 **Contributing Guidelines**

### **Code Review Process**
1. **Before Creating PR**
   - All tests pass: `uv run pytest`
   - Code is formatted: `uv run ruff format .`
   - No linting errors: `uv run ruff check .`
   - Type checking passes: `uv run mypy services/ packages/`

2. **PR Requirements**
   - Clear description of changes
   - Tests for new functionality
   - Documentation updates if needed
   - Breaking changes clearly marked

3. **Review Checklist**
   - ✅ Code follows project conventions
   - ✅ Tests cover new functionality
   - ✅ No security vulnerabilities
   - ✅ Performance implications considered
   - ✅ Documentation updated

### **Git Workflow**
```bash
# Feature development
git checkout main
git pull origin main
git checkout -b feature/new-feature

# Regular commits with conventional format
git commit -m "feat: add study plan export functionality"
git commit -m "fix: handle timezone conversion in schedules"
git commit -m "docs: update API documentation"

# Before pushing
uv run pytest
uv run ruff format .
uv run ruff check .

git push origin feature/new-feature
```

### **Commit Message Conventions**
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions or updates
- `chore:` Maintenance tasks

---

## 🐛 **Debugging & Troubleshooting**

### **Common Issues**

1. **Database Connection Errors**
   ```bash
   # Check database connectivity
   uv run python -c "
   import asyncio
   from packages.database.connection import get_database_engine
   async def test():
       engine = get_database_engine()
       print('Connected to database successfully')
   asyncio.run(test())
   "
   ```

2. **Import Errors**
   ```bash
   # Check Python path
   uv run python -c "import sys; print('\n'.join(sys.path))"
   
   # Verify package installation
   uv run python -c "import fastapi, sqlalchemy, pydantic; print('All packages available')"
   ```

3. **Migration Issues**
   ```bash
   # Reset migrations (development only)
   uv run alembic downgrade base
   uv run alembic upgrade head
   ```

### **Debugging Tools**
```python
# Add debugging to FastAPI routes
import logging
logger = logging.getLogger(__name__)

@router.post("/debug-endpoint")
async def debug_endpoint(data: dict):
    logger.debug(f"Received data: {data}")
    # Add breakpoint for debugging
    import pdb; pdb.set_trace()
    return {"status": "debug"}

# Use async debugging
import asyncio
import aiomonitor

# Start monitoring
with aiomonitor.start_monitor(asyncio.get_running_loop()):
    # Your async code here
    pass
```

---

This development guide provides everything needed to effectively contribute to the CertCoach platform. Follow these patterns and practices to maintain code quality and consistency across the project.
