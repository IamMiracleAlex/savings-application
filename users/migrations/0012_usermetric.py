# Generated by Django 2.2 on 2020-07-07 19:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_auto_20200408_0853'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserMetric',
            fields=[
            ],
            options={
                'verbose_name_plural': 'User Metrics',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('users.customuser',),
        ),
    ]
