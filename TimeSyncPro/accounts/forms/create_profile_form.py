import logging
from django import forms
from django.contrib.auth import get_user_model
from ..form_mixins import RequiredFieldsFormMixin
from ..models import Profile


logger = logging.getLogger(__name__)

UserModel = get_user_model()


class CrateProfileBaseForm(RequiredFieldsFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ["user", "company", "is_company_admin"]

        widgets = {
            "date_of_hire": forms.DateInput(attrs={"type": "date"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }


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
        self.fields['role'] = forms.ChoiceField(
            choices=[
                (Profile.EmployeeRoles.HR, 'HR'),
                (Profile.EmployeeRoles.MANAGER, 'Manager'),
            ]
        )


