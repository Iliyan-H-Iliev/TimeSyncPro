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



class EditCompanyForm(CheckCompanyExistingSlugMixin, CompanyBaseForm):
    class Meta(CompanyBaseForm.Meta):
        fields = CompanyBaseForm.Meta.fields + ["holiday_approver"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            company = Company.objects.get(pk=self.instance.pk)
            self.fields["holiday_approver"].queryset = company.get_company_holiday_approvers()
        else:
            self.fields["holiday_approver"].queryset = Profile.objects.none()

    def clean_holiday_approver(self):
        holiday_approver = self.cleaned_data.get("holiday_approver")
        if holiday_approver is None:
            raise forms.ValidationError("Leave approver is required.")
        return holiday_approver
