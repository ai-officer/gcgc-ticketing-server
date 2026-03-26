"""Async SQLAlchemy engine, session factory, and declarative base."""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
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
