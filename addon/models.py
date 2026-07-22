from django.db import models
from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel


class AddOn(UniversalIdModel, TimeStampedModel, ReferenceModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_available = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Add-On"
        verbose_name_plural = "Add-Ons"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - KES {self.price}"
