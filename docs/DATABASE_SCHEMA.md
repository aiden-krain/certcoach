# 🗄️ **Database Schema Documentation**

This document provides comprehensive documentation for the CertCoach database schema, including table structures, relationships, and design decisions.

## 📋 **Schema Overview**

CertCoach uses a simplified 8-table schema optimized for the core learning workflows:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  User Management │    │ Content & Exam  │    │ Learning Progress│
│                 │    │   Structure     │    │                 │
│  • users        │    │ • exam_blueprints│    │ • attempts      │
│  • study_plans  │    │ • objectives    │    │ • mastery_records│
│  • study_sessions│   │ • practice_items│    │ • notes         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🔐 **User Management Tables**

### **`users`** - Supabase-Integrated User Accounts
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    preferences JSONB DEFAULT '{}',
    
    -- Supabase Auth integration
    auth_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid() = auth_id);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = auth_id);
```

**Purpose**: Central user profile management with Supabase Auth integration
**Key Features**:
- Timezone support for scheduling
- JSON preferences for UI settings
- RLS for data isolation
- Audit timestamps

### **`study_plans`** - User Study Plans with Timelines
```sql
CREATE TABLE study_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exam_blueprint_id UUID NOT NULL REFERENCES exam_blueprints(id),
    name VARCHAR(255) NOT NULL,
    exam_date DATE,
    daily_study_hours DECIMAL(3,1) DEFAULT 1.0,
    session_duration_minutes INTEGER DEFAULT 45,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'archived')),
    settings JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT valid_study_hours CHECK (daily_study_hours > 0 AND daily_study_hours <= 12),
    CONSTRAINT valid_session_duration CHECK (session_duration_minutes >= 15 AND session_duration_minutes <= 180)
);

-- Indexes
CREATE INDEX idx_study_plans_user_id ON study_plans(user_id);
CREATE INDEX idx_study_plans_status ON study_plans(status);
CREATE INDEX idx_study_plans_exam_date ON study_plans(exam_date);

-- RLS
ALTER TABLE study_plans ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own study plans" ON study_plans FOR ALL USING (user_id IN (
    SELECT id FROM users WHERE auth_id = auth.uid()
));
```

**Purpose**: Study plan configuration and timeline management
**Key Features**:
- Flexible scheduling parameters
- Progress tracking integration
- Status lifecycle management
- JSON settings for customization

### **`study_sessions`** - Individual Practice Sessions
```sql
CREATE TABLE study_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_plan_id UUID NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    session_type VARCHAR(20) DEFAULT 'practice' CHECK (session_type IN ('practice', 'review', 'mock_exam')),
    target_objectives UUID[] DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    results JSONB,
    
    -- Performance tracking
    items_attempted INTEGER DEFAULT 0,
    items_correct INTEGER DEFAULT 0,
    avg_confidence DECIMAL(3,2),
    session_rating INTEGER CHECK (session_rating >= 1 AND session_rating <= 5),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_study_sessions_plan_id ON study_sessions(study_plan_id);
CREATE INDEX idx_study_sessions_scheduled ON study_sessions(scheduled_at);
CREATE INDEX idx_study_sessions_type ON study_sessions(session_type);
CREATE INDEX idx_study_sessions_status ON study_sessions(started_at, completed_at);

-- RLS (inherited from study_plans)
ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own sessions" ON study_sessions FOR ALL USING (study_plan_id IN (
    SELECT id FROM study_plans WHERE user_id IN (
        SELECT id FROM users WHERE auth_id = auth.uid()
    )
));
```

**Purpose**: Individual session tracking and performance analysis
**Key Features**:
- Session lifecycle tracking
- Performance metrics capture
- Objective targeting
- User feedback collection

---

## 📚 **Content & Assessment Tables**

### **`exam_blueprints`** - Official Exam Structure Definitions
```sql
CREATE TABLE exam_blueprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    provider VARCHAR(100) NOT NULL,
    description TEXT,
    total_questions INTEGER,
    passing_score INTEGER,
    duration_minutes INTEGER,
    domains JSONB NOT NULL, -- Hierarchical domain structure
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    
    -- Metadata
    version VARCHAR(20) DEFAULT '1.0',
    effective_date DATE,
    retirement_date DATE
);

