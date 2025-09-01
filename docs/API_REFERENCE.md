# 📚 **API Reference Documentation**

Complete API documentation for the CertCoach platform. All endpoints use JSON for request/response bodies and follow RESTful conventions.

## 🔗 **Base Information**

- **Base URL**: `http://localhost:8000` (development) / `https://api.certcoach.com` (production)
- **API Version**: `v1`
- **Authentication**: Bearer JWT tokens
- **Content-Type**: `application/json`
- **Rate Limiting**: 1000 requests/hour per user

---

## 🔐 **Authentication**

All endpoints except health checks and registration require authentication via JWT tokens.

### **Headers**
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### **Error Responses**
```json
{
    "detail": "Not authenticated",
    "status_code": 401
}
```

---

## 🏥 **Health & Monitoring**

### **GET** `/health` - Basic Health Check
Check if the API is responsive.

**Response**: `200 OK`
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0"
}
```

### **GET** `/health/deep` - Comprehensive Health Check
Check all system dependencies including database and external services.

**Response**: `200 OK`
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "components": {
        "database": {
            "status": "healthy",
            "response_time_ms": 45,
            "connection_pool": {
                "active": 2,
                "idle": 3,
                "total": 5
            }
        },
        "redis": {
            "status": "healthy",
            "response_time_ms": 12
        },
        "openai": {
            "status": "healthy",
            "response_time_ms": 234
        }
    },
    "performance": {
        "memory_usage_mb": 156,
        "cpu_percent": 23.5,
        "uptime_seconds": 3600
    }
}
```

### **GET** `/metrics` - Prometheus Metrics
Prometheus-compatible metrics for monitoring.

**Response**: `200 OK` (text/plain)
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/health",status="200"} 1542

# HELP response_time_seconds Response time in seconds
# TYPE response_time_seconds histogram
response_time_seconds_bucket{endpoint="/api/v1/study-plans",le="0.1"} 98
response_time_seconds_bucket{endpoint="/api/v1/study-plans",le="0.5"} 127
```

---

## 🔐 **Authentication Endpoints**

### **POST** `/api/v1/auth/register` - User Registration
Create a new user account.

**Request Body**:
```json
{
    "email": "user@example.com",
    "password": "securePassword123",
    "full_name": "John Doe",
    "timezone": "America/New_York"
}
```

**Response**: `201 Created`
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "timezone": "America/New_York",
    "created_at": "2024-01-15T10:30:00Z",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

**Errors**:
- `400` - Invalid email format or weak password
- `409` - Email already registered

### **POST** `/api/v1/auth/login` - User Login
Authenticate user and receive access token.

**Request Body**:
```json
{
    "email": "user@example.com",
    "password": "securePassword123"
}
```

**Response**: `200 OK`
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "user@example.com",
        "full_name": "John Doe",
        "timezone": "America/New_York"
    }
}
```

**Errors**:
- `401` - Invalid credentials
- `429` - Too many failed login attempts

### **POST** `/api/v1/auth/logout` - User Logout
Invalidate current access token.

**Response**: `200 OK`
```json
{
    "message": "Successfully logged out"
}
```

### **GET** `/api/v1/auth/profile` - Get User Profile
Retrieve current user's profile information.

