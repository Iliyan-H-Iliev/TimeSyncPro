from django import forms
from django.contrib.auth import get_user_model

from ..form_mixins import ReadonlyFieldsFormMixin, RequiredFieldsFormMixin

from ..models import Profile
from ...companies.models import Team, Shift, Department

UserModel = get_user_model()


class EditProfileBaseForm(forms.ModelForm):
    RELATED_FIELDS = {
        'department': Department,
        'team': Team,
        'shift': Shift
    }

    class Meta:
        model = Profile
        fields = [
            "is_company_admin",
            "department",
            "first_name",
            "last_name",
            "role",
            "employee_id",
            "team",
            "shift",
            "date_of_hire",
            "remaining_leave_days",
            "phone_number",
            "date_of_birth",
            "profile_picture"
        ]

        widgets = {
            "date_of_hire": forms.DateInput(attrs={"type": "date"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

        if self.request and hasattr(self.request, 'user'):
            if not self.request.user.is_company_admin:
                self.fields.pop("is_company_admin")

        if hasattr(self.instance, 'company'):
            for field_name, model in self.RELATED_FIELDS.items():
                if field_name in self.fields:
                    queryset = model.objects.filter(company=self.instance.company)
                    self.fields[field_name].queryset = queryset

                    if not queryset.exists():
                        self.fields[field_name].widget = forms.HiddenInput()
                        self.fields[field_name].required = False


class BasicEditProfileForm(ReadonlyFieldsFormMixin, EditProfileBaseForm):
    readonly_fields = [
        "department",
        "manages_departments",
        "first_name",
        "last_name",
        "employee_id",
        "role",
        "team",
        "shift",
        "date_of_hire",
        "remaining_leave_days"
    ]

    class Meta(EditProfileBaseForm.Meta):
        model = Profile

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_readonly_on_fields()


class DetailedEditOwnProfileForm(RequiredFieldsFormMixin, EditProfileBaseForm):

    required_fields = (
        "first_name",
        "last_name",
        "role",
        "date_of_hire",
        "remaining_leave_days",
    )

    def clean_is_company_admin(self):
        count_company_admins = Profile.objects.filter(company=self.instance.company, is_company_admin=True).count()
        obj = self.instance
        if self.request.user.is_company_admin and obj == self.request.user.profile:
            if not self.cleaned_data.get("is_company_admin") and count_company_admins == 1:
                raise forms.ValidationError("There must be at least one company admin.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_required_on_fields()


class DetailedEditProfileForm(DetailedEditOwnProfileForm):
    class Meta(DetailedEditOwnProfileForm.Meta):
        model = Profile
        exclude = ["profile_picture"]


class AdminEditProfileForm(DetailedEditOwnProfileForm):
    class Meta(DetailedEditOwnProfileForm.Meta):
        model = Profile
        fields = [
            "is_company_admin",
            "first_name",
            "last_name",
            "phone_number",
            "date_of_birth",
            "profile_picture"
        ]