-- Indexes
CREATE INDEX idx_exam_blueprints_code ON exam_blueprints(code);
CREATE INDEX idx_exam_blueprints_provider ON exam_blueprints(provider);
CREATE INDEX idx_exam_blueprints_active ON exam_blueprints(is_active);

-- Example domains structure:
-- {
--   "domains": [
--     {
--       "id": "domain_1",
--       "name": "Implement and manage a solution",
--       "weight": 35,
--       "objectives": [
--         {
--           "id": "1.1",
--           "description": "Implement lakehouse architecture",
--           "weight": 10,
--           "sub_objectives": [...]
--         }
--       ]
--     }
--   ]
-- }
```

**Purpose**: Official exam structure and weighting definitions
**Key Features**:
- Hierarchical domain/objective structure
- Weight-based prioritization
- Version and lifecycle management
- Provider-agnostic design

### **`objectives`** - Hierarchical Learning Objectives
```sql
CREATE TABLE objectives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_blueprint_id UUID NOT NULL REFERENCES exam_blueprints(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL, -- e.g., "1.1.1"
    title VARCHAR(500) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES objectives(id),
    weight DECIMAL(5,2) NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1, -- 1=domain, 2=objective, 3=sub-objective
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_weight CHECK (weight >= 0 AND weight <= 100),
    CONSTRAINT valid_level CHECK (level >= 1 AND level <= 5),
    UNIQUE (exam_blueprint_id, code)
);

-- Indexes
CREATE INDEX idx_objectives_blueprint_id ON objectives(exam_blueprint_id);
CREATE INDEX idx_objectives_parent_id ON objectives(parent_id);
CREATE INDEX idx_objectives_code ON objectives(code);
CREATE INDEX idx_objectives_level ON objectives(level);

-- Hierarchical query helper
CREATE INDEX idx_objectives_path ON objectives USING GIN (
    string_to_array(code, '.')
);
```

**Purpose**: Structured learning objective hierarchy for targeted practice
**Key Features**:
- Hierarchical parent-child relationships
- Weight-based importance
- Flexible depth levels
- Efficient hierarchical queries

### **`practice_items`** - Questions with Metadata and Solutions
```sql
CREATE TABLE practice_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    objective_id UUID NOT NULL REFERENCES objectives(id),
    item_type VARCHAR(50) NOT NULL CHECK (item_type IN (
        'multiple_choice', 'multiple_select', 'drag_drop', 'fill_blank', 
        'scenario', 'code_analysis', 'troubleshoot'
    )),
    difficulty_level INTEGER NOT NULL CHECK (difficulty_level >= 1 AND difficulty_level <= 5),
    
    -- Content
    question_text TEXT NOT NULL,
    options JSONB, -- For multiple choice/select
    correct_answer JSONB NOT NULL,
    explanation TEXT,
    hints JSONB DEFAULT '[]',
    
    -- Metadata
    estimated_duration_seconds INTEGER DEFAULT 120,
    tags VARCHAR(100)[] DEFAULT '{}',
    source VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Quality metrics
    usage_count INTEGER DEFAULT 0,
    avg_score DECIMAL(3,2),
    discrimination_index DECIMAL(3,2),
    is_validated BOOLEAN DEFAULT false,
    
    -- Vector search (pgvector extension)
    embedding vector(1536) -- OpenAI ada-002 dimensions
);

-- Indexes
CREATE INDEX idx_practice_items_objective ON practice_items(objective_id);
CREATE INDEX idx_practice_items_difficulty ON practice_items(difficulty_level);
CREATE INDEX idx_practice_items_type ON practice_items(item_type);
CREATE INDEX idx_practice_items_validated ON practice_items(is_validated);
CREATE INDEX idx_practice_items_tags ON practice_items USING GIN (tags);

-- Vector similarity search
CREATE INDEX idx_practice_items_embedding ON practice_items 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

