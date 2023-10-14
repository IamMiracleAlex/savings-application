# Generated by Django 2.2 on 2020-02-08 14:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('withdraws', '0001_initial'),
        ('users', '0002_customuser_default_deposit_fund_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='default_withdraw_beneficiary',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='withdraws.Beneficiary'),
        ),
    ]
