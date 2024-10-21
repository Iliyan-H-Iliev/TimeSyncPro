# Generated by Django 5.0.7 on 2024-10-21 11:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0020_remove_profile_manages_departments'),
    ]

    operations = [
        migrations.CreateModel(
            name='Absence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('reason', models.TextField(blank=True, max_length=500, null=True)),
                ('absence_type', models.CharField(choices=[('sick', 'Sick Leave'), ('personal', 'Personal Leave'), ('unpaid', 'Unpaid Leave'), ('other', 'Other')], max_length=8)),
                ('absentee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='absences', to='accounts.profile')),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='added_absences', to='accounts.profile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('reason', models.TextField(blank=True, max_length=500, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied'), ('cancelled', 'Cancelled')], default='pending', max_length=9)),
                ('review_reason', models.TextField(blank=True, max_length=500, null=True)),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='holidays', to='accounts.profile')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_holidays', to='accounts.profile')),
                ('reviewer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='holiday_for_review', to='accounts.profile')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
