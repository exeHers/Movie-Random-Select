import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.migrate import run_migrations

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Query keys meant for libpq (psycopg2, JDBC, etc.). asyncpg passes the rest of
# the URL query as connect() kwargs and errors on these (e.g. sslmode,
# channel_binding).
_LIBPQ_ONLY_QUERY_KEYS = frozenset(
    {
        "channel_binding",
        "connect_timeout",
        "options",
        "target_session_attrs",
    }
)


def _normalize_database_url(raw: str) -> tuple[str, dict]:
    """Return (sqlalchemy_url, connect_args) for create_async_engine."""
    raw = raw.strip()
    if not raw:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        db_path = _DATA_DIR / "movie_night.sqlite"
        return f"sqlite+aiosqlite:///{db_path}", {}

    connect_args: dict = {}

    # Parse postgres URLs; strip libpq-only ?params= so asyncpg won't see them.
    if raw.startswith("postgresql://") or raw.startswith("postgres://"):
        unified = raw.replace("postgres://", "postgresql://", 1)
        parsed = urlparse(unified)
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        sslmode_val: str | None = None
        kept: list[tuple[str, str]] = []
        for key, val in pairs:
            lk = key.lower()
            if lk == "sslmode":
                sslmode_val = (val or "require").lower()
                continue
            if lk in _LIBPQ_ONLY_QUERY_KEYS:
                continue
            kept.append((key, val))

        if sslmode_val in ("require", "verify-ca", "verify-full", "prefer"):
            connect_args["ssl"] = True
        elif sslmode_val in ("disable", "allow"):
            pass

        new_query = urlencode(kept)
        rebuilt = urlunparse(parsed._replace(query=new_query))
        url = rebuilt.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url, connect_args

    return raw, {}


DATABASE_URL, _ENGINE_CONNECT_ARGS = _normalize_database_url(os.environ.get("DATABASE_URL", ""))


def is_postgres_backend() -> bool:
    return "postgresql" in DATABASE_URL or "asyncpg" in DATABASE_URL


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=_ENGINE_CONNECT_ARGS,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await run_migrations(engine)
