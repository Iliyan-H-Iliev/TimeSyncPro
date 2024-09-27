from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta
from django.utils.deconstruct import deconstructible


def validate_date_of_hire(value):
    if value < date(1980, 1, 1) or value > timezone.now().date():
        raise ValidationError("The date of hire must be between 1st January 1980, and today.")


def validate_date_of_birth(value):
    sixteen_years_ago = timezone.now().date() - relativedelta(years=16)
    if value < date(1940, 1, 1) or value > sixteen_years_ago:
        raise ValidationError(
            f"The date of birth must be between 01/01/1940 and {sixteen_years_ago.strftime('%m/%d/%Y')}.")


@deconstructible
class IsDigitsValidator:
    def __init__(self, message=None):
        self.__message = message

    @property
    def message(self):
        return self.__message

    @message.setter
    def message(self, message):
        if message is None:
            self.__message = f"Must contain only digits."
        else:
            self.__message = message

    def __call__(self, value):
        if not value.isdigit():
            raise ValidationError(self.message)


@deconstructible
class DateValidator:
    YEARS_AGO = 100

    def __init__(self, start_date=None, end_date=None, min_age=None, message=None):
        self.start_date = start_date or (timezone.now().date() - relativedelta(years=self.YEARS_AGO))
        self.end_date = end_date or timezone.now().date()
        self.min_age = min_age
        self.__message = message

    @property
    def message(self):
        if self.__message is None:
            if self.min_age:
                max_valid_date = self.end_date - relativedelta(years=self.min_age)
                return f"Not a valid date. Must be between {self.start_date.strftime('%m/%d/%Y')} and {max_valid_date.strftime('%m/%d/%Y')}."
            return f"Not a valid date. Must be between {self.start_date.strftime('%m/%d/%Y')} and {self.end_date.strftime('%m/%d/%Y')}."
        return self.__message

    @message.setter
    def message(self, value):
        self.__message = value

    def __call__(self, value):
        # If min_age is specified, calculate the maximum valid date based on the age
        if self.min_age:
            max_valid_date = self.end_date - relativedelta(years=self.min_age)
            if value < self.start_date or value > max_valid_date:
                raise ValidationError(self.message)
        # General date validation between start_date and end_date
        elif value < self.start_date or value > self.end_date:
            raise ValidationError(self.message)

    def __eq__(self, other):
        return (
            isinstance(other, DateValidator) and
            self.start_date == other.start_date and
            self.end_date == other.end_date and
            self.min_age == other.min_age and
            self.message == other.message
        )

