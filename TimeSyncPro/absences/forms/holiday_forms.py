from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from TimeSyncPro.absences.models import Holiday
from TimeSyncPro.accounts.models import Profile
from TimeSyncPro.common.form_mixins import LabelMixin


class RequestHolidayForm(LabelMixin, forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', id: 'start_date'}),
            'end_date': forms.DateInput(attrs={'type': 'date', id: 'end_date'}),
            'reason': forms.Textarea(attrs={'rows': 5}),
        }

        labels = {
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'reason': 'Reason',
        }
        error_messages = {
            'start_date': {
                'required': 'Please provide a start date for your holiday request.',
            },
            'end_date': {
                'required': 'Please provide an end date for your holiday request.',
            },
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        requester = self.request.user.profile
        remaining_days = requester.remaining_leave_days
        requested_days = requester.get_working_days_by_period(start_date, end_date)
        today = timezone.now().date()

        if not start_date or not end_date:
            return cleaned_data

        if start_date < today:
            self.add_error('start_date', 'The start date must be in the future.')
        if end_date < today:
            self.add_error('end_date', 'The end date must be in the future.')

        if start_date > end_date:
            self.add_error('start_date', 'The start date must be before the end date.')

        if requested_days > remaining_days:
            self.add_error('start_date', 'You do not have enough holiday days remaining for this request.')

        overlapping_holidays = Holiday.objects.filter(
            requester=requester,
            start_date__lte=end_date,
            end_date__gte=start_date
        )

        if overlapping_holidays.exists():
            raise ValidationError(
                f"Holiday request already exists for the date range {start_date} to {end_date}."
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
                    # Reduce remaining leave days
                    holiday.requester.remaining_leave_days = F('remaining_leave_days') - holiday.days_requested
                    holiday.requester.save(update_fields=['remaining_leave_days'])
                return holiday
            except Exception as e:
                raise forms.ValidationError(f"An error occurred: {e}")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)


class ReviewHolidayForm(LabelMixin, forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ['review_reason']
        widgets = {
            'review_reason': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'review_reason': 'Review Reason',
        }
        help_texts = {
            'review_reason': 'Please provide a reason for your review.'
                             'It is required for denied holiday requests.',
        }
    #
    # def save(self, commit=True):
    #     holiday = super().save(commit=False)
    #     holiday.reviewed_by = self.request.user
    #     if commit:
    #         holiday.save()
    #     return holiday
    #
    # def __init__(self, *args, **kwargs):
    #     self.request = kwargs.pop('request')
    #     self.action = kwargs.pop('action')
    #     super().__init__(*args, **kwargs)
    #
    # def clean(self):
    #     cleaned_data = super().clean()
    #     action = self.action
    #     review_reason = cleaned_data.get('review_reason')
    #
    #     if action == Holiday.StatusChoices.DENIED and not review_reason:
    #         raise forms.ValidationError('Please provide a review reason for an approved holiday.')
