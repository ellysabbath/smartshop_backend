from rest_framework import serializers
from .models import ProfitCalc, TitheOffering


class ProfitCalcSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfitCalc
        fields = "__all__"


class TitheOfferingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TitheOffering
        fields = ["id", "payment_type", "amount", "receipt_number",
                  "note", "paid_date", "recorded_by"]
        read_only_fields = ["id", "recorded_by"]