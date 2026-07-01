from django.urls import path
from . import views

urlpatterns = [
    path("", views.ShopListView.as_view(), name="shops"),
    path("my/", views.MyShopView.as_view(), name="my-shop"),
    path("my/create/", views.MyShopCreateView.as_view(), name="my-shop-create"),
    path("my/kyc/", views.KYCDocumentListCreateView.as_view(), name="kyc"),
    path("my/kyc/submit/", views.KYCSubmitView.as_view(), name="kyc-submit"),
    path("my/pro-seller/apply/", views.ProSellerApplyView.as_view(), name="pro-seller-apply"),
    path("my/kyc/<int:pk>/", views.KYCDocumentDetailView.as_view(), name="kyc-detail"),
    path("followed/", views.FollowedShopsView.as_view(), name="followed-shops"),
    # slug routes MUST come after all fixed "my/" routes
    path("<slug:handle>/follow/", views.ShopFollowView.as_view(), name="shop-follow"),
    path("<slug:handle>/products/", views.ShopProductsView.as_view(), name="shop-products"),
    path("<slug:handle>/reviews/", views.ShopReviewListCreateView.as_view(), name="shop-reviews"),
    path("<slug:handle>/", views.ShopDetailView.as_view(), name="shop-detail"),
]
