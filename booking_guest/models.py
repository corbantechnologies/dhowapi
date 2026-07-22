from django.db import models
from accounts.abstracts import UniversalIdModel, TimeStampedModel


class BookingGuest(UniversalIdModel, TimeStampedModel):
    booking = models.ForeignKey(
        "booking.Booking",
        on_delete=models.CASCADE,
        related_name="booking_guests",
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    dietary_needs = models.TextField(blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Booking Guest"
        verbose_name_plural = "Booking Guests"
        ordering = ["-is_primary", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.booking.reference})"
