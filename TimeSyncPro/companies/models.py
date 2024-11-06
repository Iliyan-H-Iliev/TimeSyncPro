from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.core.validators import MinValueValidator, MinLengthValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
from django_countries.fields import CountryField
import pytz

from TimeSyncPro.accounts.models import Profile
from datetime import timedelta

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
        'name',
        'email',
        'address',
        'holiday_approver',
        'location',
        'time_zone',
        'holiday_days_per_year',
        'transferable_holiday_days',
        'minimum_holiday_notice',
        'maximum_holiday_days_per_request',
        'working_on_local_holidays',
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
        related_name='company',
    )

    holiday_approver = models.ForeignKey(
        'accounts.Profile',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='companies',
    )

    time_zone = models.CharField(
        max_length=MAX_TIMEZONE_LENGTH,
        choices=[(tz, tz) for tz in pytz.all_timezones],
        default='UTC',
        blank=False,
        null=False,
    )

    holiday_days_per_year = models.PositiveSmallIntegerField(
        null=False,
        blank=False,
    )

    transferable_holiday_days = models.PositiveSmallIntegerField(
        # default=DEFAULT_TRANSFERABLE_LEAVE_DAYS,
        null=False,
        blank=False,
    )

    minimum_holiday_notice = models.PositiveSmallIntegerField(
        # default=MIN_LEAVE_NOTICE,
        null=False,
        blank=False,
    )

    maximum_holiday_days_per_request = models.PositiveSmallIntegerField(
        # default=MAX_LEAVE_DAYS_PER_REQUEST,
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
                country_timezones = pytz.country_timezones.get(self.address.country.code)[0]
                if country_timezones:
                    return country_timezones  # Return the first timezone for the country
        return 'UTC'

    # TODO Check ii works correctly
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

    # # TODO FIX IT
    # def get_all_company_members(self):
    #     return Employee.objects.filter(company=self)
    #
    # def get_all_company_departments(self):
    #     return apps.get_model('management', 'Department').objects.filter(company=self)
    #
    # def get_all_company_teams(self):
    #     return apps.get_model('management', 'Team').objects.filter(company=self)
    #
    # def get_all_company_shift_patterns(self):
    #     return apps.get_model('management', 'ShiftPattern').objects.filter(company=self)

    # def get_group_name(self):
    #     return 'Company'

    def __str__(self):
        return f"{self.__class__.__name__} - {self.name}"

    @staticmethod
    def slug_generator(name, max_length):
        return slugify(name)[:max_length]


class Department(HistoryMixin, models.Model):
    MAX_DEPARTMENT_NAME_LENGTH = 50
    MIN_DEPARTMENT_NAME_LENGTH = 3

    tracked_fields = ['name', 'holiday_approver']

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='departments',
        blank=False,
        null=False,
    )

    name = models.CharField(
        max_length=MAX_DEPARTMENT_NAME_LENGTH,
        validators=[MinLengthValidator(MIN_DEPARTMENT_NAME_LENGTH)],
        blank=False,
        null=False,
    )

    holiday_approver = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='departments',
    )

    class Meta:
        unique_together = ('company', 'name')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class ShiftPattern(HistoryMixin, models.Model):
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 50
    MIN_ROTATION_WEEKS = 1
    MAX_ROTATION_WEEKS = 52

    tracked_fields = ['name', 'description', 'start_date', 'rotation_weeks']

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='shift_patterns',
        blank=False,
        null=False,
    )

    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        validators=[MinLengthValidator(MIN_NAME_LENGTH)],
        blank=False,
        null=False,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    start_date = models.DateField(
        default=timezone.now,
        blank=False,
        null=False,
    )

    rotation_weeks = models.IntegerField(
        default=MIN_ROTATION_WEEKS,
        validators=[
            MinValueValidator(MIN_ROTATION_WEEKS),
            MaxValueValidator(MAX_ROTATION_WEEKS),
        ],
        blank=False,
        null=False,
    )

    def generate_shift_working_dates(self):
        # end_date = date(date.today().year + 1, 12, 31)
        current_date = self.start_date
        end_date = current_date + timedelta(days=30)

        blocks = self.blocks.all().filter(pattern=self).order_by('order')

        for block in blocks:
            block.working_dates.clear()

        while current_date <= end_date:
            for block in blocks:
                for day in block.on_off_days:
                    if current_date > end_date:
                        break
                    if day == 1:  # Only create assignments for working days
                        date_obj, created = Date.objects.get_or_create(date=current_date)
                        block.working_dates.add(date_obj)
                    current_date += timedelta(days=1)

    class Meta:
        unique_together = ('company', 'name')

    def get_current_block(self):
        current_date = timezone.now().date()
        for block in self.blocks.all():
            if current_date in block.working_dates.all():
                return block
        return None

    def __str__(self):
        return f"{self.name}"


