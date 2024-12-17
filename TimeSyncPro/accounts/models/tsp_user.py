from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.text import slugify
import uuid
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import models as auth_models

from django.utils import timezone

from ..managers import TSPUserManager
from ...history.model_mixins import HistoryMixin


class TSPUser(HistoryMixin, auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    MAX_SLUG_LENGTH = 100

    tracked_fields = ["email"]

    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="users",
        related_query_name="user",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
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

    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

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

    activation_token = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["slug"]),
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
                raise ValueError(
                    "Unable to generate unique slug after multiple attempts"
                )
            slug = f"{base_slug}-{attempts}"

        return slug

    def _have_fields_changed(self, first_name, last_name, employee_id):
        if not hasattr(self, "profile"):
            return True

        Profile = apps.get_model("accounts", "Profile")
        current_profile = (
            Profile.objects.filter(id=self.profile.id)
            .values("first_name", "last_name", "employee_id")
            .first()
        )

        return any(
            [
                first_name is not None and first_name != current_profile["first_name"],
                last_name is not None and last_name != current_profile["last_name"],
                employee_id is not None
                and employee_id != current_profile["employee_id"],
            ]
        )

    def save(self, *args, first_name=None, last_name=None, employee_id=None, **kwargs):

        if self._have_fields_changed(first_name, last_name, employee_id):
            base_slug = self._generate_slug(first_name, last_name, employee_id)
            self.slug = self._get_unique_slug(base_slug)

        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)

        super().save(*args, **kwargs)

    @staticmethod
    def generate_activation_token():
        return get_random_string(64)

    def __str__(self):
        return f"{self.__class__.__name__} - {self.email}"

    def _generate_slug(
        self, first_name=None, last_name=None, employee_id=None, is_existing=False
    ):

        slug_components = []

        employee_id = self._get_employee_id(employee_id, is_existing)

        for param in [first_name, last_name, employee_id]:
            if param is not None:
                slug_components.append(str(param))

        slug = slugify(" ".join(slug_components))[: self.MAX_SLUG_LENGTH]

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
        return self.profile.company if hasattr(self, "profile") else None

    @property
    def is_company_admin(self):
        return hasattr(self, "profile") and self.profile.is_company_admin

    def __str__(self):
        return f"{self.email}"

    USERNAME_FIELD = "email"

    objects = TSPUserManager()
