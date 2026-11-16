# customers/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.customers_list, name="customers"),
    path("<uuid:pk>/", views.customers_detail, name="customer-detail"),
]