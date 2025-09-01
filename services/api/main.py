"""
Main FastAPI application for CertCoach.

Single backend service handling all core functionality:
- Study planning and scheduling
- Practice sessions and assessment  
- Mastery tracking and analytics
- Notes and flashcard management
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import os
import structlog

from packages.database.connection import initialize_database, close_database
from .routers import study_plans, practice, mastery, notes, auth, health
from .middleware.auth import AuthMiddleware
from .middleware.logging import LoggingMiddleware


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    logger.info("Starting CertCoach API server")
    await initialize_database()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CertCoach API server")
    await close_database()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="CertCoach API",
    description="Adaptive certification exam preparation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
)

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(study_plans.router, prefix="/api/v1/study-plans", tags=["study-plans"])
app.include_router(practice.router, prefix="/api/v1/practice", tags=["practice"])
app.include_router(mastery.router, prefix="/api/v1/mastery", tags=["mastery"])
app.include_router(notes.router, prefix="/api/v1/notes", tags=["notes"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "CertCoach API",
        "version": "1.0.0",
        "description": "Adaptive certification exam preparation platform",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1")
async def api_info():
    """API version information."""
    return {
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/v1/health",
            "auth": "/api/v1/auth",
            "study_plans": "/api/v1/study-plans",
            "practice": "/api/v1/practice", 
            "mastery": "/api/v1/mastery",
            "notes": "/api/v1/notes"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info("Starting server", host=host, port=port, debug=debug)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )
