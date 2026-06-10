"""
Production settings — PostgreSQL, locked-down CORS, Whitenoise for static files.
"""
from .base import *  # noqa: F401, F403
import dj_database_url
from decouple import config, Csv

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
    "http://localhost:3000",
    "http://localhost:5173",
]
CORS_ALLOW_CREDENTIALS = True  # needed for HttpOnly cookie to be sent cross-origin

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

# Cloudflare R2 — S3-compatible object storage
# django-storages stores DB paths WITHOUT the location prefix but re-adds it in url().
# AWS_LOCATION must match the prefix used when files were originally uploaded ('grabit-media'),
# otherwise url() generates the wrong path and all existing files 404.
AWS_STORAGE_BUCKET_NAME  = config('R2_BUCKET_NAME')
AWS_S3_ENDPOINT_URL      = config('R2_ENDPOINT_URL')
AWS_ACCESS_KEY_ID        = config('R2_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY    = config('R2_SECRET_ACCESS_KEY')
AWS_S3_REGION_NAME       = 'auto'
AWS_S3_FILE_OVERWRITE    = False
AWS_DEFAULT_ACL          = 'public-read'
AWS_QUERYSTRING_AUTH     = False
AWS_LOCATION             = 'grabit-media'
AWS_S3_CUSTOM_DOMAIN     = config('R2_PUBLIC_URL').replace('https://', '')

# Email (configure your SMTP provider here)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.sendgrid.net")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@grabit.cm")

# ── Security hardening ────────────────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = False          # Railway terminates HTTPS at the proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# HSTS — tell browsers to only use HTTPS for 1 year, include subdomains
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# JWT refresh cookie must also be Secure in production
JWT_REFRESH_COOKIE_SECURE = True
JWT_REFRESH_COOKIE_SAMESITE = "Strict"

# Fapshi webhook — HMAC secret for request signature verification
FAPSHI_WEBHOOK_SECRET = config("FAPSHI_WEBHOOK_SECRET", default="")

# security.W008 is intentionally silenced: SECURE_SSL_REDIRECT is False because
# Railway terminates TLS at its edge proxy and forwards traffic over HTTP internally.
# SECURE_PROXY_SSL_HEADER is set so Django correctly detects the original HTTPS scheme.
SILENCED_SYSTEM_CHECKS = ["security.W008"]
