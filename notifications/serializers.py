from rest_framework import serializers
from .models import OTP, NotificationLog


class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ["id", "phone", "code", "purpose", "is_used",
                  "expires_at", "created_at"]
        read_only_fields = ["id", "is_used", "created_at"]


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = ["id", "channel", "recipient", "subject",
                  "message", "success", "error", "read",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]