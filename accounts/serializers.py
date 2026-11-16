from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["id", "phone", "full_name", "role", "store",
                  "is_active", "password"]

    def create(self, validated):
        pw = validated.pop("password", None)
        return User.objects.create_user(password=pw, **validated)