from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Model, Q
from django.utils.crypto import get_random_string
import uuid

from django.utils.text import slugify

from django.utils.translation import gettext_lazy as _
from django.contrib.auth import models as auth_models

from django.utils import timezone

from TimeSyncPro.core.model_mixins import CreatedModifiedMixin, EmailFormatingMixin

from .managers import TimeSyncProUserManager


# from .proxy_models import ManagerProxy, HRProxy, TeamLeaderProxy, StaffProxy

from .validators import IsDigitsValidator, DateRangeValidator, DateOfBirthValidator


class TimeSyncProUser(EmailFormatingMixin, auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
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
        editable=False,
    )

    activation_token = models.CharField(max_length=64, blank=True, null=True)

    def save(self, *args, first_name=None, last_name=None, **kwargs):

        if not self.slug:

            if first_name and last_name:
                full_name = f"{first_name} {last_name}"
            else:
                full_name = self.email.split('@')[0]

            slug = self.generate_unique_slug(full_name, self.MAX_SLUG_LENGTH)

            while TimeSyncProUser.objects.filter(slug=slug).exists():
                slug = self.generate_unique_slug(full_name, self.MAX_SLUG_LENGTH)

            self.slug = slug

        if self.email:
            self.email = self.formated_email(self.email)
        super().save(*args, **kwargs)

    def generate_activation_token(self):
        self.activation_token = get_random_string(64)
        self.save()
        return self.activation_token

    def __str__(self):
        return f"{self.__class__.__name__} - {self.email}"

    @staticmethod
    def generate_unique_slug(full_name, max_length):
        base_slug = slugify(full_name)[:max_length - 9]
        unique_slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"

        return unique_slug[:max_length]

    @property
    def company(self):
        return self.profile.company

    USERNAME_FIELD = "email"

    objects = TimeSyncProUserManager()


class Profile(CreatedModifiedMixin):
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
        ADMINISTRATOR = 'Administrator', 'Administrator'

    # objects = EmployeeManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['employee_id', 'company'],
                name='unique_employee_id_per_company'
            )]
        permissions = [
            ('add_administrator', 'Can add Administrator'),
            ('change_administrator', 'Can change Administrator'),
            ('delete_administrator', 'Can delete Administrator'),
            ('view_administrator', 'Can view Administrator'),
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
        related_name="profile",
    )

    company = models.ForeignKey(
        to='management.Company',
        on_delete=models.DO_NOTHING,
        related_name="employees",
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

    days_off_left = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        default=0,
    )

    phone_number = models.CharField(
        max_length=MAX_PHONE_NUMBER_LENGTH,
        validators=[
            MinLengthValidator(MIN_PHONE_NUMBER_LENGTH),
            IsDigitsValidator("Phone number must contain only digits"),
        ],
        blank=True,
        null=True)

    address = models.TextField(
        blank=True,
        null=True)

    date_of_birth = models.DateField(
        validators=[
            DateOfBirthValidator,
        ],
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
        related_name="employees",
        blank=True,
        null=True,
    )

    # For Manager and HR
    manages_departments = models.ManyToManyField(
        'management.Department',
        related_name="managers",

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
    def is_administrator(self):
        return self.role == 'Administrator'

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
        employee_role = [role.value for role in cls.EmployeeRoles]
        return employee_role

    def get_role_specific_instance(self):
        if self.role == 'Administrator':
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
        return self.role

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_employee_needed_permission_codename(self, action):
        return f'{action}_{self.role.lower().replace(" ", "_")}'

    def __str__(self):
        return f"{self.full_name} - {self.role}"
