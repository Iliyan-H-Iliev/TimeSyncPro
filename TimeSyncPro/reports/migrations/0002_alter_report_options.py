# Generated by Django 5.0.7 on 2024-12-15 18:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="report",
            options={
                "default_permissions": (),
                "managed": False,
                "permissions": (
                    ("generate_all_reports", "Can generate all reports"),
                    ("generate_department_reports", "Can generate department reports"),
                    ("generate_team_reports", "Can generate team reports"),
                    ("generate_reports", "Can generate own reports"),
                ),
            },
        ),
    ]
