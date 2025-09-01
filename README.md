# 🎓 CertCoach - Adaptive Certification Exam Preparation Platform

**Intelligent, blueprint-driven study planning with AI-powered practice sessions and spaced repetition.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009639.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Supabase](https://img.shields.io/badge/Supabase-181818?style=flat&logo=supabase&logoColor=white)](https://supabase.com)

## 🌟 **Core Features**

### 🎯 **Blueprint-First Study Planner**
- **Weighted scheduling** based on official exam blueprints
- **Auto-reschedule** missed sessions with intelligent gap filling
- **Calendar integration** with iCal export for external apps
- **Progress tracking** with mastery-based timeline adjustments

### 🧠 **Adaptive Practice Engine**
- **Smart session assembly**: 2-3 reviews + 8-12 focus items
- **FSRS spaced repetition** for optimal memory retention
- **Difficulty adaptation** based on user performance
- **Contextual explanations** with official documentation links

### 📊 **Mastery Map & Analytics**
- **Bayesian mastery tracking** per learning objective
- **Gap analysis** highlighting weak areas
- **Weekly mock exams** with performance insights
- **Study velocity** and confidence interval tracking

### 📝 **Notes → Flashcards Pipeline**
- **One-click conversion** from markdown notes to flashcards
- **Vector semantic search** across all study materials
- **Integrated SRS scheduling** with the practice engine
- **Automatic Q&A extraction** from structured notes

## 🏗️ **Architecture Overview**

### **Simplified Single-Service Design**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js Web   │────│   FastAPI Backend │────│  Supabase DB    │
│   Frontend      │    │   (Single Service) │    │  + Auth + RT    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────────────────┐
                       │   Redis Cache    │
                       │   + Job Queue    │
                       └──────────────────┘
```

### **Technology Stack**
- **Backend**: FastAPI with async SQLAlchemy
- **Database**: Supabase (PostgreSQL + pgvector + Auth)
- **Cache/Queue**: Redis for sessions and background jobs
- **AI/ML**: OpenAI API for embeddings and content generation
- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Mobile**: React Native + Expo (roadmap)

## 📁 **Repository Structure**

```
certcoach/
├── services/
│   └── api/                    # Main FastAPI backend service
│       ├── main.py            # FastAPI application entry point
│       ├── routers/           # API route handlers
│       │   ├── health.py      # Health checks and monitoring
│       │   ├── auth.py        # Authentication endpoints
│       │   ├── study_plans.py # Study plan management
│       │   ├── practice.py    # Practice session API
│       │   ├── mastery.py     # Mastery tracking
│       │   └── notes.py       # Notes and flashcards
│       ├── core/              # Business logic modules
│       │   ├── planner.py     # Study plan generation
│       │   ├── practice.py    # Practice engine + FSRS
│       │   ├── mastery.py     # Bayesian mastery tracking
│       │   └── calendar.py    # iCal export functionality
│       ├── models/            # Pydantic request/response models
│       │   ├── study_plans.py # Study plan schemas
│       │   ├── practice.py    # Practice session schemas
│       │   └── notes.py       # Notes and flashcard schemas
│       ├── middleware/        # FastAPI middleware
│       │   ├── auth.py        # JWT authentication
│       │   └── logging.py     # Request/response logging
│       └── dependencies.py   # Shared FastAPI dependencies
├── packages/
│   └── database/              # Shared database layer
│       ├── models.py         # SQLAlchemy ORM models
│       └── connection.py     # Database connection management
├── data/
│   ├── blueprints/           # Exam blueprint definitions
│   │   ├── dp-700.yaml       # Microsoft DP-700 blueprint
│   │   └── databricks-dea.yaml # Databricks DEA blueprint
│   └── templates/            # Question templates
│       ├── scenario_mcq.py   # Multi-choice scenarios
│       ├── code_output.py    # Code execution questions
│       └── troubleshoot.py   # Problem-solving scenarios
├── scripts/
│   ├── setup_database.py    # Database initialization
│   ├── seed_blueprints.py   # Blueprint data loading
│   └── seed_sample_data.py  # Development sample data
├── migrations/               # Alembic database migrations
├── docs/                    # Comprehensive documentation
│   └── ARCHITECTURE_COMPONENTS.md # Detailed component docs
└── tests/                   # Test suites (unit + integration)
```

## 🗄️ **Database Schema**

### **Core Tables (8 Optimized Tables)**
```sql
-- User Management
users                  -- Supabase-integrated user accounts
study_plans           -- User study plans with timelines
study_sessions        -- Individual practice sessions

-- Content & Assessment  
exam_blueprints       -- Official exam structure definitions
objectives           -- Hierarchical learning objectives
practice_items       -- Questions with metadata and solutions

-- Learning & Progress
attempts             -- User responses with FSRS scheduling
mastery_records      -- Bayesian mastery probability per objective
notes               -- User notes with vector embeddings + flashcards
```

### **Key Relationships**
- Users → Study Plans (1:N) → Sessions (1:N)
- Blueprints → Objectives (1:N) → Practice Items (1:N)
- Users + Items → Attempts (N:N) → Mastery Updates
- Notes → Vector Search + Flashcard Generation

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.12+
- Node.js 18+ (for frontend)
- Supabase account
- Redis (optional, for caching)

### **1. Environment Setup**
```bash
# Clone repository
git clone https://github.com/your-org/certcoach.git
cd certcoach

# Install Python dependencies
uv sync --dev

# Create environment file
cp .env.example .env
# Edit .env with your Supabase credentials
```

### **2. Database Setup**
```bash
# Initialize database schema
python scripts/setup_database.py

# Load exam blueprints
python scripts/seed_blueprints.py

# (Optional) Load sample data for development
python scripts/seed_sample_data.py
```

### **3. Start Development Server**
```bash
# Start FastAPI backend
python -m uvicorn services.api.main:app --reload

# API documentation available at:
# http://localhost:8000/docs
```

### **4. Frontend Setup (Coming Soon)**
```bash
cd apps/web
npm install
npm run dev
# Frontend available at http://localhost:3000
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Database & Authentication
DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
SUPABASE_URL=https://[project].supabase.co
SUPABASE_ANON_KEY=[anon-key]
SUPABASE_SERVICE_ROLE_KEY=[service-key]

# AI & Content Generation
OPENAI_API_KEY=[your-openai-key]
DEFAULT_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Performance & Caching
REDIS_URL=redis://localhost:6379/0
DB_POOL_SIZE=5
SLOW_QUERY_THRESHOLD=1.0

# Study Planning Defaults
DEFAULT_SESSION_DURATION_MINUTES=45
DEFAULT_DAILY_STUDY_HOURS=1.0
MASTERY_PROBABILITY_THRESHOLD=0.8
```

## 📚 **API Documentation**

### **Authentication**
```bash
POST /api/v1/auth/register    # User registration
POST /api/v1/auth/login       # User authentication
GET  /api/v1/auth/profile     # Get user profile
```

### **Study Planning**
```bash
POST /api/v1/study-plans      # Create study plan
GET  /api/v1/study-plans      # List user's plans
GET  /api/v1/study-plans/{id} # Get specific plan
PUT  /api/v1/study-plans/{id} # Update plan
GET  /api/v1/study-plans/{id}/calendar # Export iCal
```

### **Practice Sessions**
```bash
POST /api/v1/practice/sessions # Generate practice session
POST /api/v1/practice/attempts # Submit answer attempt
GET  /api/v1/practice/review-queue # Get items due for review
```

### **Mastery & Analytics**
```bash
GET /api/v1/mastery/{user_id}       # Overall mastery overview
GET /api/v1/mastery/objectives/{id} # Per-objective mastery
GET /api/v1/mastery/gaps           # Gap analysis report
```

### **Notes & Flashcards**
```bash
POST /api/v1/notes                # Create note
GET  /api/v1/notes/search         # Semantic search
POST /api/v1/notes/{id}/flashcards # Generate flashcards
GET  /api/v1/notes/flashcards/due  # Get due flashcards
```

## 🧪 **Testing**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov=packages --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests  
pytest tests/api/           # API endpoint tests
```

## 🚀 **Deployment**

### **Development**
```bash
# Local development with hot reload
python -m uvicorn services.api.main:app --reload --port 8000
```

### **Production**
```bash
# Using Gunicorn with uvicorn workers
gunicorn services.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### **Docker**
```bash
# Build and run with Docker
docker build -t certcoach-api .
docker run -p 8000:8000 --env-file .env certcoach-api
```

## � **Documentation**

### **Component Documentation**
- **[Architecture Components](docs/ARCHITECTURE_COMPONENTS.md)** - Detailed documentation of each component, its purpose, and how it works
- **[API Reference](http://localhost:8000/docs)** - Interactive OpenAPI documentation (when server is running)
- **[Database Schema](docs/DATABASE_SCHEMA.md)** - Complete database schema documentation
- **[Development Guide](docs/DEVELOPMENT.md)** - Development setup and contribution guidelines

### **Architecture Overview**
The simplified architecture consolidates all backend functionality into a single FastAPI service with clear separation of concerns:

- **Routers**: Handle HTTP requests and responses
- **Core**: Business logic and algorithms (FSRS, Bayesian mastery, planning)
- **Models**: Type-safe Pydantic schemas for API contracts
- **Database**: SQLAlchemy ORM models and connection management
- **Middleware**: Cross-cutting concerns (auth, logging, CORS)

## 🤝 **Contributing**

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

### **Development Guidelines**
- Follow **PEP 8** style guide for Python
- Use **type hints** throughout
- Write **comprehensive tests** for new features
- Update **documentation** for API changes
- Run **pre-commit hooks** before submitting

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## � **Acknowledgments**

- **FSRS Algorithm**: Inspired by the Free Spaced Repetition Scheduler
- **Supabase**: For providing excellent backend-as-a-service platform
- **FastAPI**: For the high-performance async Python framework
- **Exam Providers**: Microsoft, Databricks for blueprint specifications

---

**Built with ❤️ for certification exam success**
