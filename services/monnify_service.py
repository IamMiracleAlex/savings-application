from celery import shared_task
import requests
import base64
# from accounts.models import Beneficiary
from celery import shared_task

from decouple import config

BASE_URL = config('MONNIFY_BASE_URL')
MONNIFY_KEY = config('MONNIFY_KEY')
MONNIFY_SECRET = config('MONNIFY_SECRET')
MONNIFY_CONTRACT_CODE = config('MONNIFY_CONTRACT_CODE')


class MonnifyService:
	def create_reserved_accounts(self, user):
		path = '/api/v1/bank-transfer/reserved-accounts/'
		return post_request(path, {
			"accountReference": user.public_id,
			"accountName": user.full_name(),
			"currencyCode": "NGN",
			"contractCode": MONNIFY_CONTRACT_CODE,
			"customerEmail": user.email,
		})

	def verify_transaction(self, t):
		response = requests.get(
			(BASE_URL+'/api/v2/transactions/{}'.format(t.reference)),
			headers = {'Authorization': "Bearer {}".format(auth)}
		).json()
		return response

def post_request(path, data):
	response = requests.post(
		(BASE_URL+path),
		json = data,
		headers = {'Authorization': "Bearer{}".format(authenticate())}
	).json()
	return response

def authenticate():
	login = '{}:{}'.format(MONNIFY_KEY, MONNIFY_SECRET)
	encoded = base64.b64encode(login.encode('utf-8'))
	path = '/api/v1/auth/login'
	response = requests.post(
		(BASE_URL+path),
		headers = {'Authorization': "Basic {}".format(str(encoded, 'utf-8'))}
		).json()
	return response['responseBody']['accessToken']

auth = authenticate()