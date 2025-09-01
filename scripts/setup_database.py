#!/usr/bin/env python3
"""
Simplified database setup script for CertCoach.

Sets up Supabase database with optimized schema and enables required extensions.
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_command(cmd: str, description: str = None) -> bool:
    """Run a shell command and return success status."""
    if description:
        print(f"🔄 {description}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False


async def check_database_connection():
    """Check if database connection is working."""
    print("🔍 Checking database connection...")
    
    try:
        from packages.database.connection import db_manager
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Test connection
        success = await db_manager.health_check()
        if success:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    finally:
        from packages.database.connection import db_manager
        await db_manager.close()


def setup_database_schema():
    """Set up database schema using Alembic."""
    print("\n📊 Setting up simplified database schema...")
    
    # Create initial migration if it doesn't exist
    if not any(Path("migrations/versions").glob("*.py")):
        print("Creating initial migration...")
        success = run_command(
            ".venv\\Scripts\\python.exe -m alembic revision --autogenerate -m 'Initial simplified schema'",
            "Generating initial migration"
        )
        if not success:
            return False
    
    # Run migrations
    success = run_command(
        ".venv\\Scripts\\python.exe -m alembic upgrade head",
        "Applying database migrations"
    )
    
    if success:
        print("✅ Simplified database schema setup complete")
    return success


async def main():
    """Main setup function."""
    print("🚀 CertCoach Simplified Database Setup")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        print("   Please create a .env file with your Supabase database configuration")
        print("   Example: cp .env.example .env")
        print("\n📝 Supabase Setup Instructions:")
        print("   1. Create project at https://supabase.com/dashboard")
        print("   2. Get connection details from Settings → Database")
        print("   3. Enable pgvector: CREATE EXTENSION IF NOT EXISTS vector;")
        print("   4. Update .env with your credentials")
        return False
    
    print(f"📊 Database URL: {database_url.split('@')[1] if '@' in database_url else 'configured'}")
    
    # Test database connection
    connection_ok = await check_database_connection()
    if not connection_ok:
        print("\n❌ Database connection failed!")
        return False
    
    # Setup schema
    schema_ok = setup_database_schema()
    if not schema_ok:
        print("❌ Schema setup failed!")
        return False
    
    print("\n🎉 Simplified database setup completed successfully!")
    print("\nNext steps:")
    print("1. Run: python scripts/seed_blueprints.py")
    print("2. Start API: python -m uvicorn services.api.main:app --reload")
    print("3. View docs: http://localhost:8000/docs")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
