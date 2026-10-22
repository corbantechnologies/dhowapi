import uuid
from django.db import models
from django.conf import settings
from django.db.models import Sum
from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel


class ScheduleQuerySet(models.QuerySet):
    def with_pax(self):
        """Count booked guests in the same query, instead of once per schedule field."""
        from django.db.models import IntegerField, OuterRef, Subquery, Value
        from django.db.models.functions import Coalesce
        from booking.models import Booking

        pax = (
            Booking.objects.filter(
                schedule=OuterRef("pk"), status__in=["pending", "confirmed", "completed"]
            )
            .order_by()
            .values("schedule")
            .annotate(total=Sum("party_size"))
            .values("total")
        )
        return self.select_related("dhow").annotate(
            _pax_count=Coalesce(Subquery(pax), Value(0), output_field=IntegerField())
        )


class Schedule(UniversalIdModel, TimeStampedModel, ReferenceModel):
    MEAL_TYPE_CHOICES = (
        ("lunch", "Lunch"),
        ("sunset_cruise", "Sunset Cruise"),
        ("booze_cruise", "Booze Cruise"),
        ("special_cruise", "Special Cruise"),
        ("dinner_cruise", "Dinner Cruise"),
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
    price_per_child = models.DecimalField(
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
    manifest_token = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="Permanent public manifest sharing token (UUID hex)",
    )
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

    objects = ScheduleQuerySet.as_manager()

    def __str__(self):
        return f"{self.dhow.name} - {self.date} {self.get_meal_type_display()} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Auto-generate a permanent manifest token on first save
        if not self.manifest_token:
            self.manifest_token = uuid.uuid4().hex
        if self.status in ["completed", "cancelled"]:
            self.is_open = False
        self.__dict__.pop("_pax_count", None)
        super().save(*args, **kwargs)
        if self.status == "completed":
            # Iterate and call b.save() on each booking so that all model
            # hooks fire (payment auto-generation, guest status sync, etc.)
            for b in self.bookings.filter(status__in=["pending", "confirmed"]):
                b.status = "completed"
                b.save()

    @property
    def current_pax_count(self):
        # Calculate total confirmed/pending guests booked on this schedule
        if "_pax_count" in self.__dict__:
            return self._pax_count
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
