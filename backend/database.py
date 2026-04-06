from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
import redis.asyncio as aioredis
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@pgbouncer:6432/scoring")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

engine = create_async_engine(DATABASE_URL, pool_size=20, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 全局redis连接
redis = aioredis.from_url(REDIS_URL, decode_responses=True)


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：提供异步数据库会话"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_redis():
    """FastAPI 依赖注入：提供 Redis 连接"""
    yield redis
