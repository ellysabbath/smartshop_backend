from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("api/notifications/", include("notifications.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/firebase/", include("firebase_sync.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/stores/", include("stores.urls")),
    path("api/products/", include("products.urls")),
    path("api/customers/", include("customers.urls")),
    path("api/suppliers/", include("suppliers.urls")),
    path("api/orders/", include("sales.urls")),
    path("api/inventory/", include("inventory.urls")),
    path("api/staff/", include("staff.urls")),
    path("api/expenses/", include("expenses.urls")),
    path("api/finance/", include("finance.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/", include("accounts.mmilikiUrls")),
]