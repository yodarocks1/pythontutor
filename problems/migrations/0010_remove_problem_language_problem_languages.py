# Generated by Django 4.1.7 on 2023-11-24 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0009_remove_problem_test_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='problem',
            name='language',
        ),
        migrations.AddField(
            model_name='problem',
            name='languages',
            field=models.JSONField(default=['Python']),
            preserve_default=False,
        ),
    ]
