from django.db import models
from django.conf import settings
from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel


class BookingReschedule(UniversalIdModel, TimeStampedModel, ReferenceModel):
    STATUS_CHOICES = (
        ("pending", "Pending New Schedule Choice"),
        ("confirmed", "Reschedule Confirmed"),
        ("rejected", "Reschedule Rejected"),
    )

    booking = models.ForeignKey(
        "booking.Booking",
        on_delete=models.CASCADE,
        related_name="reschedules",
    )
    original_schedule = models.ForeignKey(
        "schedule.Schedule",
        on_delete=models.CASCADE,
        related_name="rescheduled_from",
    )
    new_schedule = models.ForeignKey(
        "schedule.Schedule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rescheduled_to",
    )
    reason = models.TextField(blank=True, null=True)
    rescheduled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reschedules_initiated",
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="pending"
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Booking Reschedule"
        verbose_name_plural = "Booking Reschedules"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reschedule {self.reference} for Booking {self.booking.reference} ({self.get_status_display()})"
