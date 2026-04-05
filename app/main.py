import random
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Annotated
from urllib.parse import urlencode

from dotenv import load_dotenv

# Project root .env (Windows-friendly; no need to set env vars in CMD manually)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.asset_links import router as asset_links_router
from app.context import configured_public_base_url, share_url_for_request, sync_mode_key
from app.db import SessionLocal, init_db
from app.models import AppSetting, Profile, SeenMovie, WatchlistItem
from app.suggest import (
    ANCHOR_KEY,
    ROTATION_SLUGS,
    suggest_blended_tmdb_id,
    suggest_tmdb_id_for_profile,
    tonight_profile,
)
from app.tmdb import movie_detail, movie_videos

templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with SessionLocal() as session:
        await _ensure_family_profiles(session)
        await session.commit()
    yield


app = FastAPI(title="Movie Night", lifespan=lifespan)
app.include_router(asset_links_router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def attach_sync_context(request: Request, call_next):
    request.state.sync_mode = sync_mode_key()
    request.state.share_url = share_url_for_request(request)
    return await call_next(request)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


@app.get("/health")
async def health():
    """Liveness + database connectivity for load balancers and monitors."""
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "unreachable"},
        )
    return {"status": "ok", "database": "ok"}


def _default_profiles() -> list[Profile]:
    # Each person: TMDB genre IDs (see Tastes page). Edit per family in the app.
    return [
        Profile(
            slug="dad",
            display_name="Dad",
            genre_ids="80,28,18",  # Crime, Action, Drama — adjust in Tastes
            min_vote_average=7.0,
            min_vote_count=600,
            rotation_order=0,
            exclude_keywords="",
        ),
        Profile(
            slug="mom",
            display_name="Mom",
            genre_ids="10749,35,18",  # Romance, Comedy, Drama — adjust in Tastes
            min_vote_average=6.9,
            min_vote_count=700,
            rotation_order=1,
            exclude_keywords="",
        ),
        Profile(
            slug="son",
            display_name="Son",
            genre_ids="878,53,9648,16",  # Sci-Fi, Thriller, Mystery, Animation — adjust in Tastes
            min_vote_average=7.0,
            min_vote_count=400,
            rotation_order=2,
            exclude_keywords="",
        ),
    ]


async def _ensure_family_profiles(session: AsyncSession) -> None:
    existing = (await session.execute(select(Profile.slug))).scalars().all()
    existing_set = set(existing)
    for p in _default_profiles():
        if p.slug not in existing_set:
            session.add(p)
            existing_set.add(p.slug)
    rot_rows = (
        await session.execute(select(Profile).where(Profile.slug.in_(ROTATION_SLUGS)))
    ).scalars().all()
    for i, slug in enumerate(ROTATION_SLUGS):
        row = next((r for r in rot_rows if r.slug == slug), None)
        if row is not None and row.rotation_order is None:
            row.rotation_order = i


@app.get("/sync", response_class=HTMLResponse)
async def sync_page(request: Request):
    return templates.TemplateResponse(
        "sync.html",
        {
            "request": request,
            "public_base_configured": bool(configured_public_base_url()),
        },
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session: SessionDep):
    all_profiles = (await session.execute(select(Profile).order_by(Profile.display_name))).scalars().all()
    tonight_p, rotation = await tonight_profile(session)
    idx = rotation.index(tonight_p) if tonight_p and tonight_p in rotation else 0
    next_picker = rotation[(idx + 1) % len(rotation)] if tonight_p and rotation else None
    anchor_s = (
        await session.execute(select(AppSetting).where(AppSetting.key == ANCHOR_KEY))
    ).scalar_one_or_none()
    anchor_val = anchor_s.value if anchor_s else ""

    seen_total = (await session.execute(select(func.count(SeenMovie.id)))).scalar_one()
    seen_rows = (
        await session.execute(select(SeenMovie).order_by(SeenMovie.marked_at.desc()).limit(30))
    ).scalars().all()
    wl = (
        await session.execute(select(WatchlistItem).order_by(WatchlistItem.added_at.desc()).limit(20))
    ).scalars().all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "profiles": all_profiles,
            "rotation": rotation,
            "tonight": tonight_p,
            "next_picker": next_picker,
            "anchor_date": anchor_val,
            "seen_movies": seen_rows,
            "seen_total": seen_total,
            "watchlist": wl,
        },
    )


@app.post("/rotation/anchor")
async def set_rotation_anchor(
    session: SessionDep,
    anchor_date: Annotated[str, Form()],
):
    d = date.fromisoformat(anchor_date.strip())
    row = (
        await session.execute(select(AppSetting).where(AppSetting.key == ANCHOR_KEY))
    ).scalar_one_or_none()
    if row is None:
        session.add(AppSetting(key=ANCHOR_KEY, value=d.isoformat()))
    else:
        row.value = d.isoformat()
    await session.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/suggest/watchlist")
