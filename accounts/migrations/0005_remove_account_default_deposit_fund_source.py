# Generated by Django 2.2 on 2020-02-07 22:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_account_default_deposit_fund_source'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='default_deposit_fund_source',
        ),
    ]