**Response**: `200 OK`
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "timezone": "America/New_York",
    "avatar_url": "https://example.com/avatar.jpg",
    "created_at": "2024-01-15T10:30:00Z",
    "last_login_at": "2024-01-20T14:22:00Z",
    "preferences": {
        "theme": "dark",
        "notifications": true,
        "study_reminders": true
    }
}
```

### **PUT** `/api/v1/auth/profile` - Update User Profile
Update current user's profile information.

**Request Body**:
```json
{
    "full_name": "John Smith",
    "timezone": "Europe/London",
    "preferences": {
        "theme": "light",
        "notifications": false
    }
}
```

**Response**: `200 OK` (same as GET profile)

---

## 📅 **Study Plans**

### **GET** `/api/v1/study-plans` - List Study Plans
Get all study plans for the current user.

**Query Parameters**:
- `limit` (int, default=10): Maximum number of results
- `offset` (int, default=0): Number of results to skip
- `status` (string, optional): Filter by status ('active', 'paused', 'completed', 'archived')

**Response**: `200 OK`
```json
{
    "items": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Microsoft DP-700 Preparation",
            "exam_blueprint": {
                "id": "dp-700-blueprint-id",
                "name": "Microsoft Fabric Analytics Engineer",
                "code": "DP-700"
            },
            "exam_date": "2024-06-01",
            "daily_study_hours": 2.0,
            "session_duration_minutes": 45,
            "status": "active",
            "progress": {
                "total_sessions": 48,
                "completed_sessions": 12,
                "completion_percentage": 25.0,
                "estimated_completion_date": "2024-05-25"
            },
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-20T14:22:00Z"
        }
    ],
    "total": 1,
    "limit": 10,
    "offset": 0
}
```

### **POST** `/api/v1/study-plans` - Create Study Plan
Create a new study plan.

**Request Body**:
```json
{
    "name": "Microsoft DP-700 Preparation",
    "exam_blueprint_id": "dp-700-blueprint-id",
    "exam_date": "2024-06-01",
    "daily_study_hours": 2.0,
    "session_duration_minutes": 45,
    "settings": {
        "auto_reschedule": true,
        "weekend_sessions": false,
        "difficulty_adaptation": true
    }
}
```

**Response**: `201 Created`
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Microsoft DP-700 Preparation",
    "exam_blueprint": {
        "id": "dp-700-blueprint-id",
        "name": "Microsoft Fabric Analytics Engineer",
        "code": "DP-700"
    },
    "exam_date": "2024-06-01",
    "daily_study_hours": 2.0,
    "session_duration_minutes": 45,
    "status": "active",
    "settings": {
        "auto_reschedule": true,
        "weekend_sessions": false,
        "difficulty_adaptation": true
    },
    "schedule": {
        "total_sessions": 48,
        "sessions_per_week": 7,
        "estimated_completion_date": "2024-05-25"
    },
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors**:
- `400` - Invalid blueprint ID or past exam date
- `422` - Validation errors in request data

### **GET** `/api/v1/study-plans/{plan_id}` - Get Study Plan
Retrieve a specific study plan with detailed information.

**Response**: `200 OK`
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Microsoft DP-700 Preparation",
    "exam_blueprint": {
        "id": "dp-700-blueprint-id",
        "name": "Microsoft Fabric Analytics Engineer",
        "code": "DP-700",
        "domains": [
            {
                "name": "Implement and manage a solution",
                "weight": 35,
                "objectives": [
                    {
                        "id": "1.1",
                        "description": "Implement lakehouse architecture",
                        "weight": 10,
                        "mastery_level": 0.75
                    }
                ]
            }
        ]
    },
    "schedule": {
        "next_session": {
            "scheduled_at": "2024-01-21T09:00:00Z",
            "session_type": "practice",
            "estimated_duration_minutes": 45,
            "target_objectives": ["1.1", "2.3", "3.1"]
        },
        "upcoming_sessions": [
            {
                "scheduled_at": "2024-01-22T09:00:00Z",
                "session_type": "review",
                "target_objectives": ["1.2", "2.1"]
            }
        ]
    },
    "progress": {
        "overall_mastery": 0.45,
        "weak_areas": ["2.4", "3.2"],
        "strong_areas": ["1.1", "1.3"],
        "study_velocity": 1.2,
        "confidence_trend": "improving"
    }
}
```

**Errors**:
- `404` - Study plan not found
- `403` - Access denied to plan

### **PUT** `/api/v1/study-plans/{plan_id}` - Update Study Plan
Update an existing study plan.

**Request Body**:
```json
{
    "name": "Updated Plan Name",
    "exam_date": "2024-06-15",
    "daily_study_hours": 1.5,
    "status": "paused",
    "settings": {
        "auto_reschedule": false
    }
}
```