async def suggest_from_watchlist(session: SessionDep):
    seen_ids = set((await session.execute(select(SeenMovie.tmdb_id))).scalars().all())
    wl = (await session.execute(select(WatchlistItem))).scalars().all()
    candidates = [w for w in wl if w.tmdb_id not in seen_ids]
    if not candidates:
        return RedirectResponse(url="/?err=watchlist_empty", status_code=303)
    pick = random.choice(candidates)
    return RedirectResponse(url=f"/movie/{pick.tmdb_id}?from=watchlist", status_code=303)


@app.post("/tonight")
async def suggest_tonight(session: SessionDep):
    tonight_p, _ = await tonight_profile(session)
    if tonight_p is None:
        return RedirectResponse(url="/?err=no_rotation", status_code=303)
    tid = await suggest_tmdb_id_for_profile(session, tonight_p)
    if tid is None:
        return RedirectResponse(url="/?err=no_movies", status_code=303)
    return RedirectResponse(url=f"/movie/{tid}?from=tonight", status_code=303)


@app.post("/suggest")
async def suggest_custom(
    session: SessionDep,
    audience: Annotated[list[str] | None, Form()] = None,
):
    audience = audience or []
    if not audience:
        return RedirectResponse(url="/?err=no_audience", status_code=303)
    profiles = (
        await session.execute(select(Profile).where(Profile.slug.in_(audience)))
    ).scalars().all()
    if not profiles:
        return RedirectResponse(url="/?err=bad_audience", status_code=303)
    tid = await suggest_blended_tmdb_id(session, profiles)
    if tid is None:
        return RedirectResponse(url="/?err=no_movies", status_code=303)
    q = urlencode([("from", "custom")] + [("audience", s) for s in audience])
    return RedirectResponse(url=f"/movie/{tid}?{q}", status_code=303)


def _youtube_trailer_url(videos_payload: dict) -> str | None:
    results = videos_payload.get("results") or []
    trailers = [v for v in results if (v.get("type") or "").lower() == "trailer"]
    youtube = [v for v in trailers if (v.get("site") or "").lower() == "youtube"]
    pick = None
    if youtube:
        pick = next((v for v in youtube if "official" in (v.get("name") or "").lower()), youtube[0])
    else:
        yt_any = [v for v in results if (v.get("site") or "").lower() == "youtube"]
        if yt_any:
            pick = yt_any[0]
    if not pick:
        return None
    key = pick.get("key")
    if not key:
        return None
    return f"https://www.youtube.com/embed/{key}?rel=0"


def _runtime_str(runtime_min: int | None) -> str | None:
    if not runtime_min or runtime_min <= 0:
        return None
    h, m = divmod(runtime_min, 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m} min"


@app.get("/movie/{tmdb_id}", response_class=HTMLResponse)
async def movie_page(request: Request, tmdb_id: int, session: SessionDep):
    try:
        detail = await movie_detail(tmdb_id)
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": str(e)},
            status_code=502,
        )
    try:
        vids = await movie_videos(tmdb_id)
        trailer_url = _youtube_trailer_url(vids)
    except Exception:
        trailer_url = None

    seen = (
        await session.execute(select(SeenMovie).where(SeenMovie.tmdb_id == tmdb_id))
    ).scalar_one_or_none()
    on_wl = (
        await session.execute(select(WatchlistItem).where(WatchlistItem.tmdb_id == tmdb_id))
    ).scalar_one_or_none()
    tonight_p, rotation = await tonight_profile(session)
    blend_audience = request.query_params.getlist("audience")
    backdrop_url = None
    if detail.get("backdrop_path"):
        backdrop_url = f"https://image.tmdb.org/t/p/w780{detail['backdrop_path']}"

    return templates.TemplateResponse(
        "movie.html",
        {
            "request": request,
            "m": detail,
            "seen": seen is not None,
            "on_watchlist": on_wl is not None,
            "trailer_url": trailer_url,
            "runtime_display": _runtime_str(detail.get("runtime")),
            "tonight": tonight_p,
            "rotation": rotation,
            "blend_audience": blend_audience,
            "backdrop_url": backdrop_url,
        },
    )


@app.post("/seen/{tmdb_id}")
async def mark_seen(tmdb_id: int, session: SessionDep):
    try:
        detail = await movie_detail(tmdb_id)
    except Exception:
        return RedirectResponse(url=f"/movie/{tmdb_id}", status_code=303)
    title = detail.get("title") or detail.get("original_title") or "Unknown"
    existing = (
        await session.execute(select(SeenMovie).where(SeenMovie.tmdb_id == tmdb_id))
    ).scalar_one_or_none()
    if existing is None:
        session.add(SeenMovie(tmdb_id=tmdb_id, title=title))
    await session.execute(delete(WatchlistItem).where(WatchlistItem.tmdb_id == tmdb_id))
    await session.commit()
    return RedirectResponse(url=f"/movie/{tmdb_id}", status_code=303)


@app.post("/unseen/{tmdb_id}")
async def mark_unseen(tmdb_id: int, session: SessionDep):
    await session.execute(delete(SeenMovie).where(SeenMovie.tmdb_id == tmdb_id))
    await session.commit()
    return RedirectResponse(url=f"/movie/{tmdb_id}", status_code=303)