class ShiftBlock(HistoryMixin, models.Model):
    MIN_DAYS_ON = 1
    MAX_DAYS_ON = 28
    MIN_DAYS_OFF = 1
    MAX_DAYS_OFF = 28

    tracked_fields = [
        "on_off_days",
        "selected_days",
        "days_on",
        "days_off",
        "start_time",
        "end_time",
        "duration",
        "order",
        "working_dates",
    ]

    pattern = models.ForeignKey(
        ShiftPattern,
        on_delete=models.CASCADE,
        related_name='blocks'
    )

    on_off_days = ArrayField(
        models.IntegerField(),
        size=60,
        blank=False,
        null=False,
    )

    selected_days = ArrayField(
        models.IntegerField(),
        size=7,
        blank=True,
        null=True,
    )

    days_on = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_DAYS_ON), MaxValueValidator(MAX_DAYS_ON)],
        blank=True,
        null=True,
    )

    days_off = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_DAYS_OFF), MaxValueValidator(MAX_DAYS_OFF)],
        blank=True,
        null=True,
    )

    start_time = models.TimeField(
        blank=False,
        null=False,
    )

    end_time = models.TimeField(
        blank=False,
        null=False,
    )

    duration = models.DurationField(
        blank=True,
        null=True,
    )

    order = models.PositiveIntegerField(
        blank=False,
        null=False,
    )

    working_dates = models.ManyToManyField(
        'Date',
        related_name='shift_blocks',
        blank=True,
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.pattern.name} - block {self.order}"

    def save(self, *args, **kwargs):

        if not self.duration:
            # Calculate duration if not provided
            start_datetime = timezone.make_aware(timezone.datetime.combine(timezone.now().date(), self.start_time))
            end_datetime = timezone.make_aware(timezone.datetime.combine(timezone.now().date(), self.end_time))
            if end_datetime <= start_datetime:
                end_datetime += timezone.timedelta(days=1)
            self.duration = end_datetime - start_datetime

        super().save(*args, **kwargs)


class Team(HistoryMixin, models.Model):
    MAX_TEAM_NAME_LENGTH = 50
    MIN_TEAM_NAME_LENGTH = 3
    DEFAULT_EMPLOYEES_HOLIDAYS_AT_A_TIME = 99
    MIN_EMPLOYEES_HOLIDAYS_AT_A_TIME = 1
    MAX_EMPLOYEES_HOLIDAYS_AT_A_TIME = 99

    tracked_fields = [
        "name",
        "shift_pattern",
        "holiday_approver",
        "department",
        "employees_holidays_at_a_time",
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='teams',
        null=False,
        blank=False,
    )

    name = models.CharField(
        max_length=MAX_TEAM_NAME_LENGTH,
        validators=[MinLengthValidator(MIN_TEAM_NAME_LENGTH)],
        blank=False,
        null=False,
    )

    shift_pattern = models.ForeignKey(
        ShiftPattern,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='teams',
    )
    
    holiday_approver = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='teams',
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='teams',
    )

    employees_holidays_at_a_time = models.PositiveIntegerField(
        default=DEFAULT_EMPLOYEES_HOLIDAYS_AT_A_TIME,
        validators=[
            MinValueValidator(MIN_EMPLOYEES_HOLIDAYS_AT_A_TIME),
            MaxValueValidator(MAX_EMPLOYEES_HOLIDAYS_AT_A_TIME),
        ],
        blank=False,
        null=False,
    )

    class Meta:
        unique_together = ('company', "department", 'name')

    def get_team_members(self):
        return self.employees.all()

    def get_team_leaders(self):
        return self.employees.filter(role=Profile.EmployeeRoles.TEAM_LEADER)

    def __str__(self):
        return self.name


class Date(models.Model):
    date = models.DateField(
        unique=True,
        blank=False,
        null=False,
    )

    class Meta:
        indexes = [
            models.Index(fields=['date']),
        ]

    def is_holiday(self, company):
        #TODO Implement holiday check logic
        pass

    def is_working_day(self, shift_pattern):
        return self.shift_blocks.filter(pattern=shift_pattern).exists()


# class ShiftAssignment(models.Model):
#     date = models.DateField()
#     shift_block = models.ForeignKey(ShiftBlock, on_delete=models.CASCADE, related_name='assignments')
#
#     class Meta:
#         # TODO make it unique for many companies
#         unique_together = ('date', 'shift_block',)
#
#     def __str__(self):
#         return f"{self.shift_block.pattern.name} - {self.date}"


