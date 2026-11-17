from django.urls import path

from .mmiliki import (
    MmilikiUsersListCreateView,
    MmilikiUserDetailView,
    MmilikiUserSetPasswordView,
    MmilikiUserToggleActiveView,
    MmilikiUserChangeRoleView,
    MmilikiUsersSummaryView,
)

urlpatterns = [
    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    path(
        "mmiliki/users/",
        MmilikiUsersListCreateView.as_view(),
        name="mmiliki-users-list",
    ),
    path(
        "mmiliki/users/summary/",
        MmilikiUsersSummaryView.as_view(),
        name="mmiliki-users-summary",
    ),
    path(
        "mmiliki/users/<uuid:pk>/",
        MmilikiUserDetailView.as_view(),
        name="mmiliki-user-detail",
    ),
    path(
        "mmiliki/users/<uuid:pk>/set-password/",
        MmilikiUserSetPasswordView.as_view(),
        name="mmiliki-user-set-password",
    ),
    path(
        "mmiliki/users/<uuid:pk>/toggle-active/",
        MmilikiUserToggleActiveView.as_view(),
        name="mmiliki-user-toggle-active",
    ),
    path(
        "mmiliki/users/<uuid:pk>/change-role/",
        MmilikiUserChangeRoleView.as_view(),
        name="mmiliki-user-change-role",
    ),
]