from django.db import models

# Create your models here.
import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra):
        if not phone:
            raise ValueError("Phone is required")
        user = self.model(phone=phone, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", User.Role.MMIlIKI)
        extra.setdefault("full_name", "Super Admin")
        return self.create_user(phone, password, **extra)


class User(AbstractUser):
    class Role(models.TextChoices):
        MMIlIKI = "mmiliki", "Mmiliki"
        ADMIN = "admin", "Admin"
        MHazini = "mhazini", "Mhazini"
        MUUZAJI = "muuzaji", "Muuzaji"
        MTEJA = "mteja", "Mteja"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    phone = models.CharField(max_length=15, unique=True)
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=Role.choices)
    store = models.ForeignKey("stores.Store", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="staff")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name", "role"]

    objects = UserManager()

    def __str__(self):
        return f"{self.full_name} ({self.role})"