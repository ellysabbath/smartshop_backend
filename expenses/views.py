from datetime import date

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notifications.services import send_sms, sms_expense_decision

from .models import ExpenseCategory, ExpenseRequest, Expense
from .serializers import (
    ExpenseCategorySerializer,
    ExpenseRequestSerializer,
    ExpenseSerializer,
)


# ==================================================================
# Helper
# ==================================================================
def _notify_requester(request_obj, approved: bool):
    """Tuma SMS kwa aliyeomba (best-effort)."""
    try:
        phone = request_obj.requested_by.phone
        send_sms(
            phone,
            sms_expense_decision(
                str(request_obj.id),
                approved,
                f"{request_obj.amount:.0f}",
            ),
        )
    except Exception:
        # Usizuie mchakato kama SMS imeshindikana
        pass


# ==================================================================
# CATEGORIES — GET (list) + POST (create)
# ==================================================================
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def categories_list_create(request):
    if request.method == "GET":
        qs = ExpenseCategory.objects.all().order_by("name")
        return Response(ExpenseCategorySerializer(qs, many=True).data)

    serializer = ExpenseCategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================================================================
# EXPENSE REQUESTS — GET (list) + POST (create)
# ==================================================================
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def requests_list_create(request):
    # ------------------------------------------------------------------
    # GET — orodhesha maombi
    # ------------------------------------------------------------------
    if request.method == "GET":
        qs = ExpenseRequest.objects.select_related(
            "store", "category", "requested_by", "approved_by"
        ).all()

        # Filters
        store_id = request.query_params.get("store")
        requested_by_id = request.query_params.get("requested_by")
        status_param = request.query_params.get("status")

        if store_id:
            qs = qs.filter(store_id=store_id)
        if requested_by_id:
            qs = qs.filter(requested_by_id=requested_by_id)
        if status_param:
            qs = qs.filter(status=status_param)

        qs = qs.order_by("-request_date")
        return Response(ExpenseRequestSerializer(qs, many=True).data)

    # ------------------------------------------------------------------
    # POST — unda ombi jipya
    # ------------------------------------------------------------------
    serializer = ExpenseRequestSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(
            requested_by=request.user,
            status=ExpenseRequest.Status.PENDING,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================================================================
# EXPENSE REQUEST DETAIL
# ==================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def requests_detail(request, pk):
    req = get_object_or_404(
        ExpenseRequest.objects.select_related(
            "store", "category", "requested_by", "approved_by"
        ),
        pk=pk,
    )
    return Response(ExpenseRequestSerializer(req).data)


# ==================================================================
# APPROVE REQUEST — kubali ombi + unda Expense
# ==================================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_request(request, pk):
    req = get_object_or_404(
        ExpenseRequest.objects.select_related(
            "store", "category", "requested_by"
        ),
        pk=pk,
    )

    if req.status != ExpenseRequest.Status.PENDING:
        return Response(
            {"detail": "Ombi hili tayari limeshughulikiwa."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Sasisha ombi
    req.status = ExpenseRequest.Status.APPROVED
    req.approved_by = request.user
    req.approval_notes = request.data.get("approval_notes", "")
    req.save(update_fields=["status", "approved_by", "approval_notes"])

    # Unda Expense moja kwa moja
    Expense.objects.create(
        request=req,
        store=req.store,
        category=req.category,
        amount=req.amount,
        expense_date=date.today(),
        description=req.description,
        recorded_by=request.user,
    )

    # Tuma SMS (best-effort)
    _notify_requester(req, approved=True)

    return Response(ExpenseRequestSerializer(req).data)


# ==================================================================
# REJECT REQUEST — kataa ombi
# ==================================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_request(request, pk):
    req = get_object_or_404(
        ExpenseRequest.objects.select_related("requested_by"),
        pk=pk,
    )

    if req.status != ExpenseRequest.Status.PENDING:
        return Response(
            {"detail": "Ombi hili tayari limeshughulikiwa."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    notes = (request.data.get("approval_notes", "") or "").strip()
    if not notes:
        return Response(
            {"detail": "Sababu ya kukataa inahitajika."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    req.status = ExpenseRequest.Status.REJECTED
    req.approved_by = request.user
    req.approval_notes = notes
    req.save(update_fields=["status", "approved_by", "approval_notes"])

    # Tuma SMS (best-effort)
    _notify_requester(req, approved=False)

    return Response(ExpenseRequestSerializer(req).data)


# ==================================================================
# EXPENSES — GET (list) + POST (create manually)
# ==================================================================
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def expenses_list_create(request):
    # ------------------------------------------------------------------
    # GET — orodhesha matumizi yaliyokwisha kubaliwa
    # ------------------------------------------------------------------
    if request.method == "GET":
        qs = Expense.objects.select_related(
            "store", "category", "recorded_by", "request"
        ).all()

        store_id = request.query_params.get("store")
        if store_id:
            qs = qs.filter(store_id=store_id)

        qs = qs.order_by("-expense_date", "-created_at")
        return Response(ExpenseSerializer(qs, many=True).data)

    # ------------------------------------------------------------------
    # POST — ongeza matumizi kwa mkono (bila ombi)
    # ------------------------------------------------------------------
    serializer = ExpenseSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(recorded_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================================================================
# EXPENSE DETAIL
# ==================================================================
@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def expense_detail(request, pk):
    expense = get_object_or_404(Expense, pk=pk)

    if request.method == "GET":
        return Response(ExpenseSerializer(expense).data)

    expense.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)