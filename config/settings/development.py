"""
Development settings — SQLite by default, permissive CORS, verbose errors.

Note: allauth (Google OAuth) uses JSONField which requires SQLite >= 3.38.
If your local SQLite is older, set LOCAL_DB_URL in .env to a PostgreSQL URL:
  LOCAL_DB_URL=postgresql://user:pass@localhost/grabit
"""
from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = True

ALLOWED_HOSTS = ["*"]

# SQLite < 3.38 triggers a JSONField system check error but works in practice
# for allauth's usage. Silence it in dev; production uses PostgreSQL which
# has full JSONField support.
SILENCED_SYSTEM_CHECKS = ["fields.E180"]

_local_db_url = config("LOCAL_DB_URL", default="")

if _local_db_url:
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(_local_db_url)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Allow all origins in dev so the React dev server (any port) can connect
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Mailtrap — HTTP API (avoids SMTP port issues in any environment)
EMAIL_BACKEND = "accounts.email_backend.MailtrapAPIBackend"
MAILTRAP_API_TOKEN = config("MAILTRAP_API_TOKEN", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@grabit.sale")

# Refresh cookie does not need Secure flag in local dev (no HTTPS)
JWT_REFRESH_COOKIE_SECURE = False
JWT_REFRESH_COOKIE_SAMESITE = "Lax"

# Generate a manifest during collectstatic so production's CompressedManifestStaticFilesStorage
# can find hashed filenames at runtime.
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

# Use in-memory channel layer locally if Redis is not running.
# WebSocket tracking won't work, but all REST endpoints will.
import redis as _redis_lib
_redis_url = config("REDIS_URL", default="redis://localhost:6379/0")
try:
    _r = _redis_lib.from_url(_redis_url, socket_connect_timeout=1)
    _r.ping()
except Exception:
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }

# Run Celery tasks synchronously in dev — analytics events write immediately
# without needing a Redis broker or worker process running locally.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = False  # swallow task exceptions so broker errors don't crash views

# Show full exception tracebacks in API error responses
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",  # enables the HTML browser UI
    ],
}
