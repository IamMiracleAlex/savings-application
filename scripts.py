import os
import django
from decouple import config
os.environ.setdefault('DJANGO_SETTINGS_MODULE', config('DEFAULT_SETTINGS'))
django.setup()

from deposits.models import Deposit
from withdraws.models import Withdraw
from transfers.models import Transfer
from payments.models import Payment
from accounts.models import Account
from transactions.models import TransactionOptions, Transaction

def move_deposits():
	deposits = Deposit.objects.all()
	for deposit in deposits:
		transaction, _ = Transaction.objects.get_or_create(
			amount = deposit.amount,
			reference = deposit.reference,
			created_at = deposit.created_at,
			updated_at = deposit.updated_at,
			status = deposit.status,
			type_of_transaction = TransactionOptions.Deposit,
			account = deposit.account
		)
		transaction.data = {}
		transaction.data['fund_source_id'] = deposit.fund_source_id
		transaction.data['type_of_deposit'] = deposit.get_type_of_deposit_display()
		transaction.data['subscription_id'] = deposit.subscription_id
		transaction.save()

def move_withdrawals():
	withdraws = Withdraw.objects.all()
	for withdraw in withdraws:
		transaction, _ = Transaction.objects.get_or_create(
			amount = withdraw.amount,
			reference = withdraw.reference,
			created_at = withdraw.created_at,
			updated_at = withdraw.updated_at,
			status = withdraw.status,
			fee = withdraw.fee,
			type_of_transaction = TransactionOptions.Withdraw,
			account = withdraw.account
		)
		transaction.data = {}
		transaction.data['beneficiary_id'] = withdraw.beneficiary_id
		transaction.save()

def move_transfers():
	transfers = Transfer.objects.all()
	for transfer in transfers:
		transaction, _ = Transaction.objects.get_or_create(
			amount = transfer.amount,
			reference = transfer.reference,
			created_at = transfer.created_at,
			updated_at = transfer.updated_at,
			status = transfer.status,
			type_of_transaction = TransactionOptions.Transfer,
			account = transfer.from_account,
			dest_account = transfer.to_account,
			fee = transfer.fee,
			memo = transfer.transaction_description
		)
		transaction.data = {}
		transaction.data['transfer_type'] = transfer.get_transfer_type_display()
		transaction.save()

def move_payments():
	payments = Payment.objects.all()
	for payment in payments:
		account = Account.objects.get(user=payment.user, type_of_account=Account.WALLET)
		transaction, _ = Transaction.objects.get_or_create(
			amount = payment.amount,
			reference = payment.reference,
			created_at = payment.created_at,
			updated_at = payment.updated_at,
			status = payment.status,
			type_of_transaction = TransactionOptions.Payment,
			account = account,
			fee = payment.fee,
		)
		transaction.data = {}
		transaction.data['name_of_biller'] = payment.name_of_biller
		transaction.data['customer_id'] = payment.customer_id
		transaction.data['type_of_biller'] = payment.get_type_of_biller_display()
		transaction.data['fund_source_type'] = payment.get_fund_source_type_display()
		transaction.data['fund_source_id'] = payment.fund_source_id
		transaction.save()

def fix_all():
	payments = Payment.objects.all()
	withdraws = Withdraw.objects.all()
	deposits = Deposit.objects.all()
	transfers = Transfer.objects.all()
	for payment in payments:
		transaction = Transaction.objects.get(reference = payment.reference)
		transaction.created_at = payment.created_at
		transaction.updated_at = payment.updated_at
		transaction.save()
	for withdraw in withdraws:
		transaction = Transaction.objects.get(reference = withdraw.reference)
		transaction.created_at = withdraw.created_at
		transaction.updated_at = withdraw.updated_at
		transaction.save()
	for deposit in deposits:
		transaction = Transaction.objects.get(reference = deposit.reference)
		transaction.created_at = deposit.created_at
		transaction.updated_at = deposit.updated_at
		transaction.save()
	for transfer in transfers:
		transaction = Transaction.objects.get(reference = transfer.reference)
		transaction.created_at = transfer.created_at
		transaction.updated_at = transfer.updated_at
		transaction.save()