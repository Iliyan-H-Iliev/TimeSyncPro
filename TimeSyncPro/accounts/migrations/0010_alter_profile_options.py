# Generated by Django 5.0.7 on 2024-12-04 10:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0009_alter_profile_company_alter_profile_first_name_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="profile",
            options={
                "permissions": [
                    ("add_company_admin", "Can add Company Administrator"),
                    ("change_company_admin", "Can change Company Administrator"),
                    ("delete_company_admin", "Can delete Company Administrator"),
                    ("view_company_admin", "Can view Company Administrator"),
                    ("add_hr", "Can add HR"),
                    ("change_hr", "Can change HR"),
                    ("delete_hr", "Can delete HR"),
                    ("view_hr", "Can view HR"),
                    ("add_manager", "Can add Manager"),
                    ("change_manager", "Can change Manager"),
                    ("delete_manager", "Can delete Manager"),
                    ("view_manager", "Can view Manager"),
                    ("add_team_leader", "Can add TeamLeader"),
                    ("change_team_leader", "Can change TeamLeader"),
                    ("delete_team_leader", "Can delete TeamLeader"),
                    ("view_team_leader", "Can view TeamLeader"),
                    ("add_staff", "Can add Staff"),
                    ("change_staff", "Can change Staff"),
                    ("delete_staff", "Can delete Staff"),
                    ("view_staff", "Can view Staff"),
                    ("view_employees", "Can view Employees"),
                ]
            },
        ),
    ]
