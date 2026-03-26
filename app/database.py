"""Async SQLAlchemy engine, session factory, and declarative base."""
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Vercel serverless cannot maintain persistent connection pools
_pool_kwargs = (
    {"poolclass": NullPool}
    if os.environ.get("VERCEL") == "1"
    else {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}
)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    **_pool_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency that yields a managed AsyncSession.

    The session is automatically closed after the request regardless of
    whether an exception occurred.
    """
    async with AsyncSessionLocal() as session:
        yield session
