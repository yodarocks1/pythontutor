# Generated by Django 4.1.7 on 2023-11-13 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0005_problem_test_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProblemTest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('run_on_save', models.BooleanField()),
                ('run_on_test', models.BooleanField()),
                ('run_on_hint', models.BooleanField()),
                ('run_on_submit', models.BooleanField()),
                ('halt_testing_on_fail', models.BooleanField()),
                ('priority', models.IntegerField(help_text='Higher values run first. Syntax errors occur at priority 2000000000. Values must be between -2147483648 to 2147483647.')),
                ('code', models.TextField()),
            ],
        ),
    ]