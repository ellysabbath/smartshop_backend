from django.db import models

# Create your models here.
from django.db import models
from core.models import UUIDModel


class Customer(UUIDModel):
    class Type(models.TextChoices):
        RETAIL = "rejareja", "Rejareja"
        WHOLESALE = "jumla", "Jumla"
        CONTRACTOR = "mkandarasi", "Mkandarasi"

    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, unique=True)
    location = models.CharField(max_length=200, blank=True)
    customer_type = models.CharField(max_length=20, choices=Type.choices,
                                     default=Type.RETAIL)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return self.full_name