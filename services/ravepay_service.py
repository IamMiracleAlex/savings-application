from celery import shared_task
import requests

# from accounts.models import Beneficiary
from celery import shared_task

from decouple import config

BASE_URL = config('RAVEPAY_BASE_URL')
RAVEPAY_KEY = config('RAVEPAY_KEY')

class RavepayService:
	def bill_payments(self, payment):
		response = post_request(
			data = {
				'Country': 'NG', 'CustomerId': payment.customer_id, 
				'Reference': payment.reference, 'Amount': payment.amount, 
				'RecurringType': 0, 'IsAirtime': (payment.type_of_biller=='Airtime'), 'BillerName': payment.name_of_biller.upper()
			}
		)
		return response

	def trans_bill_payments(self, payment):
		response = post_request(
			data = {
				'Country': 'NG', 'CustomerId': payment.data['customer_id'], 
				'Reference': payment.reference, 'Amount': int(payment.amount), 
				'RecurringType': 0, 'IsAirtime': (payment.data['type_of_biller']=='Airtime'), 'BillerName': payment.data['name_of_biller'].upper()
			}
		)
		return response

def post_request(data):
	payload = { 
		'secret_key': RAVEPAY_KEY,
		'service': 'fly_buy',
		'service_method': 'post',
		'service_version': 'v1',
		'service_channel': 'rave', 
		'service_payload': data 
	}
	response =  requests.post((BASE_URL), json=payload).json()
	return response