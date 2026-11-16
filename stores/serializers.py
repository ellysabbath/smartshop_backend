from rest_framework import serializers
from .models import Store


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["id", "name", "location", "owner", "is_active",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]