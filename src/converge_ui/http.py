from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response as StarletteResponse

from converge_ui.logging import emit
from converge_ui.rate_limit import check_rate_limit, get_remaining


def client_ip_for_request(request: Request, *, trust_proxy_headers: bool) -> str:
    if trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            first = forwarded.split(",")[0].strip()
            if first:
                return first
        forwarded_header = request.headers.get("forwarded", "")
        if forwarded_header:
            parts = forwarded_header.split(";")
            for part in parts:
                item = part.strip()
                if item.startswith("for="):
                    return item[4:].strip("\"")
    return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> StarletteResponse:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, trust_proxy_headers: bool = False) -> None:
        super().__init__(app)
        self.trust_proxy_headers = trust_proxy_headers

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> StarletteResponse:
        client_ip = client_ip_for_request(request, trust_proxy_headers=self.trust_proxy_headers)
        path = request.url.path
        if not check_rate_limit(client_ip, path):
            remaining = get_remaining(client_ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"X-RateLimit-Remaining": str(remaining)},
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(get_remaining(client_ip))
        return response


@asynccontextmanager
async def app_lifespan(_app):
    emit("app.starting", {})
    yield
    emit("app.stopping", {})
