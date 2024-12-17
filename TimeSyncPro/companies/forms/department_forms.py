from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

from .mixins import Select2SlideCheckboxWidget
from ..models import Department, Team

from TimeSyncPro.common.form_mixins import CheckExistingNamePerCompanyMixin
from ...accounts.models import Profile

UserModel = get_user_model()


class DepartmentBaseForm(CheckExistingNamePerCompanyMixin, forms.ModelForm):

    department_members = forms.ModelMultipleChoiceField(
        queryset=UserModel.objects.none(),
        required=False,
        widget=Select2SlideCheckboxWidget(
            attrs={"class": "select2-checkbox", "data-placeholder": "Select members..."}
        ),
    )

    class Meta:
        model = Department
        fields = ["name", "holiday_approver", "department_members"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)
        self.user = user
        self.company = company

        if self.company:
            self.fields["department_members"].queryset = self.company.employees.filter(
                department=None
            )
            self.fields["holiday_approver"].queryset = (
                self.company.get_company_holiday_approvers()
            )
        else:
            self.fields["department_members"].queryset = UserModel.objects.none()
            self.fields["holiday_approver"].queryset = UserModel.objects.none()

        self.fields["department_members"].label = "Department Members"

    def save(self, commit=True):
        department = super().save(commit=False)
        department.company = self.company

        if commit:
            department.save()
            if "department_members" in self.cleaned_data:
                (
                    Profile.objects.filter(
                        id__in=[m.id for m in self.cleaned_data["department_members"]]
                    ).update(department=department)
                )
        return department


class CreateDepartmentForm(DepartmentBaseForm):
    pass


class EditDepartmentForm(DepartmentBaseForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        company = kwargs.pop("company", None)
        department = kwargs.pop("department", None)
        super().__init__(*args, **kwargs)
        self.user = user
        self.company = company
        self.department = department
        self.initial_department_members = set(
            self.department.employees.all() if self.department else []
        )

        if self.company:
            sorted_department_members = self.department.employees.all().order_by(
                "first_name", "last_name"
            )
            sorted_non_department_members = self.company.employees.filter(
                department=None
            ).order_by("first_name", "last_name")
            combined_queryset = (
                sorted_department_members | sorted_non_department_members
            )

            self.fields["department_members"].queryset = combined_queryset
            self.fields["department_members"].initial = self.initial_department_members
            self.fields["holiday_approver"].queryset = (
                self.company.get_company_holiday_approvers()
            )
            self.fields["department_members"].label = "Department Members"

    @transaction.atomic
    def save(self, commit=True):
        department = super().save(commit=False)
        if commit:
            department.save()

            final_department_members = set(self.cleaned_data["department_members"])
            members_to_remove = (
                self.initial_department_members - final_department_members
            )
            Profile.objects.filter(id__in=[m.id for m in members_to_remove]).update(
                department=None
            )

            members_to_add = final_department_members - self.initial_department_members
            Profile.objects.filter(id__in=[m.id for m in members_to_add]).update(
                department=department
            )


class DeleteDepartmentForm(forms.ModelForm):
    pass
