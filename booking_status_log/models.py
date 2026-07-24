from django.db import models
from django.conf import settings
from accounts.abstracts import UniversalIdModel, TimeStampedModel


class BookingStatusLog(UniversalIdModel, TimeStampedModel):
    booking = models.ForeignKey(
        "booking.Booking",
        on_delete=models.CASCADE,
        related_name="status_logs",
    )
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_status_logs",
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Booking Status Log"
        verbose_name_plural = "Booking Status Logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking {self.booking.reference}: {self.old_status} -> {self.new_status}"
