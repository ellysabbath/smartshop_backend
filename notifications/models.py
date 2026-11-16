from django.db import models
from core.models import UUIDModel


class OTP(UUIDModel):
    class Purpose(models.TextChoices):
        LOGIN = "login", "Login"
        RESET = "reset", "Reset Password"
        VERIFY = "verify", "Verify Phone"

    phone = models.CharField(max_length=15, db_index=True)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=Purpose.choices,
                               default=Purpose.RESET)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta(UUIDModel.Meta):
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone", "code", "is_used"]),
        ]

    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP {self.phone} — {self.purpose}"


class NotificationLog(UUIDModel):
    class Channel(models.TextChoices):
        SMS = "sms", "SMS"
        EMAIL = "email", "Email"

    channel = models.CharField(max_length=10, choices=Channel.choices, db_index=True)
    recipient = models.CharField(max_length=150, db_index=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    success = models.BooleanField(default=False, db_index=True)
    error = models.TextField(blank=True)
    read = models.BooleanField(default=False, db_index=True)  # ← MPYA

    class Meta(UUIDModel.Meta):
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.channel} → {self.recipient} ({'OK' if self.success else 'FAIL'})"