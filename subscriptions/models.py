from django.db import models
from deposits.models import Deposit
from django.core.validators import MinValueValidator
from decimal import Decimal
from utils.choices import Transaction as TransactionOptions
from datetime import timedelta, date
from transactions.models import Transaction

class Subscription(models.Model):
    DAILY, WEEKLY, MONTHLY, ANNUALY = range(4)
    INTERVAL_CHOICES = (
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
        (MONTHLY, 'Monthly'),
        (ANNUALY, 'Annualy')
    )
    name = models.CharField(max_length=50)
    fund_source = models.ForeignKey('deposits.FundSource',on_delete=models.SET_NULL, null=True, blank=True)
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=12,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    interval = models.PositiveSmallIntegerField(choices=INTERVAL_CHOICES)
    is_active = models.BooleanField(default=False)
    start_date = models.DateField(blank=True)
    previous_paydate = models.DateField(blank=True, null=True)
    next_paydate = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def user(self):
        return self.account.user
    def auth(self):
        return self.fund_source.auth_code
    def enable(self):
        self.is_active = True
        self.save()

    def disable(self):
        self.is_active = False
        self.save()
        
    def set_next_paydate(self):
        if (self.interval == Subscription.DAILY):
            days=1
        if (self.interval == Subscription.WEEKLY):
            days=7
        if (self.interval == Subscription.MONTHLY):
            days=30
        if (self.interval == Subscription.ANNUALY):
            days=365
        
        self.next_paydate = self.previous_paydate + timedelta(days=days)
        self.save() # added this, changes are not saved

        while (self.next_paydate <= date.today()):
            self.next_paydate += timedelta(days=days)
        
    def create_deposit(self):
        transaction = Transaction.objects.create(
            account = self.account,
            type_of_transaction = TransactionOptions.Deposit,
            amount = self.amount,
        )
        transaction.data = {}
        transaction.data['fund_source_id'] = self.fund_source_id
        transaction.data['type_of_deposit'] = 'AutoSave'
        transaction.data['subscription_id'] = self.id
        transaction.save()
        transaction.process()
        return transaction

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = "{}'s {} subscription".format(self.account.user.first_name, self.get_interval_display())
        super(Subscription, self).save(*args, **kwargs)

    def __str__(self):
        return "{}".format(self.name)