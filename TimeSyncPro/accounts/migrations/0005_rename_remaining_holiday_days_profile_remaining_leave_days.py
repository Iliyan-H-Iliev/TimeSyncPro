# Generated by Django 5.0.7 on 2024-11-08 23:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_rename_manage_department_profile_manages_departments"),
    ]

    operations = [
        migrations.RenameField(
            model_name="profile",
            old_name="remaining_holiday_days",
            new_name="remaining_leave_days",
        ),
    ]
