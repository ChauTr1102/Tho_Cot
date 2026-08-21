#!/bin/bash
set -euo pipefail

# Always resolve paths relative to this script, so both `./run.sh` from the
# backend directory and `./backend/run.sh` from the repository root work.
BACKEND_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ENV="$BACKEND_DIR/env"

if [ ! -x "$BACKEND_ENV/bin/python" ]; then
    echo "Creating backend virtual environment..."
    python3 -m venv "$BACKEND_ENV"
fi

# Repair incomplete environments before starting the application.
if ! "$BACKEND_ENV/bin/python" -c "import pydantic_settings, uvicorn" >/dev/null 2>&1; then
    echo "Installing backend dependencies..."
    "$BACKEND_ENV/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"
fi

cd "$BACKEND_DIR"
echo "Starting FastAPI server on http://localhost:8000 ..."
exec "$BACKEND_ENV/bin/python" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
