from django.db import models
from django.conf import settings
from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel


class ScheduleTemplate(UniversalIdModel, TimeStampedModel, ReferenceModel):
    MEAL_TYPE_CHOICES = (
        ("lunch", "Lunch"),
        ("sunset_cruise", "Sunset Cruise"),
        ("booze_cruise", "Booze Cruise"),
        ("special_cruise", "Special Cruise"),
        ("dinner_cruise", "Dinner Cruise"),
    )

    dhow = models.ForeignKey(
        "dhow.Dhow",
        on_delete=models.CASCADE,
        related_name="schedule_templates",
    )
    meal_type = models.CharField(
        max_length=50, choices=MEAL_TYPE_CHOICES, default="sunset_cruise"
    )
    departure_time = models.TimeField()
    return_time = models.TimeField()
    days_of_week = models.JSONField(
        default=list,
        help_text="List of days of week (e.g. ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'])",
    )
    price_per_person = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )
    price_per_child = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )
    exclusive_flat_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="schedule_templates_created",
    )

    class Meta:
        verbose_name = "Schedule Template"
        verbose_name_plural = "Schedule Templates"
        ordering = ["dhow", "departure_time"]

    def __str__(self):
        return f"{self.dhow.name} - {self.get_meal_type_display()} ({self.departure_time.strftime('%H:%M')})"
