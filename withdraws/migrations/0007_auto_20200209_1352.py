# Generated by Django 2.2 on 2020-02-09 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('withdraws', '0006_auto_20200209_1328'),
    ]

    operations = [
        migrations.AlterField(
            model_name='beneficiary',
            name='recipient_code',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]