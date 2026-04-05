#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create necessary directories for runtime
mkdir -p backend/models
mkdir -p uploads/resumes
mkdir -p logs

# Note: frontend_v2/dist is pre-built and included in the repo.
echo "Build pipeline complete. No additional build steps required for the static frontend."
