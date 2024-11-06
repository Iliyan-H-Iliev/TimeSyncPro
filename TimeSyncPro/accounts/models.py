from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.core.validators import MinLengthValidator
from django.db import models, transaction
from django.utils.crypto import get_random_string
from django.utils.text import slugify
import uuid
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import models as auth_models

from django.utils import timezone


from .managers import TSPUserManager

# from .proxy_models import ManagerProxy, HRProxy, TeamLeaderProxy, StaffProxy

from .validators import IsDigitsValidator, DateRangeValidator, DateOfBirthValidator

from TimeSyncPro.common.model_mixins import CreatedModifiedMixin, EmailFormatingMixin
from ..history.model_mixins import HistoryMixin


class TSPUser(HistoryMixin, EmailFormatingMixin, auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    MAX_SLUG_LENGTH = 100

    tracked_fields = ['email', 'is_active']

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="users",
        related_query_name="user",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="users",
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

    slug = models.SlugField(
        max_length=MAX_SLUG_LENGTH,
        unique=True,
        null=False,
        blank=True,
        editable=True,
    )

    activation_token = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['slug']),
        ]

        permissions = [
            ("activate_user", "Can activate user"),
            ("deactivate_user", "Can deactivate user"),
            ("reset_user_password", "Can reset password"),
        ]

    def _get_unique_slug(self, base_slug):
        """Get a unique slug by adding numeric suffix if needed."""
        slug = base_slug
        attempts = 0
        max_attempts = 10

        while TSPUser.objects.filter(slug=slug).exclude(id=self.id).exists():
            attempts += 1
            if attempts >= max_attempts:
                raise ValueError("Unable to generate unique slug after multiple attempts")
            slug = f"{base_slug}-{attempts}"

        return slug

    def _have_fields_changed(self, first_name, last_name, employee_id):
        """Check if any of the slug-related fields have changed."""
        if not hasattr(self, 'profile'):
            return True

        current_profile = Profile.objects.filter(id=self.profile.id).values(
            'first_name', 'last_name', 'employee_id'
        ).first()

        fname = current_profile['first_name']
        lname = current_profile['last_name']
        emp_id = current_profile['employee_id']

        return any([
            first_name is not None and first_name != current_profile['first_name'],
            last_name is not None and last_name != current_profile['last_name'],
            employee_id is not None and employee_id != current_profile['employee_id']
        ])

    def save(self, *args, first_name=None, last_name=None, employee_id=None, **kwargs):
        """Save method with intelligent slug generation."""
        if self._have_fields_changed(first_name, last_name, employee_id):
            base_slug = self._generate_slug(first_name, last_name, employee_id)
            self.slug = self._get_unique_slug(base_slug)

        if self.email:
            self.email = self.format_email(self.email)

        super().save(*args, **kwargs)

    # def save(self, *args, first_name=None, last_name=None, employee_id=None, **kwargs):
    #
    #     should_generate_slug = True
    #
    #     if hasattr(self, 'profile') and self.slug:
    #
    #         if (first_name is not None and first_name == self.profile.first_name) or \
    #                 (last_name is not None and last_name == self.profile.last_name) or \
    #                 (employee_id is not None and employee_id == self.profile.employee_id):
    #             should_generate_slug = False
    #
    #     if should_generate_slug:
    #
    #         slug = self._generate_slug(first_name, last_name, employee_id)
    #         max_attempts = 10
    #         attempts = 0
    #
    #         while TSPUser.objects.filter(slug=slug).exclude(id=self.id).exists():
    #             attempts += 1
    #             if attempts >= max_attempts:
    #                 raise ValueError("Unable to generate unique slug after multiple attempts")
    #
    #             slug = self._generate_slug(first_name, last_name, employee_id, is_existing=True)
    #
    #         self.slug = slug
    #
    #     if self.email:
    #         self.email = self.format_email(self.email)
    #     super().save(*args, **kwargs)

    def generate_activation_token(self, save=True):
        self.activation_token = get_random_string(64)
        if save:
            self.save(update_fields=['activation_token'])
        return self.activation_token

    def __str__(self):
        return f"{self.__class__.__name__} - {self.email}"

    def _generate_slug(self, first_name=None, last_name=None, employee_id=None, is_existing=False):

        slug_components = []

        employee_id = self._get_employee_id(employee_id, is_existing)

        for param in [first_name, last_name, employee_id]:
            if param is not None:
                slug_components.append(str(param))

        slug = slugify(" ".join(slug_components))[:self.MAX_SLUG_LENGTH]

        return slug

    @staticmethod
    def _get_employee_id(staff_id=None, existing=False):

        if existing and staff_id:
            return f"{str(staff_id)}{uuid.uuid4().hex[:2]}"

        if not staff_id:
            return uuid.uuid4().hex[:10]

        return str(staff_id)

    @property
    def company(self):
        return self.profile.company if hasattr(self, 'profile') else None

    @property
    def is_company_admin(self):
        return self.profile.is_company_admin if hasattr(self, 'profile') else False

    def __str__(self):
        return f"{self.__class__.__name__} - {self.email}"

    USERNAME_FIELD = "email"

    objects = TSPUserManager()


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
        STAFF = 'Staff', 'Staff'
        TEAM_LEADER = 'Team Leader', 'Team Leader'
        MANAGER = 'Manager', 'Manager'
        HR = 'HR', 'HR'
        # ADMINISTRATOR = 'Administrator', 'Administrator'

    # objects = EmployeeManager()

    tracked_fields = [
        'first_name',
        'last_name',
        'employee_id',
        'role',
        'date_of_hire',
        'days_off_left',
        'phone_number',
        'address',
        'date_of_birth',
        'department',
        'manage_department',
        'shift_pattern',
        'team',
    ]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['employee_id', 'company'],
                name='unique_employee_id_per_company'
            )]

        permissions = [
            ('add_company_admin', 'Can add Company Administrator'),
            ('change_company_admin', 'Can change Company Administrator'),
            ('delete_company_admin', 'Can delete Company Administrator'),
            ('view_company_admin', 'Can view Company Administrator'),
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
        blank=False,
        null=False,
    )

    is_company_admin = models.BooleanField(
        default=False,
        blank=True,
        null=True,
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
        blank=True,
        null=True,
    )

    role = models.CharField(
        max_length=max([len(choice) for choice in EmployeeRoles.values]),
        choices=EmployeeRoles.choices,
        default=EmployeeRoles.STAFF,
        blank=False,
        null=False,
    )

    date_of_hire = models.DateField(
        validators=[
            DateRangeValidator,
        ],
        blank=True,
        null=True,
    )

    remaining_holiday_days = models.PositiveSmallIntegerField(
        blank=False,
        null=False,
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
        'common.Address',
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
        upload_to='profile_pictures/',
        blank=True,
        null=True,
    )

    # For Employee, TeamLeader and Manager
    department = models.ForeignKey(
        "companies.Department",
        on_delete=models.SET_NULL,
        related_name="employees",
        blank=True,
        null=True,
    )

    manages_departments = models.ManyToManyField(
        "companies.Department",
        related_name="managers",
        blank=True,
    )

    shift_pattern = models.ForeignKey(
        "companies.ShiftPattern",
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

    def get_role_specific_instance(self):
        if self.is_company_admin:
            AdministratorProxy = apps.get_model('accounts', 'AdministratorProxy')
            return AdministratorProxy.objects.get(id=self.id)
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

    @property
    def group_name(self):
        if self.is_company_admin:
            return 'Company_Admin'
        return self.role

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_employee_needed_permission_codename(self, action):
        return f'{action}_{self.role.lower().replace(" ", "_")}'

    def __str__(self):
        return f"{self.full_name} - {self.role}"

    def save(self, *args, **kwargs):

        self.first_name = self.format_name(self.first_name)
        self.last_name = self.format_name(self.last_name)

        super().save(*args, **kwargs)

    @staticmethod
    def format_name(name):

        if not name:
            return ""

        name = " ".join(name.split())

        return name.title()



