from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField

from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel


class Dhow(UniversalIdModel, TimeStampedModel, ReferenceModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    total_capacity = models.PositiveIntegerField(
        default=50, help_text="Maximum guests vessel can physically accommodate"
    )
    min_quota = models.PositiveIntegerField(
        default=10, help_text="Minimum confirmed guests required to sail"
    )
    image = CloudinaryField("image", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dhows_created",
    )

    class Meta:
        verbose_name = "Dhow"
        verbose_name_plural = "Dhows"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
