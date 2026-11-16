from django.db import models

# Create your models here.
from django.db import models
from core.models import UUIDModel


class ProfitCalc(UUIDModel):
    store = models.ForeignKey("stores.Store", null=True, blank=True,
                              on_delete=models.CASCADE)
    period_start = models.DateField()
    period_end = models.DateField()
    total_sales = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_cogs = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_opex = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_salaries = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    zaka_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    sadaka_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    remaining = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_loss = models.BooleanField(default=False)
    generated_at = models.DateTimeField(auto_now_add=True)


class TitheOffering(UUIDModel):
    class Type(models.TextChoices):
        ZAKA = "zaka", "Zaka"
        SADAKA = "sadaka", "Sadaka"

    payment_type = models.CharField(max_length=20, choices=Type.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    receipt_number = models.CharField(max_length=50)
    note = models.CharField(max_length=250, blank=True)
    paid_date = models.DateField()
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)