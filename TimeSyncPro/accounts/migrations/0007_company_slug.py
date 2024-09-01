# Generated by Django 5.0.7 on 2024-08-26 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_remove_company_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='slug',
            field=models.SlugField(blank=True, editable=False, max_length=255, unique=True),
        ),
    ]