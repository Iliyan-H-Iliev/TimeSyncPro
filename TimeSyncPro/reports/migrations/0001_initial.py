# Generated by Django 5.0.7 on 2024-12-15 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'permissions': (('generate_all_reports', 'Can generate all reports'), ('generate_department_reports', 'Can generate department reports'), ('generate_team_reports', 'Can generate team reports')),
                'managed': False,
                'default_permissions': (),
            },
        ),
    ]