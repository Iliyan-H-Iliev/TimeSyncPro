from django import forms
from ..models import Company

from TimeSyncPro.common.form_mixins import CheckCompanyExistingSlugMixin
from ...accounts.models import Profile


class CompanyBaseForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "name",
            "email",
            "annual_leave",
            "max_carryover_leave",
            "minimum_leave_notice",
            "maximum_leave_days_per_request",
            "working_on_local_holidays",
            "time_zone",
        ]


class CreateCompanyForm(CompanyBaseForm):
    pass

    # def __init__(self, *args, **kwargs):
    #     self.user = kwargs.pop('user', None)
    #     super().__init__(*args, **kwargs)

    # def save(self, commit=True):
    #     company = super().save(commit=False)
    #     if commit:
    #         company.save()
    #     return company

    # TODO only Administrator can edit company


class EditCompanyForm(CheckCompanyExistingSlugMixin, CompanyBaseForm):
    class Meta(CompanyBaseForm.Meta):
        fields = CompanyBaseForm.Meta.fields + ["holiday_approver"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["holiday_approver"].queryset = Company.objects.get(
            pk=self.instance.pk).employees.filter(
            role__in=[
                Profile.EmployeeRoles.HR,
                Profile.EmployeeRoles.MANAGER],
        )

    def clean_holiday_approver(self):
        holiday_approver = self.cleaned_data.get("holiday_approver")
        if holiday_approver is None:
            raise forms.ValidationError("Leave approver is required.")
        return holiday_approver

    # def save(self, commit=True):
    #     company = super().save(commit=False)
    #     if commit:
    #         company.save()
    #     return company

    # def clean(self):
    #     cleaned_data = super().clean()
    #     if 'location' in cleaned_data and not cleaned_data.get('time_zone'):
    #         # If a location is set but no time zone, suggest one
    #         cleaned_data['time_zone'] = self.instance.suggest_time_zone()
    #     return cleaned_data
