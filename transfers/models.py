from django.db import models
from accounts.models import Account
from utils.choices import Transaction
from django.core.validators import MinValueValidator
from decimal import Decimal
from utils.helpers import generate_unique_id
from services.firebase_service import FirebaseService

class Transfer(models.Model):
    PeerToPeer, InternalTransfer, Interest, BillPayment, ReferralBonus = range(5)
    TRANSFER_TYPES = (
        (PeerToPeer, 'PeerToPeer'),
        (InternalTransfer, 'InternalTransfer'),
        (Interest, 'Interest'),
        (BillPayment, 'BillPayment'),
        (ReferralBonus, 'ReferralBonus'),
    )

    from_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='source')
    to_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='destination')
    status = models.PositiveSmallIntegerField(
        choices=Transaction.TRANSACTION_STATUS, 
        default=Transaction.PROCESSING
    )
    amount = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=12,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    fee = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=12,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    transfer_type = models.PositiveSmallIntegerField(
        choices=TRANSFER_TYPES,
        default=PeerToPeer
    )
    transaction_description = models.CharField(max_length=150, blank=True, null=True)
    reference = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_transfer_type(self):
        if (self.transfer_type == Transfer.PeerToPeer):
            return "From {} to {}".format(
               self.from_account.user.first_name.title(),  
               self.to_account.user.first_name.title()
            )
        elif (self.transfer_type == Transfer.InternalTransfer):
            return "{}'s {} to {}'s {} account".format(
                self.from_account.user.first_name,
                self.from_account.get_type_of_account_display(),
                self.to_account.user.first_name,
                self.to_account.get_type_of_account_display()
            )
        return self.get_transfer_type_display()
        

    def __str__(self):
        return self.get_transfer_type()

    def succeed(self):
        if (self.status == Transaction.SUCCESS) or (self.status == Transaction.FAILED):
            return
        from_account = self.from_account
        to_account = self.to_account
        from_account.balance -= Decimal(self.amount) + Decimal(self.fee)
        from_account.save()
        to_account.balance += self.amount
        to_account.save()
        self.status = Transaction.SUCCESS
        self.save()
        if self.transfer_type == Transfer.PeerToPeer:
            push = FirebaseService()
            push.transfer_successful(self, self.from_account.user, self.to_account.user)
        return True

    def save(self, *args, **kwargs):
        if not self.pk:
            self.reference = generate_unique_id(Transfer, 'reference', len=21)
        super(Transfer, self).save(*args, **kwargs)