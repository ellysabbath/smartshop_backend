from django.db import models

# Create your models here.
from django.db import models

from core.models import UUIDModel


class Document(UUIDModel):
    class Aina(models.TextChoices):
        MAUZO = "mauzo", "Mauzo"
        STOKI = "stoki", "Stoki"
        WATEJA = "wateja", "Wateja"
        MADENI = "madeni", "Madeni"
        GHARAMA = "gharama", "Gharama"
        JUMLA = "jumla", "Jumla"

    class Format(models.TextChoices):
        PDF = "pdf", "PDF"
        CSV = "csv", "CSV"
        EXCEL = "excel", "Excel"

    class Hali(models.TextChoices):
        TAYARI = "tayari", "Tayari"
        INASINDIKA = "inasindika", "Inasindika"
        IMEMALIZIKA = "imemalizika", "Imemalizika"

    jina = models.CharField(max_length=200)
    aina = models.CharField(max_length=20, choices=Aina.choices)
    format = models.CharField(
        max_length=10, choices=Format.choices, default=Format.PDF
    )
    hali = models.CharField(
        max_length=20, choices=Hali.choices, default=Hali.TAYARI
    )
    ukubwa = models.CharField(max_length=20, default="0 KB")
    kipindi = models.CharField(max_length=80, blank=True)

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )
    aliyezalisha = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="documents_made",
    )

    # Snapshot ya data wakati document ilizalishwa
    data_snapshot = models.JSONField(default=dict, blank=True)

    class Meta(UUIDModel.Meta):
        db_table = "documents_document"
        indexes = [
            models.Index(fields=["store", "aina"]),
            models.Index(fields=["hali"]),
        ]

    def __str__(self):
        return f"{self.jina} ({self.aina})"