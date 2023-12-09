# Generated by Django 4.1.7 on 2023-11-15 18:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0006_problemtest'),
    ]

    operations = [
        migrations.AddField(
            model_name='problemtest',
            name='problem',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='tests', to='problems.problem'),
            preserve_default=False,
        ),
    ]
