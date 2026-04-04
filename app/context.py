import os

from starlette.requests import Request

from app.db import is_postgres_backend


def configured_public_base_url() -> str:
    return os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")


def share_url_for_request(request: Request) -> str:
    fixed = configured_public_base_url()
    if fixed:
        return fixed
    return str(request.base_url).rstrip("/")


def sync_mode_key() -> str:
    return "shared" if is_postgres_backend() else "local"
