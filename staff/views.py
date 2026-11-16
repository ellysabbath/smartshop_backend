from django.shortcuts import render

# Create your views here.
from datetime import date

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Salary
from .serializers import SalarySerializer
from accounts.models import User
from notifications.services import send_sms, sms_salary_paid


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def salaries_list_create(request):
    if request.method == "GET":
        qs = Salary.objects.all().select_related("staff", "store")
        return Response(SalarySerializer(qs, many=True).data)

    data = request.data
    staff_id = data.get("staff_id") or data.get("staff")
    store_id = data.get("store_id") or data.get("store")
    month_str = data.get("month")
    basic = data.get("basic_salary", 0)
    allowances = data.get("allowances", 0)
    deductions = data.get("deductions", 0)

    if not staff_id or not store_id or not month_str:
        return Response(
            {"detail": "staff_id, store_id, month vinahitajika."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    year, mon, day = [int(x) for x in month_str.split("-")] if len(month_str.split("-")) == 3 else (int(month_str[:4]), int(month_str[5:7]), 1)
    month_date = date(year, mon, 1)
    total_paid = float(basic) + float(allowances) - float(deductions)

    salary = Salary.objects.create(
        staff_id=staff_id, store_id=store_id, month=month_date,
        basic_salary=basic, allowances=allowances,
        deductions=deductions, total_paid=total_paid,
    )
    return Response(SalarySerializer(salary).data,
                    status=status.HTTP_201_CREATED)


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def salaries_detail(request, pk):
    salary = get_object_or_404(Salary, pk=pk)
    if request.method == "GET":
        return Response(SalarySerializer(salary).data)
    salary.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pay_salary(request, pk):
    salary = get_object_or_404(Salary, pk=pk)
    if salary.status == Salary.Status.PAID:
        return Response({"detail": "Mshahara tayari umelipwa."},
                        status=status.HTTP_400_BAD_REQUEST)
    salary.status = Salary.Status.PAID
    salary.paid_at = timezone.now()
    salary.save()

    try:
        send_sms(
            salary.staff.phone,
            sms_salary_paid(salary.month.strftime("%m/%Y"),
                            f"{salary.total_paid:.0f}"),
        )
    except Exception:
        pass

    return Response(SalarySerializer(salary).data)