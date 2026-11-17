from rest_framework.permissions import BasePermission


class IsMmiliki(BasePermission):
    """Ruhusu mmiliki na admin pekee."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["mmiliki", "admin"]
        )