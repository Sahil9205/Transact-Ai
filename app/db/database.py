from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


class DatabaseManager:
    """Manager for database connections and sessions."""

    def __init__(self, database_url: str) -> None:
        """Initialize the database manager.
        
        Args:
            database_url: The database connection URL.
        """
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            echo=False,
            future=True,
        )
        self.async_session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def init_db(self) -> None:
        """Create all tables from Base.metadata."""
        # Ensure the directory for SQLite file exists
        url_str = str(self.engine.url)
        if url_str.startswith("sqlite"):
            import os
            # Extract file path from SQLite URL (after :///)
            db_path = url_str.split("///")[-1] if "///" in url_str else None
            if db_path and db_path != ":memory:":
                os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        """Close the database engine."""
        await self.engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional scope around a series of operations."""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


_db_manager: DatabaseManager | None = None


def init_database_manager(database_url: str) -> DatabaseManager:
    """Initialize the global database manager.
    
    Args:
        database_url: The database connection URL.
        
    Returns:
        The initialized DatabaseManager.
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url)
    return _db_manager


def get_database_manager() -> DatabaseManager:
    """Get the global database manager.
    
    Returns:
        The DatabaseManager instance.
        
    Raises:
        RuntimeError: If the manager has not been initialized.
    """
    if _db_manager is None:
        raise RuntimeError("DatabaseManager is not initialized. Call init_database_manager first.")
    return _db_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding a database session."""
    manager = get_database_manager()
    async for session in manager.get_session():
        yield session
