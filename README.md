# converge-ui

Control plane alpha para operar `converge` + `converge-orchestrator`.

## Qué incluye

- Backend FastAPI tipo BFF para agregar y degradar datos de `converge` y `converge-orchestrator`.
- Endpoints UI-oriented bajo `/api/v1/...`.
- Modo `hybrid` por defecto: usa datos reales cuando existen y cae a dataset demo cuando faltan servicios o endpoints.
- Shell frontend servida por FastAPI con vistas:
  - `/`
  - `/operations`
  - `/jobs/{job_id}`
- Scaffold de SPA React/Vite en `frontend/` para evolucionar la interfaz sin reestructurar el repo.

## Configuración

Variables relevantes:

- `CONVERGE_UI_HOST`
- `CONVERGE_UI_PORT`
- `CONVERGE_BASE_URL`
- `ORCHESTRATOR_BASE_URL`
- `CONVERGE_UI_DATA_MODE` = `hybrid` | `real` | `demo`
- `CONVERGE_UI_TIMEOUT_SECONDS`
- `CONVERGE_UI_FRONTEND_DIST`

## Ejecutar

```bash
pip install -e .
converge-ui
```

Por defecto levanta en `http://127.0.0.1:9988`.

## Frontend SPA

El repo incluye un frontend en `frontend/` con Vite + React + TypeScript.

```bash
cd frontend
npm install
npm run dev
```

Mientras no exista `frontend/dist`, FastAPI sirve una shell estática de fallback ubicada en `src/converge_ui/web/`.
