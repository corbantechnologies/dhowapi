from django.db import models
from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel


class EscrowRecord(UniversalIdModel, TimeStampedModel, ReferenceModel):
    STATUS_CHOICES = (
        ("holding", "Holding in Escrow"),
        ("released_to_finance", "Released to Finance"),
        ("reversed_to_guest", "Reversed to Guest"),
        ("failed", "Escrow Failed"),
    )

    RESOLUTION_METHOD_CHOICES = (
        ("schedule_confirmed", "Schedule Confirmed"),
        ("schedule_cancelled", "Schedule Cancelled"),
        ("manual_override", "Manual Override"),
    )

    payment = models.OneToOneField(
        "payment.Payment",
        on_delete=models.CASCADE,
        related_name="escrow",
    )
    schedule = models.ForeignKey(
        "schedule.Schedule",
        on_delete=models.CASCADE,
        related_name="escrow_records",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="holding"
    )
    held_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolution_method = models.CharField(
        max_length=50, choices=RESOLUTION_METHOD_CHOICES, blank=True, null=True
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Escrow Record"
        verbose_name_plural = "Escrow Records"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Escrow {self.reference} - KES {self.amount} ({self.get_status_display()})"
