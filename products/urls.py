from django.urls import path
from . import views, admin_views

urlpatterns = [
    # Public
    path("", views.ProductListView.as_view(), name="products"),
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("<int:pk>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("<int:pk>/reviews/", views.ProductReviewListCreateView.as_view(), name="product-reviews"),
    # Buyer
    path("wishlist/", views.WishlistView.as_view(), name="wishlist"),
    path("wishlist/<int:pk>/", views.WishlistItemView.as_view(), name="wishlist-item"),
    # Vendor
    path("vendor/", views.VendorProductListCreateView.as_view(), name="vendor-products"),
    path("vendor/<int:pk>/", views.VendorProductDetailView.as_view(), name="vendor-product-detail"),
    path("vendor/<int:pk>/images/", views.ProductImageListCreateView.as_view(), name="vendor-product-images"),
    path("vendor/<int:pk>/images/<int:img_pk>/", views.ProductImageDetailView.as_view(), name="vendor-product-image-detail"),
    # Admin
    path("admin/categories/", admin_views.AdminCategoryListCreateView.as_view(), name="admin-categories"),
    path("admin/categories/<int:pk>/", admin_views.AdminCategoryDetailView.as_view(), name="admin-category-detail"),
]
