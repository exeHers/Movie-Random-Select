import asyncio
import random
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppSetting, Profile, SeenMovie, WatchlistItem
from app.tmdb import discover_movies, movie_detail


ROTATION_SLUGS = ("stepdad", "mom", "you")
ANCHOR_KEY = "rotation_anchor_date"


async def get_setting(session: AsyncSession, key: str, default: str = "") -> str:
    row = (await session.execute(select(AppSetting).where(AppSetting.key == key))).scalar_one_or_none()
    if row is None or not row.value:
        return default
    return row.value


async def set_setting(session: AsyncSession, key: str, value: str) -> None:
    row = (await session.execute(select(AppSetting).where(AppSetting.key == key))).scalar_one_or_none()
    if row is None:
        session.add(AppSetting(key=key, value=value))
    else:
        row.value = value


def _parse_anchor(s: str) -> date | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


async def profiles_for_rotation(session: AsyncSession) -> list[Profile]:
    rows = (await session.execute(select(Profile))).scalars().all()
    rot = [p for p in rows if p.slug in ROTATION_SLUGS]
    rot.sort(key=lambda p: (p.rotation_order is None, p.rotation_order or 999, p.display_name))
    return rot


def _tonight_index(anchor: date, today: date, n: int) -> int:
    if n <= 0:
        return 0
    delta = (today - anchor).days
    if delta < 0:
        delta = 0
    return delta % n


async def tonight_profile(session: AsyncSession) -> tuple[Profile | None, list[Profile]]:
    rot = await profiles_for_rotation(session)
    if not rot:
        return None, rot
    anchor_s = await get_setting(session, ANCHOR_KEY, "")
    anchor = _parse_anchor(anchor_s)
    today = datetime.now(timezone.utc).date()
    if anchor is None:
        anchor = today
        await set_setting(session, ANCHOR_KEY, anchor.isoformat())
        await session.commit()
    idx = _tonight_index(anchor, today, len(rot))
    return rot[idx], rot


def genre_ids_for_profile(p: Profile) -> list[int]:
    return [int(x) for x in p.genre_ids.split(",") if x.strip().isdigit()]


def title_excluded(title: str, exclude_csv: str) -> bool:
    title_l = (title or "").lower()
    for part in (exclude_csv or "").split(","):
        w = part.strip().lower()
        if w and w in title_l:
            return True
    return False


async def _fetch_discover_pool(
    p: Profile,
    *,
    seen_ids: set[int],
    max_pages: int = 6,
) -> dict[int, dict]:
    gids = genre_ids_for_profile(p)
    out: dict[int, dict] = {}
    pages = random.sample(range(1, 21), k=min(max_pages, 20))
    for page in pages:
        try:
            data = await discover_movies(
                genre_ids=gids,
                min_vote_average=p.min_vote_average,
                min_vote_count=p.min_vote_count,
                page=page,
            )
        except Exception:
            continue
        for m in data.get("results") or []:
            mid = m.get("id")
            tit = m.get("title") or m.get("original_title") or ""
            if not mid or mid in seen_ids:
                continue
            if title_excluded(tit, p.exclude_keywords):
                continue
            if mid not in out:
                out[mid] = m
    return out


async def suggest_tmdb_id_for_profile(
    session: AsyncSession,
    p: Profile,
    *,
    watchlist_bias: float = 0.28,
) -> int | None:
    seen_ids = set((await session.execute(select(SeenMovie.tmdb_id))).scalars().all())
    wl_rows = (
        await session.execute(select(WatchlistItem).order_by(WatchlistItem.added_at.desc()))
    ).scalars().all()
    wl_ids = [w.tmdb_id for w in wl_rows]

    if wl_ids and random.random() < watchlist_bias:
        random.shuffle(wl_ids)
        for tid in wl_ids[:12]:
            if tid in seen_ids:
                continue
            try:
                d = await movie_detail(tid)
            except Exception:
                continue
            tit = d.get("title") or d.get("original_title") or ""
            if title_excluded(tit, p.exclude_keywords):
                continue
            return tid

    pool = await _fetch_discover_pool(p, seen_ids=seen_ids)
    if not pool:
        try:
            data = await discover_movies(
                genre_ids=[],
                min_vote_average=max(6.5, p.min_vote_average - 0.3),
                min_vote_count=max(300, p.min_vote_count // 2),
                page=random.randint(1, 10),
            )
            for m in data.get("results") or []:
                mid = m.get("id")
                tit = m.get("title") or m.get("original_title") or ""
                if mid and mid not in seen_ids and not title_excluded(tit, p.exclude_keywords):
                    pool[mid] = m
        except Exception:
            pass

    if not pool:
        return None
    return random.choice(list(pool.keys()))


async def suggest_blended_tmdb_id(
    session: AsyncSession,
    profiles: list[Profile],
) -> int | None:
    seen_ids = set((await session.execute(select(SeenMovie.tmdb_id))).scalars().all())
    candidates: dict[int, dict] = {}

    async def fetch_for_profile(prof: Profile):
        pool = await _fetch_discover_pool(prof, seen_ids=seen_ids, max_pages=4)
        for mid, m in pool.items():
            if mid not in candidates:
                candidates[mid] = m

    await asyncio.gather(*[fetch_for_profile(p) for p in profiles])
    if not candidates:
        return None
    pick = random.choice(list(candidates.values()))
    return pick["id"]
