"""Health check endpoints for monitoring and status."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from packages.database.connection import get_db_session, db_manager
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "certcoach-api",
        "version": "1.0.0"
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db_session)):
    """Detailed health check including database connectivity."""
    try:
        # Test database connection
        db_healthy = await db_manager.health_check()
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "service": "certcoach-api",
            "version": "1.0.0",
            "components": {
                "database": "healthy" if db_healthy else "unhealthy",
                "supabase": "healthy" if db_manager.supabase_client else "disabled"
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "service": "certcoach-api", 
            "version": "1.0.0",
            "error": str(e)
        }


@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    try:
        db_healthy = await db_manager.health_check()
        if not db_healthy:
            return {"status": "not ready", "reason": "database unavailable"}
        
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready", "reason": "service error"}
