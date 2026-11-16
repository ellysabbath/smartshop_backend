from rest_framework import serializers
from .models import Salary


class SalarySerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.full_name", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)

    class Meta:
        model = Salary
        fields = ["id", "staff", "staff_name", "store", "store_name",
                  "month", "basic_salary", "allowances", "deductions",
                  "total_paid", "status", "paid_at"]
        read_only_fields = ["id", "total_paid", "status", "paid_at"]