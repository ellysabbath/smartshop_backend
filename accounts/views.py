import random
import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from notifications.models import OTP
from notifications.services import (
    send_sms,
    send_email,
    sms_otp,
    email_otp_html,
)
from stores.models import Store

User = get_user_model()


# ==================================================================
# Constants
# ==================================================================
# Roles zinazoruhusiwa kujisajili kupitia /register
ALLOWED_ROLES = ("mteja", "muuzaji", "mmiliki", "admin")

# Roles zinazohitaji duka
ROLES_ZENYE_DUKA = ("muuzaji", "mhazini")

# Regex ya namba ya simu ya Tanzania (0XXXXXXXXX)
PHONE_REGEX = re.compile(r"^0[67]\d{8}$")

# Muda wa OTP (dakika)
OTP_EXPIRY_MINUTES = 10


# ==================================================================
# Helpers
# ==================================================================
def _tokens_for(user):
    """Rudisha JWT tokens + user info."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": str(user.id),
            "phone": user.phone,
            "full_name": user.full_name,
            "role": user.role,
            "store_id": str(user.store_id) if user.store_id else None,
        },
    }


def _user_dict(user, include_store=True, include_created=True):
    """Geuza user kuwa dict ya JSON."""
    data = {
        "id": str(user.id),
        "phone": user.phone,
        "full_name": user.full_name,
        "role": user.role,
    }
    if include_store:
        data["store"] = str(user.store_id) if user.store_id else None
        data["store_id"] = str(user.store_id) if user.store_id else None
    if include_created:
        data["is_active"] = user.is_active
        data["created_at"] = (
            user.created_at.isoformat()
            if hasattr(user, "created_at") and user.created_at
            else None
        )
    return data


def _clean_phone(phone: str) -> str:
    """Ondoa nafasi, dashes, na alama zote."""
    return (phone or "").strip().replace(" ", "").replace("-", "")


def _is_valid_phone(phone: str) -> bool:
    """Thibitisha namba ya simu (Tanzania)."""
    return bool(PHONE_REGEX.match(phone))


def _generate_otp() -> str:
    """Tarakimu 6 za OTP."""
    return f"{random.randint(0, 999999):06d}"


def _create_and_send_otp(phone: str, purpose: str = "verify") -> dict:
    """
    Unda OTP mpya, futa zilizopita (zisizotumika), tuma SMS.
    Rudisha { ok: bool, error?: str, code?: str }
    """
    code = _generate_otp()

    # Futa OTP zilizopita za aina hii
    OTP.objects.filter(
        phone=phone, purpose=purpose, is_used=False
    ).update(is_used=True)

    # Unda mpya
    OTP.objects.create(
        phone=phone,
        code=code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )

    # Tuma SMS
    result = send_sms(phone, sms_otp(code))
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error")}
    return {"ok": True, "code": code}


# ==================================================================
# REGISTER — unda user (is_active=False) + tuma OTP
# ==================================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    phone = _clean_phone(request.data.get("phone", ""))
    full_name = (request.data.get("full_name", "") or "").strip()
    password = request.data.get("password", "")
    role = (request.data.get("role", "mteja") or "").strip().lower()

    # ------------------------------------------------------------------
    # 1. Validate fields
    # ------------------------------------------------------------------
    errors = {}

    if not phone:
        errors["phone"] = ["Namba ya simu inahitajika."]
    elif not _is_valid_phone(phone):
        errors["phone"] = [
            "Namba si sahihi. Tumia 0XXXXXXXXX (mfano 0754123456)."
        ]

    if not full_name:
        errors["full_name"] = ["Jina kamili linahitajika."]

    if not password:
        errors["password"] = ["Nywila inahitajika."]
    elif len(password) < 6:
        errors["password"] = ["Nywila iwe angalau herufi 6."]

    if role not in ALLOWED_ROLES:
        errors["role"] = [
            "Role si sahihi. Chagua mteja, muuzaji, mmiliki, au admin."
        ]

    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # 2. Angalia kama namba imetumika
    # ------------------------------------------------------------------
    if User.objects.filter(phone=phone).exists():
        return Response(
            {"phone": ["Namba hii tayari imetumika."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ------------------------------------------------------------------
    # 3. Unda user (is_active=False)
    # ------------------------------------------------------------------
    user = User.objects.create_user(
        phone=phone,
        password=password,
        full_name=full_name,
        role=role,
        is_active=False,
    )

    # ------------------------------------------------------------------
    # 4. Unda OTP + tuma SMS
    # ------------------------------------------------------------------
    sms_result = _create_and_send_otp(phone, purpose="verify")
    if not sms_result.get("ok"):
        user.delete()
        return Response(
            {
                "detail": "Imeshindikana kutuma OTP. Jaribu tena.",
                "error": sms_result.get("error"),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {
            "detail": "Akaunti imeundwa. OTP imetumwa kwa simu yako.",
            "phone": phone,
            "role": role,
        },
        status=status.HTTP_201_CREATED,
    )


# ==================================================================
# VERIFY PHONE — thibitisha OTP + activate user
# ==================================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_phone(request):
    phone = _clean_phone(request.data.get("phone", ""))
    code = (request.data.get("code", "") or "").strip()

    if not phone or not code:
        return Response(
            {"detail": "Namba na OTP vinahitajika."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    otp = OTP.objects.filter(
        phone=phone,
        code=code,
        purpose="verify",
        is_used=False,
    ).order_by("-created_at").first()

    if not otp or not otp.is_valid():
        return Response(
            {"detail": "OTP si sahihi au imeisha muda."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    otp.is_used = True
    otp.save(update_fields=["is_used"])

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        return Response(
            {"detail": "Mtumiaji haipo."},
            status=status.HTTP_404_NOT_FOUND,
        )

    user.is_active = True
    user.save(update_fields=["is_active"])

    try:
        send_sms(phone, "SmartShop: Akaunti yako imethibitishwa. Karibu!")
    except Exception:
        pass

    return Response({
        "detail": "Akaunti imethibitishwa. Sasa unaweza kuingia.",
        "phone": phone,
        "role": user.role,
    })


# ==================================================================
# RESEND OTP — tuma OTP mpya
# ==================================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def resend_otp(request):
    phone = _clean_phone(request.data.get("phone", ""))

    if not phone:
        return Response(
            {"phone": ["Namba inahitajika."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        return Response(
            {"detail": "Namba haipo."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if user.is_active:
        return Response(
            {"detail": "Akaunti tayari imethibitishwa. Ingia moja kwa moja."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    sms_result = _create_and_send_otp(phone, purpose="verify")
    if not sms_result.get("ok"):
        return Response(
            {
                "detail": "Imeshindikana kutuma OTP.",
                "error": sms_result.get("error"),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response({
        "detail": "OTP imetumwa upya.",
        "phone": phone,
    })


# ==================================================================
# LOGIN — ingia (inakataa kama is_active=False)
# ==================================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    phone = _clean_phone(request.data.get("phone", ""))
    password = request.data.get("password", "")

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        return Response(
            {"detail": "Namba au nywila si sahihi."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.check_password(password):
        return Response(
            {"detail": "Namba au nywila si sahihi."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {
                "detail": "Akaunti haijathibitishwa. Thibitisha namba yako kwanza.",
                "needs_verification": True,
                "phone": user.phone,
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response(_tokens_for(user))


# ==================================================================
# REQUEST OTP — kwa reset password (SMS au EMAIL)
# ==================================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def request_otp(request):
    phone = _clean_phone(request.data.get("phone", ""))
    purpose = request.data.get("purpose", "reset")
    channel = request.data.get("channel", "sms")

    if not phone:
        return Response(
            {"phone": ["Namba inahitajika."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not _is_valid_phone(phone):
        return Response(
            {"phone": ["Namba si sahihi."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    code = _generate_otp()
    OTP.objects.filter(
        phone=phone, purpose=purpose, is_used=False
    ).update(is_used=True)
    OTP.objects.create(
        phone=phone,
        code=code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )

    if channel == "email":
        email = (request.data.get("email", "") or "").strip()
        if not email:
            return Response(
                {"email": ["Email inahitajika."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = send_email(
            "OTP ya SmartShop",
            f"OTP yako ni {code}",
            [email],
            html_message=email_otp_html(code, phone),
        )
    else:
        result = send_sms(phone, sms_otp(code))

    if not result.get("ok"):
        return Response(
            {
                "detail": "Imeshindikana kutuma OTP.",
                "error": result.get("error"),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response({
        "detail": "OTP imetumwa.",
        "channel": channel,
    })


# ==================================================================
# VERIFY OTP — kwa reset password (inarudisha tokens kama user yupo)
# ==================================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    phone = _clean_phone(request.data.get("phone", ""))
    code = (request.data.get("code", "") or "").strip()

    if not phone or not code:
        return Response(
            {"detail": "Namba na OTP vinahitajika."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    otp = OTP.objects.filter(
        phone=phone, code=code, is_used=False
    ).order_by("-created_at").first()

    if not otp or not otp.is_valid():
        return Response(
            {"detail": "OTP si sahihi au imeisha muda."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    otp.is_used = True
    otp.save(update_fields=["is_used"])

    try:
        user = User.objects.get(phone=phone)
        return Response(_tokens_for(user))
    except User.DoesNotExist:
        return Response({
            "detail": "OTP imethibitishwa.",
            "tokens": None,
        })


# ==================================================================
# ME — taarifa za mtumiaji aliyepo (GET + PATCH)
# ==================================================================
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------
    if request.method == "GET":
        return Response(_user_dict(user))

    # ------------------------------------------------------------------
    # PATCH — full_name / phone
    # ------------------------------------------------------------------
    full_name = request.data.get("full_name")
    phone = request.data.get("phone")

    if full_name is not None:
        if not full_name.strip():
            return Response(
                {"full_name": ["Jina kamili linahitajika."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.full_name = full_name.strip()

    if phone is not None:
        phone_clean = _clean_phone(phone)
        if not _is_valid_phone(phone_clean):
            return Response(
                {"phone": ["Namba si sahihi."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(phone=phone_clean).exclude(pk=user.pk).exists():
            return Response(
                {"phone": ["Namba hii tayari imetumika."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.phone = phone_clean

    user.save()
    return Response(_user_dict(user))


# ==================================================================
# USERS — list (GET) + create (POST)
# ==================================================================
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def users_list(request):
    """
    GET  /api/users/   — orodhesha watumiaji wote
    POST /api/users/   — unda mtumiaji mpya (mfanyakazi)
    """
    if request.user.role not in ("mmiliki", "admin"):
        return Response(
            {"detail": "Hauna ruhusa."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # ------------------------------------------------------------------
    # GET — orodhesha
    # ------------------------------------------------------------------
    if request.method == "GET":
        qs = User.objects.all()

        role = request.query_params.get("role")
        store_id = request.query_params.get("store")
        search = request.query_params.get("search")

        if role:
            qs = qs.filter(role=role)
        if store_id:
            qs = qs.filter(store_id=store_id)
        if search:
            qs = qs.filter(
                Q(full_name__icontains=search) | Q(phone__icontains=search)
            )

        qs = qs.order_by("-created_at")

        return Response([_user_dict(u) for u in qs])

    # ------------------------------------------------------------------
    # POST — unda mtumiaji
    # ------------------------------------------------------------------
    phone = _clean_phone(request.data.get("phone", ""))
    full_name = (request.data.get("full_name", "") or "").strip()
    password = request.data.get("password", "")
    role = (request.data.get("role", "muuzaji") or "").strip().lower()
    store_id = request.data.get("store_id") or None
    is_active = request.data.get("is_active", True)

    errors = {}

    if not phone:
        errors["phone"] = ["Namba inahitajika."]
    elif not _is_valid_phone(phone):
        errors["phone"] = ["Namba si sahihi."]
    elif User.objects.filter(phone=phone).exists():
        errors["phone"] = ["Namba hii tayari imetumika."]

    if not full_name:
        errors["full_name"] = ["Jina kamili linahitajika."]

    if not password:
        errors["password"] = ["Nywila inahitajika."]
    elif len(password) < 6:
        errors["password"] = ["Nywila iwe angalau herufi 6."]

    if role not in ("muuzaji", "mhazini", "admin"):
        errors["role"] = ["Role si sahihi. Chagua muuzaji, mhazini, au admin."]

    if store_id:
        try:
            Store.objects.get(pk=store_id)
        except Store.DoesNotExist:
            errors["store_id"] = ["Duka haipo."]

    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        phone=phone,
        password=password,
        full_name=full_name,
        role=role,
        store_id=store_id,
        is_active=bool(is_active),
    )

    return Response(_user_dict(user), status=status.HTTP_201_CREATED)


# ==================================================================
# USERS — without store
# ==================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def users_without_store(request):
    """
    GET /api/users/without-store/
    Orodhesha watumiaji (muuzaji/mhazini) wasio na duka.
    """
    if request.user.role not in ("mmiliki", "admin"):
        return Response(
            {"detail": "Hauna ruhusa."},
            status=status.HTTP_403_FORBIDDEN,
        )

    qs = User.objects.filter(
        role__in=ROLES_ZENYE_DUKA,
        store__isnull=True,
        is_active=True,
    ).order_by("full_name")

    return Response([_user_dict(u) for u in qs])


# ==================================================================
# USERS — detail (GET + PATCH + DELETE)
# ==================================================================
@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def user_detail(request, pk):
    """
    GET    /api/users/<uuid>/   — undani
    PATCH  /api/users/<uuid>/   — sasisha (weka duka, role, n.k.)
    DELETE /api/users/<uuid>/   — futa
    """
    if request.user.role not in ("mmiliki", "admin"):
        return Response(
            {"detail": "Hauna ruhusa."},
            status=status.HTTP_403_FORBIDDEN,
        )

    user = get_object_or_404(User, pk=pk)

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------
    if request.method == "GET":
        return Response(_user_dict(user))

    # ------------------------------------------------------------------
    # PATCH
    # ------------------------------------------------------------------
    if request.method == "PATCH":
        # Store
        if "store" in request.data:
            store_id = request.data["store"]
            if store_id is None or store_id == "":
                user.store = None
            else:
                try:
                    user.store = Store.objects.get(pk=store_id)
                except Store.DoesNotExist:
                    return Response(
                        {"store": ["Duka haipo."]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        # Role
        if "role" in request.data:
            role = (request.data["role"] or "").strip().lower()
            if role in ("muuzaji", "mhazini", "admin", "mmiliki", "mteja"):
                user.role = role
            else:
                return Response(
                    {"role": ["Role si sahihi."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # is_active
        if "is_active" in request.data:
            user.is_active = bool(request.data["is_active"])

        # full_name
        if "full_name" in request.data:
            full_name = (request.data["full_name"] or "").strip()
            if not full_name:
                return Response(
                    {"full_name": ["Jina kamili linahitajika."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.full_name = full_name

        # phone
        if "phone" in request.data:
            phone = _clean_phone(request.data["phone"])
            if not _is_valid_phone(phone):
                return Response(
                    {"phone": ["Namba si sahihi."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if User.objects.filter(phone=phone).exclude(pk=user.pk).exists():
                return Response(
                    {"phone": ["Namba hii tayari imetumika."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.phone = phone

        user.save()
        return Response(_user_dict(user))

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)