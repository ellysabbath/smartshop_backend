from django.db import models

# Create your models here.
from django.db import models
from core.models import UUIDModel


class Supplier(UUIDModel):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=250, blank=True)

    def __str__(self):
        return self.name