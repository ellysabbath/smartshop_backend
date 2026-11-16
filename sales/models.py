from django.db import models

# Create your models here.
from django.db import models
from core.models import UUIDModel


class Order(UUIDModel):
    class Status(models.TextChoices):
        PENDING = "inasubiri_malipo", "Inasubiri Malipo"
        COMPLETED = "imekamilika", "Imekamilika"
        REJECTED = "imekataliwa", "Imekataliwa"

    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT,
                                 related_name="orders")
    store = models.ForeignKey("stores.Store", on_delete=models.PROTECT,
                              related_name="orders")
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices,
                              default=Status.PENDING)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)


class OrderItem(UUIDModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)


class Payment(UUIDModel):
    class Method(models.TextChoices):
        MPESA = "mpesa", "M-Pesa"
        TIGOPESA = "tigopesa", "Tigo Pesa"
        AIRTEL = "airtel", "Airtel Money"
        HALOPESA = "halopesa", "Halo Pesa"
        CASH = "cash", "Cash"
        BANK = "bank", "Bank"

    class Status(models.TextChoices):
        PENDING = "inasubiri", "Inasubiri"
        CONFIRMED = "imethibitishwa", "Imethibitishwa"
        REJECTED = "imekataliwa", "Imekataliwa"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    method = models.CharField(max_length=20, choices=Method.choices)
    phone = models.CharField(max_length=15, blank=True)
    reference = models.CharField(max_length=80)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices,
                              default=Status.PENDING)
    confirmed_by = models.ForeignKey("accounts.User", null=True, blank=True,
                                     on_delete=models.SET_NULL)
    confirmed_at = models.DateTimeField(null=True, blank=True)