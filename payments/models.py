from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from utils.choices import Transaction
from decimal import Decimal
from utils.helpers import generate_unique_id

# Create your models here.

class Payment(models.Model):
	Wallet, Card = range(2)
	FUNDSOURCE_TYPES = (
		(Wallet, 'Wallet'),
		(Card, 'Card'),
	)
	Airtime, CableTV, TollPayment, Electricity = range(4)
	BILLER_TYPES = (
		(Airtime, 'Airtime'),
		(CableTV, 'CableTV'),
		(TollPayment, 'TollPayment'),
		(Electricity, 'Electricity'),
	)
	BILLER_NAMES = ['AIRTIME', 'DSTV', 'DSTV BOX OFFICE', 'EKO DISCO BILLS']

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE
	)
	name_of_biller = models.CharField(max_length=150, null=True, blank=True)
	type_of_biller = models.PositiveSmallIntegerField(
		choices=BILLER_TYPES,
		default=Airtime
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
	status = models.PositiveSmallIntegerField(
		choices=Transaction.TRANSACTION_STATUS,
		default=Transaction.SUBMITTED
	)
	fund_source = models.ForeignKey('deposits.FundSource', on_delete=models.SET_NULL, null=True, blank=True)
	fund_source_type = models.PositiveSmallIntegerField(
		choices=FUNDSOURCE_TYPES,
		default=Wallet
	)
	customer_id = models.CharField(max_length=50, null=True, blank=True)
	reference = models.CharField(max_length=50, unique=True, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	def save(self, *args, **kwargs):
		if self.reference is None:
			self.reference = generate_unique_id(Payment, 'reference', len=21)
		super(Payment, self).save(*args, **kwargs)

	def reject(self):
		if (self.status == Transaction.PROCESSING):
			self.status = Transaction.FAILED
			account = self.user.account_set.get(type_of_account=0)
			account.balance += self.amount
			account.save()
			self.save()

	def process(self):
		if (self.status == Transaction.SUBMITTED):
			account = self.user.account_set.get(type_of_account=0)
			account.balance -= self.amount
			account.save()
			self.status = Transaction.PROCESSING
			self.save()

	def succeed(self):
		if (self.status == Transaction.SUCCESS) or (self.status == Transaction.FAILED):
			return
		self.status = Transaction.SUCCESS
		self.save()