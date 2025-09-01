# CertCoach Development Roadmap & Backend Requirements

## ✅ Phase 1: Repository Setup (COMPLETED)
- [x] Monorepo structure with Turborepo
- [x] Database models and schema design
- [x] Core service architecture
- [x] Blueprint definitions (DP-700, DBX-DEA)
- [x] Development environment setup

## 🔄 Phase 2: Core Backend Infrastructure (IN PROGRESS)

### Database & Vector Store Setup
```bash
# Required services to set up:
1. PostgreSQL with pgvector extension
2. Supabase integration for auth + real-time
3. Redis for caching and sessions
4. Embedding service for semantic search
```

#### Database Schema Implementation
- **Primary Tables**: ✅ Designed (11 core tables)
  - `exam_blueprints` - Exam structure definitions
  - `objectives` - Learning objectives with weights
  - `users` - User accounts (Supabase auth integration)
  - `study_plans` - User study plans with timeline
  - `study_sessions` - Individual practice sessions
  - `items` - Practice questions with metadata
  - `attempts` - User question attempts
  - `mastery_records` - Bayesian mastery tracking
  - `notes` - User notes with vector embeddings
  - `audit_logs` - Compliance and security
  - `content_sources` - Documentation provenance

- **Vector Search Capabilities**:
  - Notes with semantic search (384-dim embeddings)
  - Content similarity detection for compliance
  - Contextual question recommendations

#### Supabase Integration Strategy
```typescript
// Supabase provides:
1. Authentication (OAuth + email)
2. Real-time subscriptions
3. Row-level security (RLS)
4. Edge functions for serverless logic
5. Storage for media assets

// Our PostgreSQL provides:
1. Complex relational data
2. Vector search with pgvector
3. Advanced analytics
4. ACID transactions
5. Custom business logic
```

### Authentication & Authorization
- **Supabase Auth** for user management
- **JWT tokens** for API authentication  
- **Row-level security** for data isolation
- **Role-based permissions** (student, instructor, admin)
- **OAuth providers**: GitHub, Microsoft, Google

### Content Management & Compliance
- **Source verification** system for documentation links
- **Similarity detection** to prevent exam dumps
- **Human review queue** for content quality
- **License compliance** tracking
- **Automated content quarantine**

## 🎯 Phase 3: Core Services Implementation

### 1. Study Planner Service (`/api/v1/planner`)
```python
# Key endpoints:
POST /plans                    # Create new study plan
GET  /plans/{id}              # Get plan details
PUT  /plans/{id}/schedule     # Update schedule
GET  /plans/{id}/sessions     # Get upcoming sessions
POST /plans/{id}/reschedule   # Handle missed sessions

# Core algorithms:
- Blueprint-weighted session planning
- Automatic rescheduling on slips
- Calendar integration (iCal export)
- Adaptive timeline adjustments
```

### 2. Practice Engine Service (`/api/v1/practice`)
```python
# Key endpoints:
GET  /sessions/{plan_id}      # Generate practice session
POST /sessions/{id}/submit    # Submit session results
GET  /items/review           # Get due review items
POST /items/{id}/attempt     # Submit item attempt

# Core features:
- 2-3 reviews + 8-12 focus items per session
- Difficulty and novelty constraints
- Question templates with rationales
- Official documentation citations
```

### 3. Mastery & SRS Service (`/api/v1/mastery`)
```python
# Key endpoints:
GET  /mastery/{user_id}       # Get mastery overview
GET  /objectives/{id}/mastery # Per-objective mastery
POST /attempts                # Update mastery from attempts
GET  /review/due             # Get items due for review

# Core algorithms:
- Bayesian mastery probability tracking
- FSRS spaced repetition scheduling
- Learning velocity calculations
- Confidence interval tracking
```

### 4. Item Factory Service (`/api/v1/items`)
```python
# Key endpoints:
POST /generate               # Generate new items
GET  /templates              # Get question templates
POST /review                 # Human review workflow
GET  /quality-metrics        # Item quality analytics

# AI-powered features:
- LLM-based question generation
- Automatic quality scoring
- Content similarity detection
- Multi-template support (T1, T2, T3)
```

## 🗂 Phase 4: Vector Database & Search

### Embedding Strategy
```python
# Vector embeddings for:
1. User notes (semantic search)
2. Question content (similarity detection)
3. Documentation anchors (contextual links)
4. Learning objective relationships

# Model selection:
- all-MiniLM-L6-v2 (384 dimensions, fast)
- OpenAI text-embedding-ada-002 (1536 dimensions, high quality)
- Custom domain-specific fine-tuned model
```

### Search Capabilities
- **Semantic note search** across user's study materials
- **Question recommendation** based on content similarity
- **Documentation lookup** for contextual explanations
- **Duplicate detection** for content compliance

## 🔧 Development Environment Setup

### 1. Database Setup
```bash
# Start PostgreSQL with pgvector
docker run -d \
  --name certcoach-postgres \
  -e POSTGRES_DB=certcoach \
  -e POSTGRES_USER=certcoach \
  -e POSTGRES_PASSWORD=certcoach_dev \
  -p 5432:5432 \
  ankane/pgvector

# Install pgvector extension
docker exec certcoach-postgres psql -U certcoach -d certcoach -c "CREATE EXTENSION vector;"
```

### 2. Supabase Project Setup
```bash
# Create Supabase project at https://supabase.com/dashboard
# Configure environment variables:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key

# Set up RLS policies for data isolation
# Configure OAuth providers (GitHub, Microsoft)
```

### 3. Redis Setup
```bash
# Start Redis for caching
docker run -d \
  --name certcoach-redis \
  -p 6379:6379 \
  redis:7-alpine redis-server --appendonly yes
```

### 4. Environment Configuration
```bash
# Copy and configure environment
cp .env.example .env

# Key variables to set:
DATABASE_URL=postgresql://certcoach:certcoach_dev@localhost:5432/certcoach
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-openai-key
```

## 🚀 Next Immediate Steps

### Week 1: Database Foundation
1. **Set up PostgreSQL with pgvector**
   ```bash
   docker-compose -f infra/docker/docker-compose.dev.yml up -d postgres
   ```

2. **Run initial migrations**
   ```bash
   cd migrations
   alembic upgrade head
   ```

3. **Seed blueprint data**
   ```bash
   python scripts/seed_blueprints.py
   ```

### Week 2: Authentication Service
1. **Set up Supabase project** and configure OAuth
2. **Implement JWT middleware** in API gateway
3. **Create user registration/login** endpoints
4. **Test authentication flow** with web app

### Week 3: Study Planner MVP
1. **Implement blueprint parsing** from YAML files
2. **Create study plan generation** algorithm
3. **Build session scheduling** logic
4. **Add calendar export** functionality

### Week 4: Practice Engine MVP
1. **Implement question templates** (T1, T2, T3)
2. **Build session assembly** algorithm
3. **Create attempt tracking** system
4. **Add basic mastery updates**

## 📊 Success Metrics

### Technical KPIs
- **API Response Time**: < 200ms p95
- **Database Query Time**: < 50ms average
- **Vector Search Speed**: < 100ms for note search
- **Authentication Success Rate**: > 99.9%

### User Experience KPIs
- **Study Plan Adherence**: > 70% of scheduled sessions
- **Question Quality Score**: > 4.0/5.0 average rating
- **Mastery Improvement Rate**: Measurable progress week-over-week
- **Content Compliance**: 0 copyright violations

Would you like me to implement any specific component next, such as:
1. Database migrations and seeding
2. Supabase integration setup
3. Authentication service implementation
4. Blueprint loading system
