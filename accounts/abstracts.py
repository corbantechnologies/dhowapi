import uuid

from django.db import models
from accounts.utils import generate_reference, generate_user_number


class UniversalIdModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        max_length=2550,
    )

    class Meta:
        abstract = True


class UserNumberModel(models.Model):
    usercode = models.CharField(
        max_length=40,
        unique=True,
        editable=False,
        default=generate_user_number,
        help_text="Unique identifier for the user. This helps in system audit and logs.",
    )

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ReferenceModel(models.Model):
    reference = models.CharField(max_length=255, blank=True, null=True, unique=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):

        if not self.reference:
            self.reference = generate_reference()
        super().save(*args, **kwargs)
