from django.shortcuts import render

# Create your views here.
from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ProductReport
from .serializers import ProductReportSerializer
from inventory.models import StockLevel, StockMovement


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def reports_list_create(request):
    if request.method == "GET":
        qs = ProductReport.objects.all().select_related("product", "reported_by")
        return Response(ProductReportSerializer(qs, many=True).data)

    serializer = ProductReportSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(reported_by=request.user,
                        status=ProductReport.Status.PENDING)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def report_detail(request, pk):
    r = get_object_or_404(ProductReport, pk=pk)
    return Response(ProductReportSerializer(r).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_report(request, pk):
    report = get_object_or_404(ProductReport, pk=pk)
    if report.status != ProductReport.Status.PENDING:
        return Response({"detail": "Ripoti tayari imeshughulikiwa."},
                        status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        report.status = ProductReport.Status.APPROVED
        report.approved_by = request.user
        report.save()

        level, _ = StockLevel.objects.get_or_create(
            product=report.product, store=report.store,
            defaults={"quantity": 0},
        )
        qty = Decimal(str(report.quantity))
        level.quantity = Decimal(str(level.quantity)) - qty
        level.save()

        StockMovement.objects.create(
            product=report.product, store=report.store,
            movement_type=StockMovement.Type.DAMAGE,
            quantity=-qty, unit_cost=report.product.cost_price,
            reference_id=report.id, reference_type="report",
            note=report.description,
            created_by=request.user,
        )

    return Response(ProductReportSerializer(report).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_report(request, pk):
    report = get_object_or_404(ProductReport, pk=pk)
    if report.status != ProductReport.Status.PENDING:
        return Response({"detail": "Ripoti tayari imeshughulikiwa."},
                        status=status.HTTP_400_BAD_REQUEST)
    report.status = ProductReport.Status.REJECTED
    report.approved_by = request.user
    report.save()
    return Response(ProductReportSerializer(report).data)