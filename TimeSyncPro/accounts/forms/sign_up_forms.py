import logging
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction, IntegrityError
from django.db.models import Prefetch
from django.urls import reverse

from TimeSyncPro.common.form_mixins import CleanEmailMixin, RequiredFieldsFormMixin
from TimeSyncPro.accounts.tasks import send_activation_email
from ..models import Profile
from ...companies.models import Team, Shift, Department, Company

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class SignupCompanyAdministratorForm(UserCreationForm):

    class Meta:
        model = UserModel
        fields = ["email", "password1", "password2"]

    def save(self, commit=True):
        try:
            user = super().save(commit=False)
            user.skip_profile_creation = True
            user.email = self.cleaned_data["email"]
            user.save()
            return user

        except Exception as e:
            logger.exception(
                f"Unexpected error occurred while creating administrator account: {str(e)}"
            )
            self.add_error(None, f"An unexpected error. Please try again.")
            return None


class SignupEmployeeForm(RequiredFieldsFormMixin, CleanEmailMixin, UserCreationForm):
    employee_role = []

    profile_fields = (
        "is_company_admin",
        "first_name",
        "last_name",
        "role",
        "date_of_hire",
        "remaining_leave_days",
        "employee_id",
        "department",
        "team",
        "shift",
    )

    required_fields = (
        "first_name",
        "last_name",
        "role",
        "date_of_hire",
        "remaining_leave_days",
    )

    class Meta:
        model = UserModel
        fields = [
            "email",
            "password1",
            "password2",
        ]

        help_texts = {
            "remaining_leave_days": "Number of days off left for the year",
        }

    def clean_email(self):
        return super().clean_email()

    def clean(self):
        cleaned_data = super().clean()
        user = self.request.user

        company = user.company
        company_with_departments = Company.objects.prefetch_related("departments").get(
            id=company.id
        )

        company_departments = company_with_departments.departments.all()
        role = cleaned_data.get("role")

        if company_departments.exists() and (role == "Staff" or role == "Team Leader"):
            if not cleaned_data.get("department"):
                self.add_error(
                    "department", "Please select a department for the Employee role"
                )

        if role == "Manager" and company_departments.exists():
            if not cleaned_data.get("manages_departments") and not cleaned_data.get(
                "department"
            ):
                self.add_error(
                    "department",
                    "Please select a 'department' or 'manages departments' for the Manager role",
                )

        return cleaned_data

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        self._add_profile_fields()
        self._apply_required_on_fields()

        user = self.request.user

        company = user.company

        random_password = UserModel.objects.make_random_password()

        if not company:
            raise forms.ValidationError(
                "You must be associated with a company to register employees"
            )

        company_with_related_data = Company.objects.prefetch_related(
            Prefetch("teams", queryset=Team.objects.all()),
            Prefetch("shifts", queryset=Shift.objects.all()),
            Prefetch("departments", queryset=Department.objects.all()),
        ).get(id=company.id)

        teams = company_with_related_data.teams.all()
        shifts = company_with_related_data.shifts.all()
        departments = company_with_related_data.departments.all()

        if not teams.exists():
            self.fields["team"].widget = forms.HiddenInput()
            self.fields["team"].initial = None
        else:
            self.fields["team"].queryset = teams

        if not shifts.exists():
            self.fields["shift"].widget = forms.HiddenInput()
            self.fields["shift"].initial = None
        else:
            self.fields["shift"].queryset = shifts

        if not departments.exists():
            self.fields["department"].widget = forms.HiddenInput()
            self.fields["department"].initial = None
        else:
            self.fields["department"].queryset = departments

        self.fields["password1"].widget = forms.HiddenInput()
        self.fields["password2"].widget = forms.HiddenInput()
        self.fields["password1"].required = False
        self.fields["password2"].required = False
        self.fields["password1"].initial = random_password
        self.fields["password2"].initial = random_password
        self._random_password = random_password

        self.fields["role"].choices = self._adjust_role_choices(user)

        if not user.has_perm("accounts.add_company_admin"):
            self.fields["is_company_admin"].widget = forms.HiddenInput()
            self.fields["is_company_admin"].initial = False  # Add this

        self.fields["remaining_leave_days"].help_text = (
            "Number of days off left for the year"
        )
        self.fields["shift"].help_text = (
            "Select shift if employee is not assigned to a team with shift"
            " or if is different shift than the team."
        )
        self.fields["team"].help_text = "Select the team the employee is assigned to."
        self.fields["date_of_hire"].widget = forms.DateInput(attrs={"type": "date"})

    def _add_profile_fields(self):
        profile_fields = forms.models.fields_for_model(
            Profile, fields=self.profile_fields
        )
        self.fields.update(profile_fields)

    @staticmethod
    def _adjust_role_choices(user):

        employee_role = Profile.get_all_employee_roles()
        role_choices = []

        for role in employee_role:
            if user.has_perm(f'accounts.add_{role.lower().replace(" ", "_")}'):
                role_choices.append((role, role))
        return role_choices

    def save(self, commit=True):
        try:
            with transaction.atomic():

                company = self.request.user.company
                activation_token = UserModel.generate_activation_token()

                user = UserModel(
                    email=self.cleaned_data["email"],
                    is_active=False,
                    activation_token=activation_token,
                )
                user.set_password(self._random_password)

                user.skip_profile_creation = True
                user.save(
                    first_name=self.cleaned_data["first_name"],
                    last_name=self.cleaned_data["last_name"],
                    employee_id=self.cleaned_data["employee_id"],
                )

                common_data = {
                    "user": user,
                    "company": company,
                    "first_name": self.cleaned_data["first_name"],
                    "last_name": self.cleaned_data["last_name"],
                    "is_company_admin": self.cleaned_data["is_company_admin"],
                    "role": self.cleaned_data["role"],
                    "employee_id": self.cleaned_data["employee_id"],
                    "department": self.cleaned_data["department"],
                    "shift": self.cleaned_data["shift"],
                    "team": self.cleaned_data["team"],
                    "date_of_hire": self.cleaned_data["date_of_hire"],
                    "remaining_leave_days": self.cleaned_data["remaining_leave_days"],
                }

                employee = Profile.objects.create(**common_data)

            try:
                email = user.email
                site_domain = self.request.get_host()
                protocol = "https" if self.request.is_secure() else "http"
                relative_url = reverse(
                    "activate_and_set_password", args=[activation_token]
                )

                task = send_activation_email.apply_async(
                    args=[email, site_domain, protocol, relative_url], countdown=1
                )

            except Exception as e:
                print(f"DEBUG: Email task error: {str(e)}")  # Debug print
                logger.error(f"Failed to queue email: {str(e)}")

            return user

        except IntegrityError as e:

            self.add_error(
                None,
                "An integrity error occurred. Please check your data and try again.",
            )
            raise

        except Exception as e:
            self.add_error(
                None, f"An unexpected error occurred: {str(e)}. Please try again."
            )
            raise
