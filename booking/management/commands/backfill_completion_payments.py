"""
Management command: backfill_completion_payments

Scans all completed bookings that have an outstanding balance with no
corresponding auto-completion payment, and creates the missing Payment records.

Usage:
    python manage.py backfill_completion_payments
    python manage.py backfill_completion_payments --dry-run       # preview only
    python manage.py backfill_completion_payments --schedule REF  # single sailing
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = (
        "Backfill auto-completion payments for previously completed bookings "
        "that still show an outstanding balance."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Print what would be created without writing to the database.",
        )
        parser.add_argument(
            "--schedule",
            dest="schedule_ref",
            default=None,
            help="Limit backfill to a specific schedule reference (e.g. ZIFSHHS5VCMW).",
        )

    def handle(self, *args, **options):
        from booking.models import Booking
        from payment.models import Payment

        dry_run = options["dry_run"]
        schedule_ref = options.get("schedule_ref")

        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n=== Backfill Completion Payments ==="
        ))
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN mode — nothing will be saved.\n"))

        # Fetch all completed bookings
        qs = Booking.objects.filter(status="completed").select_related("schedule")
        if schedule_ref:
            qs = qs.filter(schedule__reference=schedule_ref)

        created_count = 0
        skipped_count = 0
        error_count = 0

        for booking in qs:
            try:
                balance = booking.outstanding_balance
                if balance <= Decimal("0.00"):
                    skipped_count += 1
                    continue

                # Determine payment method from last completed payment
                last_payment = (
                    booking.payments.filter(status="completed")
                    .order_by("-created_at")
                    .first()
                )
                method = last_payment.payment_method if last_payment else "cash"

                self.stdout.write(
                    f"  [+] Booking {booking.reference} | "
                    f"Schedule {booking.schedule.reference} | "
                    f"Balance: KES {balance:,.2f} | "
                    f"Method: {method.upper()}"
                )

                if not dry_run:
                    with transaction.atomic():
                        Payment.objects.create(
                            booking=booking,
                            amount=balance,
                            payment_method=method,
                            status="completed",
                            notes=(
                                f"Backfill: auto-collected outstanding balance on sailing completion. "
                                f"Method: {method.upper()}"
                            ),
                        )

                created_count += 1

            except Exception as exc:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Booking {booking.reference} failed: {exc}"
                    )
                )

        self.stdout.write("\n" + "-" * 50)
        action = "Would create" if dry_run else "Created"
        self.stdout.write(
            self.style.SUCCESS(
                f"[OK] {action} {created_count} payment(s)."
            )
        )
        self.stdout.write(f"  Skipped (already settled): {skipped_count}")
        if error_count:
            self.stdout.write(self.style.ERROR(f"  Errors: {error_count}"))
        self.stdout.write("")
