# Generated by Django 2.2 on 2020-07-07 19:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0011_auto_20200602_1052'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransactionMetric',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Transaction Metrics',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('transactions.transaction',),
        ),
    ]