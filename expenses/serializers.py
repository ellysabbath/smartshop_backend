from rest_framework import serializers

from .models import ExpenseCategory, ExpenseRequest, Expense


# ==================================================================
# Category
# ==================================================================
class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ["id", "name"]
        read_only_fields = ["id"]


# ==================================================================
# Expense Request
# ==================================================================
class ExpenseRequestSerializer(serializers.ModelSerializer):
    # Read-only display fields
    requested_by_name = serializers.CharField(
        source="requested_by.full_name", read_only=True
    )
    category_name = serializers.CharField(
        source="category.name", read_only=True
    )
    store_name = serializers.CharField(source="store.name", read_only=True)
    approved_by_name = serializers.CharField(
        source="approved_by.full_name", read_only=True, default=None
    )

    # Write-only field: aina ya matumizi inaandikwa kwa mkono
    category_text = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )

    class Meta:
        model = ExpenseRequest
        fields = [
            "id",
            "store",
            "store_name",
            "category",
            "category_name",
            "category_text",
            "requested_by",
            "requested_by_name",
            "description",
            "reason",
            "amount",
            "status",
            "approved_by",
            "approved_by_name",
            "approval_notes",
            "request_date",
        ]
        read_only_fields = [
            "id",
            "requested_by",
            "status",
            "approved_by",
            "request_date",
        ]
        extra_kwargs = {
            "category": {"required": False},
            "approved_by": {"required": False},
        }

    def validate_amount(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError(
                "Kiasi lazima kiwe zaidi ya 0."
            )
        return value

    def validate(self, attrs):
        # Kama category haipo na category_text pia haipo → kosa
        category = attrs.get("category")
        category_text = (attrs.get("category_text") or "").strip()
        if not category and not category_text:
            raise serializers.ValidationError(
                {"category_text": "Aina ya matumizi inahitajika."}
            )
        return attrs

    def create(self, validated_data):
        # Toa category_text kabla ya kuunda
        category_text = (validated_data.pop("category_text", "") or "").strip()
        category = validated_data.get("category")

        # Kama category haipo lakini category_text ipo → unda au tumia iliyopo
        if not category and category_text:
            cat = ExpenseCategory.objects.filter(
                name__iexact=category_text
            ).first()
            if not cat:
                cat = ExpenseCategory.objects.create(name=category_text)
            validated_data["category"] = cat

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Vivyo hivyo kwa update
        category_text = (validated_data.pop("category_text", "") or "").strip()
        category = validated_data.get("category")

        if not category and category_text:
            cat = ExpenseCategory.objects.filter(
                name__iexact=category_text
            ).first()
            if not cat:
                cat = ExpenseCategory.objects.create(name=category_text)
            validated_data["category"] = cat

        return super().update(instance, validated_data)


# ==================================================================
# Expense (matumizi yaliyokubaliwa)
# ==================================================================
class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name", read_only=True
    )
    store_name = serializers.CharField(source="store.name", read_only=True)
    recorded_by_name = serializers.CharField(
        source="recorded_by.full_name", read_only=True
    )

    class Meta:
        model = Expense
        fields = [
            "id",
            "request",
            "store",
            "store_name",
            "category",
            "category_name",
            "amount",
            "expense_date",
            "description",
            "recorded_by",
            "recorded_by_name",
        ]
        read_only_fields = ["id", "recorded_by"]