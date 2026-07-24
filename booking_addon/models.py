from django.db import models
from accounts.abstracts import UniversalIdModel, TimeStampedModel


class BookingAddOn(UniversalIdModel, TimeStampedModel):
    booking = models.ForeignKey(
        "booking.Booking",
        on_delete=models.CASCADE,
        related_name="booking_addons",
    )
    addon = models.ForeignKey(
        "addon.AddOn",
        on_delete=models.PROTECT,
        related_name="booking_addons",
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Price snapshot at time of booking"
    )

    class Meta:
        verbose_name = "Booking Add-On"
        verbose_name_plural = "Booking Add-Ons"
        ordering = ["booking", "addon"]

    def __str__(self):
        return f"{self.addon.name} x{self.quantity} ({self.booking.reference})"

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        if not self.unit_price and self.addon:
            self.unit_price = self.addon.price
        super().save(*args, **kwargs)
