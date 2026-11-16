from django.urls import path

from . import views

urlpatterns = [
    path("", views.documents_list, name="documents-list"),
    path("generate/", views.generate_document, name="documents-generate"),
    path("<uuid:pk>/", views.document_detail, name="document-detail"),
    path(
        "<uuid:pk>/download/",
        views.download_pdf,
        name="document-download-pdf",
    ),
    path(
        "<uuid:pk>/download-csv/",
        views.download_csv,
        name="document-download-csv",
    ),
]