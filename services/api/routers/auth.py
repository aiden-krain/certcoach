"""Authentication and user management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from packages.database.connection import get_db_session, get_supabase_client
from packages.database.models import User
from sqlalchemy import select
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/register")
async def register_user(
    email: str,
    password: str,
    full_name: str = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Register a new user via Supabase Auth."""
    try:
        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(
                status_code=500,
                detail="Authentication service unavailable"
            )
        
        # Register with Supabase Auth
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"full_name": full_name}
            }
        })
        
        if response.user:
            # Create user record in our database
            user = User(
                id=response.user.id,
                email=email,
                full_name=full_name
            )
            db.add(user)
            await db.commit()
            
            return {
                "message": "User registered successfully",
                "user_id": response.user.id,
                "email": email
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to register user"
            )
            
    except Exception as e:
        logger.error("User registration failed", email=email, error=str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login")
async def login_user(email: str, password: str):
    """Login user via Supabase Auth."""
    try:
        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(
                status_code=500,
                detail="Authentication service unavailable"
            )
        
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.session:
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email
                }
            }
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
            
    except Exception as e:
        logger.error("User login failed", email=email, error=str(e))
        raise HTTPException(
            status_code=401,
            detail="Login failed"
        )


@router.get("/profile")
async def get_user_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get current user profile."""
    try:
        result = await db.execute(
            select(User).where(User.id == current_user["id"])
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "timezone": user.timezone,
            "preferences": user.preferences,
            "created_at": user.created_at,
            "last_active": user.last_active
        }
        
    except Exception as e:
        logger.error("Failed to get user profile", user_id=current_user["id"], error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve profile"
        )


# Dependency to get current user from JWT token
async def get_current_user(token: str = Depends(get_jwt_token)):
    """Extract current user from JWT token."""
    try:
        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(
                status_code=500,
                detail="Authentication service unavailable"
            )
        
        user = supabase.auth.get_user(token)
        if user and user.user:
            return {
                "id": user.user.id,
                "email": user.user.email
            }
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
            
    except Exception as e:
        logger.error("Token validation failed", error=str(e))
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )
