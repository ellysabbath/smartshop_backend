from django.db import models

from core.models import UUIDModel


# ==================================================================
# StockLevel — stoki ya sasa (cache)
# ==================================================================
class StockLevel(UUIDModel):
    """
    Stoki ya sasa ya bidhaa kwenye duka.
    Ni cache — inasasishwa kila StockMovement inapoundwa.
    """
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="stock_levels",
    )
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="stock_levels",
    )
    quantity = models.DecimalField(
        max_digits=14, decimal_places=3, default=0
    )

    class Meta(UUIDModel.Meta):
        db_table = "inventory_stocklevel"
        unique_together = [("product", "store")]
        indexes = [
            models.Index(fields=["product", "store"]),
        ]

    def __str__(self):
        return f"{self.product.name} @ {self.store.name}: {self.quantity}"


# ==================================================================
# StockMovement — ledger ya kila mwendo
# ==================================================================
class StockMovement(UUIDModel):
    """
    Kila mwendo wa stoki (kuingia, kutoka, kurekebisha).
    Hii ni source of truth — StockLevel ni cache.
    """

    class Type(models.TextChoices):
        PURCHASE = "manunuzi", "Manunuzi"
        SALE = "mauzo", "Mauzo"
        RETURN = "kurudisha", "Kurudisha"
        ADJUSTMENT = "marekebisho", "Marekebisho"
        DAMAGE = "uharibifu", "Uharibifu"

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    movement_type = models.CharField(
        max_length=20, choices=Type.choices, db_index=True
    )
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    reference_id = models.UUIDField(null=True, blank=True)
    reference_type = models.CharField(max_length=30, blank=True)
    note = models.CharField(max_length=250, blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )

    class Meta(UUIDModel.Meta):
        db_table = "inventory_stockmovement"
        indexes = [
            models.Index(fields=["product", "store"]),
            models.Index(fields=["movement_type"]),
            models.Index(fields=["reference_id"]),
        ]

    def __str__(self):
        sign = "+" if self.quantity > 0 else ""
        return f"{sign}{self.quantity} {self.product.name} ({self.movement_type})"


# ==================================================================
# StockAdjustment — marekebisho yanayohitaji idhini
# ==================================================================
class StockAdjustment(UUIDModel):
    """
    Marekebisho ya stoki yanayohitaji idhini ya mmiliki.
    Mfano: uharibifu, upotevu, marekebisho ya makosa.
    """

    class Status(models.TextChoices):
        PENDING = "inasubiri", "Inasubiri"
        APPROVED = "imekubaliwa", "Imekubaliwa"
        REJECTED = "imekataliwa", "Imekataliwa"

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="stock_adjustments",
    )
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="stock_adjustments",
    )
    reason = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
        db_index=True,
    )
    requested_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="adjustments_requested",
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="adjustments_approved",
    )

    class Meta(UUIDModel.Meta):
        db_table = "inventory_stockadjustment"
        indexes = [
            models.Index(fields=["store", "status"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self):
        return f"{self.product.name} ({self.quantity}) — {self.status}"