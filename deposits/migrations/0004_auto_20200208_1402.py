# Generated by Django 2.2 on 2020-02-08 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deposits', '0003_auto_20200208_1258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deposit',
            name='reference',
            field=models.CharField(default='sa', max_length=50, unique=True),
            preserve_default=False,
        ),
    ]