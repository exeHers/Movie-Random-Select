from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SeenMovie(Base):
    __tablename__ = "seen_movies"
    __table_args__ = (UniqueConstraint("tmdb_id", name="uq_seen_tmdb_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    marked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("tmdb_id", name="uq_watchlist_tmdb_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(512), default="")


class Profile(Base):
    """Taste hints per family member — used as TMDB discover filters."""

    __tablename__ = "profiles"
    __table_args__ = (UniqueConstraint("slug", name="uq_profile_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    genre_ids: Mapped[str] = mapped_column(String(256), default="")
    min_vote_average: Mapped[float] = mapped_column(default=7.0)
    min_vote_count: Mapped[int] = mapped_column(default=500)
    rotation_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exclude_keywords: Mapped[str] = mapped_column(String(512), default="")
