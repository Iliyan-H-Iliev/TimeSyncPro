from django.db import models
from django_countries.fields import CountryField

# Create your models here.


class Address(models.Model):
    MAX_LENGTH_HOUSE_NUMBER_OR_NAME = 100
    MAX_LENGTH_LINE1 = 100
    MAX_LENGTH_LINE2 = 100
    MAX_LENGTH_STREET = 100
    MAX_LENGTH_CITY = 100
    MAX_LENGTH_POSTCODE = 20
    MAX_LENGTH_COUNTRY = 100

    house_number_or_name = models.CharField(
        max_length=MAX_LENGTH_HOUSE_NUMBER_OR_NAME,
        blank=True,
        null=True,
    )

    line1 = models.CharField(
        max_length=MAX_LENGTH_LINE1,
        blank=True,
        null=True,
    )

    line2 = models.CharField(
        max_length=MAX_LENGTH_LINE2,
        blank=True,
        null=True,
    )

    street = models.CharField(
        max_length=MAX_LENGTH_STREET,
        blank=True,
        null=True,
    )

    city = models.CharField(
        max_length=MAX_LENGTH_CITY,
        blank=True,
        null=True,
    )

    postcode = models.CharField(
        max_length=MAX_LENGTH_POSTCODE,
        blank=True,
        null=True,
    )

    country = CountryField(
        blank_label="(select country)",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.house_number_or_name}, {self.street}, {self.city}, {self.postcode}, {self.country}"
