from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Model, Q
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.utils import timezone
import pytz

from django.utils.translation import gettext_lazy as _
from django.contrib.auth import models as auth_models

from django.utils import timezone
from django_countries.fields import CountryField

# from .managers import LeaveOpsManagerUserManager, EmployeeManager

from .base_models import CreatedModifiedMixin
from .managers import TimeSyncProUserManager
from .mixins import AbstractSlugMixin, GroupAssignmentMixin
# from .proxy_models import ManagerProxy, HRProxy, TeamLeaderProxy, StaffProxy

from .validators import validate_date_of_hire, phone_number_validator


# from TimeSyncPro.accounts.utils import get_related_instance


class TimeSyncProUser(auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    MAX_SLUG_LENGTH = 100

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="user_set",
        related_query_name="user",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="user_set",
        related_query_name="user",
    )

    email = models.EmailField(
        _("email address"),
        unique=True,
        error_messages={
            "unique": _("A user with that email already exists."),
        },
        blank=False,
        null=False,
    )

    is_company = models.BooleanField(
        default=False,
        blank=False,
        null=False,
    )

    date_joined = models.DateTimeField(
        _("date joined"),
        default=timezone.now
    )

    is_staff = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    @property
    def related_instance(self):
        if self.is_company:
            return self.company

        return self.employee

    @property
    def slug(self):
        return self.related_instance.slug if self.related_instance else None

    @property
    def full_name(self):

        if self.is_company:
            return self.related_instance.company_name

        return self.related_instance.full_name

    @property
    def get_company(self):

        if self.is_company:
            return self.related_instance

        company = self.related_instance.company if hasattr(self.related_instance, 'company') else None
        return company

    @property
    def get_company_name(self):
        company = self.get_company

        return company.company_name if company else None

    @property
    def get_all_user_permissions(self):
        return Permission.objects.filter(
            Q(group__in=self.groups.all()) | Q(user=self)
        ).distinct()

    @property
    def user_permissions_codenames(self):
        a = self.get_all_user_permissions.values_list('codename', flat=True)
        print(a)
        return self.get_all_user_permissions.values_list('codename', flat=True)

    USERNAME_FIELD = "email"

    objects = TimeSyncProUserManager()


class Company(AbstractSlugMixin, GroupAssignmentMixin, CreatedModifiedMixin):
    MAX_COMPANY_NAME_LENGTH = 50
    MIN_COMPANY_NAME_LENGTH = 3
    DEFAULT_LEAVE_DAYS_PER_YEAR = 0
    DEFAULT_TRANSFERABLE_LEAVE_DAYS = 0
    RANDOM_STRING_LENGTH = 10
    MAX_LEAVE_DAYS_PER_REQUEST = 30
    MIN_LEAVE_NOTICE = 0
    MAX_TIMEZONE_LENGTH = 50

    company_name = models.CharField(
        max_length=MAX_COMPANY_NAME_LENGTH,
        validators=[MinLengthValidator(MIN_COMPANY_NAME_LENGTH)],
        null=False,
        blank=False,
    )

    leave_approver = models.ForeignKey(
        'accounts.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies',
    )

    location = CountryField(
        blank_label='(select country)',
        blank=True,
        null=True
    )

    time_zone = models.CharField(
        max_length=MAX_TIMEZONE_LENGTH,
        choices=[(tz, tz) for tz in pytz.all_timezones],
        default='UTC',
        blank=False,
        null=False
    )

    leave_days_per_year = models.PositiveIntegerField(
        default=DEFAULT_LEAVE_DAYS_PER_YEAR,
        null=False,
        blank=False,
    )

    transferable_leave_days = models.PositiveIntegerField(
        default=DEFAULT_TRANSFERABLE_LEAVE_DAYS,
        null=False,
        blank=False,
    )

    minimum_leave_notice = models.PositiveIntegerField(
        default=MIN_LEAVE_NOTICE,
        null=False,
        blank=False,
    )

    maximum_leave_days_per_request = models.PositiveIntegerField(
        default=MAX_LEAVE_DAYS_PER_REQUEST,
        null=False,
        blank=False,
    )

    user = models.OneToOneField(
        TimeSyncProUser,
        on_delete=models.CASCADE,
        related_name="company",
    )

    def suggest_time_zone(self):
        if self.location:
            country_timezones = pytz.country_timezones.get(self.location.code)
            if country_timezones:
                return country_timezones[0]  # Return the first timezone for the country
        return 'UTC'

    def save(self, *args, **kwargs):
        self.time_zone = self.suggest_time_zone()

    def get_slug_identifier(self):
        return slugify(f"{self.company_name}-{get_random_string(self.RANDOM_STRING_LENGTH)}")

    def get_all_company_members(self):
        return Employee.objects.filter(company=self)

    def get_all_company_departments(self):
        return apps.get_model('management', 'Department').objects.filter(company=self)

    def get_all_company_teams(self):
        return apps.get_model('management', 'Team').objects.filter(company=self)

    def get_all_company_shift_patterns(self):
        return apps.get_model('management', 'ShiftPattern').objects.filter(company=self)

    def get_group_name(self):
        return 'Company'

    def __str__(self):
        return f"{self.__class__.__name__} - {self.company_name}"


