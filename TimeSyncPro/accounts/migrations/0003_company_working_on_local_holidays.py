# Generated by Django 5.0.7 on 2024-07-28 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='working_on_local_holidays',
            field=models.BooleanField(default=False),
        ),
    ]
