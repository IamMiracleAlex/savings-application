# Generated by Django 2.2 on 2020-02-18 09:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kyc_profiles', '0004_auto_20200212_1624'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kycprofile',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