**Purpose**: Question bank with rich metadata and quality tracking
**Key Features**:
- Multiple question types support
- Difficulty and quality metrics
- Vector embeddings for semantic search
- Statistical tracking for item analysis

---

## 📈 **Learning Progress Tables**

### **`attempts`** - User Responses with FSRS Scheduling
```sql
CREATE TABLE attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    practice_item_id UUID NOT NULL REFERENCES practice_items(id),
    study_session_id UUID REFERENCES study_sessions(id),
    
    -- Response data
    submitted_answer JSONB NOT NULL,
    is_correct BOOLEAN NOT NULL,
    confidence_level INTEGER CHECK (confidence_level >= 1 AND confidence_level <= 5),
    time_spent_seconds INTEGER,
    hint_used BOOLEAN DEFAULT false,
    
    -- FSRS scheduling data
    fsrs_state JSONB NOT NULL DEFAULT '{
        "stability": 1.0,
        "difficulty": 5.0,
        "elapsed_days": 0,
        "scheduled_days": 1,
        "reps": 0,
        "lapses": 0,
        "last_review": null
    }',
    next_review_at TIMESTAMPTZ,
    
    attempted_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_attempts_user_id ON attempts(user_id);
CREATE INDEX idx_attempts_item_id ON attempts(practice_item_id);
CREATE INDEX idx_attempts_session_id ON attempts(study_session_id);
CREATE INDEX idx_attempts_next_review ON attempts(next_review_at) WHERE next_review_at IS NOT NULL;
CREATE INDEX idx_attempts_user_item ON attempts(user_id, practice_item_id);

-- RLS
ALTER TABLE attempts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own attempts" ON attempts FOR ALL USING (user_id IN (
    SELECT id FROM users WHERE auth_id = auth.uid()
));
```

**Purpose**: User response tracking with spaced repetition scheduling
**Key Features**:
- Complete FSRS state management
- Performance and confidence tracking
- Review queue optimization
- Session association

### **`mastery_records`** - Bayesian Mastery Probability per Objective
```sql
CREATE TABLE mastery_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    objective_id UUID NOT NULL REFERENCES objectives(id),
    
    -- Bayesian mastery tracking
    mastery_probability DECIMAL(5,4) NOT NULL DEFAULT 0.5000 CHECK (
        mastery_probability >= 0 AND mastery_probability <= 1
    ),
    confidence_interval_lower DECIMAL(5,4) NOT NULL DEFAULT 0.0000,
    confidence_interval_upper DECIMAL(5,4) NOT NULL DEFAULT 1.0000,
    
    -- Evidence tracking
    total_attempts INTEGER NOT NULL DEFAULT 0,
    correct_attempts INTEGER NOT NULL DEFAULT 0,
    recent_performance DECIMAL(3,2), -- Last 10 attempts
    
    -- Time-based factors
    last_practiced_at TIMESTAMPTZ,
    knowledge_decay_factor DECIMAL(3,2) DEFAULT 1.00,
    learning_velocity DECIMAL(3,2), -- Improvement rate
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    UNIQUE (user_id, objective_id),
    CONSTRAINT valid_attempts CHECK (correct_attempts <= total_attempts)
);

-- Indexes
CREATE INDEX idx_mastery_records_user_id ON mastery_records(user_id);
CREATE INDEX idx_mastery_records_objective_id ON mastery_records(objective_id);
CREATE INDEX idx_mastery_records_probability ON mastery_records(mastery_probability);
CREATE INDEX idx_mastery_records_last_practiced ON mastery_records(last_practiced_at);

-- RLS
ALTER TABLE mastery_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own mastery" ON mastery_records FOR ALL USING (user_id IN (
    SELECT id FROM users WHERE auth_id = auth.uid()
));
```

**Purpose**: Bayesian mastery probability tracking with confidence intervals
**Key Features**:
- Probabilistic mastery assessment
- Time-decay modeling
- Learning velocity tracking
- Confidence interval estimation

