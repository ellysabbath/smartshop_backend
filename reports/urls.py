from django.urls import path
from . import views

urlpatterns = [
    path("", views.reports_list_create, name="reports"),
    path("<uuid:pk>/", views.report_detail, name="report-detail"),
    path("<uuid:pk>/approve/", views.approve_report, name="report-approve"),
    path("<uuid:pk>/reject/", views.reject_report, name="report-reject"),
]