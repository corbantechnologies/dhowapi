from django.db import models
from django.conf import settings
from django.db.models import Sum
from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel


class Schedule(UniversalIdModel, TimeStampedModel, ReferenceModel):
    MEAL_TYPE_CHOICES = (
        ("lunch", "Lunch"),
        ("sunset_cruise", "Sunset Cruise"),
    )

    STATUS_CHOICES = (
        ("scheduled", "Scheduled"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    )

    dhow = models.ForeignKey(
        "dhow.Dhow",
        on_delete=models.CASCADE,
        related_name="schedules",
    )
    template = models.ForeignKey(
        "schedule_template.ScheduleTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_schedules",
    )
    date = models.DateField()
    meal_type = models.CharField(
        max_length=50, choices=MEAL_TYPE_CHOICES, default="sunset_cruise"
    )
    departure_time = models.TimeField()
    return_time = models.TimeField()
    price_per_person = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )
    exclusive_flat_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="scheduled"
    )
    is_exclusive = models.BooleanField(default=False)
    exclusive_booked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exclusive_schedules",
    )
    is_open = models.BooleanField(
        default=True, help_text="Manager can open or close bookings for this schedule"
    )
    cancelled_reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="schedules_created",
    )

    class Meta:
        verbose_name = "Schedule"
        verbose_name_plural = "Schedules"
        ordering = ["date", "departure_time"]

    def __str__(self):
        return f"{self.dhow.name} - {self.date} {self.get_meal_type_display()} ({self.get_status_display()})"

    @property
    def current_pax_count(self):
        # Calculate total confirmed/pending guests booked on this schedule
        total = (
            self.bookings.filter(status__in=["pending", "confirmed", "completed"]).aggregate(
                total_pax=Sum("party_size")
            )["total_pax"]
            or 0
        )
        return total

    @property
    def is_quota_met(self):
        if not self.dhow:
            return False
        return self.current_pax_count >= self.dhow.min_quota

    @property
    def available_capacity(self):
        if not self.dhow:
            return 0
        return max(0, self.dhow.total_capacity - self.current_pax_count)
