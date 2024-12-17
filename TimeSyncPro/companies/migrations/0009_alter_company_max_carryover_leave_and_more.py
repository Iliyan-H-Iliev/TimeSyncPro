# Generated by Django 5.0.7 on 2024-12-15 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0008_remove_team_department"),
    ]

    operations = [
        migrations.AlterField(
            model_name="company",
            name="max_carryover_leave",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="company",
            name="maximum_leave_days_per_request",
            field=models.PositiveSmallIntegerField(default=30),
        ),
        migrations.AlterField(
            model_name="company",
            name="minimum_leave_notice",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
