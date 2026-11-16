from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import OTP, NotificationLog
from .serializers import OTPSerializer, NotificationLogSerializer


# ==================================================================
# OTP — list (admin only) + create (admin only)
# ==================================================================
@api_view(["GET", "POST"])
@permission_classes([IsAdminUser])
def otps_list_create(request):
    if request.method == "GET":
        qs = OTP.objects.all().order_by("-created_at")[:200]
        return Response(OTPSerializer(qs, many=True).data)

    serializer = OTPSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def otp_detail(request, pk):
    try:
        otp = OTP.objects.get(pk=pk)
    except OTP.DoesNotExist:
        return Response(
            {"detail": "OTP haipo."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(OTPSerializer(otp).data)


# ==================================================================
# NotificationLog — LIST (auth) + CREATE (auth)
# ==================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def logs_list(request):
    """
    Orodhesha taarifa. Filters:
      ?channel=sms|email
      ?recipient=<namba au email>
      ?success=true|false
      ?read=true|false
      ?limit=<idadi> (default 200)
    """
    qs = NotificationLog.objects.all().order_by("-created_at")

    # Filters
    channel = request.query_params.get("channel")
    recipient = request.query_params.get("recipient")
    success = request.query_params.get("success")
    read = request.query_params.get("read")

    if channel in ("sms", "email"):
        qs = qs.filter(channel=channel)

    if recipient:
        qs = qs.filter(
            Q(recipient__icontains=recipient)
            | Q(recipient__iexact=recipient)
        )

    if success in ("true", "false"):
        qs = qs.filter(success=(success == "true"))

    if read in ("true", "false"):
        qs = qs.filter(read=(read == "true"))

    # Limit
    try:
        limit = int(request.query_params.get("limit", 200))
    except ValueError:
        limit = 200
    limit = max(1, min(limit, 500))

    qs = qs[:limit]
    return Response(NotificationLogSerializer(qs, many=True).data)


# ==================================================================
# NotificationLog — DETAIL (GET / PATCH / DELETE)
# ==================================================================
@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def log_detail(request, pk):
    log = get_object_or_404(NotificationLog, pk=pk)

    # ------------------------------------------------------------------
    # GET — undani
    # ------------------------------------------------------------------
    if request.method == "GET":
        return Response(NotificationLogSerializer(log).data)

    # ------------------------------------------------------------------
    # PATCH — weka read=true (au false) tu
    # ------------------------------------------------------------------
    if request.method == "PATCH":
        # Ruhusu tu "read" kubadilishwa
        allowed = {"read"}
        payload = {k: v for k, v in request.data.items() if k in allowed}
        if not payload:
            return Response(
                {"detail": "Hakuna field inayoruhusiwa kubadilishwa."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = NotificationLogSerializer(
            log, data=payload, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ------------------------------------------------------------------
    # DELETE — futa
    # ------------------------------------------------------------------
    log.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ==================================================================
# Stats — idadi ya SMS/Email zilizotumwa
# ==================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats(request):
    total = NotificationLog.objects.count()
    sms = NotificationLog.objects.filter(channel="sms")
    email = NotificationLog.objects.filter(channel="email")
    sms_ok = sms.filter(success=True).count()
    email_ok = email.filter(success=True).count()
    unread = NotificationLog.objects.filter(read=False).count()
    return Response({
        "total": total,
        "read": total - unread,
        "unread": unread,
        "sms_total": sms.count(),
        "sms_success": sms_ok,
        "sms_failed": sms.count() - sms_ok,
        "email_total": email.count(),
        "email_success": email_ok,
        "email_failed": email.count() - email_ok,
    })