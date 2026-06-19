from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    # Auth
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("token/refresh/", views.TokenRefreshView.as_view(), name="token-refresh"),
    # Email verification
    path("email/verify/confirm/", views.EmailVerifyConfirmView.as_view(), name="email-verify-confirm"),
    path("email/verify/resend/", views.EmailVerifyResendView.as_view(), name="email-verify-resend"),
    # Password reset
    path("password-reset/request/", views.PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/confirm/", views.PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    # Google OAuth
    path("google/", views.GoogleLoginView.as_view(), name="google-login"),
    path("google/complete/", views.GoogleCompleteView.as_view(), name="google-complete"),
    # Profile
    path("me/", views.MeView.as_view(), name="me"),
    path("me/change-password/", views.ChangePasswordView.as_view(), name="change-password"),
    path("me/delete/", views.DeleteAccountView.as_view(), name="delete-account"),
    path("me/addresses/", views.AddressListCreateView.as_view(), name="addresses"),
    path("me/addresses/<int:pk>/", views.AddressDetailView.as_view(), name="address-detail"),
    path("me/agent-kyc/", views.AgentKYCListCreateView.as_view(), name="agent-kyc"),
    path("me/agent-kyc/submit/", views.AgentKYCSubmitView.as_view(), name="agent-kyc-submit"),
    path("me/agent-kyc/<int:pk>/", views.AgentKYCDetailView.as_view(), name="agent-kyc-detail"),
    # Admin dashboard
    path("admin/stats/", admin_views.AdminStatsView.as_view(), name="admin-stats"),
    path("admin/users/", admin_views.AdminUserListView.as_view(), name="admin-users"),
    path("admin/users/<int:pk>/", admin_views.AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("admin/gmv/", admin_views.AdminGMVView.as_view(), name="admin-gmv"),
    path("admin/orders/", admin_views.AdminOrderListView.as_view(), name="admin-orders"),
    path("admin/shops/", admin_views.AdminShopListView.as_view(), name="admin-shops"),
    path("admin/verification/", admin_views.AdminVerificationQueueView.as_view(), name="admin-verification"),
    path("admin/verification/<int:shop_id>/", admin_views.AdminVerifyShopView.as_view(), name="admin-verify-shop"),
    path("admin/disputes/", admin_views.AdminDisputeListView.as_view(), name="admin-disputes"),
    path("admin/payouts/", admin_views.AdminPayoutListView.as_view(), name="admin-payouts"),
    path("admin/commissions/", admin_views.AdminCommissionsView.as_view(), name="admin-commissions"),
    path("admin/health/", admin_views.AdminHealthView.as_view(), name="admin-health"),
    path("admin/fraud/", admin_views.AdminFraudSignalsView.as_view(), name="admin-fraud"),
    path("admin/fraud-rules/", admin_views.AdminFraudRulesView.as_view(), name="admin-fraud-rules"),
    path("admin/user-growth/", admin_views.AdminUserGrowthView.as_view(), name="admin-user-growth"),
    path("admin/agent-verification/", admin_views.AdminAgentKYCQueueView.as_view(), name="admin-agent-kyc-queue"),
    path("admin/agent-verification/<int:user_id>/", admin_views.AdminVerifyAgentView.as_view(), name="admin-verify-agent"),
]