@app.post("/watchlist/{tmdb_id}")
async def add_watchlist(tmdb_id: int, session: SessionDep):
    try:
        detail = await movie_detail(tmdb_id)
    except Exception:
        return RedirectResponse(url=f"/movie/{tmdb_id}", status_code=303)
    title = detail.get("title") or detail.get("original_title") or "Unknown"
    existing = (
        await session.execute(select(WatchlistItem).where(WatchlistItem.tmdb_id == tmdb_id))
    ).scalar_one_or_none()
    if existing is None:
        session.add(WatchlistItem(tmdb_id=tmdb_id, title=title))
    await session.commit()
    return RedirectResponse(url=f"/movie/{tmdb_id}", status_code=303)


@app.post("/watchlist/{tmdb_id}/remove")
async def remove_watchlist(tmdb_id: int, session: SessionDep):
    await session.execute(delete(WatchlistItem).where(WatchlistItem.tmdb_id == tmdb_id))
    await session.commit()
    return RedirectResponse(url=f"/movie/{tmdb_id}", status_code=303)


@app.get("/profiles", response_class=HTMLResponse)
async def profiles_page(request: Request, session: SessionDep):
    rows = (
        await session.execute(
            select(Profile).order_by(Profile.rotation_order.asc().nulls_last(), Profile.display_name)
        )
    ).scalars().all()
    return templates.TemplateResponse(
        "profiles.html",
        {"request": request, "profiles": rows},
    )


@app.post("/profiles/{profile_id}")
async def profile_update(
    profile_id: int,
    session: SessionDep,
    display_name: Annotated[str, Form()],
    genre_ids: Annotated[str, Form()],
    min_vote_average: Annotated[float, Form()],
    min_vote_count: Annotated[int, Form()],
    rotation_order: Annotated[str | None, Form()] = None,
    exclude_keywords: Annotated[str | None, Form()] = None,
):
    row = (
        await session.execute(select(Profile).where(Profile.id == profile_id))
    ).scalar_one_or_none()
    if row is None:
        return RedirectResponse(url="/profiles", status_code=303)
    row.display_name = display_name.strip()[:128]
    row.genre_ids = genre_ids.strip()[:256]
    row.min_vote_average = float(min_vote_average)
    row.min_vote_count = int(min_vote_count)
    row.exclude_keywords = (exclude_keywords or "").strip()[:512]
    ro = (rotation_order or "").strip()
    row.rotation_order = int(ro) if ro.isdigit() else None
    await session.commit()
    return RedirectResponse(url="/profiles", status_code=303)


@app.post("/shuffle/{tmdb_id}")
async def shuffle_same_profile(request: Request, tmdb_id: int, session: SessionDep):
    q = request.query_params.get("from") or ""
    if q == "tonight":
        tonight_p, _ = await tonight_profile(session)
        if tonight_p is None:
            return RedirectResponse(url="/", status_code=303)
        tid = await suggest_tmdb_id_for_profile(session, tonight_p)
        if tid is None or tid == tmdb_id:
            for _ in range(4):
                tid = await suggest_tmdb_id_for_profile(session, tonight_p)
                if tid and tid != tmdb_id:
                    break
        if tid is None:
            return RedirectResponse(url="/movie/%d?from=tonight&err=no_alt" % tmdb_id, status_code=303)
        return RedirectResponse(url=f"/movie/{tid}?from=tonight", status_code=303)
    if q == "watchlist":
        seen_ids = set((await session.execute(select(SeenMovie.tmdb_id))).scalars().all())
        wl = (await session.execute(select(WatchlistItem))).scalars().all()
        candidates = [w for w in wl if w.tmdb_id not in seen_ids and w.tmdb_id != tmdb_id]
        if not candidates:
            return RedirectResponse(url=f"/movie/{tmdb_id}?from=watchlist&err=no_alt", status_code=303)
        pick = random.choice(candidates)
        return RedirectResponse(url=f"/movie/{pick.tmdb_id}?from=watchlist", status_code=303)
    if q == "custom":
        audience = request.query_params.getlist("audience")
        if not audience:
            return RedirectResponse(url="/", status_code=303)
        profiles = (
            await session.execute(select(Profile).where(Profile.slug.in_(audience)))
        ).scalars().all()
        if not profiles:
            return RedirectResponse(url="/", status_code=303)
        tid = None
        for _ in range(6):
            cand = await suggest_blended_tmdb_id(session, profiles)
            if cand and cand != tmdb_id:
                tid = cand
                break
        if tid is None:
            qfail = urlencode([("from", "custom"), ("err", "no_alt")] + [("audience", s) for s in audience])
            return RedirectResponse(url=f"/movie/{tmdb_id}?{qfail}", status_code=303)
        qstr = urlencode([("from", "custom")] + [("audience", s) for s in audience])
        return RedirectResponse(url=f"/movie/{tid}?{qstr}", status_code=303)
    return RedirectResponse(url="/", status_code=303)
