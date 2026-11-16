from rest_framework import serializers

from .models import StockLevel, StockMovement, StockAdjustment


# ==================================================================
# Stock Level
# ==================================================================
class StockLevelSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name", read_only=True
    )
    store_name = serializers.CharField(
        source="store.name", read_only=True
    )

    class Meta:
        model = StockLevel
        fields = [
            "id",
            "product", "product_name",
            "store", "store_name",
            "quantity",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]


# ==================================================================
# Stock Movement
# ==================================================================
class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name", read_only=True
    )
    store_name = serializers.CharField(
        source="store.name", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "product", "product_name",
            "store", "store_name",
            "movement_type", "quantity", "unit_cost",
            "reference_id", "reference_type", "note",
            "created_by", "created_by_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]


# ==================================================================
# Stock Adjustment
# ==================================================================
class StockAdjustmentSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name", read_only=True
    )
    store_name = serializers.CharField(
        source="store.name", read_only=True
    )
    requested_by_name = serializers.CharField(
        source="requested_by.full_name", read_only=True
    )
    approved_by_name = serializers.CharField(
        source="approved_by.full_name", read_only=True, default=None
    )

    class Meta:
        model = StockAdjustment
        fields = [
            "id",
            "product", "product_name",
            "store", "store_name",
            "reason", "quantity", "status",
            "requested_by", "requested_by_name",
            "approved_by", "approved_by_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "requested_by",
            "approved_by",
            "created_at",
        ]