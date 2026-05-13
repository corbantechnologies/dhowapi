from rest_framework import serializers
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils import timezone
import secrets
import string
from datetime import datetime
from rest_framework.validators import UniqueValidator

from accounts.validators import (
    validate_password_digit,
    validate_password_uppercase,
    validate_password_symbol,
    validate_password_lowercase,
)
from accounts.utils import (
    send_welcome_email,
    send_forgot_password_email,
    send_password_reset_success_email,
)
from dhowapi.settings import DOMAIN

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    """Base Serializer to include common user fields"""

    password = serializers.CharField(
        max_length=128,
        min_length=5,
        write_only=True,
        validators=[
            validate_password_digit,
            validate_password_uppercase,
            validate_password_symbol,
            validate_password_lowercase,
        ],
    )
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "usercode",
            "first_name",
            "last_name",
            "password",
            "phone_number",
            "country",
            "city",
            "address",
            "is_staff",
            "is_superuser",
            "is_dhow_manager",
            "is_guest",
            "is_agent",
            "is_active",
            "created_at",
            "updated_at",
            "reference",
        )

    def create_user(self, validated_data, role_field):
        """
        Create and save a new user with the given validated data.
        """
        user = User.objects.create_user(**validated_data)
        setattr(user, role_field, True)
        user.is_active = True
        user.save()
        # send_welcome_email(user)
        return user


class DhowManagerSerializer(BaseUserSerializer):
    """
    Dhow Manager Serializer
    - As this is an internal management operation, we need to send an email for the manager to activate their account.
    - Which means that a staff or superuser should be the one to create a dhow manager.
    """
    password = serializers.CharField(
        required=False, write_only=True, allow_blank=True, allow_null=True
    )

    def create(self, validated_data):
        user = self.create_user(validated_data, "is_dhow_manager")
        user.save()

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"{DOMAIN}/activate/{uid}/{token}"
        # send activation link
        
        send_account_created_by_admin_email(user, activation_link)

        return user


class GuestUserSerializer(BaseUserSerializer):
    def create(self, validated_data):
        user = self.create_user(validated_data, "is_guest")
        user.save()
        send_welcome_email(user)
        return user


class AgentUserSerializer(BaseUserSerializer):
    """
    The Tamarind Dhow Manager decides which agent to give access to the system.
    """

    password = serializers.CharField(
        required=False, write_only=True, allow_blank=True, allow_null=True
    )
    def create(self, validated_data):
        user = self.create_user(validated_data, "is_agent")
        user.save()
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"{DOMAIN}/activate/{uid}/{token}"
        # send activation link
        
        send_account_created_by_admin_email(user, activation_link)

        return user


"""
Normal Login
"""


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


"""
Forgot Password and Password reset
"""


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist")
        return value

    def save(self):
        email = self.validated_data["email"]
        user = User.objects.get(email=email)

        # Generate 6-digit code
        code = "".join(secrets.choice(string.digits) for _ in range(6))
        user.password_reset_code = code
        user.password_reset_code_created_at = timezone.now()
        user.save()

        # Send email
        send_forgot_password_email(user, code)
        return user


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, max_length=6)
    password = serializers.CharField(
        max_length=128,
        min_length=5,
        write_only=True,
        validators=[
            validate_password_digit,
            validate_password_uppercase,
            validate_password_symbol,
            validate_password_lowercase,
        ],
    )

    def validate(self, attrs):
        email = attrs.get("email")
        code = attrs.get("code")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist")

        if user.password_reset_code != code:
            raise serializers.ValidationError("Invalid reset code")

        if not user.password_reset_code_created_at:
            raise serializers.ValidationError("No reset code request found")

        # Check for expiry (e.g., 15 minutes)
        # Using timezone.now() to ensure we compare aware checks if project is aware
        created_at = user.password_reset_code_created_at
        now = timezone.now()

        if created_at + timezone.timedelta(minutes=15) < now:
            raise serializers.ValidationError("Reset code has expired")

        return attrs

    def save(self):
        email = self.validated_data["email"]
        password = self.validated_data["password"]

        user = User.objects.get(email=email)
        user.set_password(password)
        user.password_reset_code = None
        user.password_reset_code_created_at = None
        user.save()

        # Send success email
        send_password_reset_success_email(user)

        return user
