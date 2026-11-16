from django.db import models

# Create your models here.
from django.db import models
from core.models import UUIDModel


class Category(UUIDModel):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name


class Unit(UUIDModel):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class Product(UUIDModel):
    sku = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.PROTECT,
                                 related_name="products")
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    low_stock_alert = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.sku} — {self.name}"

