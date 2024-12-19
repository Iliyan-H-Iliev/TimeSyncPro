from django.conf import settings

from django.db import models
from django.core.validators import MinLengthValidator
from django.db.models import Q
from django.utils.text import slugify
import pytz

from TimeSyncPro.accounts.models import Profile

from TimeSyncPro.common.model_mixins import CreatedModifiedMixin, EmailFormatingMixin
from TimeSyncPro.history.model_mixins import HistoryMixin


class Company(HistoryMixin, EmailFormatingMixin, CreatedModifiedMixin):
    MAX_COMPANY_NAME_LENGTH = 50
    MIN_COMPANY_NAME_LENGTH = 3
    DEFAULT_LEAVE_DAYS_PER_YEAR = 0
    DEFAULT_TRANSFERABLE_LEAVE_DAYS = 0
    RANDOM_STRING_LENGTH = 10
    MAX_LEAVE_DAYS_PER_REQUEST = 30
    MIN_LEAVE_NOTICE = 0
    MAX_TIMEZONE_LENGTH = 50
    MAX_SLUG_LENGTH = 100

    tracked_fields = [
        "name",
        "email",
        "address",
        "holiday_approver",
        "location",
        "time_zone",
        "holiday_days_per_year",
        "transferable_holiday_days",
        "minimum_holiday_notice",
        "maximum_holiday_days_per_request",
        "working_on_local_holidays",
    ]

    name = models.CharField(
        max_length=MAX_COMPANY_NAME_LENGTH,
        validators=[MinLengthValidator(MIN_COMPANY_NAME_LENGTH)],
        unique=True,
        null=False,
        blank=False,
    )

    email = models.EmailField(
        blank=True,
        null=True,
    )

    address = models.OneToOneField(
        "common.Address",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="company",
    )

    holiday_approver = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="companies",
    )

    time_zone = models.CharField(
        max_length=MAX_TIMEZONE_LENGTH,
        choices=[(tz, tz) for tz in pytz.all_timezones],
        default="UTC",
        blank=False,
        null=False,
    )

    annual_leave = models.PositiveSmallIntegerField(
        null=False,
        blank=False,
    )

    max_carryover_leave = models.PositiveSmallIntegerField(
        default=DEFAULT_TRANSFERABLE_LEAVE_DAYS,
        null=False,
        blank=False,
    )

    minimum_leave_notice = models.PositiveSmallIntegerField(
        default=MIN_LEAVE_NOTICE,
        null=False,
        blank=False,
    )

    maximum_leave_days_per_request = models.PositiveSmallIntegerField(
        default=MAX_LEAVE_DAYS_PER_REQUEST,
        null=False,
        blank=False,
    )

    working_on_local_holidays = models.BooleanField(
        default=False,
        null=False,
        blank=False,
    )

    slug = models.SlugField(
        max_length=MAX_SLUG_LENGTH,
        unique=True,
        null=False,
        blank=True,
        editable=False,
    )

    def suggest_time_zone(self):
        if self.address:
            if self.address.country:
                country_timezones = pytz.country_timezones.get(
                    self.address.country.code
                )[0]
                if country_timezones:
                    return country_timezones
        return "UTC"

    def save(self, *args, **kwargs):
        self.time_zone = self.suggest_time_zone()

        if not self.slug:
            slug = self.slug_generator(self.name, self.MAX_SLUG_LENGTH)
            if Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                raise ValueError("Company with this name already exists")
            self.slug = slug

        if self.email:
            self.email = self.format_email(self.email)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.__class__.__name__} - {self.name}"

    @staticmethod
    def slug_generator(name, max_length):
        return slugify(name)[:max_length]

    @property
    def country_code(self):
        if self.address.country.code:
            return self.address.country.code
        return getattr(settings, "DEFAULT_COUNTRY_CODE", "GB")

    def get_company_holiday_approvers(self):
        return (
            Profile.objects.filter(company=self)
            .select_related("user")
            .prefetch_related(
                "user__user_permissions", "user__groups", "user__groups__permissions"
            )
            .filter(
                Q(user__user_permissions__codename="update_holiday_requests_status")
                | Q(
                    user__groups__permissions__codename="update_holiday_requests_status"
                ) | Q(user__user_permissions__codename="approve_holiday_requests")
                | Q(user__groups__permissions__codename="approve_holiday_requests")
            )
            .distinct()
        )
