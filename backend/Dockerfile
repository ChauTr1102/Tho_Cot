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

# System deps needed to build some Python wheels, plus ffmpeg/ffprobe —
# app/services/studio/assemble.py shells out to both as bare PATH commands
# (concat/re-encode the master video, mux the voiceover, render the subtitle
# overlay) and neither was ever installed here, so every voiceover/video node
# failed with FileNotFoundError: 'ffmpeg' the first time a full run reached
# them. The standard Debian package includes libx264 + aac, which is all
# this module's codecs need (see its module docstring) — no custom build.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl ffmpeg \
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
    && chown -R appuser:appuser /app /home/appuser/.cache/ms-playwright \
    && chmod +x /app/docker-entrypoint.sh

# Deliberately NOT `USER appuser` here: docker-compose.yml bind-mounts a host
# directory over /app/data, which replaces this build-time chown with
# whatever ownership the host directory happens to have (root, in the common
# case of a directory created by `docker compose up` under sudo). The
# container must start as root so the entrypoint can fix that mount's
# ownership on every start, then it drops to appuser itself before running
# the app — see docker-entrypoint.sh.

# Data volume mount point (used by the Items demo feature)
VOLUME ["/app/data"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
