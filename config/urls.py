import os

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from two_factor.urls import urlpatterns as tf_urls

# Admin URL path is driven by an env variable so it can be rotated without a code deploy.
# Falls back to a non-obvious slug when the variable is absent.
ADMIN_PATH = os.environ.get("ADMIN_URL_PATH", "internal-mgmt")

urlpatterns = [
    # Two-factor-auth login/setup views (must be included before admin)
    path("", include(tf_urls)),

    # Django admin at the obscured path (TWO_FACTOR_FORCE_OTP_ADMIN enforces TOTP for all staff)
    path(f"{ADMIN_PATH}/", admin.site.urls),

    # API v1
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/products/", include("products.urls")),
    path("api/v1/shops/", include("shops.urls")),
    path("api/v1/orders/", include("orders.urls")),
    path("api/v1/disputes/", include("disputes.urls")),
    path("api/v1/notifications/", include("notifications.urls")),
    path("api/v1/payments/", include("payments.urls")),

    # API schema & interactive docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