**Response**: `200 OK` (same structure as GET)

### **DELETE** `/api/v1/study-plans/{plan_id}` - Delete Study Plan
Delete a study plan and all associated sessions.

**Response**: `204 No Content`

### **GET** `/api/v1/study-plans/{plan_id}/calendar` - Export Calendar
Export study plan as iCal calendar.

**Query Parameters**:
- `format` (string, default='ical'): Export format ('ical', 'google', 'outlook')

**Response**: `200 OK` (text/calendar)
```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//CertCoach//Study Plan//EN
BEGIN:VEVENT
UID:session-123@certcoach.com
DTSTART:20240121T090000Z
DTEND:20240121T094500Z
SUMMARY:DP-700 Practice Session
DESCRIPTION:Practice session focusing on lakehouse architecture
LOCATION:Study Location
END:VEVENT
END:VCALENDAR
```

---

## 🎯 **Practice Sessions**

### **POST** `/api/v1/practice/sessions` - Generate Practice Session
Create a new practice session with personalized content.

**Request Body**:
```json
{
    "study_plan_id": "123e4567-e89b-12d3-a456-426614174000",
    "session_type": "practice",
    "duration_minutes": 45,
    "focus_objectives": ["1.1", "2.3"],
    "difficulty_preference": "adaptive"
}
```

**Response**: `201 Created`
```json
{
    "id": "session-456-789",
    "session_type": "practice",
    "estimated_duration_minutes": 45,
    "items": [
        {
            "id": "item-123",
            "type": "multiple_choice",
            "question": "Which of the following best describes a lakehouse architecture?",
            "options": [
                {"id": "a", "text": "A data warehouse built on cloud storage"},
                {"id": "b", "text": "A unified platform combining data lake and warehouse"},
                {"id": "c", "text": "A traditional relational database"},
                {"id": "d", "text": "A NoSQL document store"}
            ],
            "objective_id": "1.1",
            "difficulty_level": 3,
            "estimated_time_seconds": 90,
            "hints": [
                "Consider the key characteristics of modern data platforms",
                "Think about combining structured and unstructured data"
            ]
        }
    ],
    "review_items": [
        {
            "id": "item-456",
            "last_attempted": "2024-01-18T10:00:00Z",
            "due_date": "2024-01-21T09:00:00Z",
            "fsrs_interval": 3.2
        }
    ],
    "session_goals": {
        "target_accuracy": 0.75,
        "focus_areas": ["Lakehouse architecture", "Data integration"],
        "learning_objectives": ["1.1", "2.3"]
    },
    "created_at": "2024-01-21T09:00:00Z"
}
```

**Errors**:
- `400` - Invalid study plan or preferences
- `404` - Study plan not found

### **POST** `/api/v1/practice/attempts` - Submit Answer Attempt
Submit an answer for a practice item.

**Request Body**:
```json
{
    "practice_item_id": "item-123",
    "study_session_id": "session-456-789",
    "submitted_answer": ["b"],
    "confidence_level": 4,
    "time_spent_seconds": 75,
    "hints_used": false
}
```

**Response**: `201 Created`
```json
{
    "id": "attempt-789",
    "is_correct": true,
    "score": 1.0,
    "feedback": {
        "correct_answer": ["b"],
        "explanation": "Correct! A lakehouse architecture combines the best features of data lakes and data warehouses, providing unified storage and processing capabilities for both structured and unstructured data.",
        "learning_points": [
            "Lakehouse supports ACID transactions",
            "Enables both analytics and ML workloads",
            "Provides schema enforcement and evolution"
        ],
        "related_documentation": [
            {
                "title": "Azure Lakehouse Architecture",
                "url": "https://docs.microsoft.com/azure/lakehouse",
                "section": "Architecture Overview"
            }
        ]
    },
    "fsrs_update": {
        "next_review_date": "2024-01-24T09:00:00Z",
        "interval_days": 3.2,
        "stability": 2.1,
        "difficulty": 4.2
    },
    "mastery_impact": {
        "objective_id": "1.1",
        "previous_mastery": 0.72,
        "new_mastery": 0.78,
        "confidence_interval": [0.65, 0.85]
    },
    "created_at": "2024-01-21T09:01:15Z"
}
```