### **`notes`** - User Notes with Vector Embeddings + Flashcards
```sql
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'markdown' CHECK (content_type IN ('markdown', 'html', 'plain')),
    
    -- Categorization
    objectives UUID[] DEFAULT '{}', -- Related objectives
    tags VARCHAR(100)[] DEFAULT '{}',
    
    -- Vector search
    embedding vector(1536), -- OpenAI ada-002 dimensions
    
    -- Flashcard generation
    flashcards_generated BOOLEAN DEFAULT false,
    flashcard_count INTEGER DEFAULT 0,
    auto_generate_flashcards BOOLEAN DEFAULT true,
    
    -- Metadata
    word_count INTEGER,
    reading_time_minutes INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', title), 'A') ||
        setweight(to_tsvector('english', content), 'B')
    ) STORED
);

-- Indexes
CREATE INDEX idx_notes_user_id ON notes(user_id);
CREATE INDEX idx_notes_objectives ON notes USING GIN (objectives);
CREATE INDEX idx_notes_tags ON notes USING GIN (tags);
CREATE INDEX idx_notes_search ON notes USING GIN (search_vector);

-- Vector similarity search
CREATE INDEX idx_notes_embedding ON notes 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- RLS
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own notes" ON notes FOR ALL USING (user_id IN (
    SELECT id FROM users WHERE auth_id = auth.uid()
));

-- Flashcards as separate table (optional, can be embedded in notes)
CREATE TABLE flashcards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    card_type VARCHAR(20) DEFAULT 'basic' CHECK (card_type IN ('basic', 'cloze', 'image')),
    
    -- FSRS integration
    fsrs_state JSONB NOT NULL DEFAULT '{
        "stability": 1.0,
        "difficulty": 5.0,
        "elapsed_days": 0,
        "scheduled_days": 1,
        "reps": 0,
        "lapses": 0,
        "last_review": null
    }',
    next_review_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Flashcard indexes
CREATE INDEX idx_flashcards_note_id ON flashcards(note_id);
CREATE INDEX idx_flashcards_user_id ON flashcards(user_id);
CREATE INDEX idx_flashcards_next_review ON flashcards(next_review_at) WHERE next_review_at IS NOT NULL;
```

**Purpose**: Note management with automatic flashcard generation and vector search
**Key Features**:
- Vector semantic search
- Automatic flashcard extraction
- SRS integration for flashcards
- Full-text search capabilities

---

## 🔗 **Key Relationships & Constraints**

### **Primary Relationships**
```sql
-- User flow
users (1) → (N) study_plans (1) → (N) study_sessions
users (1) → (N) attempts
users (1) → (N) mastery_records  
users (1) → (N) notes

-- Content hierarchy
exam_blueprints (1) → (N) objectives (1) → (N) practice_items
objectives (1) → (N) attempts (via practice_items)
objectives (1) → (N) mastery_records

-- Session tracking
study_sessions (1) → (N) attempts
notes (1) → (N) flashcards
```

### **Data Integrity Features**
- **Cascading Deletes**: User deletion removes all associated data
- **Check Constraints**: Validate data ranges and enums
- **Unique Constraints**: Prevent duplicate records
- **Foreign Key Constraints**: Maintain referential integrity

### **Performance Optimizations**
- **Strategic Indexing**: Query-optimized indexes for common patterns
- **Vector Indexes**: Efficient similarity search with ivfflat
- **Partial Indexes**: Filtered indexes for sparse data
- **GIN Indexes**: Array and JSON search optimization

---

## 🔧 **Database Configuration**

### **Required Extensions**
```sql
-- Vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- JSON operations
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### **Row Level Security (RLS)**
All user-related tables implement RLS policies to ensure data isolation:
- Users can only access their own data
- Policies automatically filter based on authenticated user
- Service role bypasses RLS for administrative operations

### **Audit & Monitoring**
- All tables include `created_at` and `updated_at` timestamps
- Soft delete patterns where appropriate
- Performance tracking fields for optimization
- Usage statistics for content quality assessment

---

This schema design provides a solid foundation for the CertCoach platform while maintaining simplicity, performance, and data integrity. The 8-table structure efficiently supports all core features while allowing for future expansion.
