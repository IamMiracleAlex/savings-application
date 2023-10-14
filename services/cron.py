from datetime import date
import logging

from django.utils import timezone

from celery import shared_task

from subscriptions.models import Subscription
from services.paystack_service import PaystackService
from utils.helpers import get_interest
from accounts.models import Account
from safelocks.models import SafeLock
from transfers.models import Transfer
from services.gsuite_service import GsuiteService
from metrics.views import calculate_metrics
from utils.choices import Transaction as TransactionOptions
from deposits.models import FundSource
from transactions.models import Transaction
from decimal import Decimal


logger = logging.getLogger(__name__)


def daily_metrics():
	start_date = timezone.now() - timezone.timedelta(days=1)
	calculate_metrics(start_date=start_date)

def	debit_subscriptions():
	subscriptions = Subscription.objects.filter(is_active=True, next_paydate=date.today())
	paystack = PaystackService()
	for sub in subscriptions:
		deposit = sub.create_deposit()
		fund_source = FundSource.objects.get(id=deposit.data['fund_source_id'])
		resp = paystack.charge_card(deposit, fund_source)
		if (resp.get('status') == True):
			if (resp.get('data') and resp['data']['status'] == 'success'):
				deposit.succeed()
				try:
					safelock = sub.safelock
					safelock.amount += deposit.amount
					safelock.save()
				except Exception as e:
					# logger.error(f'The following error occurred on cron: {e}')
					pass
				sub.previous_paydate = date.today()
			else:
				deposit.data['failure_reason'] = resp.get('data')['gateway_response']
				deposit.reject()
		else:
			deposit.data['failure_reason'] = resp.get('message')
			deposit.data['retry_by'] = resp.get('data')['retry_by']
			deposit.reject()
		sub.set_next_paydate()
		sub.save()
	
def credit_interests():
	direct_accounts = Account.objects.filter(interest_active=True, type_of_account=Account.DIRECT, balance__gt=0.00)
	for account in direct_accounts:
		account.interest_for_today = round(get_interest(account.balance), 2) / Decimal(1.5)
		account.interest += account.interest_for_today
		account.save()

	safelocks = SafeLock.objects.filter(is_active=True)
	for safelock in safelocks:
		interest = round(get_interest(safelock.amount), 2)
		safelock.interest += interest
		account = safelock.account
		account.interest_for_today = interest
		account.interest += interest
		safelock.save()
		account.save()
	
def monthly_interest_run():
	month = timezone.now().strftime('%B')
	accounts = Account.objects.filter(interest_active=True, type_of_account = Account.DIRECT, interest__gt=0.00)
	for account in accounts:
		dest_account = Account.objects.get(type_of_account = Account.WALLET, user = account.user)
		account.balance += account.interest
		interest = account.interest
		account.interest = 0
		account.interest_for_today = 0
		account.save()
		transfer = Transaction.objects.create(
			account = account,
			type_of_transaction = TransactionOptions.Interest,
			amount = interest,
			memo = 'Interest run for {}'.format(month),
			dest_account = dest_account,
		)
		transfer.data = {}
		transfer.data['transfer_type'] = 'InterestRun'
		transfer.process()
		transfer.succeed()

def test_cron():
	subscription = Subscription.objects.last()
	subscription.amount += 200
	subscription.save()

def open_safelocks():
	safelocks = SafeLock.objects.filter(maturity_date__lte=date.today(), is_active=True)
	for safelock in safelocks:
		user = safelock.account.user
		safelock_account = safelock.account
		safelock_account.balance += safelock.interest
		safelock_account.interest -= safelock.interest
		safelock_account.interest_for_today = 0
		safelock_account.save()
		wallet = Account.objects.get(user=user,type_of_account=Account.WALLET)

		transfer_amount = Transaction.objects.create(
			account = safelock_account,
            dest_account = wallet,
            amount = safelock.amount,
			type_of_transaction = TransactionOptions.Transfer,
            memo='SaVests Target: {} matured'.format(safelock.name)
	    )
		transfer_amount.data = {}
		transfer_amount.data['transfer_type'] = 'InternalTransfer'
		transfer_amount.save()
		transfer_amount.process()
		transfer_amount.succeed()

		tranfer_interest = Transaction.objects.create(
			account = safelock_account,
            dest_account = wallet,
            amount = safelock.interest,
			type_of_transaction = TransactionOptions.Interest,
            memo='Interest earned for SaVests Target: {}'.format(safelock.name)
	    )
		tranfer_interest.data = {}
		tranfer_interest.data['transfer_type'] = 'InternalTransfer'
		tranfer_interest.save()
		tranfer_interest.process()
		tranfer_interest.succeed()

		safelock.is_active = False
		safelock.save()
		context = {
			'name': user.first_name,
			'amount': safelock.amount,
			'interest': safelock.interest,
			'total': (safelock.amount+safelock.interest),
			'email': user.email,
			'target_name': safelock.name,
			'date': safelock.maturity_date
		}
		GsuiteService.send_safelock_maturity_mail(context)
