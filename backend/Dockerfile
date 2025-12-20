FROM python:3.13-slim AS builder

# Install uv
RUN pip install uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev dependencies)
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src/ src/

# Install the project
RUN uv sync --frozen --no-dev


FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code
COPY --from=builder /app/src /app/src

# Create data directories
RUN mkdir -p /app/data/images

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV PYTHONUNBUFFERED=1

# Default configuration (can be overridden)
ENV DATABASE_URL="sqlite+aiosqlite:///./data/stocks.db"
ENV IMAGE_DIR="/app/data/images"
ENV UVICORN_HOST="0.0.0.0"
ENV UVICORN_PORT="8000"
ENV UVICORN_WORKERS="4"

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "-m", "app"]