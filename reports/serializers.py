from rest_framework import serializers
from .models import ProductReport


class ProductReportSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    reported_by_name = serializers.CharField(source="reported_by.full_name",
                                             read_only=True)

    class Meta:
        model = ProductReport
        fields = ["id", "product", "product_name", "store",
                  "report_type", "quantity", "estimated_value",
                  "description", "reported_by", "reported_by_name",
                  "status", "approved_by", "report_date"]
        read_only_fields = ["id", "reported_by", "status",
                            "approved_by", "report_date"]