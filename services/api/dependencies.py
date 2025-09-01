"""
FastAPI dependencies for authentication and common operations.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from packages.database.connection import get_supabase_client
import structlog

logger = structlog.get_logger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Extract current user from JWT token."""
    try:
        token = credentials.credentials
        supabase = get_supabase_client()
        
        if not supabase:
            raise HTTPException(
                status_code=500,
                detail="Authentication service unavailable"
            )
        
        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        if user and user.user:
            return {
                "id": user.user.id,
                "email": user.user.email,
                "metadata": user.user.user_metadata
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except Exception as e:
        logger.error("Token validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current user but don't require authentication."""
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
