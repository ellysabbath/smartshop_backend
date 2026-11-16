from django.urls import path
from . import views

urlpatterns = [
    path("profit/", views.profit_summary, name="profit-summary"),
    path("profit/snapshot/", views.save_profit_snapshot, name="profit-snapshot"),
    path("tithe-offerings/", views.tithe_offerings_list_create, name="tithe-offerings"),
]