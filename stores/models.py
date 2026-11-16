from django.db import models

# Create your models here.
from django.db import models
from core.models import UUIDModel


class Store(UUIDModel):
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=200)
    owner = models.ForeignKey("accounts.User", on_delete=models.PROTECT,
                              related_name="owned_stores")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name