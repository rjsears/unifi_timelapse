#!/bin/bash
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# docker-entrypoint.api.sh
#
# Entrypoint script for UniFi Timelapse API
# Runs database migrations before starting the app
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting API server..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
