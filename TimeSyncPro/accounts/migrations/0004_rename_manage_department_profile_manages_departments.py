# Generated by Django 5.0.7 on 2024-11-06 10:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_remove_profile_days_off_left_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='manage_department',
            new_name='manages_departments',
        ),
    ]
