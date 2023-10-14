from django.db import models
from django.conf import settings
from utils.choices import Transaction as TransactionOptions
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
from accounts.models import Account
from utils.helpers import generate_unique_id
from services.firebase_service import FirebaseService
from jsonfield import JSONField
from services.paystack_service import PaystackService
from services.gsuite_service import GsuiteService
from services.pusher_service import PusherService



class Transaction(models.Model):
	
	account = models.ForeignKey(
		Account,
		on_delete=models.CASCADE,
		blank=True,
		null=True
	)
	type_of_transaction = models.PositiveSmallIntegerField(
		choices=TransactionOptions.TRANSACTION_TYPES,
		default=TransactionOptions.Deposit
	)
	status = models.PositiveSmallIntegerField(
		choices=TransactionOptions.TRANSACTION_STATUS,
		default=TransactionOptions.SUBMITTED
	)
	reference = models.CharField(max_length=50, unique=True, null=True, blank=True)
	amount = models.DecimalField(
		default=0.00,
		decimal_places=2,
		max_digits=12,
		validators=[MinValueValidator(Decimal('0.00'))]
	)
	balance_after_transaction = models.DecimalField(
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
	total = models.DecimalField(
		default=0.00,
		decimal_places=2,
		max_digits=12,
		validators=[MinValueValidator(Decimal('0.00'))]
	)
	memo = models.CharField(max_length=200, null=True, blank=True)
	data = JSONField(null=True)
	dest_account = models.ForeignKey(
		Account,
		on_delete=models.CASCADE,
		blank=True,
		null=True,
		related_name='dest_account'
	)
	created_at = models.DateTimeField(auto_now_add=True, null=True)
	updated_at = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return "ref: {} status: {} amount: {}".format(self.reference, self.status, self.amount)

	def reject(self):
		account = self.account
		if (self.status == TransactionOptions.SUCCESS) or (self.status == TransactionOptions.FAILED):
			return
		if (self.type_of_transaction != TransactionOptions.Deposit):
			account.balance += Decimal(self.total)
			account.save()
		self.balance_after_transaction = account.balance
		self.status = TransactionOptions.FAILED
		self.save()
		notify_transaction_failed(self)

	def process(self):
		account = self.account
		self.total = Decimal(self.amount) + Decimal(self.fee)
		if (self.status != TransactionOptions.SUBMITTED):
			return
		if (self.type_of_transaction != TransactionOptions.Deposit):
			account.balance -= self.total
			account.save()
		self.status = TransactionOptions.PROCESSING
		self.balance_after_transaction = account.balance
		self.save()

	def succeed(self):
		account = self.account
		if (self.status == TransactionOptions.SUCCESS) or (self.status == TransactionOptions.FAILED):
			return
		if (self.type_of_transaction == TransactionOptions.Deposit):
			account.balance += self.amount
			account.save()
		if (self.type_of_transaction in [TransactionOptions.Transfer, TransactionOptions.Interest]):
			dest_account = Account.objects.get(id=self.dest_account_id)
			dest_account.balance += self.amount
			self.data['dest_account_balance_after_transaction']  = dest_account.balance #noqa
			dest_account.save()
		self.status = TransactionOptions.SUCCESS
		self.balance_after_transaction = account.balance
		self.save()
		notify_transaction_success(self)
		return True

	def save(self, *args, **kwargs):
		if self.reference is None:
			self.reference = generate_unique_id(Transaction, 'reference', len=21)
		super(Transaction, self).save(*args, **kwargs)
		pusher_update(self)

def notify_transaction_failed(trans):
	context = { 'email': trans.account.user.email, 
				'first_name': trans.account.user.first_name, 
				'transaction_type': trans.get_type_of_transaction_display(), 
				'transaction_status': trans.get_status_display(), 
				'transaction_reference': trans.reference, 
				'memo': trans.memo, 
				'date': trans.created_at.strftime("%b %d %Y %H:%M:%S"), 
				'amount': trans.amount
			}
	GsuiteService.send_transaction_failed_mail(context)
	notify_firebase_failed(trans)
	return True

def notify_transaction_success(trans):
	context = { 'email': trans.account.user.email, 
				'first_name': trans.account.user.first_name, 
				'transaction_type': trans.get_type_of_transaction_display(), 
				'transaction_status': trans.get_status_display(), 
				'transaction_reference': trans.reference, 
				'memo': trans.memo, 
				'date': trans.created_at.strftime("%b %d %Y %H:%M:%S"), 
				'amount': trans.amount
			}
	GsuiteService.send_transaction_success_mail(context)

	if (trans.type_of_transaction == TransactionOptions.Transfer):
		context['email'] = trans.dest_account.user.email
		GsuiteService.send_transaction_success_mail(context)
	notify_firebase_success(trans)
	return True

def notify_firebase_success(trans):
	firebase = FirebaseService()
	if (trans.type_of_transaction == TransactionOptions.Deposit):
		firebase.new_transaction(trans.account.user_id, "Deposit Successful", "Your {} Deposit of {} was successful".format(trans.data['type_of_deposit'], trans.amount))
	if (trans.type_of_transaction == TransactionOptions.Withdraw):
		firebase.new_transaction(trans.account.user_id, "Withdrawal Successful", "Your Withdrawal of {} was successful".format(trans.amount))
	if (trans.type_of_transaction == TransactionOptions.Payment):
		firebase.new_transaction(trans.account.user_id, "{} Purchase Successful".format(trans.data['name_of_biller']), "Your {} purchase of {} was successful".format(trans.data['name_of_biller'], trans.amount))
	if (trans.type_of_transaction == TransactionOptions.Transfer):
		firebase.new_transaction(trans.account.user_id, "Transfer Successful", "Your Transfer of {} to {} was successful".format(trans.amount, trans.dest_account.user.first_name))
		if (trans.account.user_id == trans.dest_account.user_id):
			return
		firebase.new_transaction(trans.dest_account.user_id, "Transfer Successful", "You just received a transfer of {} from {}".format(trans.amount, trans.account.user.first_name))
	return True
		

def notify_firebase_failed(trans):
	firebase = FirebaseService()
	if (trans.type_of_transaction == TransactionOptions.Deposit):
		firebase.new_transaction(trans.account.user_id, "Deposit Failed", "Your {} Deposit of {} was unsuccessful".format(trans.data['type_of_deposit'], trans.amount))
	if (trans.type_of_transaction == TransactionOptions.Withdraw):
		firebase.new_transaction(trans.account.user_id, "Withdrawal Failed", "Your Withdrawal of {} was unsuccessful".format(trans.amount))
	if (trans.type_of_transaction == TransactionOptions.Payment):
		firebase.new_transaction(trans.account.user_id, "{} Purchase Failed".format(trans.data['name_of_biller']), "Your {} purchase of {} was unsuccessful".format(trans.data['name_of_biller'], trans.amount))
	if (trans.type_of_transaction == TransactionOptions.Transfer):
		firebase.new_transaction(trans.account.user_id, "Transfer Failed", "Your Transfer of {} to {} was unsuccessful".format(trans.amount, trans.dest_account.user.first_name))
	return True


def pusher_update(trans):
	pusher = PusherService()
	pusher.new_transaction(trans)
	return True

	

class TransactionMetric(Transaction):
	class Meta:
		proxy = True
		verbose_name_plural = 'Transaction Metrics'  
