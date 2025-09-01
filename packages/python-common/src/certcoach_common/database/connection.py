"""
Database connection and Supabase integration
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from supabase import create_client, Client
import os
from typing import AsyncGenerator, Optional
import asyncio
from contextlib import asynccontextmanager

class DatabaseConfig:
    """Database configuration"""
    
    def __init__(self):
        # Primary database URL (PostgreSQL with pgvector)
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Supabase configuration
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # Connection pool settings
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        
        # Vector database settings
        self.vector_dimensions = int(os.getenv("VECTOR_DIMENSIONS", "384"))
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

class DatabaseManager:
    """Database connection manager with Supabase integration"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._async_engine = None
        self._sync_engine = None
        self._async_session_factory = None
        self._sync_session_factory = None
        self._supabase_client = None
        self._supabase_service_client = None
    
    def get_async_engine(self):
        """Get async SQLAlchemy engine"""
        if self._async_engine is None:
            # Convert sync URL to async
            async_url = self.config.database_url.replace("postgresql://", "postgresql+asyncpg://")
            
            self._async_engine = create_async_engine(
                async_url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
                future=True,
            )
        return self._async_engine
    
    def get_sync_engine(self):
        """Get sync SQLAlchemy engine"""
        if self._sync_engine is None:
            self._sync_engine = create_engine(
                self.config.database_url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
            )
        return self._sync_engine
    
    def get_async_session_factory(self):
        """Get async session factory"""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                self.get_async_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._async_session_factory
    
    def get_sync_session_factory(self):
        """Get sync session factory"""
        if self._sync_session_factory is None:
            self._sync_session_factory = sessionmaker(
                self.get_sync_engine(),
                expire_on_commit=False,
            )
        return self._sync_session_factory
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Async context manager for database sessions"""
        session_factory = self.get_async_session_factory()
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_supabase_client(self) -> Client:
        """Get Supabase client for user-level operations"""
        if self._supabase_client is None:
            if not self.config.supabase_url or not self.config.supabase_key:
                raise ValueError("Supabase URL and key are required")
            
            self._supabase_client = create_client(
                self.config.supabase_url,
                self.config.supabase_key
            )
        return self._supabase_client
    
    def get_supabase_service_client(self) -> Client:
        """Get Supabase service client for admin operations"""
        if self._supabase_service_client is None:
            if not self.config.supabase_url or not self.config.supabase_service_key:
                raise ValueError("Supabase URL and service key are required")
            
            self._supabase_service_client = create_client(
                self.config.supabase_url,
                self.config.supabase_service_key
            )
        return self._supabase_service_client
    
    async def initialize_vector_extension(self):
        """Initialize pgvector extension in the database"""
        async with self.get_async_session() as session:
            try:
                # Create pgvector extension if it doesn't exist
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                
                # Verify the extension is working
                result = await session.execute(
                    text("SELECT '1'::vector <-> '2'::vector AS distance;")
                )
                distance = result.scalar()
                print(f"Vector extension initialized successfully. Test distance: {distance}")
                
            except Exception as e:
                print(f"Warning: Could not initialize vector extension: {e}")
                print("Make sure pgvector is installed in your PostgreSQL instance")
    
    async def health_check(self) -> dict:
        """Perform database health check"""
        health_status = {
            "database": "unknown",
            "supabase": "unknown",
            "vector_extension": "unknown"
        }
        
        # Check database connection
        try:
            async with self.get_async_session() as session:
                await session.execute(text("SELECT 1"))
                health_status["database"] = "healthy"
        except Exception as e:
            health_status["database"] = f"unhealthy: {str(e)}"
        
        # Check Supabase connection
        try:
            client = self.get_supabase_client()
            # Simple health check - this will fail if Supabase is down
            client.table("users").select("id").limit(1).execute()
            health_status["supabase"] = "healthy"
        except Exception as e:
            health_status["supabase"] = f"unhealthy: {str(e)}"
        
        # Check vector extension
        try:
            async with self.get_async_session() as session:
                await session.execute(text("SELECT '1'::vector <-> '2'::vector;"))
                health_status["vector_extension"] = "healthy"
        except Exception as e:
            health_status["vector_extension"] = f"unhealthy: {str(e)}"
        
        return health_status

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        config = DatabaseConfig()
        _db_manager = DatabaseManager(config)
    return _db_manager

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database sessions"""
    db_manager = get_database_manager()
    async with db_manager.get_async_session() as session:
        yield session

def get_supabase_client() -> Client:
    """FastAPI dependency for Supabase client"""
    db_manager = get_database_manager()
    return db_manager.get_supabase_client()

async def init_database():
    """Initialize database on application startup"""
    db_manager = get_database_manager()
    
    # Initialize vector extension
    await db_manager.initialize_vector_extension()
    
    # Perform health check
    health = await db_manager.health_check()
    print("Database health check:", health)
    
    return db_manager
