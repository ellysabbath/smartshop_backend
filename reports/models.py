from django.db import models

# Create your models here.
from django.db import models
from core.models import UUIDModel


class ProductReport(UUIDModel):
    class Type(models.TextChoices):
        DAMAGE = "uharibifu", "Uharibifu"
        EXPIRY = "expiry", "Expiry"
        LOSS = "upotevu", "Upotevu"
        RETURN_SUPPLIER = "kurudisha_msambazaji", "Kurudisha Msambazaji"

    class Status(models.TextChoices):
        PENDING = "inasubiri", "Inasubiri"
        APPROVED = "imethibitishwa", "Imethibitishwa"
        REJECTED = "imekataliwa", "Imekataliwa"

    product = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    store = models.ForeignKey("stores.Store", on_delete=models.PROTECT)
    report_type = models.CharField(max_length=30, choices=Type.choices)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=250)
    reported_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT,
                                    related_name="reports_made")
    status = models.CharField(max_length=20, choices=Status.choices,
                              default=Status.PENDING)
    approved_by = models.ForeignKey("accounts.User", null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name="reports_approved")
    report_date = models.DateTimeField(auto_now_add=True)