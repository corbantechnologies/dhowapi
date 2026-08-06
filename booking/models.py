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
        ("confirmed", "Confirmed (Sailing Guaranteed)"),
    )

    schedule = models.ForeignKey(
        "schedule.Schedule",
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    booked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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
    adult_count = models.PositiveIntegerField(default=1)
    child_count = models.PositiveIntegerField(default=0)
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
    custom_price_per_person = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        help_text="Override standard adult price per person"
    )
    custom_price_per_child = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        help_text="Override standard child price per person"
    )
    discount_type = models.CharField(
        max_length=20,
        choices=(("amount", "Flat Amount"), ("percentage", "Percentage")),
        default="amount"
    )
    discount_value = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, blank=True,
        help_text="Percentage value or flat KES amount"
    )
    discount_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, blank=True,
        help_text="Discount amount in KES applied to the booking"
    )
    discount_reason = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Reason for the discount"
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
    table_allocation = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Direct table allocation name/number (e.g. Table 5, T10)"
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

    def save(self, *args, **kwargs):
        from decimal import Decimal
        unit_price = (
            self.schedule.exclusive_flat_fee
            if self.is_exclusive
            else (self.custom_price_per_person or self.schedule.price_per_person or (self.package.base_price if self.package else 0))
        )
        child_unit_price = (
            0.00
            if self.is_exclusive
            else (self.custom_price_per_child or getattr(self.schedule, "price_per_child", 0.00))
        )
        base_total = (
            unit_price
            if self.is_exclusive
            else ((unit_price * self.adult_count) + (child_unit_price * self.child_count))
        )
        
        if self.discount_type == "percentage":
            val = self.discount_value or Decimal("0.00")
            self.discount_amount = Decimal(str(base_total)) * (val / Decimal("100.00"))
        else:
            self.discount_amount = self.discount_value or Decimal("0.00")

        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            from booking_guest.models import BookingGuest

            first_name = "Walk-In"
            last_name = "Guest"
            email = getattr(self, "_primary_guest_email", None)
            phone = getattr(self, "_primary_guest_phone", None)

            name = getattr(self, "_primary_guest_name", None)
            if name:
                name_parts = name.strip().split(" ")
                first_name = name_parts[0] if name_parts else "Walk-In"
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                if len(name_parts) > 2:
                    last_name = " ".join(name_parts[1:])
            elif self.booked_by:
                first_name = self.booked_by.first_name or "Guest"
                last_name = self.booked_by.last_name or "1"
                email = self.booked_by.email

            BookingGuest.objects.create(
                booking=self,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                is_primary=True,
                status="pending",
            )

            for i in range(2, self.party_size + 1):
                BookingGuest.objects.create(
                    booking=self,
                    first_name="Guest",
                    last_name=str(i),
                    is_primary=False,
                    status="pending",
                )
        else:
            # Sync passenger checklist count to party_size
            try:
                from booking_guest.models import BookingGuest
                current_guests = list(self.booking_guests.all())
                current_count = len(current_guests)
                
                if self.party_size > current_count:
                    # Create more placeholders
                    for i in range(current_count + 1, self.party_size + 1):
                        BookingGuest.objects.create(
                            booking=self,
                            first_name="Guest",
                            last_name=str(i),
                            is_primary=False,
                            status="pending",
                        )
                elif self.party_size < current_count:
                    # Remove excess unboarded guests, starting with non-primary
                    excess_qty = current_count - self.party_size
                    # Filter un-checked_in guests first
                    excess_candidates = self.booking_guests.filter(is_primary=False).exclude(status="checked_in").order_by("-id")[:excess_qty]
                    for ec in excess_candidates:
                        ec.delete()
            except Exception:
                pass

            if self.status == "completed":
                # Update any still-pending guest records to checked_in
                self.booking_guests.filter(status="pending").update(status="checked_in")
                # Auto-create a completion payment for any outstanding balance
                try:
                    from decimal import Decimal
                    from payment.models import Payment
                    balance = self.outstanding_balance
                    if balance > Decimal("0.00"):
                        # Reuse the last used payment method, defaulting to cash
                        last_payment = self.payments.filter(status="completed").order_by("-created_at").first()
                        method = last_payment.payment_method if last_payment else "cash"
                        Payment.objects.create(
                            booking=self,
                            amount=balance,
                            payment_method=method,
                            status="completed",
                            notes=(
                                f"Auto-collected balance on sailing completion. "
                                f"Method: {method.upper()}"
                            ),
                        )
                except Exception:
                    pass
            elif self.status == "no_show":
                self.booking_guests.filter(status="pending").update(status="no_show")



    def __str__(self):
        email = self.booked_by.email if self.booked_by else "No Owner"
        return f"Booking {self.reference} - {email} ({self.party_size} pax: {self.adult_count}a, {self.child_count}c)"

    @property
    def total_amount(self):
        from decimal import Decimal
        # Calculate base price + add-ons
        unit_price = (
            self.schedule.exclusive_flat_fee
            if self.is_exclusive
            else (self.custom_price_per_person or self.schedule.price_per_person or (self.package.base_price if self.package else 0))
        )
        child_unit_price = (
            0.00
            if self.is_exclusive
            else (self.custom_price_per_child or getattr(self.schedule, "price_per_child", 0.00))
        )
        base_total = (
            unit_price
            if self.is_exclusive
            else ((unit_price * self.adult_count) + (child_unit_price * self.child_count))
        )
        addons_total = sum([addon.total_price for addon in self.booking_addons.all()])
        
        base_total_dec = Decimal(str(base_total))
        addons_total_dec = Decimal(str(addons_total)) if addons_total else Decimal("0.00")
        discount_dec = Decimal(str(self.discount_amount)) if self.discount_amount else Decimal("0.00")
        
        return max(Decimal("0.00"), base_total_dec + addons_total_dec - discount_dec)

    @property
    def total_paid(self):
        from decimal import Decimal
        total = self.payments.filter(status="completed").aggregate(
            total=models.Sum('amount')
        )['total']
        return Decimal(str(total)) if total is not None else Decimal("0.00")

    @property
    def outstanding_balance(self):
        from decimal import Decimal
        return max(Decimal("0.00"), self.total_amount - self.total_paid)

