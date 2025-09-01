"""
Database connection management for CertCoach platform.

This module provides async database connection handling with Supabase integration,
connection pooling, and health checking capabilities.
"""

import os
import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text, event
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
import structlog

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """Manages database connections and Supabase client."""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.supabase_client: Optional[Client] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database connections and Supabase client."""
        if self._initialized:
            return
            
        # Database configuration
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Convert postgres:// to postgresql+asyncpg://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif not database_url.startswith("postgresql+asyncpg://"):
            database_url = f"postgresql+asyncpg://{database_url}"
        
        # Create async engine with optimized settings
        self.engine = create_async_engine(
            database_url,
            echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_pre_ping=True,
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),  # 1 hour
            connect_args={
                "server_settings": {
                    "jit": "off",  # Disable JIT for better connection time
                }
            }
        )
        
        # Create session factory
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if supabase_url and supabase_key:
            options = ClientOptions(
                auto_refresh_token=True,
                persist_session=True,
                storage=None,  # Use memory storage for server-side
                realtime=None,  # Disable realtime for server-side by default
            )
            
            self.supabase_client = create_client(
                supabase_url=supabase_url,
                supabase_key=supabase_key,
                options=options
            )
            
            logger.info("Supabase client initialized", url=supabase_url)
        else:
            logger.warning("Supabase credentials not found, client not initialized")
        
        # Test database connection
        await self.health_check()
        
        self._initialized = True
        logger.info("Database manager initialized successfully")
    
    async def health_check(self) -> bool:
        """Check database connectivity and health."""
        if not self.engine:
            return False
            
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                await conn.execute(text("SELECT version()"))
                
                # Check pgvector extension
                try:
                    await conn.execute(text("SELECT vector_dims(ARRAY[1,2,3]::vector)"))
                    logger.info("pgvector extension is available")
                except Exception as e:
                    logger.warning("pgvector extension not available", error=str(e))
                
            logger.info("Database health check passed")
            return True
            
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session with automatic cleanup."""
        if not self._initialized:
            await self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None
            self._initialized = False
            logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions in FastAPI."""
    async with db_manager.get_session() as session:
        yield session


def get_supabase_client() -> Optional[Client]:
    """Get the Supabase client instance."""
    return db_manager.supabase_client


class SupabaseManager:
    """Advanced Supabase operations and utilities."""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()
        if not self.client:
            raise ValueError("Supabase client not available")
    
    async def verify_user_token(self, token: str) -> Optional[dict]:
        """Verify a JWT token and return user data."""
        try:
            user = self.client.auth.get_user(token)
            if user and user.user:
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "metadata": user.user.user_metadata,
                }
            return None
        except Exception as e:
            logger.error("Failed to verify user token", error=str(e))
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user data by ID from Supabase."""
        try:
            response = self.client.auth.admin.get_user_by_id(user_id)
            if response and response.user:
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "metadata": response.user.user_metadata,
                    "created_at": response.user.created_at,
                    "last_sign_in": response.user.last_sign_in_at,
                }
            return None
        except Exception as e:
            logger.error("Failed to get user by ID", user_id=user_id, error=str(e))
            return None
    
    def subscribe_to_changes(self, table: str, callback, filter_clause: str = None):
        """Subscribe to real-time changes on a table."""
        if not self.client:
            raise ValueError("Supabase client not initialized")
        
        subscription = self.client.table(table).on("*", callback)
        if filter_clause:
            subscription = subscription.filter(filter_clause)
        
        return subscription.subscribe()
    
    async def upload_file(self, bucket: str, file_path: str, file_data: bytes) -> Optional[str]:
        """Upload a file to Supabase storage."""
        try:
            response = self.client.storage.from_(bucket).upload(file_path, file_data)
            if response:
                # Get public URL
                public_url = self.client.storage.from_(bucket).get_public_url(file_path)
                return public_url
            return None
        except Exception as e:
            logger.error("Failed to upload file", bucket=bucket, path=file_path, error=str(e))
            return None


# Event listeners for connection management
@event.listens_for(DatabaseManager, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries for performance monitoring."""
    import time
    context._query_start_time = time.time()


@event.listens_for(DatabaseManager, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log completed queries with execution time."""
    import time
    total = time.time() - context._query_start_time
    
    if total > float(os.getenv("SLOW_QUERY_THRESHOLD", "1.0")):
        logger.warning(
            "Slow query detected",
            duration=total,
            statement=statement[:200] + "..." if len(statement) > 200 else statement
        )


async def initialize_database():
    """Initialize database on application startup."""
    await db_manager.initialize()


async def close_database():
    """Close database connections on application shutdown."""
    await db_manager.close()


# Utility functions for common operations
async def execute_raw_sql(query: str, params: dict = None) -> list:
    """Execute raw SQL query and return results."""
    async with db_manager.get_session() as session:
        result = await session.execute(text(query), params or {})
        return result.fetchall()


async def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        );
    """
    result = await execute_raw_sql(query, {"table_name": table_name})
    return result[0][0] if result else False
