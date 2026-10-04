#!/bin/bash
set -e

export DJANGO_SETTINGS_MODULE=config.settings.production

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting application server on port ${PORT:-8000}..."
exec gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --workers 4 --timeout 120
