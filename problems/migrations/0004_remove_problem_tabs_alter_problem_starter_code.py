# Generated by Django 4.1.7 on 2023-10-27 01:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0003_problem_allow_new_tabs_problem_tabs'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='problem',
            name='tabs',
        ),
        migrations.AlterField(
            model_name='problem',
            name='starter_code',
            field=models.JSONField(default=dict),
        ),
    ]
