from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health, name="firebase-health"),
    path("read/<path:path>", views.read_node, name="firebase-read"),
]