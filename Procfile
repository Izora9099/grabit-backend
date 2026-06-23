web: python manage.py migrate --noinput && gunicorn config.wsgi --workers 3 --timeout 60 --log-file -
worker: celery -A config.celery worker --loglevel=info --concurrency=2
beat: celery -A config.celery beat --loglevel=info
