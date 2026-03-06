"""API key authentication for converge-ui.

Modeled after orchestrator's auth pattern: API keys parsed from
``CONVERGE_UI_API_KEYS`` environment variable, validated via constant-time
comparison, with role-based access control.

Key format (comma-separated):
    key:role:actor

Roles: viewer, operator, admin
"""

from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

# ---------------------------------------------------------------------------
# Role hierarchy
# ---------------------------------------------------------------------------

ROLE_RANK: dict[str, int] = {"viewer": 0, "operator": 1, "admin": 2}

# Paths that bypass authentication entirely.
PUBLIC_PATHS: set[str] = {"/health/live", "/health/ready"}

# Minimum role required per route pattern.
API_ROLE_MAP: dict[str, str] = {
    "GET /api/v1/overview": "viewer",
    "GET /api/v1/operations": "viewer",
    "GET /api/v1/jobs": "viewer",
    "GET /api/v1/reviews": "viewer",
    "GET /api/v1/compliance": "viewer",
    "POST /api/v1/actions/refresh": "operator",
    "POST /api/v1/actions/jobs/*/retry": "operator",
    "POST /api/v1/actions/reviews": "operator",
    "POST /api/v1/actions/reviews/*/assign": "operator",
    "POST /api/v1/actions/reviews/*/complete": "operator",
    "POST /api/v1/actions/reviews/*/escalate": "operator",
    "POST /api/v1/actions/reviews/*/cancel": "operator",
}


@dataclass(frozen=True)
class Principal:
    """Authenticated identity resolved from an API key."""

    actor: str
    role: str

    def has_role(self, minimum: str) -> bool:
        return ROLE_RANK.get(self.role, -1) >= ROLE_RANK.get(minimum, 99)

    def to_dict(self) -> dict[str, Any]:
        return {"actor": self.actor, "role": self.role}


# ---------------------------------------------------------------------------
# Key registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _KeyEntry:
    key_hash: str
    role: str
    actor: str
    prefix: str  # first 4 chars for logging


_registry: list[_KeyEntry] = []
_auth_required: bool = False


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def init_auth() -> None:
    """Parse ``CONVERGE_UI_API_KEYS`` and ``CONVERGE_UI_AUTH_REQUIRED`` from environment."""
    global _registry, _auth_required

    _auth_required = os.environ.get("CONVERGE_UI_AUTH_REQUIRED", "0").lower() in (
        "1",
        "true",
        "yes",
    )

    raw = os.environ.get("CONVERGE_UI_API_KEYS", "")
    entries: list[_KeyEntry] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        segments = part.split(":")
        if len(segments) < 3:
            continue
        key, role, actor = segments[0], segments[1], segments[2]
        if role not in ROLE_RANK:
            continue
        entries.append(
            _KeyEntry(key_hash=_hash_key(key), role=role, actor=actor, prefix=key[:4])
        )
    _registry = entries


def is_auth_required() -> bool:
    return _auth_required


def resolve_principal(authorization: str | None) -> Principal | None:
    """Resolve an Authorization header to a Principal.

    Returns anonymous admin when auth is disabled.
    Raises ValueError if auth is required but the key is invalid.
    """
    if not _auth_required:
        return Principal(actor="anonymous", role="admin")

    if not authorization:
        raise ValueError("Missing Authorization header")

    token = authorization
    if token.lower().startswith("bearer "):
        token = token[7:]

    token_hash = _hash_key(token)
    for entry in _registry:
        if hmac.compare_digest(entry.key_hash, token_hash):
            return Principal(actor=entry.actor, role=entry.role)

    raise ValueError("Invalid API key")


def require_role(principal: Principal, minimum: str) -> None:
    """Raise ValueError if principal lacks the minimum role."""
    if not principal.has_role(minimum):
        raise ValueError(f"Insufficient role: {principal.role!r} < {minimum!r}")


def minimum_role_for(method: str, path: str) -> str:
    """Look up the minimum role required for a route."""
    key = f"{method} {path}"

    if key in API_ROLE_MAP:
        return API_ROLE_MAP[key]

    for pattern, role in API_ROLE_MAP.items():
        parts = pattern.split()
        if len(parts) == 2 and parts[0] == method:
            route_pattern = parts[1]
            if "*" in route_pattern:
                prefix = route_pattern.split("*")[0]
                if path.startswith(prefix):
                    return role

    for pattern, role in API_ROLE_MAP.items():
        parts = pattern.split()
        if len(parts) == 2 and parts[0] == method and path.startswith(parts[1]):
            return role

    return "admin"


class AuthMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that enforces API key authentication."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        method = request.method

        if path in PUBLIC_PATHS or path.startswith("/assets"):
            return await call_next(request)

        # SPA shell routes are public
        if method == "GET" and not path.startswith("/api/"):
            return await call_next(request)

        try:
            auth_header = request.headers.get("authorization") or request.headers.get(
                "x-api-key"
            )
            principal = resolve_principal(auth_header)
        except ValueError as exc:
            return JSONResponse(
                status_code=401,
                content={"error": str(exc)},
            )

        if principal is not None:
            min_role = minimum_role_for(method, path)
            if not principal.has_role(min_role):
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": f"Insufficient role: {principal.role!r} < {min_role!r}"
                    },
                )
            request.state.principal = principal

        return await call_next(request)
