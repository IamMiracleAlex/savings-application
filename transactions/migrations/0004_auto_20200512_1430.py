# Generated by Django 2.2 on 2020-05-12 13:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0003_auto_20200512_0951'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='src_account',
            new_name='account',
        ),
    ]
