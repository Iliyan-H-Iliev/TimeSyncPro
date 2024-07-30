from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.db.models import Prefetch

from django.utils.timezone import now

from .form_mixins import ReadonlyFieldsFormMixin
from .models import  Company,  Employee
from ..management.models import Team, ShiftPattern, Department

UserModel = get_user_model()

# employee_edit_fields = [
#     'first_name',
#     'last_name',
#     'employee_id',
#     'managed_by',
#     'date_of_hire',
#     'days_off_left',
#     "phone_number",
#     "address", "date_of_birth",
#     "profile_picture",
# ]
# user_edit_fields = ['email']
# company_edit_fields = ['company_name']


class SignupCompanyForm(UserCreationForm):
    company_name = forms.CharField(
        max_length=Company.MAX_COMPANY_NAME_LENGTH,
        min_length=Company.MIN_COMPANY_NAME_LENGTH,
        required=True,
        widget=forms.TextInput(attrs={'autofocus': 'autofocus'}),
    )

    class Meta:
        model = UserModel
        fields = ["company_name", "email", "password1", "password2"]

    def save(self, commit=True):

        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_company = True
        if commit:
            user.save()

        company = Company.objects.create(
            company_name=self.cleaned_data["company_name"],
            user=user,
        )

        user.company = company

        if commit:
            company.save()
            user.save()
        return user


# TODO add TeamLeader role
# TODO new Employee to chose from existing teams
# TODO use Employee as as fields model
class SignupEmployeeForm(UserCreationForm):
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
        max_length=Employee.MAX_FIRST_NAME_LENGTH,
        required=True,
    )

    last_name = forms.CharField(
        max_length=Employee.MAX_LAST_NAME_LENGTH,
        required=True,
    )

    role = forms.ChoiceField(
        choices=employee_role,
        required=True,
    )

    employee_id = forms.CharField(
        max_length=Employee.MAX_EMPLOYEE_ID_LENGTH,
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

    def clean(self):
        cleaned_data = super().clean()

        role = cleaned_data.get("role")
        company = self.request.user.get_company

        company_departments = company.get_all_company_departments()

        if company_departments and (role == "Staff" or role == "Team Leader"):
            if not cleaned_data.get("department"):
                self.add_error("department", "Please select a department for Employee role")

        if role == "Manager" and company_departments:
            if not cleaned_data.get("manages_departments") and not cleaned_data.get("department"):
                self.add_error("department",
                               "Please select a 'department' or 'manages departments' for Manager role")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if not self.request:
            raise forms.ValidationError("You must be authenticated to register employees.")

        user = self.request.user

        company = user.get_company

        if not company:
            raise forms.ValidationError("You must be associated with a company to register employees")

        company_with_related_data = Company.objects.select_related(
            'user'
        ).prefetch_related(
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

        self._adjust_role_choices(user)

    def _adjust_role_choices(self, user):

        employee_role = Employee.get_all_employee_roles()
        role_choices = []

        for role in employee_role:
            if user.has_perm(f'accounts.add_{role.lower().replace(" ", "_")}'):
                role_choices.append((role, role))

        self.fields['role'].choices = role_choices

    def save(self, commit=True):
        company = self.request.user.get_company
        user = UserModel.objects.create_user(
            email=self.cleaned_data["email"],
            # todo UserModel.objects.make_random_password(), is_active=False
            password="ilich3",
            is_active=True,
        )

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

        employee = Employee.objects.create(**common_data)

        if commit:
            employee.save()
            if employee.role == "Manager" and self.cleaned_data["manages_departments"]:
                employee.manages_departments.set(self.cleaned_data["manages_departments"])
            # TODO Send Email
            #
            # # Send email to user with link to reset password and login
            # reset_password_url = self.request.build_absolute_uri(
            #     reverse('password_reset')  # Assuming you have a named URL for password reset
            # )
            # send_mail(
            #     'Welcome to the Company',
            #     f'Please reset your password using the following link: {reset_password_url}',
            #     'from@example.com',
            #     [user.email],
            #     fail_silently=False,
            # )

        return user


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
        model = Employee
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
        model = Employee

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_readonly_on_fields()


class DetailedEditEmployeesBaseForm(EditEmployeeBaseForm):

    class Meta(EditEmployeeBaseForm.Meta):
        model = Employee


# TODO only company can edit company name and company email
class EditCompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "company_name",
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


class BasicEditEmployeeForm(BasicEditEmployeesBaseForm):
    class Meta(BasicEditEmployeesBaseForm.Meta):
        model = Employee


class DetailedEditEmployeeForm(DetailedEditEmployeesBaseForm):
    class Meta(DetailedEditEmployeesBaseForm.Meta):
        model = Employee


class DeleteUserForm(forms.Form):
    pass


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.user.is_active:
            raise forms.ValidationError("This account is already active.")
