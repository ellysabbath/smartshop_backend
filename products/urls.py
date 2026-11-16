from django.urls import path

from . import views

urlpatterns = [
    # Products
    path("", views.products_list_create, name="products"),
    path("<uuid:pk>/", views.product_detail, name="product-detail"),

    # Categories
    path("categories/", views.categories_list_create, name="categories"),

    # Units
    path("units/", views.units_list_create, name="units"),
]