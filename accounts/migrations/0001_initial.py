# Generated by Django 2.2 on 2020-02-06 14:26

from decimal import Decimal
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_id', models.CharField(editable=False, max_length=15, unique=True)),
                ('type_of_account', models.PositiveSmallIntegerField(choices=[(0, 'WALLET'), (1, 'DIRECT'), (2, 'WALLET')])),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('interest', models.DecimalField(decimal_places=2, default=0.0, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('interest_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
