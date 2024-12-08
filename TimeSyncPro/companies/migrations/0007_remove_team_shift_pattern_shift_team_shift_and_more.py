# Generated by Django 5.0.7 on 2024-11-19 08:09

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_remove_profile_shift_pattern'),
        ('companies', '0006_alter_team_unique_together'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='team',
            name='shift_pattern',
        ),
        migrations.CreateModel(
            name='Shift',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, validators=[django.core.validators.MinLengthValidator(3)])),
                ('description', models.TextField(blank=True, null=True)),
                ('start_date', models.DateField(default=django.utils.timezone.now)),
                ('rotation_weeks', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(52)])),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shifts', to='companies.company')),
            ],
            options={
                'unique_together': {('company', 'name')},
            },
        ),
        migrations.AddField(
            model_name='team',
            name='shift',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teams', to='companies.shift'),
        ),
        migrations.AlterField(
            model_name='shiftblock',
            name='pattern',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to='companies.shift'),
        ),
        migrations.DeleteModel(
            name='ShiftPattern',
        ),
    ]
