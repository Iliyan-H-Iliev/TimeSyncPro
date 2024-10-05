from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class BaseValidator:
    default_message = ""

    def __init__(self, message=None):
        self._message = message

    @property
    def message(self):
        return self._message or self.default_message

    @message.setter
    def message(self, value=None):
        self._message = value

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.message == other.message

    def __repr__(self):
        return f"{self.__class__.__name__}(message={self.message!r})"


@deconstructible
class IsDigitsValidator(BaseValidator):

    default_message = _("Must contain only digits.")

    def __call__(self, value):
        if not value.isdigit():
            raise ValidationError(self.message, code='invalid_digits')


@deconstructible
class DateRangeValidator(BaseValidator):

    YEARS_AGO = 100

    def __init__(self, start_date=None, end_date=None, message=None):
        super().__init__(message)
        self.start_date = start_date or (timezone.now().date() - relativedelta(years=self.YEARS_AGO))
        self.end_date = end_date or timezone.now().date()

        if self.start_date > self.end_date:
            raise ValueError("Start date cannot be after End date")

    @property
    def default_message(self):
        return _("Not a valid date. Must be between {start_date} and {end_date}.").format(
            start_date=self.start_date.strftime('%m/%d/%Y'),
            end_date=self.end_date.strftime('%m/%d/%Y'),
        )

    def __call__(self, value: date):
        if value < self.start_date or value > self.end_date:
            raise ValidationError(self.message, code='date_out_of_range')

    def __eq__(self, other):
        return (
            super().__eq__(other) and
            self.start_date == other.start_date and
            self.end_date == other.end_date
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"start_date={self.start_date!r}, "
            f"end_date={self.end_date!r}, "
            f"message={self.message!r})"
        )


@deconstructible
class DateOfBirthValidator(BaseValidator):

    MIN_AGE = 18
    MAX_AGE = 80

    def __init__(self,min_age=None,max_age=None,message=None):
        super().__init__(message)
        self.min_age = min_age or self.MIN_AGE
        self.max_age = max_age or self.MAX_AGE

    def _get_valid_date_range(self):
        now = timezone.now().date()
        max_valid_date = now - relativedelta(years=self.min_age)
        min_valid_date = now - relativedelta(years=self.max_age)
        return min_valid_date, max_valid_date

    @property
    def default_message(self):
        min_valid_date, max_valid_date = self._get_valid_date_range()
        return _("Not a valid date. Must be between {min_date} and {max_date}.").format(
            min_date=min_valid_date.strftime('%m/%d/%Y'),
            max_date=max_valid_date.strftime('%m/%d/%Y'),
        )

    def __call__(self, value):
        min_valid_date, max_valid_date = self._get_valid_date_range()
        if value < min_valid_date or value > max_valid_date:
            raise ValidationError(self.message, code='invalid_dob')

    def __eq__(self, other):
        return (
            super().__eq__(other) and
            self.min_age == other.min_age and
            self.max_age == other.max_age
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"min_age={self.min_age!r}, "
            f"max_age={self.max_age!r}, "
            f"message={self.message!r})"
        )
