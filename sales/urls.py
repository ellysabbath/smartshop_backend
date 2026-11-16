from django.urls import path
from . import views

urlpatterns = [
    path("", views.orders_list_create, name="orders"),
    path("<uuid:pk>/", views.orders_detail, name="order-detail"),
    path("<uuid:pk>/payments/", views.add_payment, name="order-payment-add"),
    path("<uuid:pk>/payments/<uuid:payment_pk>/confirm/",
         views.confirm_payment, name="order-payment-confirm"),
    path("<uuid:pk>/payments/<uuid:payment_pk>/reject/",
         views.reject_payment, name="order-payment-reject"),
]