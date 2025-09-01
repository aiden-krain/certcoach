#!/usr/bin/env python3
"""
Database setup script for CertCoach development environment.

This script sets up the PostgreSQL database with pgvector extension
and creates the initial schema using Alembic migrations.
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
    print("\n📊 Setting up database schema...")
    
    # Create initial migration if it doesn't exist
    if not any(Path("migrations/versions").glob("*.py")):
        print("Creating initial migration...")
        success = run_command(
            "alembic revision --autogenerate -m 'Initial schema with all models'",
            "Generating initial migration"
        )
        if not success:
            return False
    
    # Run migrations
    success = run_command(
        "alembic upgrade head",
        "Applying database migrations"
    )
    
    if success:
        print("✅ Database schema setup complete")
    return success


def setup_pgvector():
    """Instructions for setting up pgvector extension."""
    print("\n🗄️  PostgreSQL + pgvector Setup Instructions")
    print("=" * 50)
    print("""
To set up the database with pgvector extension, run these commands:

1. Using Docker (Recommended for development):
   docker run -d \\
     --name certcoach-postgres \\
     -e POSTGRES_DB=certcoach \\
     -e POSTGRES_USER=certcoach \\
     -e POSTGRES_PASSWORD=certcoach_dev \\
     -p 5432:5432 \\
     ankane/pgvector

2. Or install PostgreSQL and pgvector locally:
   # On macOS with Homebrew:
   brew install postgresql pgvector
   
   # On Ubuntu/Debian:
   sudo apt-get install postgresql postgresql-contrib
   # Then compile and install pgvector from source
   
   # Create database and user:
   sudo -u postgres createuser -d certcoach
   sudo -u postgres createdb -O certcoach certcoach
   sudo -u postgres psql -c "CREATE EXTENSION vector;" certcoach

3. Update your .env file with the database URL:
   DATABASE_URL=postgresql://certcoach:certcoach_dev@localhost:5432/certcoach
""")


async def main():
    """Main setup function."""
    print("🚀 CertCoach Database Setup")
    print("=" * 40)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        print("   Please create a .env file with your database configuration")
        print("   Example: cp .env.example .env")
        setup_pgvector()
        return False
    
    print(f"📊 Database URL: {database_url}")
    
    # Test database connection
    connection_ok = await check_database_connection()
    if not connection_ok:
        print("\n❌ Database connection failed!")
        setup_pgvector()
        return False
    
    # Setup schema
    schema_ok = setup_database_schema()
    if not schema_ok:
        print("❌ Schema setup failed!")
        return False
    
    print("\n🎉 Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Run: python scripts/seed_blueprints.py")
    print("2. Start the API gateway: uvicorn services.api-gateway.main:app --reload")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
