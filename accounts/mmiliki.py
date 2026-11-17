"""
Mmiliki views — udhibiti kamili wa users.
Bila DefaultRouter — kwa kutumia APIView na path().
Bila Store na Order.
"""
from django.contrib.auth import get_user_model
from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .permissions import IsMmiliki

User = get_user_model()


# ==================================================================
# Helper — serialize user
# ==================================================================
def serialize_user(u):
    """Serialize user bila stats za Store/Order."""
    return {
        "id": str(u.id),
        "phone": u.phone,
        "full_name": u.full_name,
        "role": u.role,
        "is_active": u.is_active,
        "date_joined": u.date_joined.isoformat() if u.date_joined else None,
        "last_login": u.last_login.isoformat() if u.last_login else None,
        "last_login_display": (
            u.last_login.strftime("%d/%m/%Y %H:%M") if u.last_login else None
        ),
    }


# ==================================================================
# GET /mmiliki/users/ — list (filter + search)
# POST /mmiliki/users/ — create
# ==================================================================
class MmilikiUsersListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsMmiliki]

    # ------------------------------------------------------------------
    # GET — list
    # ------------------------------------------------------------------
    def get(self, request):
        qs = User.objects.all().order_by("-date_joined")
        params = request.query_params

        role = params.get("role")
        is_active = params.get("is_active")
        search = params.get("search")

        if role:
            qs = qs.filter(role=role)
        if is_active is not None and is_active != "":
            qs = qs.filter(is_active=is_active.lower() == "true")
        if search:
            qs = qs.filter(
                Q(full_name__icontains=search) | Q(phone__icontains=search)
            )

        return Response([serialize_user(u) for u in qs])

    # ------------------------------------------------------------------
    # POST — create
    # ------------------------------------------------------------------
    def post(self, request):
        phone = request.data.get("phone")
        full_name = request.data.get("full_name")
        role = request.data.get("role")
        password = request.data.get("password")
        is_active = request.data.get("is_active", True)

        if not phone or not full_name or not role:
            return Response(
                {"detail": "phone, full_name, na role ni lazima"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not password or len(password) < 6:
            return Response(
                {"password": "Password lazima iwe angalau herufi 6"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(phone=phone).exists():
            return Response(
                {"phone": "Phone hii tayari ipo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_roles = ["mteja", "muuzaji", "mmiliki", "admin", "mhazini"]
        if role not in valid_roles:
            return Response(
                {"role": f"Role '{role}' si sahihi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            phone=phone,
            full_name=full_name,
            role=role,
            password=password,
            is_active=bool(is_active),
        )
        return Response(
            serialize_user(user), status=status.HTTP_201_CREATED
        )


# ==================================================================
# GET /mmiliki/users/<id>/ — detail
# PATCH /mmiliki/users/<id>/ — update
# DELETE /mmiliki/users/<id>/ — soft delete
# ==================================================================
class MmilikiUserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsMmiliki]

    def get_user(self, pk):
        try:
            return User.objects.get(id=pk)
        except User.DoesNotExist:
            return None

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------
    def get(self, request, pk):
        u = self.get_user(pk)
        if not u:
            return Response(
                {"detail": "User haipo"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(serialize_user(u))

    # ------------------------------------------------------------------
    # PATCH — update
    # ------------------------------------------------------------------
    def patch(self, request, pk):
        u = self.get_user(pk)
        if not u:
            return Response(
                {"detail": "User haipo"}, status=status.HTTP_404_NOT_FOUND
            )

        # Usimruhusu mmiliki kubadilisha role yake mwenyewe
        new_role = request.data.get("role")
        if u.id == request.user.id and new_role and new_role != u.role:
            return Response(
                {"role": "Hauwezi kubadilisha role yako mwenyewe"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update fields
        if "phone" in request.data:
            phone = request.data["phone"]
            if User.objects.filter(phone=phone).exclude(id=u.id).exists():
                return Response(
                    {"phone": "Phone hii tayari ipo"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            u.phone = phone

        if "full_name" in request.data:
            u.full_name = request.data["full_name"]

        if "role" in request.data:
            valid_roles = ["mteja", "muuzaji", "mmiliki", "admin", "mhazini"]
            if request.data["role"] not in valid_roles:
                return Response(
                    {"role": "Role si sahihi"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            u.role = request.data["role"]

        if "is_active" in request.data:
            # Usimruhusu mmiliki kuzima akaunti yake mwenyewe
            if u.id == request.user.id and not request.data["is_active"]:
                return Response(
                    {"is_active": "Hauwezi kuzima akaunti yako mwenyewe"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            u.is_active = bool(request.data["is_active"])

        u.save()
        return Response(serialize_user(u))

    # ------------------------------------------------------------------
    # DELETE — soft delete
    # ------------------------------------------------------------------
    def delete(self, request, pk):
        u = self.get_user(pk)
        if not u:
            return Response(
                {"detail": "User haipo"}, status=status.HTTP_404_NOT_FOUND
            )

        if u.id == request.user.id:
            return Response(
                {"detail": "Hauwezi kufuta akaunti yako mwenyewe"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        u.is_active = False
        u.save(update_fields=["is_active"])
        return Response({"detail": "User amezimwa (soft delete)"})


# ==================================================================
# POST /mmiliki/users/<id>/set-password/
# ==================================================================
class MmilikiUserSetPasswordView(APIView):
    permission_classes = [IsAuthenticated, IsMmiliki]

    def post(self, request, pk):
        try:
            u = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {"detail": "User haipo"}, status=status.HTTP_404_NOT_FOUND
            )

        password = request.data.get("password")
        if not password or len(password) < 6:
            return Response(
                {"password": "Password lazima iwe angalau herufi 6"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        u.set_password(password)
        u.save(update_fields=["password"])
        return Response({"detail": "Password imebadilishwa"})


# ==================================================================
# POST /mmiliki/users/<id>/toggle-active/
# ==================================================================
class MmilikiUserToggleActiveView(APIView):
    permission_classes = [IsAuthenticated, IsMmiliki]

    def post(self, request, pk):
        try:
            u = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {"detail": "User haipo"}, status=status.HTTP_404_NOT_FOUND
            )

        if u.id == request.user.id:
            return Response(
                {"detail": "Hauwezi kuzima akaunti yako mwenyewe"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        u.is_active = not u.is_active
        u.save(update_fields=["is_active"])
        return Response({
            "detail": f"User {'amewashwa' if u.is_active else 'amezimwa'}",
            "is_active": u.is_active,
        })


# ==================================================================
# POST /mmiliki/users/<id>/change-role/
# ==================================================================
class MmilikiUserChangeRoleView(APIView):
    permission_classes = [IsAuthenticated, IsMmiliki]

    def post(self, request, pk):
        try:
            u = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {"detail": "User haipo"}, status=status.HTTP_404_NOT_FOUND
            )

        new_role = request.data.get("role")
        valid_roles = ["mteja", "muuzaji", "mmiliki", "admin", "mhazini"]
        if new_role not in valid_roles:
            return Response(
                {"role": "Role si sahihi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if u.id == request.user.id:
            return Response(
                {"detail": "Hauwezi kubadilisha role yako mwenyewe"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        u.role = new_role
        u.save(update_fields=["role"])
        return Response({
            "detail": f"Role imebadilishwa kuwa {new_role}",
            "role": new_role,
        })


# ==================================================================
# GET /mmiliki/users/summary/
# ==================================================================
class MmilikiUsersSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsMmiliki]

    def get(self, request):
        from django.db.models import Count

        total = User.objects.count()
        active = User.objects.filter(is_active=True).count()
        by_role = dict(
            User.objects.values("role")
            .annotate(count=Count("id"))
            .values_list("role", "count")
        )
        return Response({
            "total": total,
            "active": active,
            "inactive": total - active,
            "by_role": by_role,
        })