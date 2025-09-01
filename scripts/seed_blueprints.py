#!/usr/bin/env python3
"""
Seed script to load exam blueprint data into the database.

This script loads exam blueprints and objectives from YAML files
into the PostgreSQL database for the CertCoach platform.
"""

import os
import sys
import asyncio
import yaml
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.database.models import ExamBlueprint, Objective
from packages.database.connection import db_manager
from sqlalchemy import select


async def load_blueprint_from_yaml(yaml_path: Path) -> dict:
    """Load and parse a blueprint YAML file."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


async def create_or_update_blueprint(session, blueprint_data: dict) -> ExamBlueprint:
    """Create or update an exam blueprint in the database."""
    code = blueprint_data['exam']['code']
    
    # Check if blueprint already exists
    result = await session.execute(
        select(ExamBlueprint).where(ExamBlueprint.code == code)
    )
    blueprint = result.scalar_one_or_none()
    
    if blueprint:
        print(f"Updating existing blueprint: {code}")
        # Update existing blueprint
        blueprint.title = blueprint_data['exam']['title']
        blueprint.description = blueprint_data['exam'].get('description')
        blueprint.provider = blueprint_data['exam']['provider']
        blueprint.level = blueprint_data['exam']['level']
        blueprint.duration_hours = blueprint_data['exam']['duration_hours']
        blueprint.updated_at = datetime.utcnow()
    else:
        print(f"Creating new blueprint: {code}")
        # Create new blueprint
        blueprint = ExamBlueprint(
            code=code,
            title=blueprint_data['exam']['title'],
            description=blueprint_data['exam'].get('description'),
            provider=blueprint_data['exam']['provider'],
            level=blueprint_data['exam']['level'],
            duration_hours=blueprint_data['exam']['duration_hours'],
            total_weight=sum(area['weight'] for area in blueprint_data['exam']['functional_areas']),
            active=True
        )
        session.add(blueprint)
    
    # Flush to get the ID
    await session.flush()
    return blueprint


async def create_objectives(session, blueprint: ExamBlueprint, functional_areas: list, parent_id: int = None, depth: int = 0):
    """Recursively create objectives from functional areas."""
    for area in functional_areas:
        # Create the main objective
        objective = Objective(
            blueprint_id=blueprint.id,
            parent_id=parent_id,
            code=area['code'],
            title=area['title'],
            description=area.get('description'),
            weight=area['weight'],
            depth=depth
        )
        session.add(objective)
        await session.flush()  # Get the ID
        
        print(f"  {'  ' * depth}Created objective: {area['code']} - {area['title']} (weight: {area['weight']})")
        
        # Create sub-objectives if they exist
        if 'sub_areas' in area:
            await create_objectives(
                session, blueprint, area['sub_areas'], 
                parent_id=objective.id, depth=depth + 1
            )


async def seed_blueprint(yaml_path: Path):
    """Seed a single blueprint from a YAML file."""
    print(f"\nProcessing blueprint: {yaml_path.name}")
    
    # Load blueprint data
    blueprint_data = await load_blueprint_from_yaml(yaml_path)
    
    async with db_manager.get_session() as session:
        try:
            # Create or update blueprint
            blueprint = await create_or_update_blueprint(session, blueprint_data)
            
            # Delete existing objectives for this blueprint (if updating)
            if blueprint.objectives:
                print(f"Removing existing objectives for {blueprint.code}")
                for obj in blueprint.objectives:
                    await session.delete(obj)
                await session.flush()
            
            # Create new objectives
            print(f"Creating objectives for {blueprint.code}")
            await create_objectives(
                session, blueprint, 
                blueprint_data['exam']['functional_areas']
            )
            
            # Commit the transaction
            await session.commit()
            print(f"✅ Successfully seeded blueprint: {blueprint.code}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding blueprint {yaml_path.name}: {e}")
            raise


async def seed_all_blueprints():
    """Seed all blueprint YAML files in the data/blueprints directory."""
    # Initialize database connection
    await db_manager.initialize()
    
    # Find all blueprint YAML files
    blueprints_dir = Path(__file__).parent.parent / "data" / "blueprints"
    
    if not blueprints_dir.exists():
        print(f"❌ Blueprints directory not found: {blueprints_dir}")
        return
    
    yaml_files = list(blueprints_dir.glob("*.yaml")) + list(blueprints_dir.glob("*.yml"))
    
    if not yaml_files:
        print(f"❌ No YAML files found in: {blueprints_dir}")
        return
    
    print(f"Found {len(yaml_files)} blueprint files to process:")
    for f in yaml_files:
        print(f"  - {f.name}")
    
    # Process each blueprint
    for yaml_file in yaml_files:
        try:
            await seed_blueprint(yaml_file)
        except Exception as e:
            print(f"❌ Failed to process {yaml_file.name}: {e}")
            continue
    
    print("\n🎉 Blueprint seeding completed!")


async def main():
    """Main function to run the seeding script."""
    print("🌱 CertCoach Blueprint Seeder")
    print("=" * 40)
    
    try:
        await seed_all_blueprints()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        await db_manager.close()


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check required environment variables
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL environment variable is required")
        sys.exit(1)
    
    # Run the seeder
    asyncio.run(main())
