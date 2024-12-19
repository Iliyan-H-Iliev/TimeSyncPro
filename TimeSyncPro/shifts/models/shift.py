from django.db import models
from django.core.validators import (
    MinValueValidator,
    MinLengthValidator,
    MaxValueValidator,
)
from django.utils import timezone
from datetime import timedelta, datetime
from TimeSyncPro.history.model_mixins import HistoryMixin
from .date import Date


class Shift(HistoryMixin, models.Model):
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 50
    MIN_ROTATION_WEEKS = 1
    MAX_ROTATION_WEEKS = 52

    tracked_fields = ["name", "description", "start_date", "rotation_weeks"]

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="shifts",
        blank=False,
        null=False,
    )

    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        validators=[MinLengthValidator(MIN_NAME_LENGTH)],
        blank=False,
        null=False,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    start_date = models.DateField(
        default=timezone.now,
        blank=False,
        null=False,
    )

    rotation_weeks = models.IntegerField(
        default=MIN_ROTATION_WEEKS,
        validators=[
            MinValueValidator(MIN_ROTATION_WEEKS),
            MaxValueValidator(MAX_ROTATION_WEEKS),
        ],
        blank=False,
        null=False,
    )

    last_generated_date = models.DateField(
        blank=True,
        null=True,
    )

    def generate_shift_working_dates(self, is_edit=False):
        today = timezone.now().date()
        current_date = (
            self.last_generated_date + timedelta(days=1)
            if self.last_generated_date
            else self.start_date
        )
        end_date = datetime(today.year + 2, 12, 31).date()
        work_on_local_holidays = self.company.working_on_local_holidays

        self.refresh_from_db()
        blocks = self.blocks.all().order_by("order")

        if is_edit:
            current_date = self.start_date
            for block in blocks:
                block.working_dates.clear()

        try:
            while current_date <= end_date:
                for block in blocks:
                    for day in block.on_off_days:

                        if day == 1:
                            date_obj, created = Date.objects.get_or_create(
                                date=current_date
                            )
                            if work_on_local_holidays or not date_obj.is_holiday(
                                self.company
                            ):
                                block.working_dates.add(date_obj)

                        current_date += timedelta(days=1)

            self.last_generated_date = current_date
            self.save()

        except ValueError as e:
            print(f"Error generating working dates: {e}")

    class Meta:
        unique_together = ("company", "name")

    def get_current_block(self):
        current_date = timezone.now().date()
        for block in self.blocks.all():
            if current_date in block.working_dates.all():
                return block
        return None

    def get_shift_pattern(self):
        block = self.blocks.first()
        if block:
            if block.days_on and block.days_off:
                return f"{block.days_on} on / {block.days_off} off"
            else:
                return "Custom"
        return "No pattern"

    def get_queryset_of_shift_working_dates_by_period(
        self, start_date=None, end_date=None
    ):
        if not start_date:
            start_date = timezone.now().date()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        queryset = Date.objects.filter(
            shift_blocks__pattern=self, date__gte=start_date, date__lte=end_date
        )
        return queryset

    def get_shift_working_dates_by_period(self, start_date=None, end_date=None):
        dates_queryset = self.get_queryset_of_shift_working_dates_by_period(
            start_date, end_date
        )
        return [d.date for d in dates_queryset] or []

    def get_count_of_shift_working_days_by_period(self, start_date=None, end_date=None):
        return self.get_queryset_of_shift_working_dates_by_period(
            start_date, end_date
        ).count()

    def get_shift_working_dates_with_time_by_period(
        self, start_date=None, end_date=None
    ):
        dates_queryset = self.get_queryset_of_shift_working_dates_by_period(
            start_date, end_date
        )

        dates_dict = {}
        for d in dates_queryset:
            shift_block = d.shift_blocks.get(pattern=self)
            dates_dict[d.date] = {
                "start_time": shift_block.start_time,
                "end_time": shift_block.end_time,
            }
        return dates_dict

    def __str__(self):
        return f"{self.name}"
