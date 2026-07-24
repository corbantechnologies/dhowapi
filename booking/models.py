from django.db import models
from django.conf import settings
from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel


class Booking(UniversalIdModel, TimeStampedModel, ReferenceModel):
    BOOKING_TYPE_CHOICES = (
        ("individual", "Individual"),
        ("group_agent", "Group (Agent)"),
        ("exclusive", "Exclusive Charter"),
        ("walk_in", "Walk-In"),
    )

    STATUS_CHOICES = (
        ("pending", "Pending Payment"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("rescheduled", "Rescheduled"),
        ("completed", "Completed"),
        ("no_show", "No Show"),
    )

    CANCELLATION_PREFERENCE_CHOICES = (
        ("reschedule", "Reschedule"),
        ("refund", "Refund"),
    )

    schedule = models.ForeignKey(
        "schedule.Schedule",
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    booked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    booking_type = models.CharField(
        max_length=50, choices=BOOKING_TYPE_CHOICES, default="individual"
    )
    package = models.ForeignKey(
        "package.Package",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    party_size = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="pending"
    )
    cancellation_preference = models.CharField(
        max_length=50,
        choices=CANCELLATION_PREFERENCE_CHOICES,
        default="refund",
        help_text="Guest's preference if the sailing is cancelled (Reschedule or Refund)",
    )
    is_exclusive = models.BooleanField(default=False)
    exclusive_note = models.TextField(blank=True, null=True)
    table_request = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Requested seating preference (e.g. deck seat, window table)",
    )
    special_requests = models.TextField(
        blank=True, null=True, help_text="e.g. Birthday setup, Vegan meal"
    )
    internal_notes = models.TextField(
        blank=True, null=True, help_text="Manager or agent internal notes"
    )
    table = models.ForeignKey(
        "table.Table",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings_table",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings_created",
    )

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking {self.reference} - {self.booked_by.email} ({self.party_size} pax)"

    @property
    def total_amount(self):
        # Calculate base price + add-ons
        unit_price = (
            self.schedule.exclusive_flat_fee
            if self.is_exclusive
            else (self.schedule.price_per_person or (self.package.base_price if self.package else 0))
        )
        base_total = unit_price if self.is_exclusive else (unit_price * self.party_size)
        addons_total = sum([addon.total_price for addon in self.booking_addons.all()])
        return base_total + addons_total
