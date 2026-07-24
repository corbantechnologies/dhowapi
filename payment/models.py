from django.db import models
from django.conf import settings
from accounts.abstracts import UniversalIdModel, TimeStampedModel, ReferenceModel


class Payment(UniversalIdModel, TimeStampedModel, ReferenceModel):
    PAYMENT_METHOD_CHOICES = (
        ("mpesa", "M-Pesa"),
        ("cash", "Cash"),
        ("agent_credit", "Agent Credit"),
        ("waived", "Waived"),
    )

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing STK Push"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    booking = models.ForeignKey(
        "booking.Booking",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="KES")
    payment_method = models.CharField(
        max_length=50, choices=PAYMENT_METHOD_CHOICES, default="mpesa"
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="pending"
    )
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments_made",
    )
    paid_at = models.DateTimeField(blank=True, null=True)
    transaction_ref = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="M-Pesa CheckoutRequestID or external reference",
    )
    receipt_number = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="M-Pesa Receipt Number (e.g. QX12345678)",
    )
    phone_number = models.CharField(
        max_length=20, blank=True, null=True, help_text="M-Pesa phone number used"
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.reference} - {self.currency} {self.amount} ({self.get_status_display()})"