### **GET** `/api/v1/practice/review-queue` - Get Review Queue
Get items due for review based on spaced repetition algorithm.

**Query Parameters**:
- `limit` (int, default=20): Maximum number of items
- `study_plan_id` (UUID, optional): Filter by study plan
- `include_overdue` (bool, default=true): Include overdue items

**Response**: `200 OK`
```json
{
    "items": [
        {
            "id": "item-123",
            "objective_id": "1.1",
            "due_date": "2024-01-21T09:00:00Z",
            "priority": "high",
            "interval_days": 2.5,
            "last_score": 0.8,
            "consecutive_correct": 2,
            "estimated_time_seconds": 90
        }
    ],
    "stats": {
        "total_due": 15,
        "overdue": 3,
        "estimated_time_minutes": 22,
        "by_difficulty": {
            "easy": 5,
            "medium": 8,
            "hard": 2
        }
    }
}
```

### **POST** `/api/v1/practice/mock-exams` - Generate Mock Exam
Create a full-length practice exam.

**Request Body**:
```json
{
    "study_plan_id": "123e4567-e89b-12d3-a456-426614174000",
    "exam_type": "full",
    "difficulty_level": "exam_level",
    "time_limit_minutes": 120
}
```

**Response**: `201 Created`
```json
{
    "id": "mock-exam-789",
    "exam_type": "full",
    "total_questions": 60,
    "time_limit_minutes": 120,
    "sections": [
        {
            "name": "Implement and manage a solution",
            "question_count": 21,
            "weight": 35,
            "items": ["item-1", "item-2", "..."]
        }
    ],
    "instructions": {
        "total_time": "120 minutes",
        "passing_score": "70%",
        "question_types": ["Multiple choice", "Multiple select", "Drag and drop"]
    },
    "started_at": "2024-01-21T10:00:00Z",
    "expires_at": "2024-01-21T12:00:00Z"
}
```

---

## 📊 **Mastery Tracking**

### **GET** `/api/v1/mastery/{user_id}` - Overall Mastery Overview
Get comprehensive mastery overview for a user.

**Response**: `200 OK`
```json
{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "overall_mastery": 0.68,
    "confidence_interval": [0.62, 0.74],
    "by_blueprint": [
        {
            "blueprint_id": "dp-700-blueprint-id",
            "blueprint_name": "Microsoft DP-700",
            "mastery_level": 0.68,
            "total_objectives": 24,
            "mastered_objectives": 16,
            "domains": [
                {
                    "name": "Implement and manage a solution",
                    "mastery_level": 0.75,
                    "objectives": [
                        {
                            "id": "1.1",
                            "description": "Implement lakehouse architecture",
                            "mastery_probability": 0.82,
                            "confidence_interval": [0.75, 0.88],
                            "last_practiced": "2024-01-21T09:00:00Z",
                            "attempts": 15,
                            "success_rate": 0.87
                        }
                    ]
                }
            ]
        }
    ],
    "learning_velocity": 1.3,
    "study_streak_days": 12,
    "total_study_time_hours": 48.5,
    "last_updated": "2024-01-21T09:15:00Z"
}
```

### **GET** `/api/v1/mastery/objectives/{objective_id}` - Objective-Specific Mastery
Get detailed mastery information for a specific learning objective.

