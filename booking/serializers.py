import datetime
from rest_framework import serializers
from booking.models import Booking
from booking_guest.serializers import BookingGuestSerializer
from booking_addon.serializers import BookingAddOnSerializer


class BookingAddOnWriteSerializer(serializers.ModelSerializer):
    unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )

    class Meta:
        from booking_addon.models import BookingAddOn
        model = BookingAddOn
        fields = ("addon", "quantity", "unit_price")


class BookingSerializer(serializers.ModelSerializer):
    booked_by_email = serializers.SerializerMethodField()
    booked_by_name = serializers.SerializerMethodField()
    booking_guests = BookingGuestSerializer(many=True, read_only=True)
    booking_addons = BookingAddOnSerializer(many=True, read_only=True)
    addons = BookingAddOnWriteSerializer(many=True, write_only=True, required=False)
    schedule_date = serializers.ReadOnlyField(source="schedule.date")
    schedule_meal_type = serializers.ReadOnlyField(source="schedule.get_meal_type_display")
    package_name = serializers.ReadOnlyField(source="package.name")
    table_number = serializers.SerializerMethodField()
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    primary_guest_name = serializers.CharField(write_only=True, required=False)
    primary_guest_email = serializers.EmailField(write_only=True, required=False, allow_blank=True, allow_null=True)
    primary_guest_phone = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    outstanding_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    guest_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)

    class Meta:
        model = Booking
        fields = (
            "id",
            "reference",
            "schedule",
            "schedule_date",
            "schedule_meal_type",
            "booked_by",
            "booked_by_email",
            "booked_by_name",
            "booking_type",
            "package",
            "package_name",
            "party_size",
            "adult_count",
            "child_count",
            "status",
            "status_display",
            "cancellation_preference",
            "is_exclusive",
            "exclusive_note",
            "table_request",
            "special_requests",
            "internal_notes",
            "table",
            "table_number",
            "table_allocation",
            "total_amount",
            "custom_price_per_person",
            "custom_price_per_child",
            "discount_type",
            "discount_value",
            "discount_amount",
            "discount_reason",
            "total_paid",
            "outstanding_balance",
            "booking_guests",
            "booking_addons",
            "addons",
            "primary_guest_name",
            "primary_guest_email",
            "primary_guest_phone",
            "guest_names",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reference", "created_by", "created_at", "updated_at", "total_paid", "outstanding_balance")
        extra_kwargs = {
            "booked_by": {"required": False, "allow_null": True},
        }

    def create(self, validated_data):
        primary_name = validated_data.pop("primary_guest_name", "")
        primary_email = validated_data.pop("primary_guest_email", "")
        primary_phone = validated_data.pop("primary_guest_phone", "")
        addons_data = validated_data.pop("addons", [])
        guest_names = validated_data.pop("guest_names", [])

        booking = Booking(**validated_data)
        booking._primary_guest_name = primary_name
        booking._primary_guest_email = primary_email
        booking._primary_guest_phone = primary_phone
        booking.save()

        # Update other guests names if supplied
        if guest_names:
            other_guests = booking.booking_guests.filter(is_primary=False).order_by("id")
            for idx, g_name in enumerate(guest_names):
                if idx < len(other_guests):
                    cleaned_name = g_name.strip() if g_name else ""
                    if cleaned_name:
                        parts = cleaned_name.split(" ")
                        other_guests[idx].first_name = parts[0] if parts else "Guest"
                        other_guests[idx].last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
                        other_guests[idx].save()

        # Create nested addons
        from booking_addon.models import BookingAddOn
        for addon_item in addons_data:
            addon_obj = addon_item["addon"]
            qty = addon_item.get("quantity", 1)
            u_price = addon_item.get("unit_price") or addon_obj.price
            BookingAddOn.objects.create(
                booking=booking,
                addon=addon_obj,
                quantity=qty,
                unit_price=u_price
            )

        return booking

    def update(self, instance, validated_data):
        addons_data = validated_data.pop("addons", None)
        primary_name = validated_data.pop("primary_guest_name", None)
        primary_email = validated_data.pop("primary_guest_email", None)
        primary_phone = validated_data.pop("primary_guest_phone", None)
        guest_names = validated_data.pop("guest_names", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # If primary guest fields were supplied in update (e.g. for walk-in form modifications)
        primary_guest = instance.booking_guests.filter(is_primary=True).first()
        if primary_guest and (primary_name or primary_email or primary_phone):
            if primary_name:
                name_parts = primary_name.strip().split(" ")
                primary_guest.first_name = name_parts[0] if name_parts else "Walk-In"
                primary_guest.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            if primary_email is not None:
                primary_guest.email = primary_email
            if primary_phone is not None:
                primary_guest.phone = primary_phone
            primary_guest.save()

        if guest_names is not None:
            # Sync / update names of non-primary guests
            other_guests = instance.booking_guests.filter(is_primary=False).order_by("id")
            for idx, g_name in enumerate(guest_names):
                if idx < len(other_guests):
                    cleaned_name = g_name.strip() if g_name else ""
                    if cleaned_name:
                        parts = cleaned_name.split(" ")
                        other_guests[idx].first_name = parts[0] if parts else "Guest"
                        other_guests[idx].last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
                    else:
                        other_guests[idx].first_name = "Guest"
                        other_guests[idx].last_name = str(idx + 2)
                    other_guests[idx].save()

        if addons_data is not None:
            from booking_addon.models import BookingAddOn
            instance.booking_addons.all().delete()
            for addon_item in addons_data:
                addon_obj = addon_item["addon"]
                qty = addon_item.get("quantity", 1)
                u_price = addon_item.get("unit_price") or addon_obj.price
                BookingAddOn.objects.create(
                    booking=instance,
                    addon=addon_obj,
                    quantity=qty,
                    unit_price=u_price
                )
        return instance

    def validate(self, attrs):
        schedule = attrs.get("schedule")
        adult_count = attrs.get("adult_count")
        child_count = attrs.get("child_count")
        if adult_count is not None or child_count is not None:
            ac = adult_count if adult_count is not None else 1
            cc = child_count if child_count is not None else 0
            attrs["party_size"] = ac + cc

        party_size = attrs.get("party_size", 1)
        is_exclusive = attrs.get("is_exclusive", False)

        if schedule:
            is_schedule_changing = True
            if self.instance and self.instance.schedule == schedule:
                is_schedule_changing = False

            if is_schedule_changing:
                if schedule.date < datetime.date.today():
                    raise serializers.ValidationError("Cannot book a sailing in the past.")
                if not schedule.is_open:
                    raise serializers.ValidationError("Bookings are closed for this schedule.")
                if schedule.status in ["cancelled", "completed"]:
                    raise serializers.ValidationError(
                        f"Cannot book a schedule that is {schedule.status}."
                    )
                if schedule.is_exclusive:
                    raise serializers.ValidationError(
                        "This schedule is already exclusively chartered."
                    )
                if is_exclusive and schedule.bookings.filter(status__in=["pending", "confirmed"]).exists():
                    raise serializers.ValidationError(
                        "Cannot book exclusively: this schedule already has existing bookings."
                    )
                if not is_exclusive and schedule.available_capacity < party_size:
                    raise serializers.ValidationError(
                        f"Requested party size ({party_size}) exceeds available capacity ({schedule.available_capacity})."
                    )
            else:
                # Even if schedule is the same, if party size increases, check capacity
                if not is_exclusive:
                    capacity_change = party_size - self.instance.party_size
                    if capacity_change > 0 and schedule.available_capacity < capacity_change:
                        raise serializers.ValidationError(
                            f"Increasing party size by {capacity_change} exceeds available capacity ({schedule.available_capacity})."
                        )

        return attrs


    def get_booked_by_name(self, obj):
        primary_guest = obj.booking_guests.filter(is_primary=True).first()
        if primary_guest:
            return f"{primary_guest.first_name} {primary_guest.last_name}"
        return obj.booked_by.get_full_name() if obj.booked_by else ""

    def get_booked_by_email(self, obj):
        primary_guest = obj.booking_guests.filter(is_primary=True).first()
        if primary_guest and primary_guest.email:
            return primary_guest.email
        return obj.booked_by.email if obj.booked_by else ""

    def get_table_number(self, obj):
        if obj.table_allocation:
            return obj.table_allocation
        tables = obj.assigned_tables.all()
        if tables.exists():
            return ", ".join([t.table_number for t in tables])
        return ""



