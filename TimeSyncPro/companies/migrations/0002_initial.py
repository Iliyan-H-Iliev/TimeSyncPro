# Generated by Django 5.1.4 on 2024-12-18 15:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('companies', '0001_initial'),
        ('shifts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='shift',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teams', to='shifts.shift'),
        ),
        migrations.AlterUniqueTogether(
            name='department',
            unique_together={('company', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='team',
            unique_together={('company', 'name')},
        ),
    ]