**Response**: `200 OK`
```json
{
    "objective_id": "1.1",
    "description": "Implement lakehouse architecture",
    "mastery_probability": 0.82,
    "confidence_interval": [0.75, 0.88],
    "evidence": {
        "total_attempts": 15,
        "correct_attempts": 13,
        "recent_performance": 0.90,
        "difficulty_distribution": {
            "easy": {"attempts": 5, "correct": 5},
            "medium": {"attempts": 7, "correct": 6},
            "hard": {"attempts": 3, "correct": 2}
        }
    },
    "learning_progress": {
        "first_attempt": "2024-01-10T09:00:00Z",
        "last_attempt": "2024-01-21T09:00:00Z",
        "improvement_rate": 0.12,
        "plateau_indicator": false,
        "estimated_mastery_date": "2024-01-25T00:00:00Z"
    },
    "related_objectives": [
        {
            "id": "1.2",
            "description": "Configure data storage",
            "correlation": 0.65
        }
    ],
    "recommendations": [
        "Focus on advanced lakehouse patterns",
        "Practice with real-world scenarios",
        "Review integration with analytics tools"
    ]
}
```

### **GET** `/api/v1/mastery/gaps` - Gap Analysis Report
Identify knowledge gaps and weaknesses.

**Query Parameters**:
- `study_plan_id` (UUID, optional): Filter by study plan
- `threshold` (float, default=0.7): Mastery threshold for gap identification

**Response**: `200 OK`
```json
{
    "analysis_date": "2024-01-21T10:00:00Z",
    "mastery_threshold": 0.7,
    "gaps": [
        {
            "objective_id": "2.4",
            "description": "Implement data governance",
            "current_mastery": 0.45,
            "gap_severity": "high",
            "evidence": {
                "attempts": 8,
                "success_rate": 0.38,
                "common_mistakes": [
                    "Incorrect policy configuration",
                    "Missing compliance controls"
                ]
            },
            "recommendations": [
                "Review governance fundamentals",
                "Practice with compliance scenarios",
                "Study regulatory requirements"
            ],
            "estimated_time_to_mastery": "8-12 hours",
            "priority": 1
        }
    ],
    "strengths": [
        {
            "objective_id": "1.1",
            "description": "Implement lakehouse architecture",
            "mastery_level": 0.82,
            "consistency": 0.91
        }
    ],
    "recommendations": {
        "focus_areas": ["Data governance", "Security implementation"],
        "study_plan_adjustments": [
            "Increase time allocation for domain 2",
            "Add specialized governance scenarios"
        ],
        "next_mock_exam_readiness": false,
        "estimated_exam_readiness_date": "2024-02-15T00:00:00Z"
    }
}
```

### **POST** `/api/v1/mastery/update` - Manual Mastery Update
Manually update mastery scores (for admin or special cases).

**Request Body**:
```json
{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "objective_id": "1.1",
    "mastery_probability": 0.85,
    "reason": "Instructor assessment",
    "evidence": {
        "assessment_type": "practical_exam",
        "score": 0.92,
        "assessor": "instructor@example.com"
    }
}
```

**Response**: `200 OK`
```json
{
    "updated": true,
    "previous_mastery": 0.82,
    "new_mastery": 0.85,
    "updated_at": "2024-01-21T10:30:00Z"
}
```

---

## 📝 **Notes & Flashcards**

### **GET** `/api/v1/notes` - List Notes
Get user's notes with pagination and filtering.

**Query Parameters**:
- `limit` (int, default=20): Maximum number of notes
- `offset` (int, default=0): Number of notes to skip
- `tags` (string[], optional): Filter by tags
- `objective_ids` (UUID[], optional): Filter by learning objectives
- `search` (string, optional): Full-text search query

**Response**: `200 OK`
```json
{
    "items": [
        {
            "id": "note-123",
            "title": "Lakehouse Architecture Patterns",
            "content": "# Lakehouse Architecture\n\nKey patterns for implementing lakehouse...",
            "content_type": "markdown",
            "tags": ["architecture", "patterns", "lakehouse"],
            "objectives": ["1.1", "1.2"],
            "word_count": 450,
            "reading_time_minutes": 3,
            "flashcard_count": 5,
            "created_at": "2024-01-20T14:00:00Z",
            "updated_at": "2024-01-21T09:30:00Z"
        }
    ],
    "total": 15,
    "limit": 20,
    "offset": 0
}
```

