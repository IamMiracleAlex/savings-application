# Generated by Django 2.2 on 2020-02-09 00:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('withdraws', '0002_auto_20200208_1535'),
    ]

    operations = [
        migrations.RenameField(
            model_name='beneficiary',
            old_name='type_of_deposit',
            new_name='type_of_beneficiary',
        ),
    ]