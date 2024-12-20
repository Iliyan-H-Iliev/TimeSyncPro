from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

import TimeSyncPro.common.model_mixins as common_mixins
from TimeSyncPro.history.model_mixins import HistoryMixin

User_Model = get_user_model()


class AbsenceBase(common_mixins.CreatedModifiedMixin, models.Model):
    MAX_LENGTH_REASON = 500

    class Meta:
        abstract = True

    start_date = models.DateField(
        blank=False,
        null=False,
    )

    end_date = models.DateField(
        blank=False,
        null=False,
    )

    reason = models.TextField(
        max_length=MAX_LENGTH_REASON,
        blank=True,
        null=True,
    )


class Holiday(AbsenceBase):
    MAX_LENGTH_REVIEW_REASON = 500

    tracked_fields = [
        "start_date",
        "end_date",
        "reason",
        "status",
        "reviewer",
        "reviewed_by",
        "review_reason",
    ]

    class StatusChoices(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        DENIED = "denied", "Denied"
        CANCELLED = "cancelled", "Cancelled"

    requester = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.CASCADE,
        related_name="holidays",
        blank=False,
        null=False,
    )

    status = models.CharField(
        max_length=max([len(choice) for choice in StatusChoices.values]),
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        blank=False,
        null=False,
    )

    reviewer = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="holiday_for_review",
    )

    reviewed_by = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_holidays",
    )

    review_reason = models.TextField(
        max_length=MAX_LENGTH_REVIEW_REASON,
        blank=True,
        null=True,
    )

    days_requested = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["start_date"]
        permissions = [
            ("view_all_holidays_requests", "Can view all holiday requests"),
            (
                "view_department_holidays_requests",
                "Can view department holiday requests",
            ),
            ("view_team_holidays_requests", "Can view own holiday requests"),
            ("update_holiday_requests_status", "Can update holiday status"),
            ("view_holidays_requests", "Can view holiday requests"),
            ("approve_holiday_requests", "Can approve holiday requests"),
        ]

    def __str__(self):
        return f"{self.requester.full_name} - Holiday ({self.start_date} to {self.end_date})"

    @property
    def is_approved(self):
        return self.status == self.StatusChoices.APPROVED

    @property
    def is_denied(self):
        return self.status == self.StatusChoices.DENIED

    @property
    def is_pending(self):
        return self.status == self.StatusChoices.PENDING

    @property
    def is_cancelled(self):
        return self.status == self.StatusChoices.CANCELLED

    @property
    def is_started(self):
        return self.start_date < timezone.now().date()

    def get_reviewer(self):
        return self.requester.get_holiday_approver()

    def get_requested_days(self):
        return self.requester.get_count_of_working_days_by_period(
            self.start_date, self.end_date
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.reviewer:
            self.reviewer = self.get_reviewer()
        if not self.days_requested:
            self.days_requested = self.get_requested_days()
        super().save(*args, **kwargs)


class Absence(HistoryMixin, AbsenceBase):

    tracked_fields = ["start_date", "end_date", "reason"]

    class Meta:
        ordering = ["start_date"]
        permissions = [
            ("view_all_absences", "Can view all absences"),
            ("view_department_absences", "Can view department absences"),
            ("view_team_absences", "Can view own absences"),
            ("view_absences", "Can view absences"),
        ]

    class AbsenceTypes(models.TextChoices):
        SICK = "sick", "Sick Leave"
        PERSONAL = "personal", "Personal Leave"
        UNPAID = "unpaid", "Unpaid Leave"
        OTHER = "other", "Other"

    absentee = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.CASCADE,
        related_name="absences",
        blank=False,
        null=False,
    )

    absence_type = models.CharField(
        max_length=max([len(choice) for choice in AbsenceTypes.values]),
        choices=AbsenceTypes.choices,
        blank=False,
        null=False,
    )

    added_by = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.SET_NULL,
        related_name="added_absences",
        blank=True,
        null=True,
    )

    days_of_absence = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
    )

    def get_days_of_absence(self):
        return self.absentee.get_count_of_working_days_by_period(
            self.start_date, self.end_date
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.days_of_absence:
            self.days_of_absence = self.get_days_of_absence()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.absentee.full_name()} - {self.absence_type} ({self.start_date} to {self.end_date})"
