# suppliers/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.suppliers_list, name="suppliers"),
    path("<uuid:pk>/", views.suppliers_detail, name="supplier-detail"),
]