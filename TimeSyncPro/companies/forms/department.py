from django import forms
from django.contrib.auth import get_user_model

from .mixins import Select2SlideCheckboxWidget
from ..models import Department, Team

from TimeSyncPro.common.form_mixins import CheckExistingNamePerCompanyMixin
from ...accounts.models import Profile

UserModel = get_user_model()


class DepartmentBaseForm(CheckExistingNamePerCompanyMixin, forms.ModelForm):

    department_members = forms.ModelMultipleChoiceField(
        queryset=UserModel.objects.none(),
        required=False,
        widget=Select2SlideCheckboxWidget(attrs={
            'class': 'select2-checkbox',
            'data-placeholder': 'Select members...'
        })
    )

    class Meta:
        model = Department
        fields = ['name', 'holiday_approver', 'department_members']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        self.user = user
        self.company = company

        if self.company:
            self.fields['department_members'].queryset = self.company.employees.filter(department=None)
            self.fields['holiday_approver'].queryset = self.company.employees.filter(role__in=["HR", "MANAGER"])
            self.fields['teams'].queryset = Team.objects.filter(company=self.company, team_department=None)
        else:
            self.fields['department_members'].queryset = UserModel.objects.none()
            self.fields['holiday_approver'].queryset = UserModel.objects.none()

        self.fields['department_members'].label = "Department Members"

    def save(self, commit=True):
        department = super().save(commit=False)
        department.company = self.company

        if commit:
            department.save()
            if 'department_members' in self.cleaned_data:
                Profile.objects.filter(id__in=[m.id for m in self.cleaned_data['team_members']]).update(department=department)

        return department


class CreateDepartmentForm(DepartmentBaseForm):
    pass


# class EditDepartmentForm(CheckExistingNamePerCompanyMixin, DepartmentBaseForm):
#     class Meta:
#         model = Department
#         fields = ['name', 'holiday_approver']
#
#
#
#
