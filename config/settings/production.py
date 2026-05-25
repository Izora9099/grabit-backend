"""
Production settings — PostgreSQL, locked-down CORS, Whitenoise for static files.
"""
from .base import *  # noqa: F401, F403
import dj_database_url
from decouple import config

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

DATABASES = {
    # Supabase transaction pooler (port 6543) — used for all live queries
    "default": dj_database_url.parse(
        config("SUPABASE_TRANSACTION_URI"),
        conn_max_age=600,
    ),
    # Supabase direct connection (port 5432) — used only for migrations
    "direct": dj_database_url.parse(
        config("SUPABASE_DIRECT_URI"),
        conn_max_age=0,
    ),
}

CORS_ALLOWED_ORIGINS = [
    "https://grabit.sale",
    "https://grab-it.ndifonlemuel.workers.dev",
]

# Whitenoise serves compressed static files without a CDN
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # must be right after SecurityMiddleware
    *MIDDLEWARE[2:],  # noqa: F405
]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
}

# Supabase Storage — S3-compatible object storage
AWS_STORAGE_BUCKET_NAME = "grabit-media"
AWS_S3_ENDPOINT_URL = config("SUPABASE_STORAGE_URL")
AWS_ACCESS_KEY_ID = config("SUPABASE_STORAGE_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = config("SUPABASE_STORAGE_SECRET_KEY")
AWS_S3_REGION_NAME = config("SUPABASE_STORAGE_REGION", default="auto")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "public-read"
AWS_QUERYSTRING_AUTH = False

# Email (configure your SMTP provider here)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.sendgrid.net")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@grabit.cm")

# Security hardening
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = False  # Railway terminates HTTPS at the proxy; Django must not also redirect
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
