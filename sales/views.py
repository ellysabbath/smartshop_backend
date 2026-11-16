from django.shortcuts import render

# Create your views here.
from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Order, OrderItem, Payment
from .serializers import OrderSerializer, PaymentSerializer
from inventory.models import StockLevel, StockMovement
from products.models import Product
from notifications.services import send_sms, sms_order_confirmed


# ==================================================================
# GET /api/orders/     POST /api/orders/
# ==================================================================
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def orders_list_create(request):
    if request.method == "GET":
        qs = Order.objects.all().select_related("customer", "store")
        serializer = OrderSerializer(qs, many=True)
        return Response(serializer.data)

    # POST — unda order + items + update stoki
    data = request.data
    customer_id = data.get("customer_id")
    store_id = data.get("store_id")
    items = data.get("items", [])
    discount = Decimal(str(data.get("discount", 0)))

    if not customer_id or not store_id or not items:
        return Response(
            {"detail": "customer_id, store_id, items vinahitajika."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        subtotal = Decimal("0")
        prepared = []
        for it in items:
            product = get_object_or_404(Product, pk=it["product_id"])
            qty = Decimal(str(it["quantity"]))
            price = Decimal(str(it.get("unit_price", product.selling_price)))
            cost = Decimal(str(product.cost_price))
            sub = qty * price
            subtotal += sub
            prepared.append((product, qty, price, cost, sub))

        total = subtotal - discount

        order = Order.objects.create(
            customer_id=customer_id,
            store_id=store_id,
            status=Order.Status.PENDING,
            subtotal=subtotal,
            discount=discount,
            total=total,
            created_by=request.user,
        )

        for product, qty, price, cost, sub in prepared:
            OrderItem.objects.create(
                order=order, product=product,
                quantity=qty, unit_price=price,
                unit_cost=cost, subtotal=sub,
            )

        # Punguza stoki papo hapo kama order inaundwa
        for product, qty, price, cost, sub in prepared:
            level, _ = StockLevel.objects.get_or_create(
                product=product, store_id=store_id,
                defaults={"quantity": 0},
            )
            level.quantity = Decimal(str(level.quantity)) - qty
            level.save()

            StockMovement.objects.create(
                product=product, store_id=store_id,
                movement_type=StockMovement.Type.SALE,
                quantity=-qty, unit_cost=cost,
                reference_id=order.id, reference_type="order",
                created_by=request.user,
            )

    return Response(OrderSerializer(order).data,
                    status=status.HTTP_201_CREATED)


# ==================================================================
# GET /api/orders/<uuid>/    PUT    PATCH    DELETE
# ==================================================================
@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def orders_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == "GET":
        return Response(OrderSerializer(order).data)

    if request.method in ("PUT", "PATCH"):
        serializer = OrderSerializer(
            order, data=request.data, partial=(request.method == "PATCH"),
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    order.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ==================================================================
# POST /api/orders/<uuid>/payments/    (ongeza malipo)
# ==================================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_payment(request, pk):
    order = get_object_or_404(Order, pk=pk)
    serializer = PaymentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    payment = serializer.save(order=order, status=Payment.Status.PENDING)
    return Response(PaymentSerializer(payment).data,
                    status=status.HTTP_201_CREATED)


# ==================================================================
# POST /api/orders/<uuid>/payments/<payment_uuid>/confirm/
# ==================================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirm_payment(request, pk, payment_pk):
    order = get_object_or_404(Order, pk=pk)
    payment = get_object_or_404(Payment, pk=payment_pk, order=order)

    if payment.status != Payment.Status.PENDING:
        return Response({"detail": "Malipo haya tayari yameshughulikiwa."},
                        status=status.HTTP_400_BAD_REQUEST)

    payment.status = Payment.Status.CONFIRMED
    payment.confirmed_by = request.user
    payment.confirmed_at = timezone.now()
    payment.save()

    # Angalia kama jumla ya malipo yaliyothibitishwa >= total
    paid = sum(
        Decimal(str(p.amount)) for p in order.payments.all()
        if p.status == Payment.Status.CONFIRMED
    )
    if paid >= Decimal(str(order.total)):
        order.status = Order.Status.COMPLETED
        order.save()

        # SMS kwa mteja
        try:
            send_sms(
                order.customer.phone,
                sms_order_confirmed(str(order.id), f"{order.total:.0f}"),
            )
        except Exception:
            pass

    return Response(OrderSerializer(order).data)


# ==================================================================
# POST /api/orders/<uuid>/payments/<payment_uuid>/reject/
# ==================================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_payment(request, pk, payment_pk):
    order = get_object_or_404(Order, pk=pk)
    payment = get_object_or_404(Payment, pk=payment_pk, order=order)

    payment.status = Payment.Status.REJECTED
    payment.confirmed_by = request.user
    payment.confirmed_at = timezone.now()
    payment.save()

    return Response(PaymentSerializer(payment).data)