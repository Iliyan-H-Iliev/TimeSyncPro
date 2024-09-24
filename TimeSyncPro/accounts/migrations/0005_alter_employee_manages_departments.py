# Generated by Django 5.0.7 on 2024-08-26 00:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_remove_company_group_remove_company_user_and_more'),
        ('management', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='manages_departments',
            field=models.ManyToManyField(related_name='managers', to='management.department'),
        ),
    ]
