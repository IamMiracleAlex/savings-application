# Generated by Django 2.2 on 2020-02-08 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deposits', '0002_auto_20200207_1136'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deposit',
            name='reference',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]