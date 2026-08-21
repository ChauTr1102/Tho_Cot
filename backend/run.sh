#!/bin/bash
# Script to run FastAPI backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "Starting FastAPI server on http://localhost:8000 ..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
