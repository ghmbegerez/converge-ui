# converge-ui

Control plane para operar `converge` + `converge-orchestrator`.

## Estado

- SPA React/Vite servida por FastAPI.
- Backend BFF con modos `real`, `hybrid` y `demo`.
- Superficies activas:
  - `/`
  - `/operations`
  - `/reviews`
  - `/compliance`
  - `/jobs/{job_id}`
  - `/intents/{intent_id}`
- Acciones operativas:
  - `refresh`
  - `retry job`
  - `request review`
  - `assign/complete/escalate/cancel review`

## Arquitectura

- `src/converge_ui/app.py`: composición de la app FastAPI.
- `src/converge_ui/bff/service.py`: agregación y fallback entre `converge` y `orchestrator`.
- `src/converge_ui/api/`: endpoints HTTP y auth.
- `src/converge_ui/web/`: shell fallback mínima.
- `frontend/`: SPA principal.

## Configuración

Variables relevantes:

- `CONVERGE_UI_HOST`
- `CONVERGE_UI_PORT`
- `CONVERGE_BASE_URL`
- `ORCHESTRATOR_BASE_URL`
- `CONVERGE_UI_DATA_MODE` = `hybrid` | `real` | `demo`
- `CONVERGE_UI_TIMEOUT_SECONDS`
- `CONVERGE_UI_FRONTEND_DIST`
- `CONVERGE_UI_CORS_ORIGINS`
- `CONVERGE_UI_ENV` = `local` | `staging` | `production` | `test`
- `CONVERGE_UI_AUTH_REQUIRED`
- `CONVERGE_UI_API_KEYS`
- `CONVERGE_UI_RATE_LIMIT_ENABLED`
- `CONVERGE_UI_RATE_LIMIT_RPM`
- `CONVERGE_UI_TRUST_PROXY_HEADERS`
- `CONVERGE_UI_ALLOW_FALLBACK_UI`

## Ejecutar backend

```bash
pip install -e ".[dev]"
converge-ui
```

Por defecto levanta en `http://127.0.0.1:9988`.

## Ejecutar frontend

```bash
cd frontend
npm install
npm run dev
```

Para producción, generar `frontend/dist`:

```bash
cd frontend
npm run build
```

Si no existe `frontend/dist`, FastAPI usa la shell fallback de `src/converge_ui/web/` solo cuando `CONVERGE_UI_ALLOW_FALLBACK_UI=1`. En producción, el comportamiento recomendado es deshabilitar ese fallback.

## Validación

```bash
pytest -q
cd frontend && npm test -- --run
cd frontend && npm run build
```

## Debug operativo

- `GET /api/v1/system/debug`
  - expone contadores internos mínimos del BFF para entender uso de fallback y acciones ejecutadas.
- `GET /metrics`
  - expone contadores internos del servicio en formato Prometheus.

## Producción detrás de proxy

- usar `CONVERGE_UI_TRUST_PROXY_HEADERS=1` solo si un reverse proxy confiable inyecta `X-Forwarded-For` o `Forwarded`.
- si el proceso recibe tráfico directo, mantener `CONVERGE_UI_TRUST_PROXY_HEADERS=0` para que el rate limiting no dependa de headers falsificables.

## Despliegue

Variables base:

```bash
cp .env.example .env
docker compose up --build
```

Runbook operativo:

- [RUNBOOK.md](/Users/ext-marcos.begerez/Documents/Prod/converge-ui/docs/RUNBOOK.md)
