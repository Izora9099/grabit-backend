from django.urls import path
from . import views

urlpatterns = [
    path("vendor/", views.VendorAnalyticsView.as_view(), name="vendor-analytics"),
]
