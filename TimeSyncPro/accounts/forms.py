import logging
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.hashers import make_password
from django.db import transaction, IntegrityError
from django.db.models import Prefetch
from django.core.exceptions import ValidationError
from django.utils.text import slugify
# from django.urls import reverse
from django.utils.timezone import now

from .form_mixins import ReadonlyFieldsFormMixin, CleanEmailMixin
# from .tasks import send_welcome_email, send_password_reset_email, send_activation_email
from .utils import format_email
from .models import Company, Profile
from ..management.models import Team, ShiftPattern, Department

logger = logging.getLogger(__name__)

UserModel = get_user_model()


# TODO Autintication request
class SignupCompanyAdministratorForm(CleanEmailMixin, UserCreationForm):
    first_name = forms.CharField(
        max_length=Profile.MAX_FIRST_NAME_LENGTH,
        min_length=Profile.MIN_FIRST_NAME_LENGTH,
        required=True,
    )

    last_name = forms.CharField(
        max_length=Profile.MAX_LAST_NAME_LENGTH,
        min_length=Profile.MIN_LAST_NAME_LENGTH,
        required=True,
    )

    company_name = forms.CharField(
        max_length=Company.MAX_COMPANY_NAME_LENGTH,
        min_length=Company.MIN_COMPANY_NAME_LENGTH,
        required=True,
    )

    class Meta:
        model = UserModel
        fields = ["first_name", "last_name", "email", "company_name", "password1", "password2"]

    # def clean_email(self):
    #     email = self.cleaned_data.get('email')
    #     if email:
    #         email = format_email(email)
    #         if UserModel.objects.filter(email=email).exists():
    #             raise ValidationError("A user with this email already exists.")
    #     return email

    def clean_email(self):
        # Call the mixin method and pass in the User model
        return super().clean_email()

    def clean_company_name(self):
        company_name = self.cleaned_data.get('company_name')

        if company_name:
            slug_name = slugify(company_name)
            if Company.objects.filter(slug=slug_name).exists():
                raise ValidationError("A company with this name already exists.")
        return company_name

    def save(self, commit=True):
        try:
            with transaction.atomic():
                user = super().save(commit=False)
                user.email = self.cleaned_data["email"]
                logger.debug(f"Generated slug: {user.slug}")

                first_name = self.cleaned_data["first_name"]
                last_name = self.cleaned_data["last_name"]

                # Pass the first_name and last_name to the user save method
                user.save(first_name=first_name, last_name=last_name)

                company = Company.objects.create(
                    name=self.cleaned_data["company_name"],
                )

                employee = Profile.objects.create(
                    user=user,
                    company=company,
                    first_name=self.cleaned_data["first_name"],
                    last_name=self.cleaned_data["last_name"],
                    role=Profile.EmployeeRoles.ADMINISTRATOR,
                    days_off_left=0,
                )

                if commit:
                    company.save()
                    employee.save()

                    logger.info(
                        f"Successfully created administrator account for {user.email} at company {company.name}")

                # send_welcome_email.delay(user.email)

                return user

        except IntegrityError as e:
            logger.error(f"IntegrityError occurred while creating administrator account: {str(e)}")
            self.add_error(None, "An integrity error occurred. Please check your data and try again.")
            return None  # Return None in case of an error
        except Exception as e:
            logger.exception(f"Unexpected error occurred while creating administrator account: {str(e)}")
            self.add_error(None, f"An unexpected error occurred: {str(e)}. Please try again.")
            return None  # Return None in case of an error


