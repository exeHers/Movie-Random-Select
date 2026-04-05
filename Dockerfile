# Optional: deploy on Render, Fly.io, Koyeb, VPS, etc.
# Build: docker build -t movie-night .
# Run:   docker run -p 8000:8000 -e TMDB_API_KEY=... -e DATABASE_URL=... -e PUBLIC_BASE_URL=... -e PORT=8000 movie-night

FROM python:3.12-slim-bookworm

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY templates ./templates
COPY static ./static

EXPOSE 8000

# Hosts like Render/Fly set PORT; default 8000 for local docker run
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
