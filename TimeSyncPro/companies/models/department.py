from django.db import models
from django.core.validators import MinLengthValidator
from TimeSyncPro.accounts.models import Profile
from .company import Company
from TimeSyncPro.history.model_mixins import HistoryMixin


class Department(HistoryMixin, models.Model):
    MAX_DEPARTMENT_NAME_LENGTH = 50
    MIN_DEPARTMENT_NAME_LENGTH = 3

    tracked_fields = ["name", "holiday_approver"]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="departments",
        blank=False,
        null=False,
    )

    name = models.CharField(
        max_length=MAX_DEPARTMENT_NAME_LENGTH,
        validators=[MinLengthValidator(MIN_DEPARTMENT_NAME_LENGTH)],
        blank=False,
        null=False,
    )

    holiday_approver = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="departments",
    )

    class Meta:
        unique_together = ("company", "name")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
