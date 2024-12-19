# Generated by Django 5.1.4 on 2024-12-18 15:59

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        ('companies', '0001_initial'),
        ('shifts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='employees', to='companies.company'),
        ),
        migrations.AddField(
            model_name='profile',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employees', to='companies.department'),
        ),
        migrations.AddField(
            model_name='profile',
            name='shift',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employees', to='shifts.shift'),
        ),
        migrations.AddField(
            model_name='profile',
            name='team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employees', to='companies.team'),
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='tspuser',
            index=models.Index(fields=['email'], name='accounts_ts_email_2e69d1_idx'),
        ),
        migrations.AddIndex(
            model_name='tspuser',
            index=models.Index(fields=['slug'], name='accounts_ts_slug_d172c0_idx'),
        ),
        migrations.AddConstraint(
            model_name='profile',
            constraint=models.UniqueConstraint(fields=('employee_id', 'company'), name='unique_employee_id_per_company'),
        ),
    ]
