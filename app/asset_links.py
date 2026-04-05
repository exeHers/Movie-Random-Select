"""
Digital Asset Links for Trusted Web Activity (Android Studio / Bubblewrap APK).

Google verifies your APK signing cert against this JSON at:
  https://<your-domain>/.well-known/assetlinks.json

Set ANDROID_TWA_PACKAGE and ANDROID_TWA_SHA256 on the server (e.g. Render env).
"""

import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

router = APIRouter(tags=["twa"])


def _parse_sha256_fingerprints(raw: str) -> list[str]:
    """Accept comma/newline-separated SHA-256 fingerprints (keytool format)."""
    out: list[str] = []
    for line in raw.replace(",", "\n").splitlines():
        s = line.strip().upper()
        if not s:
            continue
        for prefix in ("SHA256:", "SHA-256:"):
            if s.startswith(prefix):
                s = s[len(prefix) :].strip()
                break
        if s:
            out.append(s)
    return out


@router.get("/.well-known/assetlinks.json", include_in_schema=False)
def asset_links_json():
    package = os.environ.get("ANDROID_TWA_PACKAGE", "").strip()
    fps = _parse_sha256_fingerprints(os.environ.get("ANDROID_TWA_SHA256", ""))
    if not package or not fps:
        return Response(status_code=404)
    payload = [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": package,
                "sha256_cert_fingerprints": fps,
            },
        }
    ]
    return JSONResponse(
        content=payload,
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=3600"},
    )