class Employee(AbstractSlugMixin, GroupAssignmentMixin, CreatedModifiedMixin, models.Model):
    MAX_FIRST_NAME_LENGTH = 30
    MIN_FIRST_NAME_LENGTH = 2
    MAX_LAST_NAME_LENGTH = 30
    MIN_LAST_NAME_LENGTH = 2
    MAX_EMPLOYEE_ID_LENGTH = 15
    MIN_EMPLOYEE_ID_LENGTH = 5
    MAX_PHONE_NUMBER_LENGTH = 15

    class EmployeeRole(models.TextChoices):
        STAFF = 'Staff', 'Staff'
        TEAM_LEADER = 'Team Leader', 'Team Leader'
        MANAGER = 'Manager', 'Manager'
        HR = 'HR', 'HR'

    # objects = EmployeeManager()

    class Meta:
        permissions = [
            ('add_hr', 'Can add HR'),
            ('change_hr', 'Can change HR'),
            ('delete_hr', 'Can delete HR'),
            ('view_hr', 'Can view HR'),
            ('add_manager', 'Can add Manager'),
            ('change_manager', 'Can change Manager'),
            ('delete_manager', 'Can delete Manager'),
            ('view_manager', 'Can view Manager'),
            ('add_team_leader', 'Can add TeamLeader'),
            ('change_team_leader', 'Can change TeamLeader'),
            ('delete_team_leader', 'Can delete TeamLeader'),
            ('view_team_leader', 'Can view TeamLeader'),
            ('add_staff', 'Can add Staff'),
            ('change_staff', 'Can change Staff'),
            ('delete_staff', 'Can delete Staff'),
            ('view_staff', 'Can view Staff'),
        ]

    user = models.OneToOneField(
        TimeSyncProUser,
        on_delete=models.CASCADE,
        related_name="employee",
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="employees",
        blank=False,
        null=False,
    )

    first_name = models.CharField(
        max_length=MAX_FIRST_NAME_LENGTH,
        validators=[MinLengthValidator(MIN_FIRST_NAME_LENGTH)],
        blank=False,
        null=False,
    )

    last_name = models.CharField(
        max_length=MAX_LAST_NAME_LENGTH,
        validators=[MinLengthValidator(MIN_LAST_NAME_LENGTH)],
        blank=False,
        null=False,
    )

    employee_id = models.CharField(
        max_length=MAX_EMPLOYEE_ID_LENGTH,
        validators=[MinLengthValidator(MIN_EMPLOYEE_ID_LENGTH)],
        unique=True,
        blank=False,
        null=False,
    )

    role = models.CharField(
        max_length=max([len(choice) for choice in EmployeeRole.values]),
        choices=EmployeeRole.choices,
        default=EmployeeRole.STAFF,
        blank=False,
        null=False,
    )

    date_of_hire = models.DateField(
        validators=[validate_date_of_hire],
        blank=False,
        null=False,
    )

    days_off_left = models.PositiveSmallIntegerField(
        blank=False,
        null=False,
    )

    phone_number = models.CharField(
        max_length=MAX_PHONE_NUMBER_LENGTH,
        validators=[phone_number_validator],
        blank=True,
        null=True)

    address = models.TextField(
        blank=True,
        null=True)

    date_of_birth = models.DateField(
        blank=True,
        null=True,
    )

    profile_picture = models.URLField(
        blank=True,
        null=True,
    )

    # For Employee and TeamLeader
    department = models.ForeignKey(
        'management.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )

    # For Manager and HR
    manages_departments = models.ManyToManyField(
        'management.Department',
        related_name="managers",
        blank=True,
    )

    shift_pattern = models.ForeignKey(
         'management.ShiftPattern',
         on_delete=models.SET_NULL,
         null=True,
         blank=True,
         related_name="employees",
     )

    team = models.ForeignKey(
         'management.Team',
         on_delete=models.SET_NULL,
         null=True,
         blank=True,
         related_name="employees",
     )

    @property
    def is_manager(self):
        return self.role == 'Manager'

    @property
    def is_hr(self):
        return self.role == 'HR'

    @property
    def is_team_leader(self):
        return self.role == 'Team Leader'

    @property
    def is_staff(self):
        return self.role == 'Staff'

    @classmethod
    def get_all_employee_roles(cls):
        employee_role = [role.value for role in cls.EmployeeRole]
        return employee_role

    def get_role_specific_instance(self):
        if self.role == 'Manager':
            ManagerProxy = apps.get_model('accounts', 'ManagerProxy')
            return ManagerProxy.objects.get(id=self.id)
        elif self.role == 'HR':
            HRProxy = apps.get_model('accounts', 'HRProxy')
            return HRProxy.objects.get(id=self.id)
        elif self.role == 'Team Leader':
            TeamLeaderProxy = apps.get_model('accounts', 'TeamLeaderProxy')
            return TeamLeaderProxy.objects.get(id=self.id)
        elif self.role == 'Staff':
            StaffProxy = apps.get_model('accounts', 'StaffProxy')
            return StaffProxy.objects.get(id=self.id)
        return self

    def get_slug_identifier(self):
        return slugify(f"{self.full_name}-{self.employee_id}")

    def get_group_name(self):
        return self.role

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return f"{self.full_name} - {self.role}"



    # def promote_to_manager(self):
    #     # Create a new Manager instance with the same attributes as the employee
    #     manager = Manager.objects.create(
    #         first_name=self.first_name,
    #         last_name=self.last_name,
    #         employee_id=self.employee_id,
    #         date_of_hire=self.date_of_hire,
    #         days_off_left=self.days_off_left,
    #         phone_number=self.phone_number,
    #         address=self.address,
    #         date_of_birth=self.date_of_birth,
    #         profile_picture=self.profile_picture,
    #         user=self.user,
    #         company=self.company,
    #     )
    #
    #     # Delete the Employee instance
    #     self.delete()
    #
    #     return manager


