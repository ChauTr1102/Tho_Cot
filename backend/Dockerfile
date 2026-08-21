# backend/Dockerfile
# FastAPI backend (Python 3.12). The BP-01 QA compliance pipeline itself lives
# in QA_checklist.py at the repo root and is run standalone, not through this
# API service.

FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps needed to build some Python wheels (kept minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the Playwright browser binaries + OS-level deps (chrome-headless-shell,
# Chromium) the extractor's crawler needs. `pip install playwright` above only
# installs the Python driver, not the actual browser executables.
RUN playwright install --with-deps chromium

# Copy application source
COPY . .

# Create a non-root user and hand over ownership of the app + data dir.
# Playwright's browsers were downloaded to root's cache above; move that
# cache under appuser's home so the non-root process can still launch them.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/data \
    && mkdir -p /home/appuser/.cache \
    && cp -r /root/.cache/ms-playwright /home/appuser/.cache/ms-playwright \
    && chown -R appuser:appuser /app /home/appuser/.cache/ms-playwright
USER appuser

# Data volume mount point (used by the Items demo feature)
VOLUME ["/app/data"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
