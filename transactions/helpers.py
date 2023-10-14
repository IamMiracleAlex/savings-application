from decimal import Decimal

from decouple import config
from celery import shared_task

from services.paystack_service import PaystackService
from .models import Transaction, TransactionOptions
from deposits.models import FundSource
from services.ravepay_service import RavepayService
from services.pusher_service import PusherService
from users.models import CustomUser
from accounts.models import Account
from django.utils import timezone

# why i shared task if celery doesnt process them?

def process_transaction(transaction):
	if (transaction.type_of_transaction == TransactionOptions.Deposit):
		return paystack_deposit(transaction.id)
	if (transaction.type_of_transaction == TransactionOptions.Withdraw):
		return paystack_withdraw(transaction.id)
	if (transaction.type_of_transaction == TransactionOptions.Payment):
		return ravepay_bills(transaction.id)
	if (transaction.type_of_transaction == TransactionOptions.Transfer):
		transaction.succeed()
		return 'success', transaction


@shared_task
def paystack_deposit(transaction_id):
	paystack = PaystackService()
	deposit = Transaction.objects.get(id=transaction_id)
	fund_source = FundSource.objects.get(id=deposit.data['fund_source_id'])
	response = paystack.charge_card(deposit, fund_source=fund_source)
	if (response['status'] == True):
		if (response['data']['status'] == 'success'):
			deposit.succeed()
			return response['message'], deposit
		else:
			deposit.data['failure_reason'] = response['data']['gateway_response']
			deposit.reject()
			return response['data']['gateway_response'], deposit
	deposit.reject()
	return response['message'], deposit

@shared_task
def paystack_withdraw(transaction_id):
	paystack = PaystackService()
	withdraw = Transaction.objects.get(id=transaction_id)
	response = paystack.transfer(withdraw)
	if (response['status'] == True):
		if (response['data']['status'] == 'success'):
			withdraw.succeed()
	else:
		withdraw.reject()
	return response['message'], withdraw

@shared_task
def ravepay_bills(transaction_id):
	ravepay = RavepayService()
	payment = Transaction.objects.get(id=transaction_id)
	try:
		response = ravepay.trans_bill_payments(payment)
		if (response.get('data')['Status'] == 'success'):
			payment.succeed()
			if (payment.amount > 199) and (payment.data['type_of_biller'] == 'Airtime'):
				create_airtime_deposit(payment.account.user, payment.amount)
			return response['message'], payment
		payment.reject()
	except:
		payment.reject()
	return response['message'], payment

@shared_task
def create_fund_source(user_id, reference, amount):
	paystack = PaystackService()
	user = CustomUser.objects.get(id=user_id)
	response = paystack.verify_transaction(reference)
	if response.get('data') and response['data']['status'] == 'success':
		data = response['data']['authorization']
		account = Account.objects.get(
			user=user,
			type_of_account=Account.WALLET
		)
		fund_source, _ = FundSource.objects.get_or_create(user = user, last4 = data['last4'], bank_name = data['bank'], 
			exp_month = data['exp_month'], exp_year = data['exp_year'], card_type = data['card_type'], is_active = True)
		fund_source.auth_code = data['authorization_code']
		fund_source.save()
		deposit, _ = Transaction.objects.get_or_create(reference = reference, account = account, amount = Decimal(amount))
		deposit.data['fund_source_id'] = fund_source.id
		deposit.succeed()

		if user.default_deposit_fund_source is None:
			user.default_deposit_fund_source = fund_source
			user.save()

		if user.account_activated == False:
			user.account_activated = True
			user.save()
			create_referral_deposit(user)


def create_referral_deposit(user):
	ReferralAdminUser = CustomUser.objects.get(id=config('ReferralUserID'))
	referer = user.referer
	if referer:
		if referer.referrals.count() >= 10:
			return
		from_account = Account.objects.get(type_of_account=Account.WALLET, user=ReferralAdminUser)
		to_account = Account.objects.get(type_of_account=Account.WALLET, user=referer)
		transfer = Transaction.objects.create(
			account=from_account,
			type_of_transaction = TransactionOptions.Transfer,
            amount = Decimal(config('ReferralBonusAmount')),
			memo = '{} Referral Bonus earned referring {}'.format(config('ReferralBonusAmount'), user.first_name) 
		)
		transfer.dest_account_id = to_account.id
		transfer.data = {}
		transfer.data['transfer_type'] = 'ReferralBonus'
		transfer.succeed()

def create_airtime_deposit(user, amount):
	ReferralAdminUser = CustomUser.objects.get(id=config('ReferralUserID'))
	from_account = Account.objects.get(type_of_account=Account.WALLET, user=ReferralAdminUser)
	to_account = Account.objects.get(type_of_account=Account.DIRECT, user=user)
	amount = round(Decimal(amount) * Decimal(0.01), 2)
	transfer = Transaction.objects.create(
		account=from_account,
		type_of_transaction = TransactionOptions.Transfer,
		amount = amount,
		memo = 'Airtime Purchase Bonus'
	)
	transfer.dest_account = to_account
	transfer.data = {}
	transfer.data['transfer_type'] = 'AirtimeBonus'
	transfer.save()
	transfer.process()
	transfer.succeed()



def create_deposit(account, amount, fundsource):
	deposit = Transaction.objects.create(
				account = account,
				amount = amount,
				type_of_transaction= TransactionOptions.Deposit
	)
	deposit.data = {}
	deposit.data['fund_source_id'] = fundsource.id
	deposit.data['type_of_deposit'] = 'QuickSave'
	deposit.save()
	deposit.process()
	paystack = PaystackService()
	response = paystack.charge_card(deposit, fundsource)
	if (response['status'] == True):
		if (response['data']['status'] == 'success'):
			deposit.succeed()
			return response['message'], deposit
	deposit.data['failure_reason'] =  response.get('data')['gateway_response']
	deposit.reject()
	return response['message'], deposit

def create_referral_refund(user, amount):
	ReferralAdminUser = CustomUser.objects.get(id=config('ReferralUserID'))
	from_account = Account.objects.get(type_of_account=Account.WALLET, user=user)
	to_account = Account.objects.get(type_of_account=Account.WALLET, user=ReferralAdminUser)
	if amount > 0:
		transfer = Transaction.objects.create(
			account=from_account,
			type_of_transaction = TransactionOptions.Transfer,
			amount = Decimal(amount),
			memo = '{} Referral Bonus withdrawn'.format(amount) 
		)
		transfer.dest_account = to_account
		transfer.data = {}
		transfer.data['transfer_type'] = 'ReferralBonusWithdraw'
		transfer.save()
		transfer.process()
		transfer.succeed()
	user.is_active=True
	user.save()