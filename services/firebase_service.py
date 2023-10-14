from celery import shared_task
from push_notifications.models import GCMDevice, APNSDevice

class FirebaseService:
	# def new_transaction(self, transaction):
	# 	message = "Amount: {}\nTransaction Type: {}\nStatus: {}\nDT:{}".format(transaction.amount, transaction.get_type_of_transaction_display(), transaction.get_status_display(), transaction.updated_at)
	# 	send_notification.delay(transaction.account.user.id, "SaVests {} Transaction".format(transaction.get_type_of_transaction_display()), message)
	
	def new_transaction(self, user_id, title, message):
		send_notification.delay(user_id, title, message)


@shared_task
def send_notification(user_id, title, message):
	devices = GCMDevice.objects.filter(user_id=user_id, active=True)
	for device in devices:
		if device and device.user.send_notifications:
			device.send_message(message, extra={"title": title})
	
	devices = APNSDevice.objects.filter(user_id=user_id, active=True)
	for device in devices:
		if device and device.user.send_notifications:
			device.send_message(message={"title" : title, "body" : message})