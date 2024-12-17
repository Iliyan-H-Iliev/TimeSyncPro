# Generated by Django 5.0.7 on 2024-11-19 08:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_remove_profile_shift_pattern"),
        ("companies", "0007_remove_team_shift_pattern_shift_team_shift_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="shift",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="employees",
                to="companies.shift",
            ),
        ),
    ]
