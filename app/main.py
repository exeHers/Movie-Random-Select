import asyncio
import random
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal, init_db
from app.models import Profile, SeenMovie
from app.tmdb import discover_movies, movie_detail

templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with SessionLocal() as session:
        await _seed_profiles_if_empty(session)
        await session.commit()
    yield


app = FastAPI(title="Movie Night", lifespan=lifespan)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def _seed_profiles_if_empty(session: AsyncSession) -> None:
    result = await session.execute(select(Profile).limit(1))
    if result.scalar_one_or_none() is not None:
        return
    # TMDB genre ids: https://developer.themoviedb.org/reference/genre-movie-list
    defaults = [
        Profile(
            slug="parents",
            display_name="Parents",
            genre_ids="18,36,10749",  # drama, history, romance
            min_vote_average=7.0,
            min_vote_count=800,
        ),
        Profile(
            slug="you",
            display_name="You",
            genre_ids="878,53,9648",  # sci-fi, thriller, mystery
            min_vote_average=7.0,
            min_vote_count=400,
        ),
        Profile(
            slug="everyone",
            display_name="Everyone (lighter)",
            genre_ids="35,12,16",  # comedy, adventure, animation
            min_vote_average=6.8,
            min_vote_count=1200,
        ),
    ]
    session.add_all(defaults)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session: SessionDep):
    profiles = (await session.execute(select(Profile).order_by(Profile.display_name))).scalars().all()
    seen_total = (
        await session.execute(select(func.count(SeenMovie.id)))
    ).scalar_one()
    seen_rows = (
        await session.execute(select(SeenMovie).order_by(SeenMovie.marked_at.desc()).limit(50))
    ).scalars().all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "profiles": profiles,
            "seen_movies": seen_rows,
            "seen_total": seen_total,
        },
    )


@app.post("/suggest")
async def suggest(
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

    seen_ids = set(
        (await session.execute(select(SeenMovie.tmdb_id))).scalars().all()
    )

    candidates: dict[int, dict] = {}

    async def fetch_for_profile(p: Profile):
        gids = [int(x) for x in p.genre_ids.split(",") if x.strip().isdigit()]
        try:
            data = await discover_movies(
                genre_ids=gids,
                min_vote_average=p.min_vote_average,
                min_vote_count=p.min_vote_count,
                page=random.randint(1, 8),
            )
        except Exception:
            data = {"results": []}
        for m in data.get("results") or []:
            mid = m.get("id")
            if not mid or mid in seen_ids:
                continue
            if mid not in candidates:
                candidates[mid] = m

    await asyncio.gather(*[fetch_for_profile(p) for p in profiles])

    if not candidates:
        try:
            data = await discover_movies(
                genre_ids=[],
                min_vote_average=7.2,
                min_vote_count=2000,
                page=random.randint(1, 3),
            )
            for m in data.get("results") or []:
                mid = m.get("id")
                if mid and mid not in seen_ids:
                    candidates[mid] = m
        except Exception:
            pass

    if not candidates:
        return RedirectResponse(url="/?err=no_movies", status_code=303)

    pick = random.choice(list(candidates.values()))
    tmdb_id = pick["id"]
    return RedirectResponse(url=f"/movie/{tmdb_id}", status_code=303)


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
    seen = (
        await session.execute(select(SeenMovie).where(SeenMovie.tmdb_id == tmdb_id))
    ).scalar_one_or_none()
    return templates.TemplateResponse(
        "movie.html",
        {
            "request": request,
            "m": detail,
            "seen": seen is not None,
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
        await session.commit()
    return RedirectResponse(url=f"/movie/{tmdb_id}", status_code=303)


@app.post("/unseen/{tmdb_id}")
async def mark_unseen(tmdb_id: int, session: SessionDep):
    await session.execute(delete(SeenMovie).where(SeenMovie.tmdb_id == tmdb_id))
    await session.commit()
    return RedirectResponse(url=f"/movie/{tmdb_id}", status_code=303)
