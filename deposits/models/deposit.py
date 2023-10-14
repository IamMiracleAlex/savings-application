from django.db import models
from django.conf import settings
from utils.choices import Transaction
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
from accounts.models import Account
from utils.helpers import generate_unique_id
from services.firebase_service import FirebaseService

class Deposit(models.Model):
    QuickSave, AutoSave, ReferralBonus, TermDeposit, BankTransfer = range(5)
    DEPOSIT_TYPES = (
        (AutoSave, 'AutoSave'),
        (QuickSave, 'QuickSave'),
        (ReferralBonus, 'ReferralBonus'),
        (TermDeposit, 'TermDeposit'),
        (BankTransfer, 'BankTransfer'),
    )

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    type_of_deposit = models.PositiveSmallIntegerField(
        choices=DEPOSIT_TYPES,
        default=QuickSave
    )
    status = models.PositiveSmallIntegerField(
        choices=Transaction.TRANSACTION_STATUS,
        default=Transaction.PROCESSING
    )
    reference = models.CharField(max_length=50, unique=True, null=True, blank=True)
    amount = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=12,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    fund_source = models.ForeignKey('deposits.FundSource', on_delete=models.SET_NULL, null=True, blank=True)
    subscription = models.ForeignKey('subscriptions.Subscription', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "ref: {} status: {} amount: {}".format(self.reference, self.status, self.amount)

    def reject(self):
        if (self.status == Transaction.SUCCESS) or (self.status == Transaction.FAILED):
            return
        self.status = Transaction.FAILED
        self.save()
        push = FirebaseService()
        push.deposit_rejected(self, self.account.user)

    def process(self):
        self.status = Transaction.PROCESSING
        self.save()

    def succeed(self):
        if (self.status == Transaction.SUCCESS) or (self.status == Transaction.FAILED):
            return
        account = self.account
        account.balance += self.amount
        account.save()
        self.status = Transaction.SUCCESS
        self.save()
        push = FirebaseService()
        push.deposit_successful(self, self.account.user)

    def save(self, *args, **kwargs):
        if self.reference is None:
            self.reference = generate_unique_id(Deposit, 'reference', len=21)
        super(Deposit, self).save(*args, **kwargs)

