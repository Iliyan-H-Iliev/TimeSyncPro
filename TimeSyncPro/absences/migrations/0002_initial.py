# Generated by Django 5.0.7 on 2024-11-03 16:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('absences', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='absence',
            name='absentee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='absences', to='accounts.profile'),
        ),
        migrations.AddField(
            model_name='absence',
            name='added_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='added_absences', to='accounts.profile'),
        ),
        migrations.AddField(
            model_name='holiday',
            name='requester',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='holidays', to='accounts.profile'),
        ),
        migrations.AddField(
            model_name='holiday',
            name='reviewed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_holidays', to='accounts.profile'),
        ),
        migrations.AddField(
            model_name='holiday',
            name='reviewer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='holiday_for_review', to='accounts.profile'),
        ),
    ]