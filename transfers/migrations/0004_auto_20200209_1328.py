# Generated by Django 2.2 on 2020-02-09 12:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('transfers', '0003_auto_20200209_0904'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transfer',
            name='from_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source', to='accounts.Account'),
        ),
        migrations.AlterField(
            model_name='transfer',
            name='to_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='destination', to='accounts.Account'),
        ),
    ]
