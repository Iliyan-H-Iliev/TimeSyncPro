from django import forms
from django.utils import timezone

from TimeSyncPro.absences.models import Holiday


class RequestHolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'reason': 'Reason',
        }
        help_texts = {
            'reason': 'Please provide a reason for your holiday request.',
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

        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError('The start date must be before the end date.')
        return cleaned_data

    def save(self, commit=True):
        holiday = super().save(commit=False)
        holiday.user = self.request.user
        if commit:
            holiday.save()
        return holiday

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']
        if start_date < timezone.now().date():
            raise forms.ValidationError('The start date must be in the future.')
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data['end_date']
        if end_date < timezone.now().date():
            raise forms.ValidationError('The end date must be in the future.')
        return end_date


class ReviewHolidayForm(forms.ModelForm):

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
            'review_reason': 'Please provide a reason for your review.',
        }

    def save(self, commit=True):
        holiday = super().save(commit=False)
        holiday.reviewed_by = self.request.user
        if commit:
            holiday.save()
        return holiday

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.action = kwargs.pop('action')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        action = self.action
        review_reason = cleaned_data.get('review_reason')

        if action == Holiday.StatusChoices.DENIED and not review_reason:
            raise forms.ValidationError('Please provide a review reason for an approved holiday.')