# TODO add TeamLeader role
# TODO new Employee to chose from existing teams
# TODO use Employee as as fields model
class SignupEmployeeForm(CleanEmailMixin, UserCreationForm):
    employee_role = []

    class Meta:
        model = UserModel
        fields = [
            "first_name",
            "last_name",
            "email",
            "role",
            "employee_id",
            "department",
            "manages_departments",
            "shift_pattern",
            "team",
            "date_of_hire",
            "days_off_left",
        ]

    email = forms.EmailField(
        required=True
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
    )

    first_name = forms.CharField(
        max_length=Profile.MAX_FIRST_NAME_LENGTH,
        min_length=Profile.MIN_FIRST_NAME_LENGTH,
        required=True,
    )

    last_name = forms.CharField(
        max_length=Profile.MAX_LAST_NAME_LENGTH,
        min_length=Profile.MIN_LAST_NAME_LENGTH,
        required=True,
    )

    role = forms.ChoiceField(
        choices=employee_role,
        required=True,
    )

    employee_id = forms.CharField(
        max_length=Profile.MAX_EMPLOYEE_ID_LENGTH,
        min_length=Profile.MIN_EMPLOYEE_ID_LENGTH,
        required=True,
    )

    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
    )

    manages_departments = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
    )

    shift_pattern = forms.ModelChoiceField(
        queryset=None,
        required=False,
    )

    team = forms.ModelChoiceField(
        queryset=None,
        required=False,
    )

    date_of_hire = forms.DateField(
        required=True,
        initial=now().date(),
    )

    days_off_left = forms.IntegerField(
        required=True,
    )

    def clean_email(self):
        return super().clean_email()

    def clean(self):
        cleaned_data = super().clean()
        user = self.request.user

        company = user.company
        company_with_departments = Company.objects.prefetch_related('departments').get(id=company.id)

        company_departments = company_with_departments.departments.all()
        role = cleaned_data.get("role")

        # Role-specific validation
        if company_departments.exists() and (role == "Staff" or role == "Team Leader"):
            if not cleaned_data.get("department"):
                self.add_error("department", "Please select a department for the Employee role")

        if role == "Manager" and company_departments.exists():
            if not cleaned_data.get("manages_departments") and not cleaned_data.get("department"):
                self.add_error("department",
                               "Please select a 'department' or 'manages departments' for the Manager role")

        # Email validation
        # email = cleaned_data.get("email")
        # if email:
        #     email = format_email(email)
        #     if UserModel.objects.filter(email=email).exists():
        #         self.add_error("email", "A user with this email already exists.")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        self.request = kwargs.get("request", None)
        super().__init__(*args, **kwargs)

        if not self.request:
            raise forms.ValidationError("You must be authenticated to register employees.")

        user = self.request.user

        company = user.company

        if not company:
            raise forms.ValidationError("You must be associated with a company to register employees")

        # all_user_related_data = UserModel.objects.prefetch_related(
        #     Prefetch('profile', queryset=Profile.objects.all()),
        #     Prefetch('company', queryset=Company.objects.all()),
        #     Prefetch('team', queryset=Team.objects.all()),
        #     Prefetch('department', queryset=Department.objects.all()),
        #     Prefetch('shift_pattern', queryset=ShiftPattern.objects.all()),
        # ).get(id=user.id)

        # company_with_related_data = Company.objects.select_related(
        #     'user'
        # ).prefetch_related(
        #     Prefetch('teams', queryset=Team.objects.all()),
        #     Prefetch('shift_patterns', queryset=ShiftPattern.objects.all()),
        #     Prefetch('departments', queryset=Department.objects.all()),
        # ).get(id=company.id)

        company_with_related_data = Company.objects.prefetch_related(
            Prefetch('teams', queryset=Team.objects.all()),
            Prefetch('shift_patterns', queryset=ShiftPattern.objects.all()),
            Prefetch('departments', queryset=Department.objects.all()),
        ).get(id=company.id)

        teams = company_with_related_data.teams.all()
        shift_patterns = company_with_related_data.shift_patterns.all()
        departments = company_with_related_data.departments.all()

        self.fields["team"].queryset = teams
        self.fields["department"].queryset = departments
        self.fields["manages_departments"].queryset = departments
        self.fields["shift_pattern"].queryset = shift_patterns
        self.fields["password1"].widget = forms.HiddenInput()
        self.fields["password2"].widget = forms.HiddenInput()
        self.fields['role'].choices = self._adjust_role_choices(user)

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
                # Start transaction: create user and employee records
                company = self.request.user.company
                user = UserModel.objects.create_user(
                    email=self.cleaned_data["email"],
                    password=make_password(UserModel.objects.make_random_password()),
                    is_active=False,
                )

                activation_token = user.generate_activation_token()

                common_data = {
                    "user": user,
                    "company": company,
                    "first_name": self.cleaned_data["first_name"],
                    "last_name": self.cleaned_data["last_name"],
                    "role": self.cleaned_data["role"],
                    "employee_id": self.cleaned_data["employee_id"],
                    "department": self.cleaned_data["department"],
                    "shift_pattern": self.cleaned_data["shift_pattern"],
                    "team": self.cleaned_data["team"],
                    "date_of_hire": self.cleaned_data["date_of_hire"],
                    "days_off_left": self.cleaned_data["days_off_left"],
                }

                employee = Profile.objects.create(**common_data)

                if commit:
                    user.save()
                    if employee.role == "Manager" and self.cleaned_data["manages_departments"]:
                        employee.manages_departments.set(self.cleaned_data["manages_departments"])
                    employee.save()

            # Now, perform email tasks outside the transaction.
            # try:
            #     # Generate activation URL
            #     activation_url = self.request.build_absolute_uri(
            #         reverse('activate_and_set_password', args=[activation_token])
            #     )
            #
            #     # Send activation email asynchronously using Celery
            #     send_activation_email.delay(user.email, activation_url)
            #
            # except Exception as e:
            #     # Log the email sending failure but do not roll back the user/employee creation
            #     logger.error(f"Failed to send activation email to {user.email}: {str(e)}")
            #     # Optionally, you might want to inform the user or admin about this failure

            return user

        except IntegrityError as e:
            self.add_error(None, "An integrity error occurred. Please check your data and try again.")
            return None  # Return None in case of an error
        except Exception as e:
            self.add_error(None, f"An unexpected error occurred: {str(e)}. Please try again.")
            return None  # Return None in case of an error


class EditTimeSyncProUserBaseForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ['email']


class BasicEditTimeSyncProUserForm(EditTimeSyncProUserBaseForm):
    class Meta(EditTimeSyncProUserBaseForm.Meta):
        model = UserModel


class DetailedEditTimeSyncProUserForm(EditTimeSyncProUserBaseForm):
    class Meta(EditTimeSyncProUserBaseForm.Meta):
        model = UserModel
        fields = EditTimeSyncProUserBaseForm.Meta.fields + ['is_active']


class EditEmployeeBaseForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "department",
            "first_name",
            "last_name",
            "role",
            "employee_id",
            "manages_departments",
            "team",
            "shift_pattern",
            "date_of_hire",
            "days_off_left",
            "phone_number",
            "address",
            "date_of_birth",
            "profile_picture"
        ]


class BasicEditEmployeesBaseForm(ReadonlyFieldsFormMixin, EditEmployeeBaseForm):
    readonly_fields = [
        "department",
        "manages_departments",
        "first_name",
        "last_name",
        "employee_id",
        "role",
        "team",
        "date_of_hire",
        "days_off_left",
    ]

    class Meta(EditEmployeeBaseForm.Meta):
        model = Profile

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_readonly_on_fields()


class DetailedEditEmployeesBaseForm(EditEmployeeBaseForm):
    class Meta(EditEmployeeBaseForm.Meta):
        model = Profile


class BasicEditEmployeeForm(BasicEditEmployeesBaseForm):
    class Meta(BasicEditEmployeesBaseForm.Meta):
        model = Profile


class DetailedEditEmployeeForm(DetailedEditEmployeesBaseForm):
    class Meta(DetailedEditEmployeesBaseForm.Meta):
        model = Profile


# TODO only Administrator can edit company
class EditCompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "name",
            "leave_days_per_year",
            "transferable_leave_days",
            "location",
            "leave_approver",
            "transferable_leave_days",
            "minimum_leave_notice",
            "maximum_leave_days_per_request",
            "working_on_local_holidays",
        ]

    # def clean(self):
    #     cleaned_data = super().clean()
    #     if 'location' in cleaned_data and not cleaned_data.get('time_zone'):
    #         # If a location is set but no time zone, suggest one
    #         cleaned_data['time_zone'] = self.instance.suggest_time_zone()
    #     return cleaned_data


class DeleteUserForm(forms.Form):
    pass


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.user.is_active:
            raise forms.ValidationError("This account is already active.")