### **POST** `/api/v1/notes` - Create Note
Create a new note.

**Request Body**:
```json
{
    "title": "Lakehouse Architecture Patterns",
    "content": "# Lakehouse Architecture\n\nKey patterns for implementing lakehouse architectures include:\n\n## Delta Lake\n- ACID transactions\n- Schema evolution\n- Time travel\n\n## Unity Catalog\n- Centralized governance\n- Fine-grained access control",
    "content_type": "markdown",
    "tags": ["architecture", "patterns", "lakehouse"],
    "objectives": ["1.1", "1.2"],
    "auto_generate_flashcards": true
}
```

**Response**: `201 Created`
```json
{
    "id": "note-123",
    "title": "Lakehouse Architecture Patterns",
    "content": "# Lakehouse Architecture\n\n...",
    "content_type": "markdown",
    "tags": ["architecture", "patterns", "lakehouse"],
    "objectives": ["1.1", "1.2"],
    "word_count": 450,
    "reading_time_minutes": 3,
    "flashcards_generated": true,
    "flashcard_count": 5,
    "created_at": "2024-01-21T10:00:00Z",
    "updated_at": "2024-01-21T10:00:00Z"
}
```

### **GET** `/api/v1/notes/{note_id}` - Get Note
Retrieve a specific note with full content.

**Response**: `200 OK`
```json
{
    "id": "note-123",
    "title": "Lakehouse Architecture Patterns",
    "content": "# Lakehouse Architecture\n\nDetailed content here...",
    "content_type": "markdown",
    "tags": ["architecture", "patterns", "lakehouse"],
    "objectives": ["1.1", "1.2"],
    "flashcards": [
        {
            "id": "flashcard-456",
            "question": "What are the key features of Delta Lake?",
            "answer": "ACID transactions, schema evolution, and time travel capabilities",
            "card_type": "basic",
            "next_review_at": "2024-01-22T09:00:00Z"
        }
    ],
    "related_notes": [
        {
            "id": "note-789",
            "title": "Data Governance Best Practices",
            "similarity_score": 0.75
        }
    ],
    "word_count": 450,
    "reading_time_minutes": 3,
    "created_at": "2024-01-20T14:00:00Z",
    "updated_at": "2024-01-21T09:30:00Z"
}
```

### **PUT** `/api/v1/notes/{note_id}` - Update Note
Update an existing note.

**Request Body**:
```json
{
    "title": "Updated Title",
    "content": "Updated content...",
    "tags": ["updated", "tags"],
    "auto_generate_flashcards": true
}
```

**Response**: `200 OK` (same structure as GET note)

### **DELETE** `/api/v1/notes/{note_id}` - Delete Note
Delete a note and all associated flashcards.

**Response**: `204 No Content`

### **GET** `/api/v1/notes/search` - Semantic Search
Perform semantic search across all notes.

**Query Parameters**:
- `query` (string, required): Search query
- `limit` (int, default=10): Maximum results
- `similarity_threshold` (float, default=0.7): Minimum similarity score

**Response**: `200 OK`
```json
{
    "query": "lakehouse architecture patterns",
    "results": [
        {
            "note_id": "note-123",
            "title": "Lakehouse Architecture Patterns",
            "content_snippet": "Key patterns for implementing lakehouse architectures include Delta Lake...",
            "similarity_score": 0.92,
            "matched_sections": [
                "Lakehouse Architecture",
                "Delta Lake patterns"
            ],
            "tags": ["architecture", "patterns"],
            "created_at": "2024-01-20T14:00:00Z"
        }
    ],
    "total_results": 3,
    "search_time_ms": 45
}
```

### **POST** `/api/v1/notes/{note_id}/flashcards` - Generate Flashcards
Generate flashcards from note content.

