# Generated by Django 5.0.7 on 2024-09-29 20:31

import TimeSyncPro.accounts.validators
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_delete_employee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True, validators=[TimeSyncPro.accounts.validators.DateOfBirthValidator]),
        ),
        migrations.AlterField(
            model_name='profile',
            name='days_off_left',
            field=models.PositiveSmallIntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='phone_number',
            field=models.CharField(blank=True, max_length=15, null=True, validators=[django.core.validators.MinLengthValidator(10), TimeSyncPro.accounts.validators.IsDigitsValidator('Phone number must contain only digits')]),
        ),
    ]
