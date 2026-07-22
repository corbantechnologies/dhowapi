from django.db import models
from django.conf import settings
from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel


class Refund(UniversalIdModel, TimeStampedModel, ReferenceModel):
    REASON_CHOICES = (
        ("sailing_cancelled", "Sailing Cancelled"),
        ("weather", "Bad Weather"),
        ("other", "Other Reason"),
    )

    STATUS_CHOICES = (
        ("pending", "Pending Accounts Processing"),
        ("processing", "Processing"),
        ("completed", "Refund Completed"),
        ("rejected", "Refund Rejected"),
    )

    payment = models.ForeignKey(
        "payment.Payment",
        on_delete=models.CASCADE,
        related_name="refunds",
    )
    booking = models.ForeignKey(
        "booking.Booking",
        on_delete=models.CASCADE,
        related_name="refunds",
    )
    escrow = models.ForeignKey(
        "escrow.EscrowRecord",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="refunds",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(
        max_length=50, choices=REASON_CHOICES, default="sailing_cancelled"
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="pending"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="refunds_requested",
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="refunds_processed",
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    mpesa_ref = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="M-Pesa B2C or financial reference number",
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Refund"
        verbose_name_plural = "Refunds"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Refund {self.reference} - KES {self.amount} ({self.get_status_display()})"
