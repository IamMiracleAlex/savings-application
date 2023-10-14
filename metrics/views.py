from django.utils import timezone
from .models import Metric
from users.models import CustomUser
from accounts.models import Account
from django.db.models import Sum
from transactions.models import Transaction, TransactionOptions
from django.db import transaction 

from decouple import config


@transaction.atomic
def calculate_metrics(start_date=timezone.now().today(), end_date=timezone.now().today()):
	transactions = Transaction.objects.filter(status=TransactionOptions.SUCCESS ,created_at__gte = start_date, created_at__lte = end_date)
	deposits = transactions.filter(type_of_transaction=TransactionOptions.Deposit)
	withdraws = transactions.filter(type_of_transaction=TransactionOptions.Withdraw)
	transfers = transactions.filter(type_of_transaction=TransactionOptions.Transfer)
	payments = transactions.filter(type_of_transaction=TransactionOptions.Payment)
	accounts = Account.objects.all()
	interests = accounts.filter(interest_active=True)

	users = CustomUser.objects.filter(created_at__gte = start_date, created_at__lte = end_date)
	metric, _ = Metric.objects.get_or_create(start_date=start_date, end_date=end_date)
	
	metric.new_users = users.count()
	metric.activated_users_count = users.filter(account_activated=True).count() #users with activated account
	
	# Total deposits count and sum
	metric.total_deposits = deposits.count()
	metric.total_deposits_volume = deposits.aggregate(Sum('amount'))['amount__sum'] or 0.0

	# Paystack Deposits
	paystack_deposits = deposits.exclude(reference__startswith='MNFY').exclude(data__contains='ChickenChange')
	metric.total_paystack_deposits = paystack_deposits.count()
	metric.total_paystack_deposits_volume = paystack_deposits.aggregate(Sum('amount'))['amount__sum'] or 0.0
	
	# Monnify Deposits
	monnify_deposits = deposits.filter(reference__startswith='MNFY')
	metric.total_monnify_deposits = monnify_deposits.count()
	metric.total_monnify_deposits_volume = monnify_deposits.aggregate(Sum('amount'))['amount__sum'] or 0.0
	
	# Total withdrawals count and sum
	metric.total_withdraws = withdraws.count()
	metric.total_withdraws_volume = withdraws.aggregate(Sum('amount'))['amount__sum'] or 0.0

	# Total transfers count and sum
	metric.total_transfers = transfers.count()
	metric.total_transfers_volume = transfers.aggregate(Sum('amount'))['amount__sum'] or 0.0
	
	# Chicken Change Deposits
	chicken_change = deposits.filter(data__contains='ChickenChange')
	metric.total_chicken_change_deposits =  chicken_change.count()
	metric.total_chicken_change_deposits_volume = chicken_change.aggregate(Sum('amount'))['amount__sum'] or 0.0

	# Total account balances
	referral_account = accounts.get(user__id=config("ReferralUserID"), type_of_account=Account.WALLET)
	wallet_balance = accounts.filter(type_of_account=Account.WALLET).aggregate(Sum('balance'))['balance__sum'] or 0.0
	metric.wallet_balance = wallet_balance - referral_account.balance
	metric.autosave_balance = accounts.filter(type_of_account=Account.DIRECT).aggregate(Sum('balance'))['balance__sum'] or 0.0
	metric.target_balance = accounts.filter(type_of_account=Account.DEPOSIT).aggregate(Sum('balance'))['balance__sum'] or 0.0
	
	# Total payments count and sum
	metric.total_payments = payments.count()
	metric.total_payments_volume = payments.aggregate(Sum('amount'))['amount__sum'] or 0.00
	
	# Count and sum of ACTIVE interest
	metric.total_accounts_with_interests = interests.count()
	metric.total_interests_for_today = interests.aggregate(Sum('interest_for_today'))['interest_for_today__sum'] or 0.0
	metric.total_interests_volume = interests.aggregate(Sum('interest'))['interest__sum'] or 0.0

	# Count and sum of fees
	metric.bill_payment_fees_volume = payments.filter(fee__gt=0.00).aggregate(Sum('fee'))['fee__sum'] or 0.0
	metric.autosave_breaking_fees_volume = transfers.filter(fee__gt=0.00).aggregate(Sum('fee'))['fee__sum'] or 0.0

	# wallet to autosave transfers - count and sum
	wallet_autosave_transfer = transfers.filter(account__type_of_account=Account.WALLET, dest_account__type_of_account=Account.DIRECT)
	metric.wallet_autosave_transfer_count = wallet_autosave_transfer.count()
	metric.wallet_autosave_transfer_sum = wallet_autosave_transfer.aggregate(Sum('amount'))['amount__sum'] or 0.0

	# Autosave to wallet transfers - count and sum
	autosave_wallet_transfer = transfers.filter(account__type_of_account=Account.DIRECT, dest_account__type_of_account=Account.WALLET)
	metric.autosave_wallet_transfer_count = autosave_wallet_transfer.count()
	metric.autosave_wallet_transfer_sum = autosave_wallet_transfer.aggregate(Sum('amount'))['amount__sum'] or 0.0

	# Wallet to target transfers - count and sum
	wallet_target_transfer = transfers.filter(account__type_of_account=Account.WALLET, dest_account__type_of_account=Account.DEPOSIT)
	metric.wallet_target_transfer_count = wallet_target_transfer.count()
	metric.wallet_target_transfer_sum = wallet_target_transfer.aggregate(Sum('amount'))['amount__sum'] or 0.0

	# Target to wallet transfers - count and sum
	target_wallet_transfer = transfers.filter(account__type_of_account=Account.DEPOSIT, dest_account__type_of_account=Account.WALLET)
	metric.target_wallet_transfer_count = target_wallet_transfer.count()
	metric.target_wallet_transfer_sum = target_wallet_transfer.aggregate(Sum('amount'))['amount__sum'] or 0.0

	# Wallet to wallet transfers - count and sum
	wallet_wallet_transfer = transfers.filter(account__type_of_account=Account.WALLET, dest_account__type_of_account=Account.WALLET)
	metric.wallet_wallet_transfer_count = wallet_wallet_transfer.count()
	metric.wallet_wallet_transfer_sum = wallet_wallet_transfer.aggregate(Sum('amount'))['amount__sum'] or 0.0
	
	# Interests and Bonuses 
	# Referral Bonus
	referral_bonus = transfers.filter(data__contains='ReferralBonus')
	metric.referral_bonus_total = referral_bonus.count()
	metric.referral_bonus_volume = referral_bonus.aggregate(Sum('amount'))['amount__sum'] or 0.0
	# Airtime Bonus	
	airtime_bonus = transfers.filter(data__contains='AirtimeBonus')
	metric.airtime_bonus_total = airtime_bonus.count() 
	metric.airtime_bonus_volume = airtime_bonus.aggregate(Sum('amount'))['amount__sum'] or 0.0
	
	metric.save()