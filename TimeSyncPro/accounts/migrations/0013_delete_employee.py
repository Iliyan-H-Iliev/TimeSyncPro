# Generated by Django 5.0.7 on 2024-09-24 08:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_remove_employee_company_remove_employee_department_and_more'),
        ('management', '0002_alter_department_leave_approver_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Employee',
        ),
    ]
