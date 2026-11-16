from django.urls import path
from . import views

urlpatterns = [
    path("salaries/", views.salaries_list_create, name="salaries"),
    path("salaries/<uuid:pk>/", views.salaries_detail, name="salary-detail"),
    path("salaries/<uuid:pk>/pay/", views.pay_salary, name="salary-pay"),
]