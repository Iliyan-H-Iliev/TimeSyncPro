# Generated by Django 5.0.7 on 2024-08-26 22:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_company_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='timesyncprouser',
            name='activation_token',
            field=models.CharField(blank=True, max_length=64),
        ),
    ]