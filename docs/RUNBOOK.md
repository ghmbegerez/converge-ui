# converge-ui Runbook

## Objetivo

Operar `converge-ui` como control plane de `converge` y `converge-orchestrator`.

## Arranque local

```bash
pip install -e ".[dev]"
converge-ui
```

Frontend:

```bash
cd frontend
npm install
npm run build
```

## Arranque con Docker

```bash
cp .env.example .env
docker compose up --build
```

Servicios esperados:

- `converge` -> `9876`
- `orchestrator` -> `9989` publicado, `8787` interno
- `ui` -> `9988`

## Health checks

- liveness: `GET /health/live`
- readiness: `GET /health/ready`
- debug BFF: `GET /api/v1/system/debug`
- metrics: `GET /metrics`

## Fallos comunes

### 1. `/` devuelve `503 frontend_unavailable`

Causa:
- no existe `frontend/dist`
- `CONVERGE_UI_ALLOW_FALLBACK_UI=0`

Acción:
1. construir frontend
2. verificar `CONVERGE_UI_FRONTEND_DIST`
3. habilitar fallback solo en entornos no productivos

### 2. `/health/ready` devuelve `degraded`

Causa:
- `converge` u `orchestrator` no responden

Acción:
1. revisar conectividad a `CONVERGE_BASE_URL`
2. revisar conectividad a `ORCHESTRATOR_BASE_URL`
3. consultar `/api/v1/overview` para confirmar `services.*.reachable`

### 3. Muchas respuestas `429`

Causa:
- rate limiting activo

Acción:
1. revisar `CONVERGE_UI_RATE_LIMIT_RPM`
2. revisar si hay clientes/polling excesivo
3. consultar `GET /api/v1/system/debug`
4. validar `CONVERGE_UI_TRUST_PROXY_HEADERS` si el despliegue está detrás de reverse proxy

### 4. UI en `demo` o `stale-cache`

Causa:
- upstream caído o timeout

Acción:
1. revisar `GET /api/v1/system/debug`
2. revisar logs `upstream.call`
3. confirmar si el modo configurado es `hybrid`, `real` o `demo`

## Señales mínimas a mirar

1. `GET /health/live`
2. `GET /health/ready`
3. `GET /api/v1/system/debug`
4. `GET /metrics`
5. logs JSON:
   - `http.request`
   - `http.response`
   - `upstream.call`
   - `rate_limit.exceeded`

## Política recomendada

- `production`: `CONVERGE_UI_ALLOW_FALLBACK_UI=0`
- `production`: `CONVERGE_UI_TRUST_PROXY_HEADERS=1` solo si hay reverse proxy confiable
- `staging`: fallback permitido solo para pruebas controladas
- `local`: fallback permitido

## Recuperación básica

1. si solo falla el frontend compilado:
   - reconstruir `frontend/dist`
2. si falla un upstream:
   - mantener `hybrid` si necesitas continuidad operativa
3. si el BFF degrada de forma sostenida:
   - revisar latencia/timeouts upstream
   - revisar logs `upstream.call`
