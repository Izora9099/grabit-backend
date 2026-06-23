#!/bin/bash
set -e

if [ "$RAILWAY_SERVICE_ROLE" = "worker" ]; then
  exec celery -A config.celery worker --loglevel=info --concurrency=2
elif [ "$RAILWAY_SERVICE_ROLE" = "beat" ]; then
  exec celery -A config.celery beat --loglevel=info
else
  python manage.py migrate --noinput
  exec gunicorn config.wsgi --workers 3 --timeout 60 --log-file -
fi
