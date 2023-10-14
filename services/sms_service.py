from celery import shared_task
import requests

from celery import shared_task

from decouple import config

BASE_URL = config('BULKSMS_BASE_URL')
BULKSMS_KEY = config('BULKSMS_KEY')

class BulkSMSService:
	def send_sms(self, user, body):
		response = post_request(
			data = { 
				'api_token': BULKSMS_KEY,
				'from': 'SaVests',
				'to': user.phone_number,
				'body': body,
			}
		)
		return response

def post_request(data):
	response =  requests.post((BASE_URL), json=data).json()
	return response