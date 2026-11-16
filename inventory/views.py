from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from products.models import Product
from .models import StockLevel, StockMovement, StockAdjustment
from .serializers import (
    StockLevelSerializer,
    StockMovementSerializer,
    StockAdjustmentSerializer,
)


# ==================================================================
# Stock levels
# ==================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stock_levels_list(request):
    qs = StockLevel.objects.select_related("product", "store").all()
    store_id = request.query_params.get("store")
    if store_id:
        qs = qs.filter(store_id=store_id)
    return Response(StockLevelSerializer(qs, many=True).data)


# ==================================================================
# Movements
# ==================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def movements_list(request):
    qs = StockMovement.objects.select_related("product").all()
    product_id = request.query_params.get("product")
    store_id = request.query_params.get("store")
    movement_type = request.query_params.get("movement_type")
    if product_id:
        qs = qs.filter(product_id=product_id)
    if store_id:
        qs = qs.filter(store_id=store_id)
    if movement_type:
        qs = qs.filter(movement_type=movement_type)
    qs = qs.order_by("-created_at")[:500]
    return Response(StockMovementSerializer(qs, many=True).data)


# ==================================================================
# Adjust
# ==================================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def adjust_stock(request):
    product_id = request.data.get("product_id")
    store_id = request.data.get("store_id")
    quantity = request.data.get("quantity")
    movement_type = request.data.get("movement_type", "marekebisho")
    note = request.data.get("note", "")
    reference_id = request.data.get("reference_id")   # ✅ MPYA

    if not product_id or not store_id or quantity is None:
        return Response(
            {"detail": "product_id, store_id, quantity vinahitajika."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    product = get_object_or_404(Product, pk=product_id)
    qty = Decimal(str(quantity))

    with transaction.atomic():
        level, _ = StockLevel.objects.get_or_create(
            product=product,
            store_id=store_id,
            defaults={"quantity": 0},
        )
        level.quantity = Decimal(str(level.quantity)) + qty
        level.save()

        movement = StockMovement.objects.create(
            product=product,
            store_id=store_id,
            movement_type=movement_type,
            quantity=qty,
            unit_cost=product.cost_price,
            reference_id=reference_id,      # ✅ MPYA
            reference_type="adjustment",
            note=note,
            created_by=request.user,
        )

    return Response(
        StockMovementSerializer(movement).data,
        status=status.HTTP_201_CREATED,
    )


# ==================================================================
# Stock adjustments
# ==================================================================
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def stock_adjustments_list_create(request):
    if request.method == "GET":
        qs = StockAdjustment.objects.select_related("product").all()
        store_id = request.query_params.get("store")
        status_param = request.query_params.get("status")
        product_id = request.query_params.get("product")
        if store_id:
            qs = qs.filter(store_id=store_id)
        if status_param:
            qs = qs.filter(status=status_param)
        if product_id:
            qs = qs.filter(product_id=product_id)
        qs = qs.order_by("-created_at")
        return Response(StockAdjustmentSerializer(qs, many=True).data)

    # POST
    product_id = request.data.get("product_id")
    store_id = request.data.get("store_id")
    reason = (request.data.get("reason") or "").strip()
    quantity = request.data.get("quantity")

    if not product_id or not store_id or not reason or quantity is None:
        return Response(
            {"detail": "product_id, store_id, reason, quantity vinahitajika."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    product = get_object_or_404(Product, pk=product_id)
    adj = StockAdjustment.objects.create(
        product=product,
        store_id=store_id,
        reason=reason,
        quantity=quantity,
        status="inasubiri",
        requested_by=request.user,
    )

    return Response(
        StockAdjustmentSerializer(adj).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_adjustment(request, pk):
    adj = get_object_or_404(StockAdjustment, pk=pk)

    if adj.status != "inasubiri":
        return Response(
            {"detail": "Marekebisho yameshughulikiwa."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        adj.status = "imekubaliwa"
        adj.approved_by = request.user
        adj.save()

        # Sasisha stoki
        level, _ = StockLevel.objects.get_or_create(
            product=adj.product,
            store_id=adj.store_id,
            defaults={"quantity": 0},
        )
        level.quantity = Decimal(str(level.quantity)) + Decimal(
            str(adj.quantity)
        )
        level.save()

        # Unda movement
        StockMovement.objects.create(
            product=adj.product,
            store_id=adj.store_id,
            movement_type="marekebisho",
            quantity=adj.quantity,
            unit_cost=adj.product.cost_price,
            reference_id=adj.id,
            reference_type="adjustment",
            note=adj.reason,
            created_by=request.user,
        )

    return Response(StockAdjustmentSerializer(adj).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_adjustment(request, pk):
    adj = get_object_or_404(StockAdjustment, pk=pk)

    if adj.status != "inasubiri":
        return Response(
            {"detail": "Marekebisho yameshughulikiwa."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    adj.status = "imekataliwa"
    adj.approved_by = request.user
    adj.save()

    return Response(StockAdjustmentSerializer(adj).data)