from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("verify-phone/", views.verify_phone, name="verify-phone"),
    path("resend-otp/", views.resend_otp, name="resend-otp"),
    path("request-otp/", views.request_otp, name="request-otp"),
    path("verify-otp/", views.verify_otp, name="verify-otp"),
    path("me/", views.me, name="me"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Users
    path("users/", views.users_list, name="users-list"),
    path("users/without-store/", views.users_without_store, name="users-without-store"),
    path("users/<uuid:pk>/", views.user_detail, name="user-detail"),
]