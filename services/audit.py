from transactions.models import Transaction
from .monnify_service import *
from .paystack_service import *


def verify_monnify_transactions(transactions):
	transactions = transactions.filter(reference__startswith='MNFY')
	monnify = MonnifyService()
	verified, unverified = [0, 0]
	for transaction in transactions:
		response = monnify.verify_transaction(transaction)
		print(response['responseBody']['paymentStatus'])
		if (response['responseBody']['paymentStatus'] != 'PAID'):
			print(transaction.account.user)
			print(transaction.amount)
			unverified += 1
		else:
			verified += 1
	print("All {} Monnify transactions inspected.\n{} Verified successfully\n{} Unverified".format(verified+unverified, verified, unverified))

def verify_paystack_transactions(transactions):
	transactions = transactions.exclude(reference__startswith='MNFY')
	paystack = PaystackService()
	verified, unverified = [0, 0]
	for transaction in transactions:
		response = paystack.verify_transaction(transaction)
		print(response['data']['status'])
		if (response['data']['status'] != 'success'):
			print(transaction.account.user)
			print(transaction.amount)
			unverified += 1
		else:
			verified += 1
	print("All {} Paystack transactions inspected.\n{} Verified successfully\n{} Unverified".format(verified+unverified, verified, unverified))


def verify_transactions(start_date="2020-08-01", end_date="2020-08-30"):
	transactions =  Transaction.objects.filter(type_of_transaction=0, created_at__range=[start_date, end_date], status=2)
	verify_paystack_transactions(transactions)
	verify_monnify_transactions(transactions)

# users = CustomUser.objects.annotate(Count('referrals')).values_list('phone_number', 'referrals__count', 'is_active', 'first_name', 'last_name')
# for user in users:
# 	if user[1] > 10 and user[2] == True:
# 		"{}, {}, {}, {}".format(user[3], user[4], user[0], user[1])