# Generated by Django 5.0.7 on 2024-10-05 20:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_alter_profile_date_of_birth_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='leave_approver',
        ),
    ]
