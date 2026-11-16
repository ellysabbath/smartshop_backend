from django.urls import path

from . import views

urlpatterns = [
    # Categories
    path("categories/", views.categories_list_create, name="expense-categories"),

    # Requests
    path("requests/", views.requests_list_create, name="expense-requests"),
    path("requests/<uuid:pk>/", views.requests_detail, name="expense-request-detail"),
    path("requests/<uuid:pk>/approve/", views.approve_request, name="expense-request-approve"),
    path("requests/<uuid:pk>/reject/", views.reject_request, name="expense-request-reject"),

    # Expenses (yaliyokubaliwa)
    path("", views.expenses_list_create, name="expenses"),
    path("<uuid:pk>/", views.expense_detail, name="expense-detail"),
]