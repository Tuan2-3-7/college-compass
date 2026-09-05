"""Minimal in-process rate limiting.

Deliberately dependency-free: a free-tier deployment runs one instance, where
an in-memory sliding window is correct and costs nothing. If the app is ever
scaled to multiple instances, replace the store with Redis - the limiter is
called from one place (the middleware) so that swap stays small.

Protects two things:
- auth endpoints, against password brute-forcing
- AI endpoints, against one user exhausting a free LLM tier or running up a bill
"""

import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from .config import settings

_hits: dict[str, deque] = defaultdict(deque)

# path prefix -> which limit applies
LIMITED_PATHS = {
    "/api/auth/login": "auth",
    "/api/auth/register": "auth",
    "/api/tutor/chat": "ai",
}
AI_PATH_MARKERS = ("/analyze",)  # essay analysis lives under /api/essays/.../analyze


def _limit_for(path: str) -> tuple[str, int] | None:
    for prefix, kind in LIMITED_PATHS.items():
        if path.startswith(prefix):
            return kind, settings.rate_limit_auth if kind == "auth" else settings.rate_limit_ai
    if any(marker in path for marker in AI_PATH_MARKERS):
        return "ai", settings.rate_limit_ai
    return None


def client_key(request: Request, kind: str) -> str:
    """Identify the caller. Honours X-Forwarded-For, since deployments sit
    behind a proxy where request.client is the proxy itself."""
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() if forwarded else (
        request.client.host if request.client else "unknown"
    )
    return f"{kind}:{ip}"


async def rate_limit_middleware(request: Request, call_next):
    limit_spec = _limit_for(request.url.path)
    if limit_spec is None or request.method == "OPTIONS":
        return await call_next(request)

    kind, limit = limit_spec
    key = client_key(request, kind)
    window = settings.rate_limit_window_seconds
    now = time.monotonic()

    hits = _hits[key]
    while hits and now - hits[0] > window:
        hits.popleft()

    if len(hits) >= limit:
        retry_after = int(window - (now - hits[0])) + 1
        return JSONResponse(
            status_code=429,
            content={"detail": f"Too many requests. Try again in {retry_after} seconds."},
            headers={"Retry-After": str(retry_after)},
        )

    hits.append(now)
    return await call_next(request)


def reset() -> None:
    """Clear all counters - used by tests."""
    _hits.clear()
