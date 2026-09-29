import asyncio, sys
sys.path.insert(0, 'apps/api')
sys.path.insert(0, 'packages/shared-types')
from core.database import engine
from core.db_models import Base

from sqlalchemy.sql import text

async def create_tables():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS extensions;"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis SCHEMA extensions;"))
        except Exception as e:
            print("Warning: Could not create extensions schema/postgis:", e)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print('Tables created successfully')

asyncio.run(create_tables())
