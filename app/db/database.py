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
        # Normalize PostgreSQL URL for asyncpg
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

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
        # Ensure all SQLAlchemy models are registered in Base.metadata
        import app.db.models  # noqa: F401

        # Ensure the directory for SQLite file exists safely
        url_str = str(self.engine.url)
        if url_str.startswith("sqlite"):
            import os
            # Extract file path from SQLite URL (after :///)
            db_path = url_str.split("///")[-1] if "///" in url_str else None
            if db_path and db_path != ":memory:":
                try:
                    dir_name = os.path.dirname(os.path.abspath(db_path))
                    if dir_name and not os.path.exists(dir_name):
                        os.makedirs(dir_name, exist_ok=True)
                except Exception:
                    pass
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Safe non-breaking column addition for existing tables (SQLite & Postgres)
            from sqlalchemy import text
            is_pg = not url_str.startswith("sqlite")
            if_not_exists = "IF NOT EXISTS " if is_pg else ""

            for col, col_type in [
                ("pincode", "VARCHAR(10)"),
                ("delivery_address", "TEXT"),
                ("platform", "VARCHAR(50) DEFAULT 'unknown'"),
            ]:
                try:
                    await conn.execute(text(f"ALTER TABLE orders ADD COLUMN {if_not_exists}{col} {col_type}"))
                except Exception:
                    pass  # Column already exists

            for col, col_type in [
                ("api_key", "VARCHAR(64)"),
                ("contact_email", "VARCHAR(255)"),
                ("contact_phone", "VARCHAR(20)"),
                ("business_type", "VARCHAR(50) DEFAULT 'general'"),
                ("onboarding_status", "VARCHAR(30) DEFAULT 'active'"),
                ("operational_status", "VARCHAR(30) DEFAULT 'open'"),
                ("logo_url", "VARCHAR(500)"),
                ("payout_upi_id", "VARCHAR(100)"),
                ("payout_bank_account", "VARCHAR(50)"),
                ("payout_ifsc_code", "VARCHAR(20)"),
            ]:
                try:
                    await conn.execute(text(f"ALTER TABLE merchants ADD COLUMN {if_not_exists}{col} {col_type}"))
                except Exception:
                    pass  # Column already exists

            for col, col_type in [
                ("pricing_type", "VARCHAR(30) DEFAULT 'fixed_unit'"),
                ("unit", "VARCHAR(20) DEFAULT 'piece'"),
                ("min_quantity", "FLOAT DEFAULT 1.0"),
                ("increment_step", "FLOAT DEFAULT 1.0"),
            ]:
                try:
                    await conn.execute(text(f"ALTER TABLE products ADD COLUMN {if_not_exists}{col} {col_type}"))
                except Exception:
                    pass  # Column already exists


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
