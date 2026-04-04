# Movie Night — family movie suggester

Small web app: pick who is watching (parents / you / everyone), get a random **unseen** film from [The Movie Database (TMDB)](https://www.themoviedb.org/), then **Mark as seen** so it does not come up again.

## Setup

1. Create a free TMDB API key: [Account settings → API](https://www.themoviedb.org/settings/api).
2. Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export TMDB_API_KEY=your_key_here
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Data is stored in `data/movie_night.sqlite` (gitignored).

## Customize tastes

Default “audience” profiles are seeded in `app/main.py` (`_seed_profiles_if_empty`). Edit **genre IDs** and score thresholds there, or change the `Profile` rows in the database. TMDB genre list: [genre movie list](https://developer.themoviedb.org/reference/genre-movie-list).
