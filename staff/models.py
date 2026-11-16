from django.db import models

# Create your models here.
from django.db import models
from core.models import UUIDModel


class Salary(UUIDModel):
    class Status(models.TextChoices):
        PENDING = "inasubiri", "Inasubiri"
        PAID = "imelipwa", "Imelipwa"

    staff = models.ForeignKey("accounts.User", on_delete=models.CASCADE,
                              related_name="salaries")
    store = models.ForeignKey("stores.Store", on_delete=models.CASCADE,
                              related_name="salaries")
    month = models.DateField()
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices,
                              default=Status.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta(UUIDModel.Meta):
        unique_together = [("staff", "month")]