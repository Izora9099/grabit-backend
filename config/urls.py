from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),

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
