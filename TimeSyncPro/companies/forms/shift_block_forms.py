from datetime import datetime, timedelta
from django import forms

from ..models import Shift, ShiftBlock
from django.forms.models import inlineformset_factory

from ...common.form_mixins import LabelMixin


# class HiddenDeleteFormSet(BaseModelFormSet):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         for form in self.forms:
#             if 'DELETE' in form.fields:
#                 form.fields['DELETE'].widget = HiddenInput()


class ShiftBlockBaseForm(LabelMixin, forms.ModelForm):
    MIN_DAYS_ON = 0
    MAX_DAYS_ON = 7
    MIN_DAYS_OFF = 0
    MAX_DAYS_OFF = 7
    MIN_DURATION_HOURS = 0
    MAX_DURATION_HOURS = 23
    MIN_DURATION_MINUTES = 0
    MAX_DURATION_MINUTES = 59

    CHOICES = [
        (1, "Monday"),
        (2, "Tuesday"),
        (3, "Wednesday"),
        (4, "Thursday"),
        (5, "Friday"),
        (6, "Saturday"),
        (7, "Sunday"),
    ]

    week_days = forms.MultipleChoiceField(
        choices=CHOICES, widget=forms.CheckboxSelectMultiple, required=False
    )

    duration_hours = forms.IntegerField(
        required=False,
        label="Duration (hours)",
        min_value=MIN_DURATION_HOURS,
        max_value=MAX_DURATION_HOURS,
    )

    duration_minutes = forms.IntegerField(
        required=False,
        label="Duration (minutes)",
        min_value=MIN_DURATION_MINUTES,
        max_value=MAX_DURATION_MINUTES,
    )

    class Meta:
        model = ShiftBlock
        fields = [
            "start_time",
            "end_time",
            "week_days",
            "days_on",
            "days_off",
            "duration_hours",
            "duration_minutes",
        ]

        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean_duration(self):
        start_time = self.cleaned_data.get("start_time")
        end_time = self.cleaned_data.get("end_time")
        hours = self.cleaned_data.get("duration_hours") or 0
        minutes = self.cleaned_data.get("duration_minutes") or 0

        if hours or minutes:
            return timedelta(hours=hours, minutes=minutes)

        ref_date = datetime.now().date()
        start_datetime = datetime.combine(ref_date, start_time)
        end_datetime = datetime.combine(ref_date, end_time)

        # Handle overnight shift
        if end_datetime <= start_datetime:
            end_datetime += timedelta(days=1)

        duration = end_datetime - start_datetime
        return duration

    def clean(self):
        # TODO debug this
        cleaned_data = super().clean()
        week_days = cleaned_data.get("week_days")
        days_on = cleaned_data.get("days_on")
        days_off = cleaned_data.get("days_off")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        self.instance.duration = self.clean_duration()

        if not week_days and (days_on is None and days_off is None):
            self.add_error(
                "week_days",
                "You must specify either working days or a pattern (days on and days off).",
            )

        if week_days:
            if days_on is not None or days_off is not None:
                self.add_error(
                    "week_days",
                    "You must specify either working days or a pattern (days on and days off), not both.",
                )

        if week_days:
            week_days_int = [int(day) for day in week_days]
            self.instance.selected_days = week_days_int
            on_off_days = [1 if i in week_days_int else 0 for i in range(1, 8)]
            self.instance.on_off_days = on_off_days

        else:
            on_off_days = []

            if days_on is not None:
                on_off_days.extend([1] * days_on)

            if days_off is not None:
                on_off_days.extend([0] * days_off)

            self.instance.on_off_days = on_off_days

        return cleaned_data


class CreateShiftBlockForm(ShiftBlockBaseForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)


CreateShiftBlockFormSet = forms.inlineformset_factory(
    Shift,
    ShiftBlock,
    form=CreateShiftBlockForm,
    extra=1,
    can_delete=True,
)


class UpdateShiftBlockForm(ShiftBlockBaseForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(UpdateShiftBlockForm, self).__init__(*args, **kwargs)
        a = self.instance
        if self.instance.selected_days:
            self.fields["week_days"].initial = self.instance.selected_days

        if self.instance.duration:
            total_seconds = self.instance.duration.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            self.fields["duration_hours"].initial = hours
            self.fields["duration_minutes"].initial = minutes


UpdateShiftBlockFormSet = inlineformset_factory(
    Shift,
    ShiftBlock,
    form=UpdateShiftBlockForm,
    extra=0,
    can_delete=True,
)
