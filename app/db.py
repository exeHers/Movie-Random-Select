import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.migrate import run_migrations

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _normalize_database_url(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        db_path = _DATA_DIR / "movie_night.sqlite"
        return f"sqlite+aiosqlite:///{db_path}"
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+asyncpg://", 1)
    return raw


DATABASE_URL = _normalize_database_url(os.environ.get("DATABASE_URL", ""))


def is_postgres_backend() -> bool:
    return "postgresql" in DATABASE_URL or "asyncpg" in DATABASE_URL


class Base(DeclarativeBase):
    pass


engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await run_migrations(engine)
