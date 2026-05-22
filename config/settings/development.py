"""
Development settings — SQLite, permissive CORS, verbose errors.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Allow all origins in dev so the React dev server (any port) can connect
CORS_ALLOW_ALL_ORIGINS = True

# Print emails to the console instead of sending them
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Show full exception tracebacks in API error responses
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",  # enables the HTML browser UI
    ],
}