**Request Body**:
```json
{
    "card_types": ["basic", "cloze"],
    "max_cards": 10,
    "difficulty_level": "medium",
    "focus_sections": ["Delta Lake", "Unity Catalog"]
}
```

**Response**: `201 Created`
```json
{
    "generated_cards": 5,
    "flashcards": [
        {
            "id": "flashcard-789",
            "question": "What feature of Delta Lake enables tracking changes over time?",
            "answer": "Time travel capabilities",
            "card_type": "basic",
            "source_section": "Delta Lake",
            "difficulty_level": 2,
            "next_review_at": "2024-01-22T09:00:00Z"
        }
    ],
    "skipped_content": [
        "Section too short for flashcard generation",
        "Duplicate concept already covered"
    ]
}
```

### **GET** `/api/v1/notes/flashcards/due` - Get Due Flashcards
Get flashcards due for review.

**Query Parameters**:
- `limit` (int, default=20): Maximum flashcards
- `include_overdue` (bool, default=true): Include overdue cards

**Response**: `200 OK`
```json
{
    "flashcards": [
        {
            "id": "flashcard-456",
            "note_id": "note-123",
            "question": "What are the key features of Delta Lake?",
            "answer": "ACID transactions, schema evolution, and time travel capabilities",
            "card_type": "basic",
            "due_date": "2024-01-21T09:00:00Z",
            "interval_days": 2.5,
            "difficulty": 3,
            "times_reviewed": 4,
            "success_rate": 0.75
        }
    ],
    "stats": {
        "total_due": 12,
        "overdue": 3,
        "estimated_time_minutes": 15,
        "by_difficulty": {
            "easy": 4,
            "medium": 6,
            "hard": 2
        }
    }
}
```

---

## ⚠️ **Error Handling**

### **Standard Error Response Format**
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "The request contains invalid data",
        "details": [
            {
                "field": "email",
                "message": "Invalid email format"
            }
        ],
        "request_id": "req_123456789",
        "timestamp": "2024-01-21T10:00:00Z"
    }
}
```

### **HTTP Status Codes**
- `200` - Success
- `201` - Created
- `204` - No Content
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (duplicate resources)
- `422` - Unprocessable Entity (business logic errors)
- `429` - Too Many Requests (rate limiting)
- `500` - Internal Server Error

### **Common Error Codes**
- `VALIDATION_ERROR` - Request validation failed
- `AUTHENTICATION_REQUIRED` - Missing or invalid authentication
- `PERMISSION_DENIED` - Insufficient permissions
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `RESOURCE_CONFLICT` - Resource already exists
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `BUSINESS_LOGIC_ERROR` - Business rule violation
- `EXTERNAL_SERVICE_ERROR` - External API failure

---

## 🔧 **Rate Limiting**

### **Rate Limits**
- **Authentication**: 10 requests/minute per IP
- **General API**: 1000 requests/hour per user
- **Search**: 100 requests/hour per user
- **File uploads**: 20 requests/hour per user

### **Rate Limit Headers**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642737600
X-RateLimit-Retry-After: 3600
```

---

## 📋 **Pagination**

All list endpoints support pagination using `limit` and `offset` parameters.

### **Response Format**
```json
{
    "items": [...],
    "pagination": {
        "total": 150,
        "limit": 20,
        "offset": 40,
        "has_next": true,
        "has_previous": true,
        "next_offset": 60,
        "previous_offset": 20
    }
}
```

---

## 🔍 **Filtering & Sorting**

### **Common Filter Parameters**
- `created_after` / `created_before` - Date range filtering
- `status` - Status-based filtering
- `tags` - Tag-based filtering
- `search` - Full-text search

### **Sorting**
- `sort_by` - Field to sort by
- `sort_order` - `asc` or `desc`

Example: `GET /api/v1/notes?sort_by=created_at&sort_order=desc&tags=architecture,patterns`

---

This API documentation provides complete coverage of all CertCoach endpoints with detailed request/response examples and error handling information.
