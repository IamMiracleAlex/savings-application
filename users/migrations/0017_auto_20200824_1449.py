# Generated by Django 2.2 on 2020-08-24 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_customuser_paid_referer_bonus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='phone_number',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
