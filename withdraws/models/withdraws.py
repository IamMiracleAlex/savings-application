from django.db import models
from django.conf import settings
from decimal import Decimal
from utils.choices import Transaction
from accounts.models import Account
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from services.firebase_service import FirebaseService
from utils.helpers import generate_unique_id



class Withdraw(models.Model):
	account = models.ForeignKey(
		Account,
		on_delete=models.CASCADE,
		blank=True,
		null=True
	)
	status = models.PositiveSmallIntegerField(
		choices=Transaction.TRANSACTION_STATUS,
		default=Transaction.SUBMITTED
	)
	reference = models.CharField(max_length=50, unique=True)
	amount = models.DecimalField(
		default=0.00,
		decimal_places=2,
		max_digits=12,
		validators=[MinValueValidator(Decimal(0.00))]
	)
	beneficiary = models.ForeignKey('withdraws.Beneficiary', on_delete=models.SET_NULL, null=True, blank=True)
	fee = models.DecimalField(
		default=0.00,
		decimal_places=2,
		max_digits=12,
		validators=[MinValueValidator(Decimal('0.00'))]
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return "ref: {} status: {} amount: {}".format(self.reference, self.status, self.amount)

	def reject(self):
		if (self.status == Transaction.PROCESSING):
			self.status = Transaction.FAILED
			account = self.account
			account.balance += self.amount
			account.save()
			self.save()

	def process(self):
		if (self.status == Transaction.SUBMITTED):
			account = self.account
			account.balance -= self.amount
			account.save()
			self.status = Transaction.PROCESSING
			self.save()

	def succeed(self):
		if (self.status == Transaction.SUCCESS) or (self.status == Transaction.FAILED):
			return
		self.status = Transaction.SUCCESS
		self.save()
		push = FirebaseService()
		push.withdraw_successful(self, self.account.user)

	def save(self, *args, **kwargs):
		if not self.pk:
			self.reference = generate_unique_id(Withdraw, 'reference', len=21)
		super(Withdraw, self).save(*args, **kwargs)

