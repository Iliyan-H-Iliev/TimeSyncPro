from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from TimeSyncPro.absences.models import Absence
from TimeSyncPro.accounts.form_mixins import ReadonlyFieldsFormMixin, RequiredFieldsFormMixin

UserModel = get_user_model()


class CreateAbsenceForm(RequiredFieldsFormMixin, ReadonlyFieldsFormMixin, forms.ModelForm):

    required_fields = [
        "reason",
    ]

    class Meta:
        model = Absence
        fields = ["start_date", "end_date", "absence_type", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        absence_type = cleaned_data.get("absence_type")
        absentee = self.absentee
        working_days = absentee.profile.get_working_days(start_date, end_date)

        overlapping_absence = Absence.objects.filter(
            absentee=absentee.profile,
            start_date__lte=end_date,
            end_date__gte=start_date
        )

        if overlapping_absence.exists():
            self.add_error("start_date", "An absence already exists for this period.")

        if start_date > end_date:
            self.add_error("start_date", "Start date must be before end date.")

        if absence_type is None:
            self.add_error("absence_type", "Please select an absence type.")

        if start_date not in working_days:
            self.add_error("start_date", "Cannot create an absence for a non-working day.")

        if end_date not in working_days:
            self.add_error("end_date", "Cannot create an absence for a non-working day.")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.absentee = kwargs.pop("absentee", None)
        super().__init__(*args, **kwargs)
        self._apply_required_on_fields()

    def save(self, commit=True):
        absence = super().save(commit=False)
        absence.added_by = self.request.user.profile
        absence.absentee = self.absentee.profile
        if commit:
            absence.save()
        return absence
