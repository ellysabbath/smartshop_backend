from django.urls import path
from . import views

urlpatterns = [
    path("stock-levels/", views.stock_levels_list, name="stock-levels"),
    path("movements/", views.movements_list, name="movements"),
    path("adjust/", views.adjust_stock, name="adjust"),
    path("stock-adjustments/", views.stock_adjustments_list_create, name="stock-adjustments"),
    path("stock-adjustments/<uuid:pk>/approve/", views.approve_adjustment, name="adjustment-approve"),
    path("stock-adjustments/<uuid:pk>/reject/", views.reject_adjustment, name="adjustment-reject"),
]