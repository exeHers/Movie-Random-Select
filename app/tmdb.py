import os
import random
from typing import Any

import httpx

BASE = "https://api.themoviedb.org/3"


def _api_key() -> str:
    key = os.environ.get("TMDB_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "Set TMDB_API_KEY (free at https://www.themoviedb.org/settings/api). "
            "Export it before running: export TMDB_API_KEY=your_key"
        )
    return key


async def discover_movies(
    *,
    genre_ids: list[int],
    min_vote_average: float,
    min_vote_count: int,
    page: int | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "api_key": _api_key(),
        "language": "en-US",
        "sort_by": "vote_average.desc",
        "vote_average.gte": min_vote_average,
        "vote_count.gte": min_vote_count,
        "include_adult": "false",
        "page": page or random.randint(1, 5),
    }
    if genre_ids:
        params["with_genres"] = ",".join(str(g) for g in genre_ids)

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"{BASE}/discover/movie", params=params)
        r.raise_for_status()
        return r.json()


async def movie_detail(tmdb_id: int) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            f"{BASE}/movie/{tmdb_id}",
            params={"api_key": _api_key(), "language": "en-US"},
        )
        r.raise_for_status()
        return r.json()


async def movie_videos(tmdb_id: int) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            f"{BASE}/movie/{tmdb_id}/videos",
            params={"api_key": _api_key(), "language": "en-US"},
        )
        r.raise_for_status()
        return r.json()
