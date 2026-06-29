import os

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from two_factor.urls import urlpatterns as tf_urls

# Admin URL path is driven by an env variable so it can be rotated without a code deploy.
# Falls back to a non-obvious slug when the variable is absent.
ADMIN_PATH = os.environ.get("ADMIN_URL_PATH", "internal-mgmt")

# Restrict API docs to admin users in production; AllowAny is overridden per-view in development
_docs_permission = IsAdminUser if not settings.DEBUG else AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok"})


urlpatterns = [
    # Two-factor-auth login/setup views (must be included before admin)
    path("", include(tf_urls)),

    # Django admin at the obscured path (TWO_FACTOR_FORCE_OTP_ADMIN enforces TOTP for all staff)
    path(f"{ADMIN_PATH}/", admin.site.urls),

    # Public health check for Railway/Cloudflare uptime probes
    path("health/", health_check),

    # API v1
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/products/", include("products.urls")),
    path("api/v1/shops/", include("shops.urls")),
    path("api/v1/orders/", include("orders.urls")),
    path("api/v1/disputes/", include("disputes.urls")),
    path("api/v1/notifications/", include("notifications.urls")),
    path("api/v1/payments/", include("payments.urls")),
    path("api/v1/analytics/", include("analytics.urls")),
    path("api/v1/tracking/", include("tracking.urls")),

    # API schema & interactive docs — admin-only in production, open in dev
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[_docs_permission]), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[_docs_permission]), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema", permission_classes=[_docs_permission]), name="redoc"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
