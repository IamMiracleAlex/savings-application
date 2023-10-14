from decimal import Decimal

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

from utils.helpers import generate_unique_id


class Account(models.Model):
    WALLET, DIRECT, DEPOSIT = range(3)
    ACCOUNT_CHOICES = (
        (WALLET, 'WALLET'),
        (DIRECT, 'DIRECT'),
        (DEPOSIT, 'DEPOSIT')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    public_id = models.CharField(max_length=15, unique=True, editable=False)
    type_of_account = models.PositiveSmallIntegerField(choices=ACCOUNT_CHOICES, editable=False)
    balance = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=12,
        validators=[MinValueValidator(Decimal(0.00))]
    )
    interest = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=12,
        validators=[MinValueValidator(Decimal(0.00))]
    )
    interest_for_today = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=12,
        validators=[MinValueValidator(Decimal(0.00))]
    )
    last_interest_withdrawal_day = models.DateTimeField(blank=True, null=True)
    interest_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label ='accounts'
        unique_together = ('user', 'type_of_account',)

    def __str__(self):
        return "{}'s {} account".format(
            self.user, 
            self.get_type_of_account_display()
        )

    def save(self, *args, **kwargs):
        if not self.pk:
            self.public_id = generate_unique_id(Account, 'public_id')
        super(Account, self).save(*args, **kwargs)


    def chicken_change_deposit(self, agent, amount):
        from transactions.models import Transaction, TransactionOptions
        deposit = Transaction.objects.create(
            account = self,
            type_of_transaction = TransactionOptions.Deposit,
            amount = amount,
            memo = f'NGN {amount} chicken change deposit',
        )
        deposit.data = {}
        deposit.data['type_of_deposit'] = 'ChickenChange'
        deposit.data['sales_agent'] = agent.full_name()
        deposit.data['sales_agent_id'] = agent.id
        deposit.save()
        deposit.process()
        deposit.succeed()
        return self