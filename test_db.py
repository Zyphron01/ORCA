import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

async def main():
    connect_args = {}
    
    url = "postgresql+asyncpg://orca:orca@localhost:5432/orca"
    if "asyncpg" in url:
        connect_args["server_settings"] = {"search_path": "public,extensions"}
        
    engine = create_async_engine(url, connect_args=connect_args)
    
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS extensions;"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis SCHEMA extensions;"))
        res = await conn.execute(text("SHOW search_path;"))
        print("Search path asyncpg:", res.scalar())
        
    await engine.dispose()
    
    # Test psycopg
    url = "postgresql+psycopg://orca:orca@localhost:5432/orca"
    connect_args = {"options": "-c search_path=public,extensions"}
    engine2 = create_async_engine(url, connect_args=connect_args)
    async with engine2.begin() as conn:
        res = await conn.execute(text("SHOW search_path;"))
        print("Search path psycopg:", res.scalar())
    
    await engine2.dispose()

asyncio.run(main())
