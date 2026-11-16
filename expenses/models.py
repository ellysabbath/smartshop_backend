from django.db import models

# Create your models here.
from django.db import models
from core.models import UUIDModel


class ExpenseCategory(UUIDModel):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name


class ExpenseRequest(UUIDModel):
    class Status(models.TextChoices):
        PENDING = "inasubiri", "Inasubiri"
        APPROVED = "imekubaliwa", "Imekubaliwa"
        REJECTED = "imekataliwa", "Imekataliwa"

    store = models.ForeignKey("stores.Store", on_delete=models.PROTECT)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    requested_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT,
                                     related_name="expense_requests")
    description = models.CharField(max_length=250)
    reason = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices,
                              default=Status.PENDING)
    approved_by = models.ForeignKey("accounts.User", null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name="approved_expenses")
    approval_notes = models.TextField(blank=True)
    request_date = models.DateTimeField(auto_now_add=True)


class Expense(UUIDModel):
    request = models.OneToOneField(ExpenseRequest, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="expense")
    store = models.ForeignKey("stores.Store", on_delete=models.PROTECT)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    description = models.CharField(max_length=250)
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)