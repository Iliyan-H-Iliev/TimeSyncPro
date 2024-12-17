import logging
from django import forms
from django.contrib.auth import get_user_model
from TimeSyncPro.common.form_mixins import RequiredFieldsFormMixin
from ..models import Profile


logger = logging.getLogger(__name__)

UserModel = get_user_model()


class CrateProfileBaseForm(RequiredFieldsFormMixin, forms.ModelForm):

    required_fields = [
        "first_name",
        "last_name",
        "role",
        "employee_id",
        "date_of_hire",
        "remaining_leave_days",
    ]

    class Meta:
        model = Profile
        exclude = ["user", "company", "is_company_admin"]

        widgets = {
            "date_of_hire": forms.DateInput(attrs={"type": "date"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_required_on_fields()


class CreateCompanyAdministratorProfileForm(CrateProfileBaseForm):
    class Meta(CrateProfileBaseForm.Meta):
        exclude = CrateProfileBaseForm.Meta.exclude + [
            "department",
            "manages_departments",
            "team",
            "shift",
            "address",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"] = forms.ChoiceField(
            choices=[
                (Profile.EmployeeRoles.HR, "HR"),
                (Profile.EmployeeRoles.MANAGER, "Manager"),
            ]
        )
