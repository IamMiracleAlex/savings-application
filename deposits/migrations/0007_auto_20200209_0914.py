# Generated by Django 2.2 on 2020-02-09 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deposits', '0006_auto_20200209_0110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deposit',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(0, 'SUBMITTED'), (1, 'PROCESSING'), (4, 'CANCELED'), (2, 'SUCCESS'), (3, 'FAILED')], default=1),
        ),
    ]