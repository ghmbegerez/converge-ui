FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CONVERGE_UI_HOST=0.0.0.0 \
    CONVERGE_UI_PORT=9988 \
    CONVERGE_UI_ENV=production \
    CONVERGE_UI_FRONTEND_DIST=/app/frontend/dist \
    CONVERGE_UI_ALLOW_FALLBACK_UI=0

COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install .

COPY --from=frontend-build /frontend/dist /app/frontend/dist

RUN useradd --create-home --shell /bin/bash ui
USER ui

EXPOSE 9988

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9988/health/live')"

CMD ["python", "-m", "uvicorn", "converge_ui.app:app", "--host", "0.0.0.0", "--port", "9988"]
