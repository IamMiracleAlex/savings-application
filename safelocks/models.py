from django.db import models
from accounts.models import Account
from django.core.validators import MinValueValidator
from decimal import Decimal
from transactions.models import Transaction, TransactionOptions
from subscriptions.models import Subscription

class SafeLock(models.Model):
    RentOrAccomodation, Travel, Car, Fees, Education, Business, Event, Gadget, Birthday, Investment,  LifeGoals, Other = range(12)
    TARGET_CATEGORIES = (
        (RentOrAccomodation, 'Rent/Accomodation'),
        (Travel, 'Travel'),
        (Car, 'Car'),
        (Fees, 'Fees'),
        (Education, 'Education'),
        (Business, 'Business'),
        (Event, 'Event'),
        (Gadget, 'Gadget'),
        (Birthday, 'Birthday'),
        (Investment, 'Investment'),
        (LifeGoals, 'LifeGoals'),
        (Other, 'Other'),
    )
    
    name = models.CharField(max_length=150, blank=True)
    account = models.ForeignKey(
		Account,
        on_delete=models.CASCADE,
        blank=True,
        null=True
	)
    amount = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=12,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    interest = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=12,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    target_goal = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=12,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    category = models.PositiveSmallIntegerField(
        choices=TARGET_CATEGORIES,
        default=Other
    )
    is_active = models.BooleanField(default=False)
    maturity_date = models.DateField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subscription = models.OneToOneField(Subscription, null=True, on_delete=models.SET_NULL, blank=True)

    def __str__(self):
        return "Name:{} Amount: {}".format(self.name, self.amount)

    def activate(self):
        self.is_active = True
        self.save()

    def create_deposit(self, ref, amount):
        deposit = Transaction.objects.create(
            account = self.account,
            amount = amount,
            type_of_transaction= TransactionOptions.Deposit
	    )
        deposit.data = {}
        deposit.data['fund_source_id'] = self.account.user.default_deposit_fund_source_id
        deposit.data['type_of_deposit'] = 'TermDeposit'
        deposit.process()
        return deposit