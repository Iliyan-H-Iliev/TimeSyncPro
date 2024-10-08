# Generated by Django 5.0.7 on 2024-10-09 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0003_company_alter_department_company_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='leave_days_per_year',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='company',
            name='maximum_leave_days_per_request',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='company',
            name='minimum_leave_notice',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='company',
            name='transferable_leave_days',
            field=models.PositiveIntegerField(),
        ),
    ]
