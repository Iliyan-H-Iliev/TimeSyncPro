import datetime
from datetime import timedelta, date

from django.apps import apps
from django.core.validators import MinLengthValidator
from django.db import models

from . import TSPUser
# from .proxy_models import ManagerProxy, HRProxy, TeamLeaderProxy, StaffProxy

from ..validators import IsDigitsValidator, DateRangeValidator, DateOfBirthValidator

from TimeSyncPro.common.model_mixins import CreatedModifiedMixin
from ...history.model_mixins import HistoryMixin


class Profile(HistoryMixin, CreatedModifiedMixin):
    MAX_FIRST_NAME_LENGTH = 30
    MIN_FIRST_NAME_LENGTH = 2
    MAX_LAST_NAME_LENGTH = 30
    MIN_LAST_NAME_LENGTH = 2
    MAX_EMPLOYEE_ID_LENGTH = 15
    MIN_EMPLOYEE_ID_LENGTH = 5
    MAX_PHONE_NUMBER_LENGTH = 15
    MIN_PHONE_NUMBER_LENGTH = 10
    MIN_AGE = 16

    class EmployeeRoles(models.TextChoices):
        STAFF = "Staff", "Staff"
        TEAM_LEADER = "Team Leader", "Team Leader"
        MANAGER = "Manager", "Manager"
        HR = "HR", "HR"
        # ADMINISTRATOR = "Administrator", "Administrator"

    # objects = EmployeeManager()

    tracked_fields = [
        "first_name",
        "last_name",
        "employee_id",
        "role",
        "date_of_hire",
        "days_off_left",
        "phone_number",
        "address",
        "date_of_birth",
        "department",
        "manage_department",
        "shift",
        "team",
    ]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["employee_id", "company"],
                name="unique_employee_id_per_company"
            )]

        permissions = [
            ("add_company_admin", "Can add Company Administrator"),
            ("change_company_admin", "Can change Company Administrator"),
            ("delete_company_admin", "Can delete Company Administrator"),
            ("view_company_admin", "Can view Company Administrator"),
            ("add_hr", "Can add HR"),
            ("change_hr", "Can change HR"),
            ("delete_hr", "Can delete HR"),
            ("view_hr", "Can view HR"),
            ("add_manager", "Can add Manager"),
            ("change_manager", "Can change Manager"),
            ("delete_manager", "Can delete Manager"),
            ("view_manager", "Can view Manager"),
            ("add_team_leader", "Can add TeamLeader"),
            ("change_team_leader", "Can change TeamLeader"),
            ("delete_team_leader", "Can delete TeamLeader"),
            ("view_team_leader", "Can view TeamLeader"),
            ("add_staff", "Can add Staff"),
            ("change_staff", "Can change Staff"),
            ("delete_staff", "Can delete Staff"),
            ("view_staff", "Can view Staff"),
            ("view_employee", "Can view Employees"),
            ("add_employee", "Can add Employees"),
            ("view_all_employees", "Can view all Employees"),
            ("view_department_employees", "Can view department Employees"),
            ("view_team_employees", "Can view team Employees"),



        ]

    user = models.OneToOneField(
        TSPUser,
        on_delete=models.CASCADE,
        related_name="profile",
        blank=False,
        null=False,
    )

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.DO_NOTHING,
        related_name="employees",
        blank=True,
        null=True,
    )

    is_company_admin = models.BooleanField(
        default=False,
        blank=True,
        null=False,
    )

    first_name = models.CharField(
        max_length=MAX_FIRST_NAME_LENGTH,
        validators=[MinLengthValidator(MIN_FIRST_NAME_LENGTH)],
        blank=True,
        null=True,
    )

    last_name = models.CharField(
        max_length=MAX_LAST_NAME_LENGTH,
        validators=[MinLengthValidator(MIN_LAST_NAME_LENGTH)],
        blank=True,
        null=True,
    )

    role = models.CharField(
        max_length=max([len(choice) for choice in EmployeeRoles.values]),
        choices=EmployeeRoles.choices,
        # default=EmployeeRoles.STAFF,
        blank=True,
        null=True,
    )

    employee_id = models.CharField(
        max_length=MAX_EMPLOYEE_ID_LENGTH,
        validators=[MinLengthValidator(MIN_EMPLOYEE_ID_LENGTH)],
        blank=True,
        null=True,
    )

    date_of_hire = models.DateField(
        validators=[
            DateRangeValidator,
        ],
        blank=True,
        null=True,
    )

    remaining_leave_days = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
    )

    phone_number = models.CharField(
        max_length=MAX_PHONE_NUMBER_LENGTH,
        validators=[
            MinLengthValidator(MIN_PHONE_NUMBER_LENGTH),
            IsDigitsValidator("Phone number must contain only digits"),
        ],
        blank=True,
        null=True)

    address = models.OneToOneField(
        "common.Address",
        on_delete=models.SET_NULL,
        related_name="employee",
        blank=True,
        null=True,
    )

    date_of_birth = models.DateField(
        validators=[
            DateOfBirthValidator,
        ],
        blank=True,
        null=True,
    )

    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True,
    )

    department = models.ForeignKey(
        "companies.Department",
        on_delete=models.SET_NULL,
        related_name="employees",
        blank=True,
        null=True,
    )

    shift = models.ForeignKey(
        "companies.Shift",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )

    team = models.ForeignKey(
        "companies.Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )

    @classmethod
    def get_all_employee_roles(cls):
        employee_role = [role.value for role in cls.EmployeeRoles]
        return employee_role

    # def get_role_specific_instance(self):
    #     if self.is_company_admin:
    #         AdministratorProxy = apps.get_model("accounts", "AdministratorProxy")
    #         return AdministratorProxy.objects.get(id=self.id)
    #     if self.role == "Manager":
    #         ManagerProxy = apps.get_model("accounts", "ManagerProxy")
    #         return ManagerProxy.objects.get(id=self.id)
    #     elif self.role == "HR":
    #         HRProxy = apps.get_model("accounts", "HRProxy")
    #         return HRProxy.objects.get(id=self.id)
    #     elif self.role == "Team Leader":
    #         TeamLeaderProxy = apps.get_model("accounts", "TeamLeaderProxy")
    #         return TeamLeaderProxy.objects.get(id=self.id)
    #     elif self.role == "Staff":
    #         StaffProxy = apps.get_model("accounts", "StaffProxy")
    #         return StaffProxy.objects.get(id=self.id)
    #     return self

    @property
    def group_name(self):
        if self.is_company_admin:
            return "Company_Admin"
        return self.role

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_employee_needed_permission_codename(self, action):
        return f"{action}_{self.role.lower().replace(' ', '_')}"

    def __str__(self):
        return f"{self.full_name} - {self.role}"

    def save(self, *args, **kwargs):

        if self.first_name:
            self.first_name = self.format_name(self.first_name)
        if self.last_name:
            self.last_name = self.format_name(self.last_name)

        is_new = not self.pk

        if is_new and not self.user_id:
            super().save(*args, **kwargs, skip_history=True)
            # Then create history if we have a user
            # if self.user_id:
            #     self._create_history("create", {
            #         "user": {"old": None, "new": self.user_id}
            #     })
        else:
            super().save(*args, **kwargs)

    @staticmethod
    def format_name(name):

        if not name:
            return ""

        name = " ".join(name.split())

        return name.title()

    def get_holiday_approver(self):
        if self.team and self.team.holiday_approver:
            return self.team.holiday_approver
        elif self.department and self.department.holiday_approver:
            return self.department.holiday_approver
        return self.company.holiday_approver

    def get_shift(self):
        if self.shift:
            return self.shift
        elif self.team and self.team.shift:
            return self.team.shift

    def get_team(self):
        if self.team:
            return self.team
        return None

    def get_working_days(self, start_date, end_date):
        shift = self.get_shift()
        if shift:
            return shift.get_shift_working_dates_by_period(start_date, end_date)

        working_days = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:
                working_days.append(current_date)
            current_date += timedelta(days=1)
        return working_days

    def get_working_days_with_time(self, start_date, end_date):
        shift = self.get_shift()
        if shift:
            return shift.get_shift_working_dates_with_time_by_period(start_date, end_date)

        working_days = {}
        start_time = datetime.time(9, 0)
        end_time = datetime.time(17, 0)

        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:
                working_days[current_date] = {"start_time": start_time, "end_time": end_time}
            current_date += timedelta(days=1)
        return working_days

    def get_days_off(self, start_date, end_date):
        working_days = self.get_working_days(start_date, end_date)
        all_days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        return [day for day in all_days if day not in working_days]

    def get_team_employees_holidays_at_a_time(self):
        if hasattr(self, 'team') and self.team:
            return self.team.employees_holidays_at_a_time
        return None

    def get_count_of_working_days_by_period(self, start_date, end_date):
        working_days = 0
        shift = self.get_shift()
        if shift:
            return shift.get_count_of_shift_working_days_by_period(start_date, end_date)

        current_date = start_date
        while current_date <= end_date:

            if current_date.weekday() < 5:
                working_days += 1
            current_date += timedelta(days=1)

        return working_days







