#!/bin/bash
set -e

if [ "$RAILWAY_SERVICE_ROLE" = "worker" ]; then
  exec celery -A config.celery worker --loglevel=info --concurrency=2
elif [ "$RAILWAY_SERVICE_ROLE" = "beat" ]; then
  exec celery -A config.celery beat --loglevel=info
else
  python manage.py migrate --noinput
  # daphne serves both HTTP and WebSocket over the same port via ASGI.
  exec daphne -b 0.0.0.0 -p "${PORT:-8000}" config.asgi:application
fi
