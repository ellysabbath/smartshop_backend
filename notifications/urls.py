from django.urls import path

from . import views

urlpatterns = [
    path("otps/", views.otps_list_create, name="otps"),
    path("otps/<uuid:pk>/", views.otp_detail, name="otp-detail"),
    path("logs/", views.logs_list, name="notification-logs"),
    path(
        "logs/<uuid:pk>/",
        views.log_detail,
        name="notification-log-detail",
    ),
    path("stats/", views.stats, name="notification-stats"),
]