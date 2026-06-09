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

# Print emails to the console instead of sending them
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Refresh cookie does not need Secure flag in local dev (no HTTPS)
JWT_REFRESH_COOKIE_SECURE = False
JWT_REFRESH_COOKIE_SAMESITE = "Lax"

# Show full exception tracebacks in API error responses
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",  # enables the HTML browser UI
    ],
}
