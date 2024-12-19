import datetime
from datetime import date, timedelta
from django import forms
from django.db import transaction
from django.utils import timezone
from TimeSyncPro.absences.models import Holiday
from TimeSyncPro.common.form_mixins import LabelMixin


class RequestHolidayForm(LabelMixin, forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ["start_date", "end_date", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date", id: "start_date"}),
            "end_date": forms.DateInput(attrs={"type": "date", id: "end_date"}),
            "reason": forms.Textarea(attrs={"rows": 5}),
        }

        labels = {
            "start_date": "Start Date",
            "end_date": "End Date",
            "reason": "Reason",
        }
        error_messages = {
            "start_date": {
                "required": "Please provide a start date for your holiday request.",
            },
            "end_date": {
                "required": "Please provide an end date for your holiday request.",
            },
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        requester = self.request.user.profile
        remaining_days = requester.remaining_leave_days
        next_year_remaining_days = requester.next_year_leave_days
        requested_days = requester.get_count_of_working_days_by_period(
            start_date, end_date
        )
        today = timezone.now().date()
        company = requester.company
        working_days = requester.get_working_days(start_date, end_date)
        minimum_notice_date = date.today() + timedelta(
            days=company.minimum_leave_notice
        )

        if not start_date or not end_date:
            return cleaned_data

        if start_date < today:
            self.add_error("start_date", "The start date must be in the future.")
        if end_date < today:
            self.add_error("end_date", "The end date must be in the future.")

        if start_date > end_date:
            self.add_error("start_date", "The start date must be before the end date.")

        if start_date > today + datetime.timedelta(days=365):
            self.add_error("start_date", "You cannot request a holiday more than a year in advance.")

        if end_date >= date(today.year + 1, 12, 31):
            self.add_error("end_date", "You cannot request a holiday more than a year in advance.")

        if start_date <= date(today.year, 12, 31):

            if requested_days > remaining_days:
                self.add_error(
                    "start_date",
                    "You do not have enough holiday days remaining for this request.",
                )
        elif start_date <= date(today.year + 1, 12, 31):
            if requested_days > next_year_remaining_days:
                self.add_error(
                    "start_date",
                    "You do not have enough holiday days remaining for this request.",
                )

        if requested_days > company.maximum_leave_days_per_request:
            self.add_error(
                "start_date",
                f"You cannot request more than {company.maximum_leave_days_per_request} days at a time.",
            )

        if start_date not in working_days:
            self.add_error(
                "start_date", "You cannot request a holiday on a non-working day."
            )

        if end_date not in working_days:
            self.add_error(
                "end_date", "You cannot request a holiday on a non-working day."
            )

        if start_date < minimum_notice_date:
            self.add_error(
                "start_date",
                f"You must provide at least {company.minimum_leave_notice} days notice for a holiday request.",
            )

        overlapping_holidays = Holiday.objects.filter(
            requester=requester, start_date__lte=end_date, end_date__gte=start_date
        )

        if overlapping_holidays.exists():
            self.add_error(
                "start_date", "You already have a holiday request for this date range."
            )

        return cleaned_data

    def save(self, commit=True):
        with transaction.atomic():
            try:
                holiday = super().save(commit=False)
                holiday.requester = self.request.user.profile
                holiday.status = Holiday.StatusChoices.PENDING
                if commit:
                    holiday.save()
                    today = timezone.now().date()

                    if holiday.start_date <= date(today.year, 12, 31):
                        holiday.requester.set_remaining_leave_days(holiday.days_requested)

                    else:
                        holiday.requester.set_next_year_leave_days(holiday.days_requested)

                return holiday

            except Exception as e:
                raise forms.ValidationError(f"An error occurred: {e}")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)


class ReviewHolidayForm(LabelMixin, forms.ModelForm):

    class Meta:
        model = Holiday
        fields = ["review_reason"]

        widgets = {
            "review_reason": forms.Textarea(attrs={"rows": 5}),
        }
        labels = {
            "review_reason": "Review Reason",
        }
        help_texts = {
            "review_reason": "Please provide a reason for your review."
            "It is required for denied holiday requests.",
        }
