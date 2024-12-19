import holidays
from django.db import models


class Date(models.Model):
    date = models.DateField(
        unique=True,
        blank=False,
        null=False,
    )

    class Meta:
        indexes = [
            models.Index(fields=["date"]),
        ]

    def is_holiday(self, company):
        try:
            country_code = company.country_code

            country_holidays = holidays.country_holidays(country_code)

            return self.date in country_holidays

        except (AttributeError, KeyError, ValueError) as e:
            return False

    def is_working_day(self, shift):
        return self.shift_blocks.filter(pattern=shift).exists()
