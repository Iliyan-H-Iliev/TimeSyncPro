from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.utils import timezone
from TimeSyncPro.history.model_mixins import HistoryMixin


class ShiftBlock(HistoryMixin, models.Model):
    MIN_DAYS_ON = 1
    MAX_DAYS_ON = 28
    MIN_DAYS_OFF = 1
    MAX_DAYS_OFF = 28

    tracked_fields = [
        "on_off_days",
        "selected_days",
        "days_on",
        "days_off",
        "start_time",
        "end_time",
        "duration",
    ]

    pattern = models.ForeignKey(
        "Shift",
        on_delete=models.CASCADE,
        related_name="blocks"
    )

    on_off_days = ArrayField(
        models.IntegerField(),
        size=60,
        blank=False,
        null=False,
    )

    selected_days = ArrayField(
        models.IntegerField(),
        size=7,
        blank=True,
        null=True,
    )

    days_on = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_DAYS_ON), MaxValueValidator(MAX_DAYS_ON)],
        blank=True,
        null=True,
    )

    days_off = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_DAYS_OFF), MaxValueValidator(MAX_DAYS_OFF)],
        blank=True,
        null=True,
    )

    start_time = models.TimeField(
        blank=False,
        null=False,
    )

    end_time = models.TimeField(
        blank=False,
        null=False,
    )

    duration = models.DurationField(
        blank=True,
        null=True,
    )

    order = models.PositiveIntegerField(
        blank=False,
        null=False,
    )

    working_dates = models.ManyToManyField(
        "Date",
        related_name="shift_blocks",
        blank=True,
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.pattern.name} - block {self.order}"

    def save(self, *args, **kwargs):

        if not self.duration:
            start_datetime = timezone.make_aware(
                timezone.datetime.combine(timezone.now().date(), self.start_time)
            )
            end_datetime = timezone.make_aware(
                timezone.datetime.combine(timezone.now().date(), self.end_time)
            )
            if end_datetime <= start_datetime:
                end_datetime += timezone.timedelta(days=1)
            self.duration = end_datetime - start_datetime

        super().save(*args, **kwargs)