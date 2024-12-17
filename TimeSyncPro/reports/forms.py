from django import forms
from django.utils import timezone

from TimeSyncPro.companies.models import Department, Team


class GenerateReportForm(forms.Form):

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), initial=timezone.now().date()
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), initial=timezone.now().date()
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(), required=False
    )
    team = forms.ModelChoiceField(queryset=Team.objects.none(), required=False)

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields["department"].queryset = Department.objects.filter(
                company=company
            )
            self.fields["team"].queryset = Team.objects.filter(company=company)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        print(start_date)
        end_date = cleaned_data.get("end_date")
        print(end_date)

        if start_date > end_date:
            self.add_error("start_date", "Start date must be before end date.")
            print("Start date must be before end date.")

        return cleaned_data
