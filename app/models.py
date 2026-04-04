from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
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


class Profile(Base):
    """Taste hints per family member — used as TMDB discover filters."""

    __tablename__ = "profiles"
    __table_args__ = (UniqueConstraint("slug", name="uq_profile_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    # Comma-separated TMDB genre IDs, e.g. "18,36" for drama + history
    genre_ids: Mapped[str] = mapped_column(String(256), default="")
    min_vote_average: Mapped[float] = mapped_column(default=7.0)
    min_vote_count: Mapped[int] = mapped_column(default=500)
