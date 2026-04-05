#!/bin/bash

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p backend/models
mkdir -p uploads/resumes
mkdir -p logs

# Port configuration (Render passes PORT env var)
PORT=${PORT:-8000}

# Start the uvicorn server directly to serve both API and static files
echo "Starting FastAPI server on port $PORT..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
