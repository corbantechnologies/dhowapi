from django.db import models
from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel


class Package(UniversalIdModel, TimeStampedModel, ReferenceModel):
    MEAL_TYPE_CHOICES = (
        ("lunch", "Lunch"),
        ("sunset_cruise", "Sunset Cruise"),
        ("booze_cruise", "Booze Cruise"),
        ("special_cruise", "Special Cruise"),
        ("dinner_cruise", "Dinner Cruise"),
        ("exclusive_cruise", "Exclusive Cruise"),
    )

    name = models.CharField(max_length=255)
    meal_type = models.CharField(
        max_length=50, choices=MEAL_TYPE_CHOICES, default="sunset_cruise"
    )
    description = models.TextField(blank=True, null=True)
    includes = models.TextField(
        blank=True,
        null=True,
        help_text="Details of what is included (e.g. welcome drink, full course meal)",
    )
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Package"
        verbose_name_plural = "Packages"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_meal_type_display()})"
