from rest_framework import serializers

from .models import Category, Unit, Product


# ==================================================================
# Category
# ==================================================================
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]
        read_only_fields = ["id"]


# ==================================================================
# Unit
# ==================================================================
class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ["id", "name"]
        read_only_fields = ["id"]


# ==================================================================
# Product — inakubali category_text na unit_text
# ==================================================================
class ProductSerializer(serializers.ModelSerializer):
    # Read-only display fields
    category_name = serializers.CharField(
        source="category.name", read_only=True
    )
    unit_name = serializers.CharField(
        source="unit.name", read_only=True
    )

    # ✅ Write-only fields za maandishi
    category_text = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    unit_text = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "sku", "name",
            "category", "category_name", "category_text",
            "unit", "unit_name", "unit_text",
            "cost_price", "selling_price",
            "low_stock_alert", "is_active",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "category": {"required": False},
            "unit": {"required": False},
        }

    def validate_sku(self, value):
        """Thibitisha SKU ni unique (isipokuwa kwa update)."""
        if not value:
            raise serializers.ValidationError("SKU inahitajika.")

        qs = Product.objects.filter(sku__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "SKU hii tayari imetumika."
            )
        return value.upper()

    def create(self, validated_data):
        # Toa category_text / unit_text kabla ya kuunda
        category_text = (
            validated_data.pop("category_text", "") or ""
        ).strip()
        unit_text = (validated_data.pop("unit_text", "") or "").strip()

        category = validated_data.get("category")
        unit = validated_data.get("unit")

        # Kama category haipo lakini category_text ipo → unda au tumia iliyopo
        if not category and category_text:
            cat = Category.objects.filter(
                name__iexact=category_text
            ).first()
            if not cat:
                cat = Category.objects.create(name=category_text)
            validated_data["category"] = cat

        # Kama unit haipo lakini unit_text ipo → unda au tumia iliyopo
        if not unit and unit_text:
            u = Unit.objects.filter(name__iexact=unit_text).first()
            if not u:
                u = Unit.objects.create(name=unit_text)
            validated_data["unit"] = u

        # Validate
        if not validated_data.get("category"):
            raise serializers.ValidationError(
                {"category_text": "Kundi linahitajika."}
            )
        if not validated_data.get("unit"):
            raise serializers.ValidationError(
                {"unit_text": "Kipimo linahitajika."}
            )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        category_text = (
            validated_data.pop("category_text", "") or ""
        ).strip()
        unit_text = (validated_data.pop("unit_text", "") or "").strip()

        category = validated_data.get("category")
        unit = validated_data.get("unit")

        if not category and category_text:
            cat = Category.objects.filter(
                name__iexact=category_text
            ).first()
            if not cat:
                cat = Category.objects.create(name=category_text)
            validated_data["category"] = cat

        if not unit and unit_text:
            u = Unit.objects.filter(name__iexact=unit_text).first()
            if not u:
                u = Unit.objects.create(name=unit_text)
            validated_data["unit"] = u

        return super().update(instance, validated_data)