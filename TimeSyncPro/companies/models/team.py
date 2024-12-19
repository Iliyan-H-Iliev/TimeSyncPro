from django.db import models
from django.core.validators import (
    MinValueValidator,
    MinLengthValidator,
    MaxValueValidator,
)
from django.db.models import Count
from TimeSyncPro.absences.models import Holiday
from TimeSyncPro.accounts.models import Profile

from TimeSyncPro.history.model_mixins import HistoryMixin


class Team(HistoryMixin, models.Model):
    MAX_TEAM_NAME_LENGTH = 50
    MIN_TEAM_NAME_LENGTH = 3
    DEFAULT_EMPLOYEES_HOLIDAYS_AT_A_TIME = 99
    MIN_EMPLOYEES_HOLIDAYS_AT_A_TIME = 1
    MAX_EMPLOYEES_HOLIDAYS_AT_A_TIME = 99

    tracked_fields = [
        "name",
        "shift",
        "holiday_approver",
        "department",
        "employees_holidays_at_a_time",
    ]

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="teams",
        null=False,
        blank=False,
    )

    name = models.CharField(
        max_length=MAX_TEAM_NAME_LENGTH,
        validators=[MinLengthValidator(MIN_TEAM_NAME_LENGTH)],
        blank=False,
        null=False,
    )

    shift = models.ForeignKey(
        "shifts.Shift",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="teams",
    )

    holiday_approver = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="teams",
    )

    employees_holidays_at_a_time = models.PositiveIntegerField(
        default=DEFAULT_EMPLOYEES_HOLIDAYS_AT_A_TIME,
        validators=[
            MinValueValidator(MIN_EMPLOYEES_HOLIDAYS_AT_A_TIME),
            MaxValueValidator(MAX_EMPLOYEES_HOLIDAYS_AT_A_TIME),
        ],
        blank=False,
        null=False,
    )

    class Meta:
        unique_together = ("company", "name")

    def get_team_members(self):
        return self.employees.all()

    def get_team_leaders(self):
        return self.employees.filter(role=Profile.EmployeeRoles.TEAM_LEADER)

    def get_team_members_at_holiday(
        self, start_date=None, end_date=None, statuses=None
    ):
        if statuses is None:
            statuses = [Holiday.StatusChoices.APPROVED, Holiday.StatusChoices.PENDING]

        team_holidays = (
            Holiday.objects.filter(requester__team=self, status__in=statuses)
            .select_related("requester")
            .order_by("requester__first_name", "start_date")
        )

        if start_date and end_date:
            team_holidays = team_holidays.filter(
                start_date__gte=start_date, end_date__lte=end_date
            )

        return team_holidays

    def get_numbers_of_team_members_holiday_by_period(
        self, start_date=None, end_date=None
    ):
        return (
            self.get_team_members_at_holiday(start_date, end_date)
            .filter(
                status=Holiday.StatusChoices.APPROVED,
            )
            .values("requester__id")
            .annotate(request_count=Count("id"))
            .distinct()
            .count()
        )

    @staticmethod
    def get_numbers_of_team_members_holiday_days_by_queryset(queryset):
        return (
            queryset.filter(
                status=Holiday.StatusChoices.APPROVED,
            )
            .values("requester__id")
            .annotate(request_count=Count("id"))
            .distinct()
            .count()
        )

    def __str__(self):
        return self.name
