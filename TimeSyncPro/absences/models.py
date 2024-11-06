from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

import TimeSyncPro.common.model_mixins as common_mixins
from TimeSyncPro.history.model_mixins import HistoryMixin

User_Model = get_user_model()


class AbsenceBase(common_mixins.CreatedModifiedMixin, models.Model):
    MAX_LENGTH_REASON = 500

    class Meta:
        abstract = True

    start_date = models.DateField()

    end_date = models.DateField()

    reason = models.TextField(
        max_length=MAX_LENGTH_REASON,
        blank=True,
        null=True,
    )


class Holiday(AbsenceBase):
    MAX_LENGTH_REVIEW_REASON = 500

    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        DENIED = 'denied', 'Denied'
        CANCELLED = 'cancelled', 'Cancelled'

    requester = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.CASCADE,
        related_name='holidays',
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
        related_name='holiday_for_review',
    )

    reviewed_by = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_holidays',
    )

    review_reason = models.TextField(
        max_length=MAX_LENGTH_REVIEW_REASON,
        blank=True,
        null=True,
    )

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

    def get_reviewer(self):

        if hasattr(self.requester, 'team'):
            if self.requester.team.holiday_approver:
                return self.requester.team.holiday_approver
        elif hasattr(self.requester, 'department'):
            if self.requester.department.holiday_approver:
                return self.requester.department.holiday_approver
        else:
            return self.requester.company.holiday_approver

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("End date must be after start date.")

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.reviewer:
            self.reviewer = self.get_reviewer()
        super().save(*args, **kwargs)


class Absence(HistoryMixin, AbsenceBase):
    class AbsenceTypes(models.TextChoices):
        SICK = 'sick', 'Sick Leave'
        PERSONAL = 'personal', 'Personal Leave'
        UNPAID = 'unpaid', 'Unpaid Leave'
        OTHER = 'other', 'Other'

    absentee = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.CASCADE,
        related_name='absences',
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
        related_name='added_absences',
        blank=True,
        null=True,
    )

    # TODO - Add duration field

    def __str__(self):
        return f"{self.absentee.full_name()} - {self.absence_type} ({self.start_date} to {self.end_date})"
