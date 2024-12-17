# Generated by Django 5.0.7 on 2024-11-03 20:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_remove_profile_days_off_left_and_more"),
        ("companies", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="company",
            name="location",
        ),
        migrations.AlterField(
            model_name="company",
            name="holiday_approver",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="companies",
                to="accounts.profile",
            ),
        ),
    ]
