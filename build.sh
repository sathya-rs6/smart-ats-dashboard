#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create necessary directories at the root level (relative to the project root)
mkdir -p models
mkdir -p uploads/resumes
mkdir -p logs

# Ensure the app can write to its log file
touch logs/app.log
chmod -R 777 logs
chmod -R 777 uploads
chmod -R 777 models

echo "Build pipeline complete. No additional build steps required for the static frontend."
