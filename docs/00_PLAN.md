# Plan converge-ui

## Objetivo
Crear el control plane para coordinar `converge` y `converge-orchestrator`.

## MVP mínimo (esta entrega)

1. API de salud:
- `GET /health/live`
- `GET /health/ready`

2. Dashboard base:
- `GET /v1/dashboard/summary`
- `GET /v1/dashboard/fleet`
- `GET /v1/dashboard/queue`

3. Integración inicial:
- Cliente `converge` (health + summary básico).
- Cliente `orchestrator` (fleet básico).

4. Estructura modular:
- `api/`, `clients/`, `core/`, `config/`.

## Próximos pasos

- Autenticación RBAC.
- Trazabilidad (`trace_id`) extremo a extremo.
- Páginas UI reales (frontend).
- Vista Merge Center con gate de converge.
