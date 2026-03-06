# =============================================================================
# Multi-stage Dockerfile for converge-ui
# Stage 1: Build frontend with Node
# Stage 2: Run Python BFF serving built frontend
# =============================================================================

# --- Frontend build ---
FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# --- Python BFF ---
FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy source
COPY src/ src/
RUN pip install --no-cache-dir -e .

# Copy built frontend
COPY --from=frontend-build /frontend/dist /app/frontend/dist

# Non-root user
RUN useradd --create-home --shell /bin/bash ui
USER ui

EXPOSE 9988

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9988/health/live')"

ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["converge_ui.app:app", "--host", "0.0.0.0", "--port", "9988"]
