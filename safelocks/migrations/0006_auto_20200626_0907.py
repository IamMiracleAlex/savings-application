# Generated by Django 2.2 on 2020-06-26 08:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('safelocks', '0005_auto_20200526_1214'),
    ]

    operations = [
        migrations.AlterField(
            model_name='safelock',
            name='subscription',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='subscriptions.Subscription'),
        ),
    ]
