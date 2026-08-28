from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Create the engine with strict resource controls for a multi-app server
engine = create_async_engine(settings.DATABASE_URL, echo=False)


# Explicitly pass the AsyncSession class for strict typing
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


# The dependency you inject into your FastAPI endpoints
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
