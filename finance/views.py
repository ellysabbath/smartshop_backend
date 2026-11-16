from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ProfitCalc, TitheOffering
from .serializers import ProfitCalcSerializer, TitheOfferingSerializer
from sales.models import Order, OrderItem
from expenses.models import Expense
from staff.models import Salary


def _compute_profit(store_id=None, start=None, end=None):
    orders = Order.objects.filter(status=Order.Status.COMPLETED)
    if store_id:
        orders = orders.filter(store_id=store_id)
    if start:
        orders = orders.filter(order_date__date__gte=start)
    if end:
        orders = orders.filter(order_date__date__lte=end)

    total_sales = orders.aggregate(s=Sum("total"))["s"] or Decimal("0")

    items = OrderItem.objects.filter(order__in=orders)
    total_cogs = sum(
        Decimal(str(i.unit_cost)) * Decimal(str(i.quantity))
        for i in items
    )

    exp = Expense.objects.all()
    if store_id:
        exp = exp.filter(store_id=store_id)
    if start:
        exp = exp.filter(expense_date__gte=start)
    if end:
        exp = exp.filter(expense_date__lte=end)
    total_opex = exp.aggregate(s=Sum("amount"))["s"] or Decimal("0")

    sal = Salary.objects.filter(status=Salary.Status.PAID)
    if store_id:
        sal = sal.filter(store_id=store_id)
    if start:
        sal = sal.filter(month__gte=start)
    if end:
        sal = sal.filter(month__lte=end)
    total_salaries = sal.aggregate(s=Sum("total_paid"))["s"] or Decimal("0")

    gross = total_sales - total_cogs
    total_exp = Decimal(str(total_opex)) + Decimal(str(total_salaries))
    net = gross - total_exp
    zaka = net * Decimal("0.10") if net > 0 else Decimal("0")
    sadaka = net * Decimal("0.10") if net > 0 else Decimal("0")
    remaining = net - zaka - sadaka

    return {
        "total_sales": total_sales,
        "total_cogs": total_cogs,
        "gross_profit": gross,
        "total_opex": total_opex,
        "total_salaries": total_salaries,
        "total_expenses": total_exp,
        "net_profit": net,
        "zaka_amount": zaka,
        "sadaka_amount": sadaka,
        "remaining": remaining,
        "is_loss": net < 0,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profit_summary(request):
    """GET /api/finance/profit/?store=<uuid>&start=YYYY-MM-DD&end=YYYY-MM-DD"""
    store_id = request.query_params.get("store")
    start = request.query_params.get("start")
    end = request.query_params.get("end")
    data = _compute_profit(store_id, start, end)
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_profit_snapshot(request):
    """POST /api/finance/profit/snapshot/ — hifadhi ProfitCalc"""
    store_id = request.data.get("store_id")
    start = request.data.get("period_start")
    end = request.data.get("period_end")
    if not start or not end:
        return Response({"detail": "period_start, period_end vinahitajika."},
                        status=status.HTTP_400_BAD_REQUEST)
    computed = _compute_profit(store_id, start, end)
    calc = ProfitCalc.objects.create(
        store_id=store_id, period_start=start, period_end=end,
        **computed,
    )
    return Response(ProfitCalcSerializer(calc).data,
                    status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def tithe_offerings_list_create(request):
    if request.method == "GET":
        qs = TitheOffering.objects.all().order_by("-paid_date")
        return Response(TitheOfferingSerializer(qs, many=True).data)

    serializer = TitheOfferingSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(recorded_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)