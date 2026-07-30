from django.db import models
from accounts.abstracts import UniversalIdModel, TimeStampedModel


class BookingGuest(UniversalIdModel, TimeStampedModel):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("checked_in", "Checked In"),
        ("no_show", "No Show"),
    )

    booking = models.ForeignKey(
        "booking.Booking",
        on_delete=models.CASCADE,
        related_name="booking_guests",
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True, default="")
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    dietary_needs = models.TextField(blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="pending"
    )

    class Meta:
        verbose_name = "Booking Guest"
        verbose_name_plural = "Booking Guests"
        ordering = ["-is_primary", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.booking.reference})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Bidirectional sync: update parent booking status based on all guest statuses
        try:
            booking = self.booking
            all_guests = list(booking.booking_guests.all())
            if not all_guests:
                return
            total = len(all_guests)
            checked_in = sum(1 for g in all_guests if g.status == "checked_in")
            no_shows = sum(1 for g in all_guests if g.status == "no_show")
            resolved = checked_in + no_shows

            if resolved == total and checked_in > 0:
                # All guests resolved: at least one boarded — mark booking completed
                if booking.status not in ("completed", "cancelled"):
                    booking.status = "completed"
                    booking.save()
            elif resolved == total and no_shows == total:
                # All guests are no-shows
                if booking.status not in ("no_show", "cancelled"):
                    booking.status = "no_show"
                    booking.save()
        except Exception:
            pass
