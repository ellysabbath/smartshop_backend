from django.urls import path
from . import views

urlpatterns = [
    path("", views.stores_list_create, name="store-list-create"),
    path("<uuid:pk>/", views.stores_detail, name="store-detail"),
]