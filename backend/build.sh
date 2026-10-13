#!/usr/bin/env bash
# Render build script for Django backend
# This runs on every deploy (before the web service starts)

set -o errexit  # Exit immediately on any error

# Install Python dependencies
pip install -r requirements.txt

# Collect static files (WhiteNoise will serve them)
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
