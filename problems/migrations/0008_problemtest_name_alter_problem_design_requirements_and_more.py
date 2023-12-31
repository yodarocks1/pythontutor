# Generated by Django 4.1.7 on 2023-11-23 22:53

from django.db import migrations, models
import problems.widgets


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0007_problemtest_problem'),
    ]

    operations = [
        migrations.AddField(
            model_name='problemtest',
            name='name',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AlterField(
            model_name='problem',
            name='design_requirements',
            field=problems.widgets.CodeField(),
        ),
        migrations.AlterField(
            model_name='problem',
            name='starter_code',
            field=problems.widgets.MultiCodeField(default=dict),
        ),
        migrations.AlterField(
            model_name='problemtest',
            name='code',
            field=problems.widgets.CodeField(),
        ),
    ]
