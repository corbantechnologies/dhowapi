from django.db import models
from accounts.abstracts import UniversalIdModel, TimeStampedModel


class Table(UniversalIdModel, TimeStampedModel):
    schedule = models.ForeignKey(
        "schedule.Schedule",
        on_delete=models.CASCADE,
        related_name="tables",
    )
    table_number = models.CharField(max_length=50, help_text="e.g. T1, T2, Deck-1")
    capacity = models.PositiveIntegerField(
        default=4, help_text="Number of seats at this table"
    )
    description = models.TextField(
        blank=True, null=True, help_text="e.g. window seat, upper deck front"
    )
    is_available = models.BooleanField(default=True)
    assigned_to = models.ForeignKey(
        "booking.Booking",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tables",
        help_text="Booking assigned to this table by manager",
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Table"
        verbose_name_plural = "Tables"
        ordering = ["schedule", "table_number"]

    def __str__(self):
        status_str = f" (Assigned to {self.assigned_to.reference})" if self.assigned_to else " (Available)"
        return f"Table {self.table_number} - Capacity: {self.capacity}{status_str}"
