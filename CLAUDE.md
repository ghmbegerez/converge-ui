# CLAUDE.md — converge-ui

## Project Overview

Control plane UI for operating `converge` + `converge-orchestrator`. React/Vite SPA served by a FastAPI BFF (Backend-for-Frontend) that aggregates upstream services with caching, fallback, and demo modes.

## Commands

```bash
# Install
pip install -e ".[dev]"

# Run backend (default: http://127.0.0.1:9988)
converge-ui

# Run frontend dev
cd frontend && npm install && npm run dev

# Build frontend for production
cd frontend && npm run build

# Run tests
python -m pytest tests/ -v --tb=short
cd frontend && npm test -- --run

# Lint (requires ruff)
ruff check src/ tests/
ruff format --check src/ tests/
```

## Architecture

```
src/converge_ui/
├── app.py              # FastAPI app composition + lifespan
├── main.py             # CLI entry point
├── http.py             # HTTP utilities
├── logging.py          # Structured logging with emit()
├── observability.py    # Prometheus metrics (Histogram, RuntimeStats)
├── rate_limit.py       # Sliding-window rate limiter
├── config/             # Settings (Pydantic) and configuration
├── api/                # HTTP endpoints, auth, RBAC
├── bff/                # Backend-for-Frontend
│   ├── service.py      # Main aggregation: orchestrator + converge → unified view
│   ├── helpers.py      # Helpers: operator actions, service status, alerts
│   ├── cache.py        # Snapshot cache with TTL
│   └── fixtures/       # Demo mode fixture data
├── clients/            # Upstream API clients
│   └── base.py         # ApiClient base with retry + latency tracking
├── core/               # Core business logic
└── web/                # Fallback HTML shell (when frontend/dist absent)

frontend/
├── src/
│   ├── components/     # ConnectivityBanner, DataTable, ErrorBoundary, LifecycleRail, StaleDataBanner
│   ├── pages/          # OverviewPage, OperationsPage, ReviewsPage, CompliancePage, JobPage, IntentPage
│   └── lib/            # hooks.ts, ui.ts, export.ts
├── package.json
└── vite.config.ts
```

### Key patterns

| Pattern | Detail |
|---------|--------|
| **BFF aggregation** | Single request fans out to orchestrator + converge, merges results |
| **Data modes** | `real` (live APIs), `demo` (fixture data), `hybrid` (fallback to demo on failure) |
| **Snapshot cache** | TTL-based cache with stale-while-revalidate fallback |
| **Contract tests** | Validate BFF against orchestrator and converge API shapes |

### Surfaces

```
/                  → OverviewPage
/operations        → OperationsPage
/reviews           → ReviewsPage
/compliance        → CompliancePage
/jobs/{job_id}     → JobPage
/intents/{intent_id} → IntentPage
```

## Environment variables

| Variable | Purpose |
|----------|---------|
| `CONVERGE_UI_HOST` | Bind host |
| `CONVERGE_UI_PORT` | Bind port (default `9988`) |
| `CONVERGE_BASE_URL` | Converge API URL |
| `ORCHESTRATOR_BASE_URL` | Orchestrator API URL |
| `CONVERGE_UI_DATA_MODE` | `hybrid` / `real` / `demo` |
| `CONVERGE_UI_TIMEOUT_SECONDS` | Upstream request timeout |
| `CONVERGE_UI_FRONTEND_DIST` | Path to frontend/dist |
| `CONVERGE_UI_CORS_ORIGINS` | Allowed CORS origins |
| `CONVERGE_UI_ENV` | `local` / `staging` / `production` / `test` |
| `CONVERGE_UI_AUTH_REQUIRED` | Enable API key auth |
| `CONVERGE_UI_API_KEYS` | API key registry |
| `CONVERGE_UI_RATE_LIMIT_ENABLED` | Enable rate limiting |
| `CONVERGE_UI_RATE_LIMIT_RPM` | Requests per minute per IP |
| `CONVERGE_UI_TRUST_PROXY_HEADERS` | Trust X-Forwarded-For (behind reverse proxy) |
| `CONVERGE_UI_ALLOW_FALLBACK_UI` | Serve fallback HTML shell if dist missing |

## Testing

- Framework: pytest
- 13 test files covering 180 tests: API, auth, actions, rate limiting, settings, validation, hardening
- Contract tests validate BFF against orchestrator and converge API shapes
- Frontend tests: Vitest + React Testing Library
