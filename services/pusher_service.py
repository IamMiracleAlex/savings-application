from celery import shared_task
from pusher import Pusher
from decouple import config

class PusherService:
	def new_transaction(self, transaction):
		from transactions.serializers import TransactionSerializer
		data = {}
		data['account'] = transaction.account.get_type_of_account_display()
		data['data'] = TransactionSerializer(transaction).data
		send_notification.delay(transaction.account.user.public_id, 'transactions', data)
	
	def update_subscription(self, subscription):
		data = {}
		data['data'] = SubscriptionSerializer(subscription).data
		send_notification.delay(deposit.account.user.public_id, 'subscription', data)

	def email_verified(self, user):
		send_notification.delay(user.public_id, 'email_verification', {'email_verified': user.email_verified})

	def add_card(self, fund_source):
		from deposits.serializers import FundSourceSerializer
		data = {}
		data['data'] = FundSourceSerializer(fund_source).data
		send_notification.delay(fund_source.user.public_id, 'add_card', data)


@shared_task
def send_notification(channel, event, data):
	pusher = Pusher(
		app_id=config('PUSHER_APP_ID'), 
		key=config('PUSHER_KEY'), 
		secret=config('PUSHER_SECRET'), 
		cluster=config('PUSHER_CLUSTER')
	)
	pusher.trigger(channel, event, data)
	