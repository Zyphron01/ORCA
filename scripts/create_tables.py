import asyncio, sys
sys.path.insert(0, 'apps/api')
sys.path.insert(0, 'packages/shared-types')
from core.database import engine
from core.db_models import Base

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print('Tables created successfully')

asyncio.run(create_tables())
