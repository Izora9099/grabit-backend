"""
Base settings shared across all environments.
"""
from datetime import timedelta
from pathlib import Path

from decouple import config

# Project root — three levels up from config/settings/base.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")

INSTALLED_APPS = [
    # Two-factor auth must come before django.contrib.admin
    "two_factor",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third-party
    "storages",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "axes",
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    # Allauth (required for Google OAuth)
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # Local apps
    "accounts",
    "products",
    "orders",
    "shops",
    "disputes",
    "notifications.apps.NotificationsConfig",
    "payments",
]

SITE_ID = 1

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",          # two-factor: after AuthenticationMiddleware
    "axes.middleware.AxesMiddleware",               # brute-force: after AuthenticationMiddleware
    "allauth.account.middleware.AccountMiddleware", # allauth account middleware
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",          # must be first
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "accounts.User"

# Argon2 first — PBKDF2 hashes are upgraded automatically on next login
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Douala"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── JWT ───────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": True,
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "GrabIT API",
    "DESCRIPTION": (
        "REST API for the GrabIT marketplace platform — "
        "buyers, vendors, delivery agents, and admins."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ── Django-Axes (brute-force protection) ─────────────────────────────────────
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(hours=1)
AXES_RESET_ON_SUCCESS = True
# Lock on the combination of username + IP, not IP alone
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]

# ── Two-Factor Auth ───────────────────────────────────────────────────────────
TWO_FACTOR_FORCE_OTP_ADMIN = True
LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = f"/{config('ADMIN_URL_PATH', default='internal-mgmt')}/"

# ── Allauth ───────────────────────────────────────────────────────────────────
ACCOUNT_EMAIL_VERIFICATION = "optional"   # sends email but does not block login
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_ADAPTER = "accounts.adapter.AccountAdapter"
FRONTEND_URL = config("FRONTEND_URL", default="https://grabit.sale")

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": config("GOOGLE_OAUTH2_CLIENT_ID", default=""),
            "secret": config("GOOGLE_OAUTH2_CLIENT_SECRET", default=""),
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

# ── JWT refresh cookie (shared cookie name used across views) ─────────────────
JWT_REFRESH_COOKIE_NAME = "grabit_refresh"
JWT_REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds

# ── Fapshi — collection service (buyer payments) ──────────────────────────────
# Switch FAPSHI_BASE_URL to https://live.fapshi.com when going live.
# Payout service gets its own separate credentials when built.
FAPSHI_BASE_URL       = config("FAPSHI_BASE_URL", default="https://sandbox.fapshi.com")
FAPSHI_API_USER       = config("FAPSHI_API_USER", default="")
FAPSHI_API_KEY        = config("FAPSHI_API_KEY", default="")
FAPSHI_WEBHOOK_SECRET = config("FAPSHI_WEBHOOK_SECRET", default="")
# When set, FAPSHI_BASE_URL should point to the Cloudflare Worker proxy URL.
# The Worker holds the real Fapshi credentials; Django only sends this secret.
FAPSHI_PROXY_SECRET   = config("FAPSHI_PROXY_SECRET", default="")

# ── Celery ────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL     = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_TIMEZONE       = TIME_ZONE
CELERY_BEAT_SCHEDULE  = {
    "reconcile-pending-payments": {
        "task": "payments.tasks.reconcile_pending_payments",
        "schedule": 300.0,  # every 5 minutes
    },
}


